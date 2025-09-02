@echo off
chcp 65001 > nul
title Fresh Start Complete Rebuild

echo.
echo ========================================
echo   COMPLETE FRESH START
echo ========================================
echo.
echo This script will:
echo   1. DELETE current venv completely
echo   2. Remove all build artifacts  
echo   3. Create fresh virtual environment
echo   4. Install all dependencies
echo   5. Build and deploy automatically
echo.

cd /d "%~dp0"

REM Check system Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] System Python not found
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

echo [OK] System Python ready
python --version

echo.
set /p confirm="CONTINUE WITH COMPLETE REBUILD? (y/N): "
if /i not "%confirm%"=="y" (
    echo [CANCEL] Operation cancelled.
    pause
    exit /b 0
)

echo.
echo ========================================
echo   Phase 1: Complete Cleanup
echo ========================================

REM Remove everything
if exist "venv" (
    echo Removing venv...
    rmdir /s /q venv
)

if exist "build" (
    echo Removing build...
    rmdir /s /q build
)

if exist "dist" (
    echo Removing dist...
    rmdir /s /q dist
)

if exist "deployment" (
    echo Removing deployment...
    rmdir /s /q deployment
)

if exist "portable" (
    echo Removing portable...
    rmdir /s /q portable
)

REM Remove temp files
del /q temp_*.pdf 2>nul
del /q *.zip 2>nul
del /q *.spec 2>nul

echo [OK] Cleanup complete

echo.
echo ========================================
echo   Phase 2: Fresh Setup
echo ========================================

REM Create new venv
echo Creating fresh virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] venv creation failed
    pause
    exit /b 1
)

echo [OK] Fresh venv created

REM Upgrade pip
echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Requirements installation failed
    pause
    exit /b 1
)

echo Installing PyInstaller...
venv\Scripts\python.exe -m pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] PyInstaller installation failed
    pause
    exit /b 1
)

echo [OK] All dependencies installed

echo.
echo ========================================
echo   Phase 3: Build and Deploy
echo ========================================

REM Clean
echo Cleaning project...
venv\Scripts\python.exe clean_for_deployment.py

REM Build
echo Building executable...
venv\Scripts\python.exe simple_build.py
if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

REM Package
echo Creating package...
venv\Scripts\python.exe create_zip_package.py

echo.
echo ========================================
echo [SUCCESS] FRESH START COMPLETE!
echo ========================================
echo.
echo Generated files ready for distribution:
dir /b *.zip 2>nul
dir /b dist\*.exe 2>nul
echo.
echo The system is now ready for deployment!
pause
