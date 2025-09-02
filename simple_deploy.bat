@echo off
chcp 65001 > nul
title Simple Windows Deploy

echo.
echo ========================================
echo   Simple Windows Deploy Script
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv python exists
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
    echo [OK] Using venv Python: %PYTHON_EXE%
) else (
    set PYTHON_EXE=python
    echo [WARNING] Using system Python: %PYTHON_EXE%
)

echo.
set /p confirm="Continue with build? (y/N): "
if /i not "%confirm%"=="y" (
    echo [CANCEL] Build cancelled.
    pause
    exit /b 0
)

echo.
echo Step 1: Clean project...
echo ========================================
%PYTHON_EXE% clean_for_deployment.py

echo.
echo Step 2: Simple build...
echo ========================================
%PYTHON_EXE% simple_build.py

echo.
echo Step 3: Create package...
echo ========================================
%PYTHON_EXE% create_zip_package.py

echo.
echo [DONE] Check the generated files!
pause
