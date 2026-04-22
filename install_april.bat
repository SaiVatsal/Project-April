@echo off
title April AI Assistant - Installer
color 0A
cd /d "%~dp0"

echo.
echo  ========================================================
echo       APRIL - Personal AI Assistant Installer
echo  ========================================================
echo.

REM First, ensure pip is installed
echo [Step 1/11] Ensuring pip is installed...
python -m ensurepip --default-pip 2>nul
python -m pip install --upgrade pip 2>nul

REM Check if pip works
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: pip is not available in your Python installation.
    echo.
    echo  Please install pip manually:
    echo    1. Download get-pip.py from https://bootstrap.pypa.io/get-pip.py
    echo    2. Run: python get-pip.py
    echo.
    echo  Or reinstall Python from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo  pip is ready!
echo.

echo [Step 2/11] Installing SpeechRecognition...
python -m pip install SpeechRecognition

echo.
echo [Step 3/11] Installing pyttsx3 (Text-to-Speech)...
python -m pip install pyttsx3

echo.
echo [Step 4/11] Installing GUI packages (pystray, Pillow)...
python -m pip install pystray Pillow

echo.
echo [Step 5/11] Installing data packages (pandas, numpy, requests)...
python -m pip install pandas numpy requests

echo.
echo [Step 6/11] Installing security (cryptography)...
python -m pip install cryptography

echo.
echo [Step 7/11] Installing system control (pyautogui)...
python -m pip install pyautogui

echo.
echo [Step 8/11] Installing screen capture (mss, opencv)...
python -m pip install mss opencv-python

echo.
echo [Step 9/11] Installing market data and utilities...
python -m pip install yfinance schedule python-dotenv

echo.
echo [Step 10/11] Installing optional packages...
python -m pip install pywin32 2>nul
python -m pip install screen-brightness-control 2>nul

echo.
echo [Step 11/11] Installing PyAudio (microphone support)...
python -m pip install PyAudio 2>nul
if errorlevel 1 (
    echo.
    echo  Note: PyAudio installation failed. Voice features may be limited.
    echo  You can try installing it manually later with:
    echo    pip install pipwin ^&^& pipwin install pyaudio
)

echo.
echo  ========================================================
echo       INSTALLATION COMPLETE!
echo  ========================================================
echo.
echo  To start April:
echo    Double-click "run_april.bat"
echo.
echo  Say "Hey April" to activate voice commands!
echo.
pause
