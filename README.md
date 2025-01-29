# ChronoCapture

**ChronoCapture** is a lightweight tool that records your screen at configurable intervals, organizes the images into daily folders, and converts them into videos for archival. Designed to run seamlessly in the background, ChronoCapture provides an organized way to document your screen activity with efficient storage management.

## Features
- **Flexible Capture Scheduling**: Configure frames per timescale (hour/minute) instead of fixed FPS
- **Daily Folder Organization**: Screenshots stored in structured daily directories (`YYYY-MM-DD`)
- **Automatic Video Archiving**: Convert daily screenshots into timestamped MP4 videos
- **Storage Management**: Keep recent days' folders while archiving older content
- **Customizable Output**:
  - Video resolution (height) and bitrate
  - Custom ffmpeg executable path support
  - Configurable archive retention policy
- **Background Service Support**: Run continuously as Windows service

## Use Cases
- **Machine Learning**: Provide contextual screen data for model training
- **Activity Auditing**: Maintain compliance records for regulated workflows
- **Process Documentation**: Capture repetitive workflows for training/analysis
- **Long-Term Monitoring**: Record screen activity for days/weeks with minimal storage

## Getting Started

1. Clone this repository  
2. Create and activate virtual environment:  
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```
4. Run the recorder:  
   ```bash
   python main.py -ts "minute" -f 15 -r /recordings -H 512 -b 1024 -a 2
   ```  
   *(Captures 15 frames per minute, 512p resolution, 2-day retention)*

5. Archived videos appear in `/recordings/archive` daily

## Services

### Windows Background Service

Run ChronoCapture continuously using Windows Service Manager:

1. **Install NSSM (Non-Sucking Service Manager)**  
   Download from [https://nssm.cc](https://nssm.cc) and add to PATH

2. **Create Service**  
   ```cmd
   nssm install ChronoCapture
   ```
   Configure parameters in GUI:
   - Path: `C:\Path\to\python.exe`
   - Arguments: `C:\Path\to\main.py -ts "minute" -f 15 -H 512 -b 1024 -a 2`
   - Startup Directory: Your project path

3. **Start Service**  
   ```cmd
   nssm start ChronoCapture
   ```

4. **Configure Automatic Restart**  
   In NSSM GUI > Exit tab:  
   - Set "Application Exit" to Restart  
   - Restart delay: `5000ms`

**Service Features**:  
- Auto-start on system boot  
- Graceful recovery from crashes  
- Logs stored in Event Viewer  
- Resource usage limits configurable in NSSM 
