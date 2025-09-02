@echo off
chcp 65001 > nul
title Windows Deploy

echo.
echo ========================================
echo   Windows Deploy Auto Build Script
echo ========================================
echo.

REM Check current directory
cd /d "%~dp0"
echo Working Directory: %CD%
echo.

REM Activate virtual environment if exists
if exist "venv\Scripts\python.exe" (
    echo [OK] Using virtual environment
    set PYTHON_EXE=venv\Scripts\python.exe
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found, using system Python
    set PYTHON_EXE=python
)

REM Check Python
%PYTHON_EXE% --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo [OK] Python found
%PYTHON_EXE% --version

echo.
echo ========================================
echo.

REM User confirmation  
set /p confirm="Continue with cleanup and build? (y/N): "
if /i not "%confirm%"=="y" (
    echo [CANCEL] Operation cancelled.
    pause
    exit /b 0
)

echo.
echo Step 1: Cleaning unnecessary files...
echo ========================================
%PYTHON_EXE% clean_for_deployment.py
if errorlevel 1 (
    echo [ERROR] Cleanup failed
    pause
    exit /b 1
)

echo.
echo Step 2: Building executable...
echo ========================================
%PYTHON_EXE% build_for_windows.py
if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo Step 3: Creating deployment package...
echo ========================================
%PYTHON_EXE% create_zip_package.py
if errorlevel 1 (
    echo [ERROR] Package creation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] All tasks completed!
echo ========================================
echo.
echo Generated files:
echo   - deployment/     (executable and essential files)
echo   - portable/       (portable version)  
echo   - *.zip          (distribution package)
echo.
echo Deployment instructions:
echo   1. Send ZIP file to users
echo   2. Extract and run executable
echo   3. Provide user guide as well
echo.
pause
