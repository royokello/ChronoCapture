#!/usr/bin/env python3
import os
import time
import argparse
import subprocess
import shutil
from datetime import datetime, timedelta, timezone

import mss
import mss.tools

from PIL import Image

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Continuously record screenshots and archive them based on a specified period (day or hour)."
    )
    parser.add_argument("--ffmpeg_path", "-fp", type=str, default="ffmpeg",
                        help="Path to ffmpeg executable (default: 'ffmpeg').")
    parser.add_argument("--timescale", "-ts", type=str, choices=['hour', 'minute'], required=True,
                        help="Timescale for capturing frames (hour or minute).")
    parser.add_argument("--frames", "-f", type=int, required=True,
                        help="Number of frames to capture per timescale unit.")
    parser.add_argument("--root_dir", "-r", type=str, default=".",
                        help="Root directory to store screenshot folders and the 'archive' folder.")
    parser.add_argument("--height", "-H", type=int, default=512,
                        help="Height of the output video. Width is scaled to maintain aspect ratio.")
    parser.add_argument("--bitrate", "-b", type=int, default=1024,
                        help="Video bitrate in kilobits (e.g., 1024).")
    parser.add_argument("--archive_limit", "-a", type=int, default=1,
                        help="Number of periods (days or hours) to keep in the main root_dir. Older images are removed.")
    parser.add_argument("--archive_period", "-ap", type=str, choices=['day', 'hour'], default='day',
                        help="Period for archiving: 'day' for daily archiving, 'hour' for hourly archiving.")
    return parser.parse_args()

