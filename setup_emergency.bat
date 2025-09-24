@echo off
echo Emergency fallback installation script

cd /d "%~dp0"

if exist "venv" rmdir /s /q venv
python -m venv venv

echo Installing minimal working set...
venv\Scripts\python.exe -m pip install --upgrade pip

REM Use conda-forge binaries for problematic packages
venv\Scripts\python.exe -m pip install --index-url https://pypi.anaconda.org/conda-forge/simple/ PyMuPDF
venv\Scripts\python.exe -m pip install opencv-python numpy pillow pytesseract scikit-image
venv\Scripts\python.exe -m pip install pyinstaller pytest psutil

echo Testing installation...
venv\Scripts\python.exe -c "import fitz; print('PyMuPDF OK')"
venv\Scripts\python.exe -c "import cv2; print('OpenCV OK')"
venv\Scripts\python.exe -c "import numpy; print('NumPy OK')"

echo Fallback installation complete!
pause
