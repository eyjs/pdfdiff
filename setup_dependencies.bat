@echo off
chcp 65001 > nul
title Setup Dependencies

echo.
echo ========================================
echo   Installing Dependencies for Build
echo ========================================
echo.

REM Check if we're in virtual environment
if defined VIRTUAL_ENV (
    echo [OK] Virtual environment detected: %VIRTUAL_ENV%
) else (
    echo [WARNING] Not in virtual environment
    echo Recommend activating venv first: venv\Scripts\activate
    echo.
    set /p continue="Continue anyway? (y/N): "
    if /i not "%continue%"=="y" (
        echo [CANCEL] Setup cancelled.
        pause
        exit /b 0
    )
)

echo.
echo Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] PyInstaller installation failed
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Dependencies installed!
echo Now you can run: deploy_windows.bat
echo.
pause
