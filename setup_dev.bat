@echo off
chcp 65001 > nul
title Dev Environment Setup - Fixed

echo.
echo ========================================
echo   Development Environment Setup (Fixed)
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

echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo Installing core dependencies first...
venv\Scripts\python.exe -m pip install numpy==1.26.4
venv\Scripts\python.exe -m pip install Pillow==11.3.0

echo.
echo Installing computer vision libraries...
venv\Scripts\python.exe -m pip install opencv-python==4.8.1.78
venv\Scripts\python.exe -m pip install scikit-image==0.25.2

echo.
echo Installing OCR library...
venv\Scripts\python.exe -m pip install pytesseract==0.3.10

echo.
echo Installing PDF processing (this may take a while)...
venv\Scripts\python.exe -m pip install PyMuPDF==1.26.4

echo.
echo Installing development tools...
venv\Scripts\python.exe -m pip install pyinstaller
venv\Scripts\python.exe -m pip install pytest==7.4.3 black==23.11.0 flake8==6.1.0 psutil==5.9.6

echo.
echo Verifying installation...
venv\Scripts\python.exe -c "import cv2, PIL, numpy, fitz, pytesseract, PyInstaller; print('All dependencies OK')"
if errorlevel 1 (
    echo [ERROR] Dependencies verification failed
    echo Trying alternative approach...
    goto :alternative_install
)

goto :success

:alternative_install
echo.
echo Trying with pre-compiled wheels...
venv\Scripts\python.exe -m pip install --only-binary=all PyMuPDF
venv\Scripts\python.exe -c "import cv2, PIL, numpy, fitz, pytesseract, PyInstaller; print('All dependencies OK')"
if errorlevel 1 (
    echo [ERROR] Alternative installation also failed
    echo Manual intervention required
    pause
    exit /b 1
)

:success
echo.
echo ========================================
echo [SUCCESS] Dev environment ready!
echo ========================================
echo.
echo To activate: venv\Scripts\activate.bat
echo To run app: venv\Scripts\python.exe main.py
echo To build: build_user_release.bat
echo.
echo Installed package versions:
venv\Scripts\python.exe -c "import fitz, cv2, numpy; print(f'PyMuPDF: {fitz.VersionBind}'); print(f'OpenCV: {cv2.__version__}'); print(f'NumPy: {numpy.__version__}')"
echo.
pause
