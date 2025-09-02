@echo off
chcp 65001 > nul
title Check Environment

echo.
echo ========================================
echo   Environment Check and Setup
echo ========================================
echo.

REM Check current directory
cd /d "%~dp0"
echo Working Directory: %CD%
echo.

REM Check if venv exists and has python
if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment found
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    
    echo.
    echo Checking Python and pip...
    venv\Scripts\python.exe --version
    
    echo.
    echo Checking PyInstaller...
    venv\Scripts\python.exe -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)"
    if errorlevel 1 (
        echo Installing PyInstaller...
        venv\Scripts\pip.exe install pyinstaller
    ) else (
        echo [OK] PyInstaller already installed
    )
    
) else (
    echo [ERROR] Virtual environment not found or corrupted
    echo Please recreate virtual environment:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Environment ready!
echo You can now run: deploy_windows.bat
echo.
pause
