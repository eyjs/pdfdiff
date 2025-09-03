@echo off
title User Release Builder

echo.
echo ========================================
echo   Build User Release
echo ========================================
echo.

cd /d "%~dp0"

REM Check environment
if not exist "venv\Scripts\python.exe" (
    echo "[ERROR] Development environment not ready."
    echo "Please run setup_dev.bat first."
    pause
    exit /b 1
)

REM Create required folders automatically
echo "Checking required folders..."

if not exist "vendor" (
    echo "Creating vendor folder..."
    mkdir vendor
)

if not exist "vendor\tesseract" (
    echo "[WARNING] Creating vendor\tesseract folder..."
    mkdir vendor\tesseract
    echo "[INFO] Please add tesseract files to vendor\tesseract."
    echo "[INFO] Otherwise, the OCR feature may not work properly."
)

if not exist "templates" (
    echo "Creating templates folder..."
    mkdir templates
)

if not exist "src" (
    echo "[ERROR] src folder missing - this is a required folder!"
    pause
    exit /b 1
)

if not exist "enhanced_launcher.py" (
    echo "[ERROR] enhanced_launcher.py missing - this is a required file!"
    pause
    exit /b 1
)

echo "[OK] Environment ready"
echo "[OK] Required folders checked/created"

echo.
echo "Build user release package? (y/N): y"
set "confirm=y"
if /i not "%confirm%"=="y" (
    echo "[CANCEL] Build cancelled."
    pause
    exit /b 0
)

echo.
echo ========================================
echo   Building Release
echo ========================================

REM Clean previous builds
if exist "release" (
    echo "Cleaning previous release..."
    rmdir /s /q release
)
if exist "user_package" (
    echo "Cleaning previous user package..."
    rmdir /s /q user_package
)
if exist "temp_build" (
    echo "Cleaning temp build files..."
    rmdir /s /q temp_build
)

REM Create release directory
mkdir release

echo "Building portable EXE with Tesseract..."
 venv\Scripts\python.exe -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "InsuranceDocValidator" ^
    --distpath "release" ^
    --workpath "temp_build" ^
    --clean ^
    --add-data "templates;templates" ^
    --add-data "src;src" ^
    --add-data "vendor;vendor" ^
    --add-data "README.md;." ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.scrolledtext" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "fitz" ^
    --hidden-import "pytesseract" ^
    --hidden-import "skimage" ^
    --hidden-import "skimage.metrics" ^
    enhanced_launcher.py

if errorlevel 1 (
    echo "[ERROR] Build failed"
    echo.
    echo "Common solutions:"
    echo "1. Check if enhanced_launcher.py exists."
    echo "2. Verify all dependencies are installed."
    echo "3. Run setup_dev.bat again."
    pause
    exit /b 1
)

echo "[OK] EXE build complete"

REM Create user package
echo "Creating user package..."
mkdir user_package

REM Check if EXE was created
if not exist "release\InsuranceDocValidator.exe" (
    echo "[ERROR] EXE file not found in release folder."
    dir release\
    pause
    exit /b 1
)

REM Copy executable
copy "release\InsuranceDocValidator.exe" "user_package\"
echo "[OK] EXE file copied to user package."

REM Create simple user guide
(
echo # InsuranceDocValidator v2.0 Usage
echo.

echo ## How to run
echo 1. Double-click InsuranceDocValidator.exe
echo 2. Click "Run" on Windows security warning
echo 3. Set up template and start PDF validation
echo.

echo ## Main features
echo - Template setup: Define validation areas in PDF
echo - Document validation: Check accuracy automatically
echo - Result analysis: Detailed cause analysis on failure
echo.

Contact dev team for issues
) > user_package\usage.txt

REM Create run helper
(
    echo @echo off
    echo title InsuranceDocValidator
    echo cd /d "%%~dp0"
    echo if not exist "InsuranceDocValidator.exe" ^(
    echo   echo [ERROR] Executable not found
    echo   pause
    echo   exit /b 1
    echo ^)
    echo echo [OK] Starting program...
    echo start "" "InsuranceDocValidator.exe"
    echo timeout /t 2 ^>nul
    echo echo [SUCCESS] Program started
) > user_package\run.bat

REM Clean temp build
if exist "temp_build" rmdir /s /q temp_build

REM Get file size
for %%A in ("user_package\InsuranceDocValidator.exe") do set size=%%~zA
set /a sizeMB=%size%/1024/1024

echo.
echo ========================================
echo "[SUCCESS] User release ready!"
echo ========================================
echo.
echo "Package contents:"
dir /b user_package\
echo.
echo "EXE file size: %sizeMB% MB"
echo.
echo "Distribution steps:"
echo "1. ZIP the user_package folder."
echo "2. Send the ZIP file to end users."
echo "3. Users extract the archive and run the EXE or run.bat."
echo.
pause