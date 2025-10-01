@echo off
title PDF Diff v1.0 Release Builder

echo.
echo ========================================
echo   PDF Diff v1.0 - Release Build
echo ========================================
echo.

cd /d "%~dp0"

REM --- Environment Check ---
echo [1/4] Checking environment...
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found.
    echo Please run setup_dev.bat first.
    pause
    exit /b 1
)
if not exist "resources\vendor\tesseract\tesseract.exe" (
    echo [ERROR] Tesseract OCR engine not found in resources folder.
    echo Please ensure Tesseract is correctly placed in 'resources\vendor\tesseract'.
    pause
    exit /b 1
)
echo [OK] Environment is ready.


REM --- Cleaning ---
echo.
echo [2/4] Cleaning previous build artifacts...
if exist "release" rmdir /s /q release
if exist "temp_build" rmdir /s /q temp_build
echo [OK] Cleaned previous builds.


REM --- Building Executable ---
echo.
echo [3/4] Building executable with PyInstaller...

venv\Scripts\python.exe -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "PdfDiff" ^
    --distpath "release" ^
    --workpath "temp_build" ^
    --clean ^
    --add-data "resources;resources" ^
    --add-data "settings.json;." ^
    --add-data "templates.json;." ^
    --add-data "C:\Users\USER\AppData\Local\Programs\Python\Python313\tcl;_tcl_data" ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=app.controllers.validation_controller ^
    main.py

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)
echo [OK] Executable built successfully.


REM --- Finalizing ---
echo.
echo [4/4] Finalizing release package...

REM Clean up temporary files
if exist "temp_build" rmdir /s /q temp_build
del /q "PdfDiff.spec"

echo.
echo ========================================
echo  [SUCCESS] Build Complete!
echo ========================================
echo.
echo The distributable package is located in the 'release' folder.


echo.
pause
