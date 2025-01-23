# ChronoCapture

**ChronoCapture** is a powerful yet lightweight tool that records your screen at regular intervals, organizes the images into daily folders, and converts them into videos at real-time speed. Designed to run seamlessly in the background, ChronoCapture provides an organized way to document your screen activity with efficient storage management.

## Features
- **Per-Second Screen Recording**: Capture your screen at a customizable frame rate (e.g., 1 frame per second).
- **Daily Folder Organization**: Screenshots are stored in structured daily directories named by date (`YYYY-MM-DD`).
- **Real-Time Video Creation**: Automatically convert daily screenshots into videos with regular speed playback.
- **Storage Management**: Keep the last *N* days of screenshots while archiving older content as videos.
- **Customizable Output**:
  - Frame rate (FPS) for screenshots and video playback.
  - Video resolution (e.g., 256p, 512p, 1024p) and bitrate (e.g., 512kbps, 1024kbps, 2048kbps).
  - Configurable archive limit to manage storage efficiently.
- **Seamless Automation**: Automatically handles daily rollover and archival tasks.

## Use Cases
- **Activity Logging**: Keep a detailed record of your screen for productivity tracking or compliance purposes.
- **Content Documentation**: Preserve daily workflows, presentations, or processes for future review.
- **Long-Term Monitoring**: Record screen usage for extended periods with minimal manual intervention.

## Getting Started
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the recorder:
  ```bash
  python main.py --fps 1 --root_dir /path/to/recordings --height 512 --bitrate 1024 --archive_limit 3
  ```

4. View your daily folders or check the archive folder for automatically generated videos.