@echo off
cd /d "%~dp0"

REM Use Python from installation path
set PYTHON_PATH="C:\Users\Sai Vatsal\AppData\Local\Python\pythoncore-3.14-64\python.exe"

if exist %PYTHON_PATH% (
    start /min "" %PYTHON_PATH% april.py
) else (
    start /min "" python april.py
)

