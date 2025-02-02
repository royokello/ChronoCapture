import os
import time
import argparse
import subprocess
import shutil
from datetime import datetime, timezone

import mss
import mss.tools
from PIL import Image

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Continuously record screenshots and archive them hourly."
    )
    parser.add_argument("--ffmpeg_path", "-fp", type=str, default="ffmpeg",
                        help="Path to ffmpeg executable (default: 'ffmpeg').")
    parser.add_argument("--timescale", "-ts", type=str, choices=['hour', 'minute'], required=True,
                        help="Timescale for capturing frames (hour or minute).")
    parser.add_argument("--frames", "-f", type=int, required=True,
                        help="Number of frames to capture per timescale unit.")
    parser.add_argument("--root_dir", "-r", type=str, default=".",
                        help="Root directory to store day folders with screenshots and videos.")
    parser.add_argument("--height", "-H", type=int, default=512,
                        help="Height of the output video. Width is scaled to maintain aspect ratio.")
    parser.add_argument("--bitrate", "-b", type=int, default=1024,
                        help="Video bitrate in kilobits (e.g., 1024).")
    parser.add_argument("--archive_limit", "-a", type=int, default=1,
                        help="Number of latest hour directories (for today) to keep. Older hours will be archived and deleted.")
    return parser.parse_args()

