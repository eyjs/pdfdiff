@echo off
chcp 65001 > nul
title Dev Environment Setup

echo.
echo ========================================
echo   Development Environment Setup
echo ========================================
echo.

cd /d "%~dp0"

REM Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

echo [OK] Python found
python --version

echo.
set /p confirm="Setup development environment? (y/N): "
if /i not "%confirm%"=="y" (
    echo [CANCEL] Setup cancelled.
    pause
    exit /b 0
)

echo.
echo Cleaning old environment...
if exist "venv" rmdir /s /q venv
if exist "build" rmdir /s /q build  
if exist "dist" rmdir /s /q dist

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] venv creation failed
    pause
    exit /b 1
)

echo Installing dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m pip install pyinstaller

echo.
echo Verifying installation...
venv\Scripts\python.exe -c "import cv2, PIL, numpy, fitz, pytesseract, PyInstaller; print('All dependencies OK')"
if errorlevel 1 (
    echo [ERROR] Dependencies verification failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Dev environment ready!
echo ========================================
echo.
echo To activate: venv\Scripts\activate.bat
echo To build: build_user_release.bat
echo.
pause
