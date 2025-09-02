@echo off
chcp 65001 > nul
title Fresh Deploy

echo.
echo ========================================
echo   Fresh Deploy (Clean Environment)
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv exists and is working
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found
    echo Please run: rebuild_environment.bat
    pause
    exit /b 1
)

REM Test venv python
venv\Scripts\python.exe --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Virtual environment is broken
    echo Please run: rebuild_environment.bat
    pause
    exit /b 1
)

echo [OK] Virtual environment ready
venv\Scripts\python.exe --version

REM Test PyInstaller
venv\Scripts\python.exe -c "import PyInstaller" > nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller not found in venv
    echo Please run: rebuild_environment.bat
    pause
    exit /b 1
)

echo [OK] PyInstaller ready

echo.
set /p confirm="Start fresh build process? (y/N): "
if /i not "%confirm%"=="y" (
    echo [CANCEL] Build cancelled.
    pause
    exit /b 0
)

echo.
echo Step 1: Clean temporary files...
echo ========================================
venv\Scripts\python.exe clean_for_deployment.py

echo.
echo Step 2: Build executable...
echo ========================================
venv\Scripts\python.exe simple_build.py

echo.
echo Step 3: Create deployment package...
echo ========================================
venv\Scripts\python.exe create_zip_package.py

echo.
echo ========================================
echo [SUCCESS] Fresh deploy completed!
echo ========================================
echo.
echo Check the generated files:
echo   - dist/보험서류검증시스템.exe
echo   - deployment/ folder
echo   - *.zip package file
echo.
pause