def make_sure_dir_exists(dir_path):
    """Create the directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def archive_day(day_folder, archive_folder, effective_fps, bitrate, ffmpeg_path):
    """
    Archive all PNG files in day_folder into a single video named YYYY-MM-DD.mp4
    placed directly in the archive_folder.
    """
    day_name = os.path.basename(day_folder)
    output_file = os.path.join(archive_folder, f"{day_name}.mp4")
    input_pattern = os.path.join(day_folder, "*.png").replace('\\', '/')
    
    cmd = [
        ffmpeg_path,
        "-y",  # overwrite output file if exists
        "-framerate", str(effective_fps),
        "-pattern_type", "glob",
        "-i", input_pattern,
        "-b:v", f"{bitrate}k",
        output_file
    ]

    print(f"[INFO] Archiving day {day_name} -> {output_file}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed to archive day {day_name}: {e}")

def archive_hour(period_str, root_dir, archive_folder, effective_fps, bitrate, ffmpeg_path):
    """
    Archive PNG files for a given hour (period_str formatted as YYYY-MM-DDT%H).
    The screenshots for that hour are assumed to be stored in the day folder.
    The resulting video is saved in archive/<day>/<hour>.mp4.
    """
    try:
        day, hour = period_str.split("T")
    except ValueError:
        print(f"[ERROR] Invalid period string: {period_str}")
        return

    day_folder = os.path.join(root_dir, day)
    if not os.path.exists(day_folder):
        print(f"[WARN] Day folder {day_folder} does not exist for archiving hour {period_str}. Skipping.")
        return

    # Look for screenshots that begin with "YYYY-MM-DDT%H-"
    input_pattern = os.path.join(day_folder, f"{period_str}-*.png").replace('\\', '/')
    
    # Create an archive subfolder for this day if necessary.
    day_archive_folder = os.path.join(archive_folder, day)
    make_sure_dir_exists(day_archive_folder)
    
    output_file = os.path.join(day_archive_folder, f"{hour}.mp4")
    
    cmd = [
        ffmpeg_path,
        "-y",
        "-framerate", str(effective_fps),
        "-pattern_type", "glob",
        "-i", input_pattern,
        "-b:v", f"{bitrate}k",
        output_file
    ]

    print(f"[INFO] Archiving hour {period_str} -> {output_file}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed to archive hour {period_str}: {e}")

def cleanup_old_images(root_dir, archive_limit, archive_period):
    """
    Remove old screenshots from the main root_dir.
    For daily archiving, remove whole day folders older than the cutoff date.
    For hourly archiving, remove individual screenshots older than the cutoff time.
    """
    now = datetime.now(timezone.utc)
    if archive_period == 'day':
        cutoff_date = (now - timedelta(days=archive_limit)).date()
        # Iterate over items in root_dir and remove any day folder older than cutoff_date.
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if item == "archive":
                continue
            if os.path.isdir(item_path) and _looks_like_date(item):
                try:
                    folder_date = datetime.strptime(item, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if folder_date < cutoff_date:
                    print(f"[INFO] Removing old folder: {item_path}")
                    shutil.rmtree(item_path, ignore_errors=True)
    else:  # archive_period == 'hour'
        cutoff_time = now - timedelta(hours=archive_limit)
        # For each day folder, check each PNG file's timestamp.
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if item == "archive":
                continue
            if os.path.isdir(item_path) and _looks_like_date(item):
                for filename in os.listdir(item_path):
                    if filename.endswith(".png"):
                        ts_str = filename[:-4]  # remove ".png"
                        try:
                            ts = datetime.strptime(ts_str, "%Y-%m-%dT%H-%M-%S.%f")
                            ts = ts.replace(tzinfo=timezone.utc)
                        except ValueError:
                            continue
                        if ts < cutoff_time:
                            full_path = os.path.join(item_path, filename)
                            print(f"[INFO] Removing old screenshot: {full_path}")
                            os.remove(full_path)
                # Remove the day folder if it is empty.
                if not os.listdir(item_path):
                    print(f"[INFO] Removing empty folder: {item_path}")
                    os.rmdir(item_path)

def _looks_like_date(name):
    """Return True if the folder name is formatted as YYYY-MM-DD."""
    try:
        datetime.strptime(name, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def run_recorder(timescale, frames, root_dir, height, bitrate, archive_limit, ffmpeg_path, archive_period):
    """
    Main loop:
      - Captures screenshots at an effective FPS.
      - Archives images when the current archive period (day or hour) changes.
      - Removes old images based on archive_limit.
    """
    archive_folder = os.path.join(root_dir, "archive")
    make_sure_dir_exists(archive_folder)
    
    # Calculate effective FPS and sleep interval.
    timescale_seconds = 3600 if timescale == 'hour' else 60
    effective_fps = frames / timescale_seconds
    sleep_interval = 1.0 / effective_fps

    # For saving screenshots, always use a daily folder based on UTC date.
    current_day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current_day_folder = os.path.join(root_dir, current_day_str)
    make_sure_dir_exists(current_day_folder)

    # Initialize current_period based on archive_period.
    if archive_period == 'day':
        current_period = current_day_str
    else:
        current_period = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")

    print("[INFO] Starting screenshot capture...")
    print(f"       Timescale: {timescale}, Frames per period: {frames}, Effective FPS: {effective_fps:.2f}")
    print(f"       Archive period: {archive_period}, Archive limit: {archive_limit}")

    with mss.mss() as sct:
        while True:
            utc_now = datetime.now(timezone.utc)
            new_day_str = utc_now.strftime("%Y-%m-%d")
            # Update the day folder if the day has changed.
            if new_day_str != current_day_str:
                current_day_str = new_day_str
                current_day_folder = os.path.join(root_dir, current_day_str)
                make_sure_dir_exists(current_day_folder)

            # Determine the new period string.
            if archive_period == 'day':
                new_period = new_day_str
            else:
                new_period = utc_now.strftime("%Y-%m-%dT%H")

            # If the period has changed, archive the screenshots for the previous period.
            if new_period != current_period:
                if archive_period == 'day':
                    # Archive the previous day folder.
                    prev_day = current_period
                    prev_day_folder = os.path.join(root_dir, prev_day)
                    if os.path.exists(prev_day_folder):
                        archive_day(prev_day_folder, archive_folder, effective_fps, bitrate, ffmpeg_path)
                    else:
                        print(f"[WARN] Expected day folder {prev_day_folder} not found for archiving.")
                else:
                    # Archive the previous hour's images.
                    archive_hour(current_period, root_dir, archive_folder, effective_fps, bitrate, ffmpeg_path)
                # Clean up images that are older than the archive limit.
                cleanup_old_images(root_dir, archive_limit, archive_period)
                current_period = new_period

            # Capture a screenshot.
            utc_now = datetime.now(timezone.utc)
            timestamp = utc_now.strftime("%Y-%m-%dT%H-%M-%S.%f")
            screenshot_filename = os.path.join(current_day_folder, f"{timestamp}.png")

            screenshot = sct.grab(sct.monitors[1])
            with Image.frombytes("RGB", screenshot.size, screenshot.rgb) as img:
                # Resize while maintaining aspect ratio.
                width = int(screenshot.width * (height / screenshot.height))
                resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
                resized_img.save(screenshot_filename, "PNG")

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
        ffmpeg_path=args.ffmpeg_path,
        archive_period=args.archive_period
    )

if __name__ == "__main__":
    main()
