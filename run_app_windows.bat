@echo off
REM LinkedIn Contact Validator GUI Launcher for Windows
REM This script automatically detects conda availability and launches the GUI appropriately

echo LinkedIn Contact Validator GUI Launcher for Windows
echo ================================================

REM Get the directory where this script is located and change to it
set "SCRIPT_DIR=%~dp0"
echo Script directory: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"

REM Function to check if conda is available
call :check_conda
if %errorlevel% equ 0 (
    echo ✓ Conda detected

    REM Check if scraper environment exists
    call :check_scraper_env
    if %errorlevel% equ 0 (
        echo ✓ Conda environment 'scraper' found
        echo Activating conda environment 'scraper'...

        REM Activate the scraper environment
        call conda activate scraper

        if %errorlevel% equ 0 (
            echo ✓ Environment activated successfully!
            echo Starting GUI with conda environment...
            echo Current directory: %cd%
            echo Looking for: %cd%\gui_main.py
            python gui_main.py
        ) else (
            echo ✗ Failed to activate conda environment 'scraper'
            echo Falling back to system Python...
            python gui_main.py
        )
    ) else (
        echo ⚠ Conda environment 'scraper' not found
        echo Using system Python instead...
        python gui_main.py
    )
) else (
    echo ⚠ Conda not detected
    echo Using system Python...
    python gui_main.py
)

echo GUI closed.
pause
goto :eof

:check_conda
conda --version >nul 2>&1
if %errorlevel% equ 0 (
    exit /b 0
) else (
    exit /b 1
)

:check_scraper_env
conda env list | findstr /c:"scraper" >nul 2>&1
if %errorlevel% equ 0 (
    exit /b 0
) else (
    exit /b 1
)