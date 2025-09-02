### ## 2단계: 자동 빌드 스크립트 생성 (`create_release.bat`)

기존 스크립트를 개선하여, **Tesseract 폴더를 포함**하고 최종적으로 **zip 파일까지 생성**하는 새로운 `create_release.bat` 파일을 제공합니다.

```batch:원클릭 배포 스크립트:create_release.bat
@echo off
cd /d "%~dp0"

echo ==========================================
echo  PDF 검증 시스템 - 최종 사용자 배포판 빌드
echo ==========================================
echo.

REM 가상환경 확인
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] 가상환경(venv)을 찾을 수 없습니다. one_click_setup.bat을 먼저 실행하세요.
    pause
    exit /b 1
)
call venv\Scripts\activate.bat

REM PyInstaller 설치 확인
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller를 설치합니다...
    pip install pyinstaller >nul
)

REM Tesseract 폴더 확인
if not exist "vendor\tesseract\tesseract.exe" (
    echo [ERROR] Tesseract 엔진을 찾을 수 없습니다.
    echo         DEPLOYMENT_GUIDE.md를 참고하여 'vendor\tesseract' 폴더를 구성해주세요.
    pause
    exit /b 1
)

echo [1/4] 빌드 환경 정리 중...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "release" rmdir /s /q "release"
if exist "PDF_Validator_*.zip" del "PDF_Validator_*.zip"

echo [2/4] PyInstaller로 실행 파일 빌드 중... (시간이 다소 소요될 수 있습니다)
pyinstaller --noconsole ^
    --name PDF_Validator ^
    --add-data "src;src" ^
    --add-data "templates.json;." ^
    --add-data "vendor/tesseract;tesseract" ^
    --hidden-import "pytesseract" ^
    --hidden-import "skimage.metrics" ^
    enhanced_launcher.py

if errorlevel 1 (
    echo [ERROR] PyInstaller 빌드에 실패했습니다. 오류 메시지를 확인해주세요.
    pause
    exit /b 1
)

echo [3/4] 사용자 배포 패키지 구성 중...
mkdir "release"
mkdir "release\input"
mkdir "release\output"
mkdir "release\templates"

move "dist\PDF_Validator" "release\system_files" >nul
copy "templates.json" "release\" >nul

REM 사용자용 실행 스크립트 생성
echo @echo off > "release\PDF 검증 시스템 시작.bat"
echo echo PDF 검증 시스템을 시작합니다... >> "release\PDF 검증 시스템 시작.bat"
echo start "" "system_files\PDF_Validator.exe" >> "release\PDF 검증 시스템 시작.bat"

echo [4/4] 최종 배포용 ZIP 파일 생성 중...
set VERSION=v1.0
powershell "Compress-Archive -Path 'release\*' -DestinationPath 'PDF_Validator_%VERSION%.zip' -Force"

echo.
echo ==========================================
echo      🎉 배포판 생성이 완료되었습니다! 🎉
echo ==========================================
echo.
echo - 생성된 파일: PDF_Validator_%VERSION%.zip
echo - 이 압축 파일을 사용자에게 전달하고, 압축 해제 후
echo   "PDF 검증 시스템 시작.bat" 파일을 실행하도록 안내하세요.
echo.
pause