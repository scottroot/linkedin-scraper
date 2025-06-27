@echo off
REM LinkedIn Contact Validator GUI Launcher for Windows (Conda Environment)

echo LinkedIn Contact Validator GUI Launcher for Windows
echo ================================================

REM Get the directory where this script is located and change to it
set "SCRIPT_DIR=%~dp0"
echo Script directory: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"

REM Read CONDA_ENV from .env file
setlocal enabledelayedexpansion
set CONDA_ENV=

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /i "%%A"=="CONDA_ENV" (
        set CONDA_ENV=%%B
    )
)

if "%CONDA_ENV%"=="" (
    echo ERROR: CONDA_ENV not found in .env file.
    pause
    exit /b 1
)

echo Activating conda environment: %CONDA_ENV%

CALL conda activate %CONDA_ENV%
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment "%CONDA_ENV%"
    pause
    exit /b 1
)

echo Starting GUI using conda environment...
python gui_main.py

echo GUI closed.
pause
