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
        description="Continuously record screenshots based on timescale and frames, archive them daily, and keep only N days of folders."
    )
    parser.add_argument("--ffmpeg_path", "-fp", type=str, default="ffmpeg",
                        help="Path to ffmpeg executable (default: 'ffmpeg' from system PATH).")
    parser.add_argument("--timescale", "-ts", type=str, choices=['hour', 'minute'], required=True,
                        help="Timescale for capturing frames (hour or minute).")
    parser.add_argument("--frames", "-f", type=int, required=True,
                        help="Number of frames to capture per timescale unit.")
    parser.add_argument("--root_dir", "-r", type=str, default=".",
                        help="Root directory to store daily folders and the 'archive' folder.")
    parser.add_argument("--height", "-H", type=int, default=512,
                        help="Height of the output video. Width is scaled to maintain aspect ratio.")
    parser.add_argument("--bitrate", "-b", type=int, default=1024,
                        help="Video bitrate (e.g., 1024).")
    parser.add_argument("--archive_limit", "-a", type=int, default=1,
                        help="Number of days to keep in the main root_dir. Older folders are removed (their videos stay in archive).")
    return parser.parse_args()

def make_sure_dir_exists(dir_path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def get_current_day_folder(root_dir):
    """Return the path to today's folder (YYYY-MM-DD) inside root_dir."""
    day_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(root_dir, day_str)

def archive_day(day_folder, archive_folder, effective_fps, bitrate, ffmpeg_path):
    """
    Use ffmpeg to turn all .png files in `day_folder` into a single .mp4 video
    stored in `archive_folder` with filename YYYY-MM-DD.mp4.
    """
    day_name = os.path.basename(day_folder)  # e.g., '2025-01-23'
    output_file = os.path.join(archive_folder, f"{day_name}.mp4")

    input_pattern = os.path.join(day_folder, "*.png").replace('\\', '/')

    # Build ffmpeg command
    cmd = [
        ffmpeg_path,
        "-y",  # Overwrite existing file if any
        "-framerate", str(effective_fps),
        "-pattern_type", "glob",
        "-i", input_pattern,
        "-b:v", f"{bitrate}k",
        output_file
    ]

    print(f"[INFO] Archiving {day_folder} -> {output_file}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed to archive {day_folder}: {e}")

def cleanup_old_folders(root_dir, archive_limit):
    """Remove day folders in `root_dir` older than `archive_limit` days."""
    today = datetime.now().date()
    keep_dates = set(
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(archive_limit)
    )

    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        if item == "archive":
            continue
        if os.path.isdir(item_path) and _looks_like_date(item):
            if item not in keep_dates:
                print(f"[INFO] Removing old folder from main dir: {item_path}")
                shutil.rmtree(item_path, ignore_errors=True)

def _looks_like_date(name):
    """Return True if `name` is in the format YYYY-MM-DD."""
    try:
        datetime.strptime(name, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def run_recorder(timescale, frames, root_dir, height, bitrate, archive_limit, ffmpeg_path):
    """Main loop to capture screenshots and manage archives."""
    archive_folder = os.path.join(root_dir, "archive")
    make_sure_dir_exists(archive_folder)

    # Calculate effective FPS and sleep interval
    timescale_seconds = 3600 if timescale == 'hour' else 60
    effective_fps = frames / timescale_seconds
    sleep_interval = 1.0 / effective_fps

    current_day_str = datetime.now().strftime("%Y-%m-%d")
    current_day_folder = os.path.join(root_dir, current_day_str)
    make_sure_dir_exists(current_day_folder)

    print("[INFO] Starting screenshot capture...")
    print(f"      Timescale: {timescale}, Frames per {timescale}: {frames}, Effective FPS: {effective_fps:.2f}")

    with mss.mss() as sct:
        while True:
            utc_now = datetime.now(timezone.utc)
            new_day_str = utc_now.strftime("%Y-%m-%d")

            if new_day_str != current_day_str:
                archive_day(current_day_folder, archive_folder, effective_fps, bitrate)
                cleanup_old_folders(root_dir, archive_limit)
                current_day_str = new_day_str
                current_day_folder = os.path.join(root_dir, current_day_str)
                make_sure_dir_exists(current_day_folder)

            # Capture screenshot
            utc_now = datetime.now(timezone.utc)
            timestamp = utc_now.strftime("%Y-%m-%dT%H-%M-%S.%f")
            screenshot_filename = os.path.join(current_day_folder, f"{timestamp}.png")

            screenshot = sct.grab(sct.monitors[1])
            with Image.frombytes("RGB", screenshot.size, screenshot.rgb) as img:
                width = int(screenshot.width * (height / screenshot.height))
                resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
                resized_img.save(screenshot_filename, "PNG")

            time.sleep(sleep_interval)

def main():
    args = parse_arguments()
    run_recorder(
        ffmpeg_path=args.ffmpeg_path,
        timescale=args.timescale,
        frames=args.frames,
        root_dir=args.root_dir,
        height=args.height,
        bitrate=args.bitrate,
        archive_limit=args.archive_limit
    )

if __name__ == "__main__":
    main()