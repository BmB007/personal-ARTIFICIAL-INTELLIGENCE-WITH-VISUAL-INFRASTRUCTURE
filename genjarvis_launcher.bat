@echo off
title GenJARVIS Launcher
echo Starting GenJARVIS...
echo.

:: Set the path to your Python script
set SCRIPT_PATH=C:\Users\BHARATH\Downloads\genai\gen ai 2 version 2.py

:: Check if the script exists
if not exist "%SCRIPT_PATH%" (
    echo ERROR: Could not find %SCRIPT_PATH%
    echo.
    echo Please ensure that:
    echo 1. The script file exists in the specified location
    echo 2. The filename is spelled correctly
    echo.
    pause
    exit /b 1
)

:: Run the Python script
python "%SCRIPT_PATH%"

:: If Python returns an error
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred while running GenJARVIS.
    echo If you don't have Python installed, please install it from https://www.python.org/downloads/
    echo.
)

pause
