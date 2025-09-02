@echo off
chcp 65001 > nul
title Clean Rebuild Environment

echo.
echo ========================================
echo   Clean Environment Rebuild
echo ========================================
echo.

cd /d "%~dp0"
echo Working Directory: %CD%
echo.

REM Check Python installation
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

echo [OK] System Python found
python --version
echo.

REM User confirmation
set /p confirm="This will DELETE current venv and recreate it. Continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo [CANCEL] Operation cancelled.
    pause
    exit /b 0
)

echo.
echo ========================================
echo   Cleaning Environment
echo ========================================
echo.

REM Remove existing venv
if exist "venv" (
    echo Removing existing virtual environment...
    rmdir /s /q venv
    echo [OK] Old venv removed
) else (
    echo [INFO] No existing venv found
)

REM Remove build artifacts
if exist "build" (
    echo Removing build directory...
    rmdir /s /q build
    echo [OK] Build directory removed
)

if exist "dist" (
    echo Removing dist directory...
    rmdir /s /q dist
    echo [OK] Dist directory removed
)

if exist "deployment" (
    echo Removing deployment directory...
    rmdir /s /q deployment
    echo [OK] Deployment directory removed
)

if exist "portable" (
    echo Removing portable directory...
    rmdir /s /q portable
    echo [OK] Portable directory removed
)

echo.
echo ========================================
echo   Creating New Environment
echo ========================================
echo.

REM Create new virtual environment
echo Creating new virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARNING] Pip upgrade failed, continuing...
)

REM Install requirements
echo.
echo Installing requirements...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Requirements installation failed
    pause
    exit /b 1
)
echo [OK] Requirements installed

REM Install PyInstaller
echo.
echo Installing PyInstaller...
venv\Scripts\python.exe -m pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] PyInstaller installation failed
    pause
    exit /b 1
)
echo [OK] PyInstaller installed

REM Verify installation
echo.
echo Verifying installation...
venv\Scripts\python.exe -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)"
if errorlevel 1 (
    echo [ERROR] PyInstaller verification failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Environment Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run: fresh_deploy.bat
echo   2. Or manually: python build_for_windows.py
echo.
pause
