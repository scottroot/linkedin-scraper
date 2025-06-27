@echo off
echo Installing Python packages from requirements.txt...

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo ERROR: requirements.txt not found in this directory.
    pause
    exit /b 1
)

REM Run pip install
pip install -r requirements.txt

echo.
echo Installation complete.
pause
