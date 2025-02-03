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
   For example, to capture 15 frames per minute with a 512p (default) resolution:

   ```bash
   python main.py --timescale "minute" --frames 15 --root_dir "Path\\To\\root" --ffmpeg_path "Path\\To\\ffmpeg.exe"
   ```

## Running as a Background Task on Windows

While ChronoCapture is a Python script (and not a native Windows service), you can configure it to run in the background without displaying a command window using Task Scheduler. Follow these steps:

1. **Open Task Scheduler**  
   Press `Win + R`, type `taskschd.msc`, and hit Enter.

2. **Create a New Task**  
   In the Actions pane, click **Create Task...** (avoid using "Create Basic Task" for more control).

3. **General Tab**  
   - **Name**: Enter a name for your task (e.g., `ChronoCapture Background Task`).
   - **Security Options**:  
     - Select **Run whether user is logged on or not**.
     - Check the **Hidden** box to ensure the task runs without displaying a window.

Below is the updated "Actions Tab" section with the sensitive path names replaced by placeholders:

4. **Actions Tab**  
   - Click **New...**.  
   - **Action**: Choose **Start a program**.  
   - **Program/script**: Enter the full path to your Python executable. For example:  
     ```
     C:\Path\To\Your\VirtualEnv\Scripts\python.exe
     ```  
   - **Add arguments (optional)**: Enter the path to your script and all necessary parameters. For example:  
     ```
     "C:\Path\To\Your\Project\main.py" --timescale minute --frames 15 --root_dir "D:\Your\Root\Directory" --ffmpeg_path "D:\Path\To\ffmpeg.exe"
     ```  
   - **Start in (optional)**: Specify the working directory for your script (e.g., the directory where your script resides).

5. **Triggers Tab**  
   - Add a new trigger based on when you want ChronoCapture to run (e.g., **At startup** or on a custom schedule).

6. **Conditions and Settings Tabs**  
   - Adjust these settings as needed for your environment.

7. **Save the Task**  
   - Click **OK** and provide your credentials if prompted.

Once configured, ChronoCapture will run in the background according to the specified trigger—without opening a visible command prompt window.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Pull requests and bug reports are welcome. For major changes, please open an issue first to discuss what you would like to change.
```
