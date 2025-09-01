@echo off
echo ==================================================
echo  PDFDiff Setup
echo ==================================================

echo.
echo [1/4] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python and add it to your PATH.
    goto :eof
)
echo Python found.

echo.
echo [2/4] Creating virtual environment ('venv')...
if not exist venv (
    python -m venv venv
)
echo Virtual environment created.

echo.
echo [3/4] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo [4/4] Setup complete!
echo To run the application, execute 'run.py'.
echo ==================================================
echo.
pause
