@echo off
chcp 65001 > nul
title Install PyInstaller

echo.
echo ========================================
echo   Installing PyInstaller
echo ========================================
echo.

REM Use virtual environment python directly
if exist "venv\Scripts\python.exe" (
    echo [OK] Using virtual environment Python
    echo Installing PyInstaller...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install pyinstaller
    
    if errorlevel 1 (
        echo [ERROR] PyInstaller installation failed
        echo Trying alternative installation...
        venv\Scripts\python.exe -m pip install --user pyinstaller
    )
    
    echo.
    echo Verifying installation...
    venv\Scripts\python.exe -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)"
    
    if errorlevel 1 (
        echo [ERROR] PyInstaller verification failed
        pause
        exit /b 1
    )
    
    echo [SUCCESS] PyInstaller installed successfully!
    
) else (
    echo [ERROR] Virtual environment not found
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

echo.
echo You can now run: deploy_windows.bat
pause
