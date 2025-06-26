@echo off
REM LinkedIn Contact Validator GUI Launcher for Windows (System Python Only)
echo LinkedIn Contact Validator GUI Launcher for Windows
echo ================================================

REM Get the directory where this script is located and change to it
set "SCRIPT_DIR=%~dp0"
echo Script directory: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"

echo Starting GUI with system Python...
python gui_main.py

echo GUI closed.
pause