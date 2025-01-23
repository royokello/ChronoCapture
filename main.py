#!/usr/bin/env python3
import os
import time
import argparse
import subprocess
import shutil
from datetime import datetime, timedelta

import mss
import mss.tools

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Continuously record screenshots at a given FPS, archive them daily, and keep only N days of folders."
    )
    parser.add_argument("--fps", type=int, default=1,
                        help="Number of screenshots per second (also used for final video FPS).")
    parser.add_argument("--root_dir", type=str, default=".",
                        help="Root directory to store daily folders and the 'archive' folder.")
    parser.add_argument("--height", type=int, default=512,
                        help="Height of the output video. Width is scaled to maintain aspect ratio.")
    parser.add_argument("--bitrate", type=int, default=1024,
                        help="Video bitrate (e.g., 1024).")
    parser.add_argument("--archive_limit", type=int, default=1,
                        help="Number of days to keep in the main root_dir. Older folders are removed (their videos stay in archive).")
    return parser.parse_args()

def make_sure_dir_exists(dir_path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def get_current_day_folder(root_dir):
    """Return the path to today's folder (YYYY-MM-DD) inside root_dir."""
    day_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(root_dir, day_str)

def archive_day(day_folder, archive_folder, fps, height, bitrate):
    """
    Use ffmpeg to turn all .png files in `day_folder` into a single .mp4 video
    stored in `archive_folder` with filename YYYY-MM-DD.mp4.
    """
    day_name = os.path.basename(day_folder)  # e.g., '2025-01-23'
    output_file = os.path.join(archive_folder, f"{day_name}.mp4")

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite existing file if any
        "-framerate", str(fps),
        "-pattern_type", "glob",
        "-i", os.path.join(day_folder, "*.png"),
        "-vf", f"scale=-2:{height}",
        "-b:v", f"{bitrate}k",
        output_file
    ]

    print(f"[INFO] Archiving {day_folder} -> {output_file}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed to archive {day_folder}: {e}")

def cleanup_old_folders(root_dir, archive_limit):
    """
    Remove day folders in `root_dir` that are older than `archive_limit` days.
    Does NOT remove anything from the 'archive' folder—those .mp4 files remain indefinitely.
    """
    # Determine the set of date strings we want to keep in the main root
    today = datetime.now().date()
    keep_dates = set(
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(archive_limit)
    )

    # Check each item in the root_dir
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        
        # Skip the 'archive' folder itself
        if item == "archive":
            continue
        
        # If it's a directory named YYYY-MM-DD and it's not in keep_dates, remove it
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

def run_recorder(fps, root_dir, height, bitrate, archive_limit):
    """
    Continuously record screenshots at `fps`.
    - Each day is stored in `root_dir/YYYY-MM-DD/`.
    - At midnight (when the day changes), convert the previous day's screenshots to a video in `root_dir/archive/`.
    - Remove folders older than `archive_limit` days from the main root.
    """
    archive_folder = os.path.join(root_dir, "archive")
    make_sure_dir_exists(archive_folder)

    # Prepare today's folder
    current_day_str = datetime.now().strftime("%Y-%m-%d")
    current_day_folder = os.path.join(root_dir, current_day_str)
    make_sure_dir_exists(current_day_folder)

    print("[INFO] Starting screenshot capture...")
    print(f"      FPS: {fps}, Save folder: {root_dir}, Archive limit: {archive_limit} days")

    sleep_interval = 1.0 / fps

    with mss.mss() as sct:
        while True:
            now = datetime.now()
            new_day_str = now.strftime("%Y-%m-%d")

            # If the day changed, archive the old folder, then cleanup old ones
            if new_day_str != current_day_str:
                # Archive the just-finished day
                archive_day(current_day_folder, archive_folder, fps, height, bitrate)

                # Remove old folders beyond the archive limit
                cleanup_old_folders(root_dir, archive_limit)

                # Switch to new day's folder
                current_day_str = new_day_str
                current_day_folder = os.path.join(root_dir, current_day_str)
                make_sure_dir_exists(current_day_folder)

            # Capture a screenshot
            timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
            screenshot_filename = os.path.join(current_day_folder, f"{timestamp}.png")

            screenshot = sct.grab(sct.monitors[1])  # Usually primary display
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_filename)

            time.sleep(sleep_interval)

def main():
    args = parse_arguments()
    run_recorder(
        fps=args.fps,
        root_dir=args.root_dir,
        height=args.height,
        bitrate=args.bitrate,
        archive_limit=args.archive_limit
    )

if __name__ == "__main__":
    main()