def make_sure_dir_exists(dir_path):
    """Ensure that the directory exists."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def archive_hour(day, hour, root_dir, effective_fps, bitrate, ffmpeg_path):
    """
    Archive all PNG images in the hour folder (located at root_dir/day/hour)
    into a video file named '{hour}.mp4' saved in the same day folder.
    Additionally, embed chapter markers into the output video.
    
    Each chapter corresponds to a frame and its title is the timestamp in the format:
         yyyy-mm-dd hh:mm:ss.ssssss
    The timestamp is derived from the image filename which is assumed to be:
         {unix_seconds}{microseconds:06d}.png

    Returns True on success, False otherwise.
    """
    hour_folder = os.path.join(root_dir, day, hour)
    if not os.path.exists(hour_folder):
        print(f"[WARN] Hour folder {hour_folder} does not exist for archiving {day} {hour}. Skipping.")
        return False

    # Gather and sort PNG files.
    image_files = [f for f in os.listdir(hour_folder) if f.endswith(".png")]
    if not image_files:
        print(f"[WARN] No PNG files found in {hour_folder}.")
        return False
    image_files.sort()  # Assumes filenames sort correctly (they are based on a UNIX timestamp)

    # Compute the frame duration (in seconds).
    frame_duration = 1.0 / effective_fps

    # Create a temporary ffconcat file listing all image files.
    concat_file = os.path.join(hour_folder, "filelist.txt")
    with open(concat_file, "w") as f:
        f.write("ffconcat version 1.0\n")
        for i, fname in enumerate(image_files):
            full_path = os.path.join(hour_folder, fname)
            f.write(f"file '{full_path}'\n")
            # For all but the last file, specify the duration.
            if i < len(image_files) - 1:
                f.write(f"duration {frame_duration:.6f}\n")
        # As required by ffconcat, add the last file a second time without a duration.
        last_full_path = os.path.join(hour_folder, image_files[-1])
        f.write(f"file '{last_full_path}'\n")

    # Create a temporary ffmetadata file to hold chapter markers.
    chapters_file = os.path.join(hour_folder, "chapters.txt")
    total_frames = len(image_files)
    total_video_length = total_frames * frame_duration
    with open(chapters_file, "w") as f:
        f.write(";FFMETADATA1\n")
        for i, fname in enumerate(image_files):
            # Calculate chapter start and end times (in seconds)
            start = i * frame_duration
            end = (i + 1) * frame_duration if i < total_frames - 1 else total_video_length
            # Convert to integer microseconds (using TIMEBASE 1/1000000)
            start_us = int(round(start * 1_000_000))
            end_us = int(round(end * 1_000_000))
            # Derive the chapter title from the filename.
            base = os.path.splitext(fname)[0]
            try:
                unix_seconds = int(base[:10])
                microseconds = int(base[10:16])
                dt = datetime.fromtimestamp(unix_seconds, timezone.utc).replace(microsecond=microseconds)
                chapter_title = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            except Exception as e:
                chapter_title = "InvalidTimestamp"
            # Write the chapter block.
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000000\n")
            f.write(f"START={start_us}\n")
            f.write(f"END={end_us}\n")
            f.write(f"title={chapter_title}\n")

    output_file = os.path.join(root_dir, day, f"{hour}.mp4")

    # Use ffmpeg to create the video from the concat file and embed the chapters.
    # By providing the chapters file as a second input and mapping its metadata,
    # the output video will include the chapter markers.
    cmd = [
        ffmpeg_path,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-i", chapters_file,
        "-map_metadata", "1",
        "-b:v", f"{bitrate}k",
        output_file
    ]

    print(f"[INFO] Archiving hour {day} {hour} -> {output_file}")
    try:
        subprocess.run(cmd, check=True)
        success = True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed to archive hour {day} {hour}: {e}")
        success = False

    # Clean up temporary files.
    if os.path.exists(concat_file):
        os.remove(concat_file)
    if os.path.exists(chapters_file):
        os.remove(chapters_file)

    return success

def cleanup_hour_folders(root_dir, archive_limit, ffmpeg_path, effective_fps, bitrate):
    """
    Iterate over all day folders (formatted as YYYY-MM-DD) in the root_dir.
    
    For each day folder:
      - For past days, archive (if needed) and remove all hour folders.
      - For today's folder, keep the latest 'archive_limit' hour folders (excluding the current hour)
        and for older hour folders, archive them (if not already) and then remove the folder.
    
    Note: An hour folder is only removed if its corresponding video file (HH.mp4) exists.
    """
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for day in os.listdir(root_dir):
        day_path = os.path.join(root_dir, day)
        if not os.path.isdir(day_path):
            continue
        # Check if the folder name looks like a date (YYYY-MM-DD).
        try:
            datetime.strptime(day, "%Y-%m-%d")
        except ValueError:
            continue

        # List hour folders (they should be named with two digits, e.g., "00", "01", ..., "23").
        hour_folders = [h for h in os.listdir(day_path)
                        if os.path.isdir(os.path.join(day_path, h)) and h.isdigit() and len(h) == 2]
        if not hour_folders:
            continue
        hour_folders.sort()  # ascending order (e.g., "00", "01", ...)

        if day == today_str:
            # Exclude the current hour since it is still active.
            current_hour = datetime.now(timezone.utc).strftime("%H")
            archivable = [h for h in hour_folders if h != current_hour]
            if len(archivable) > archive_limit:
                to_cleanup = archivable[:-archive_limit]
            else:
                to_cleanup = []
        else:
            # For past days, process all hour folders.
            to_cleanup = hour_folders

        for hour in to_cleanup:
            hour_folder_path = os.path.join(day_path, hour)
            video_file = os.path.join(day_path, f"{hour}.mp4")
            # If the video doesn't exist, try to archive this hour folder.
            if not os.path.exists(video_file):
                print(f"[INFO] Archiving hour {day} {hour} in cleanup...")
                success = archive_hour(day, hour, root_dir, effective_fps, bitrate, ffmpeg_path)
                if not success:
                    print(f"[WARN] Could not archive hour folder {hour_folder_path}. Skipping deletion.")
                    continue
            # Once the video exists, remove the hour folder with images.
            print(f"[INFO] Removing hour folder: {hour_folder_path}")
            shutil.rmtree(hour_folder_path, ignore_errors=True)

def run_recorder(timescale, frames, root_dir, height, bitrate, archive_limit, ffmpeg_path):
    """
    Main loop:
      - Captures screenshots at an effective FPS.
      - Saves screenshots into hourly folders (nested under a day folder).
      - When the hour changes, archives the previous hour folder into a video.
      - Periodically cleans up old hour folders (deleting the images only after archiving).
    """
    # Calculate effective FPS and sleep interval.
    timescale_seconds = 3600 if timescale == 'hour' else 60
    effective_fps = frames / timescale_seconds
    sleep_interval = 1.0 / effective_fps

    # Initialize the folder structure using UTC time.
    utc_now = datetime.now(timezone.utc)
    current_day_str = utc_now.strftime("%Y-%m-%d")
    current_hour_str = utc_now.strftime("%H")
    current_hour_folder = os.path.join(root_dir, current_day_str, current_hour_str)
    make_sure_dir_exists(current_hour_folder)

    print("[INFO] Starting screenshot capture...")
    print(f"       Timescale: {timescale}, Frames per period: {frames}, Effective FPS: {effective_fps:.2f}")
    print(f"       Archive limit (latest hour directories to keep): {archive_limit}")

    with mss.mss() as sct:
        while True:
            utc_now = datetime.now(timezone.utc)
            new_day_str = utc_now.strftime("%Y-%m-%d")
            new_hour_str = utc_now.strftime("%H")

            # If the hour (or day) has changed, archive the completed hour and run cleanup.
            if new_day_str != current_day_str or new_hour_str != current_hour_str:
                print(f"[INFO] Hour change detected. Archiving hour {current_day_str} {current_hour_str}...")
                archive_hour(current_day_str, current_hour_str, root_dir, effective_fps, bitrate, ffmpeg_path)
                cleanup_hour_folders(root_dir, archive_limit, ffmpeg_path, effective_fps, bitrate)

                # Update the current folder to the new day/hour.
                current_day_str = new_day_str
                current_hour_str = new_hour_str
                current_hour_folder = os.path.join(root_dir, current_day_str, current_hour_str)
                make_sure_dir_exists(current_hour_folder)

            # Capture a screenshot.
            utc_now = datetime.now(timezone.utc)
            unix_seconds = int(utc_now.timestamp())
            microseconds = utc_now.microsecond
            screenshot_filename = os.path.join(
                current_hour_folder,
                f"{unix_seconds}{microseconds:06d}.png"
            )

            screenshot = sct.grab(sct.monitors[1])
            with Image.frombytes("RGB", screenshot.size, screenshot.rgb) as img:
                # Resize while maintaining aspect ratio.
                width = int(screenshot.width * (height / screenshot.height))
                resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
                resized_img.save(screenshot_filename, "PNG", optimize=True)

            time.sleep(sleep_interval)

def main():
    args = parse_arguments()
    run_recorder(
        timescale=args.timescale,
        frames=args.frames,
        root_dir=args.root_dir,
        height=args.height,
        bitrate=args.bitrate,
        archive_limit=args.archive_limit,
        ffmpeg_path=args.ffmpeg_path
    )

if __name__ == "__main__":
    main()
