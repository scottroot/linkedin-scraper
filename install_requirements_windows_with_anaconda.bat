@echo off
setlocal enabledelayedexpansion

echo Reading .env file for CONDA_ENV variable...

REM Initialize variable
set CONDA_ENV=

REM Read .env file line by line
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

echo Found environment: %CONDA_ENV%

REM Initialize Conda
CALL conda activate %CONDA_ENV%
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment "%CONDA_ENV%"
    pause
    exit /b 1
)

REM Run pip install
echo Installing requirements using pip...
pip install -r requirements.txt

echo.
echo Installation complete.
pause
