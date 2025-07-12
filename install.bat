@echo off
title FortniteAPI Setup - GLOBAL
color 0A

echo [GLOBAL Setup] Checking for Python...

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found. Downloading installer...
    powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe -OutFile python_installer.exe"
    echo [*] Installing Python silently...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
    del python_installer.exe
    echo [✓] Python installed successfully. Please restart this script.
    pause
    exit /b
)

echo [GLOBAL Setup] Installing required Python packages...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt

echo.
echo [✓] GLOBAL Fortnite API GUI is ready!
echo ----------------------------------------
echo Launching the GUI now...
echo ----------------------------------------
python gui.py
pause
