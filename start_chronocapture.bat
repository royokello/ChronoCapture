@echo off
REM ============================
REM ChronoCapture Service Script
REM ============================
REM Usage:
REM start_chronocapture.bat <code_dir> <image_dir> <height> <bitrate> <fps> <archive_limit>

REM Check if all arguments are provided
IF "%~6"=="" (
    echo Usage: start_chronocapture.bat ^<code_dir^> ^<image_dir^> ^<height^> ^<bitrate^> ^<fps^> ^<archive_limit^>
    exit /b 1
)

REM Parse arguments
SET code_dir=%~1
SET image_dir=%~2
SET height=%~3
SET bitrate=%~4
SET fps=%~5
SET archive_limit=%~6

REM Activate virtual environment
cd /d "%code_dir%"
call venv\Scripts\activate

REM Start ChronoCapture
python main.py --fps %fps% --root_dir "%image_dir%" --height %height% --bitrate %bitrate% --archive_limit %archive_limit%
