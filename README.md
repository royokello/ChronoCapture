# ChronoCapture

**ChronoCapture** is a lightweight tool that records your screen at configurable intervals, organizes the images into daily (or hourly) folders, and converts them into videos for archival. Designed to run seamlessly in the background, ChronoCapture provides an organized way to document your screen activity with efficient storage management.

## Features

- **Flexible Capture Scheduling**: Configure frames per timescale (hour/minute) instead of a fixed FPS.
- **Daily or Hourly Folder Organization**: Screenshots are stored in structured directories (e.g., `YYYY-MM-DD` or parted by hour).
- **Automatic Video Archiving**: Convert screenshots into timestamped MP4 videos.
- **Storage Management**: Keep recent days/hours while archiving older content.
- **Customizable Output**:
  - Video resolution (height) and bitrate.
  - Custom `ffmpeg` executable path support.
  - Configurable archive retention policy (`archive_limit`).

## Use Cases

- **Machine Learning**: Provide contextual screen data for model training.
- **Activity Auditing**: Maintain compliance records for regulated workflows.
- **Process Documentation**: Capture repetitive workflows for training/analysis.
- **Long-Term Monitoring**: Record screen activity for days or weeks with minimal storage overhead.

## Getting Started

1. **Clone the Repository**
   Clone this repository to your local machine.

2. **Create and Activate a Virtual Environment**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Recorder**
   For example, to capture 15 frames per minute with a 512p resolution and a 2-day retention policy:

   ```bash
   python main.py --timescale "minute" --frames 15 --root_dir "Path\\To\\root" --ffmpeg_path "Path\\To\\ffmpeg.exe"
   ```

## Running as a Windows Service

You can configure ChronoCapture to run as a Windows service so that it starts automatically when the system boots.

Below is an example of creating a Windows service manually using `sc create`.

1. **Determine Your Python Interpreter Path**
   Decide which Python installation (system-wide or virtual environment) will run ChronoCapture. For example:

   - System-wide: `C:\Python39\python.exe`
   - Virtual environment: `C:\Path\To\ChronoCapture\venv\Scripts\python.exe`

2. **Create the Service via `sc create`**
   Open an elevated Command Prompt (Run as Administrator) and run:

   ```cmd
   sc create ChronoCaptureService binPath= "Path\\To\\Python.exe\" \"Path\\To\\ChronoCapture\\main.py\" --timescale "minute" --frames 15 --root_dir "Path\\To\\root" --ffmpeg_path "Path\\To\\ffmpeg.exe"
   ```

   **Explanation**:
   - `ChronoCaptureService` is the name of the Windows service.
   - `binPath=` must include the path to your chosen Python, followed by the path to `main.py` and ChronoCapture's arguments.
   - `start= auto` configures the service to start automatically on system boot.

   **Important**:
   - Pay attention to **double quotes** and **escaping backslashes**. If your paths have spaces, ensure they're properly quoted.
   - The example above sets up ChronoCapture to capture 15 images per hour and archive them hourly, storing data in `C:\recordings`.

3. **Start the Service**

   ```cmd
   net start ChronoCaptureService
   ```

   The service should begin running in the background. Verify that new screenshots and archived videos appear in the specified location.

4. **Managing the Service**
   - **Stop the service**:
     ```cmd
     net stop ChronoCaptureService
     ```
   - **Remove the service** (if no longer needed):
     ```cmd
     sc delete ChronoCaptureService
     ```

5. **Logs & Troubleshooting**
   - Check `sc query ChronoCaptureService` for status.
   - Use **Services** under Windows **Administrative Tools** to manage start/stop or set recovery options.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Pull requests and bug reports are welcome. For major changes, please open an issue first to discuss what you would like to change.

