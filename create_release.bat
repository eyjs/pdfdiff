@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==========================================
echo PDF 검증 시스템 - 사용자 배포 빌드
echo ==========================================
echo.

REM 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    echo [1/8] 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else if exist "pdf_env\Scripts\activate.bat" (
    call pdf_env\Scripts\activate.bat
) else (
    echo [ERROR] 가상환경을 찾을 수 없습니다. one_click_setup.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

REM PyInstaller 설치
echo [2/8] PyInstaller 설치 중...
pip install pyinstaller pillow-heif >nul 2>&1

REM 빌드 디렉토리 정리
echo [3/8] 빌드 환경 준비 중...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "release_package" rmdir /s /q "release_package" >nul 2>&1

REM 메인 시스템 빌드
echo [4/8] 메인 시스템 빌드 중...
pyinstaller --onefile --windowed ^
    --name "PDF_검증_시스템" ^
    --distpath "dist" ^
    --add-data "src;src" ^
    --add-data "templates.json;." ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.scrolledtext" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "fitz" ^
    --hidden-import "pytesseract" ^
    --hidden-import "skimage.metrics" ^
    run.py >nul 2>&1

if errorlevel 1 (
    echo [ERROR] 메인 시스템 빌드 실패
    pause
    exit /b 1
)

REM ROI 선택 도구 빌드
echo [5/8] ROI 선택 도구 빌드 중...
pyinstaller --onefile --windowed ^
    --name "영역_선택_도구" ^
    --distpath "dist" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.simpledialog" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "fitz" ^
    src/roi_selector.py >nul 2>&1

REM PDF 검증 도구 빌드
echo [6/8] PDF 검증 도구 빌드 중...
pyinstaller --onefile --windowed ^
    --name "PDF_검증_도구" ^
    --distpath "dist" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.scrolledtext" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "fitz" ^
    --hidden-import "pytesseract" ^
    --hidden-import "skimage.metrics" ^
    src/pdf_validator_gui.py >nul 2>&1

REM 사용자 배포 패키지 생성
echo [7/8] 사용자 배포 패키지 생성 중...
mkdir "release_package"
mkdir "release_package\templates"
mkdir "release_package\output"
mkdir "release_package\docs"

REM 실행 파일 복사
copy "dist\PDF_검증_시스템.exe" "release_package\" >nul
copy "dist\영역_선택_도구.exe" "release_package\" >nul
copy "dist\PDF_검증_도구.exe" "release_package\" >nul

REM 템플릿 파일 복사
if exist "templates\*.pdf" copy "templates\*.pdf" "release_package\templates\" >nul

REM 기본 설정 파일 복사
copy "templates.json" "release_package\" >nul

REM 사용자 가이드 생성
echo [8/8] 사용자 가이드 생성 중...

REM 시작 스크립트들 생성
call :create_start_scripts
call :create_user_guide
call :create_readme

echo.
echo ==========================================
echo 🎉 배포 빌드 완료!
echo ==========================================
echo.
echo 📁 배포 폴더: release_package\
echo 📊 패키지 크기: 
for /f %%i in ('powershell "(Get-ChildItem release_package -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"') do echo    약 %%i MB
echo.
echo 📦 배포 방법:
echo 1. release_package 폴더를 ZIP으로 압축
echo 2. 사용자에게 전달
echo 3. 사용자는 압축 해제 후 "PDF 검증 시스템 시작.bat" 실행
echo.
echo 📋 포함된 파일:
dir "release_package" /b
echo.

REM 자동으로 ZIP 파일 생성 (PowerShell 사용)
echo 📦 ZIP 파일 자동 생성 중...
powershell "Compress-Archive -Path 'release_package\*' -DestinationPath 'PDF검증시스템_v1.0.zip' -Force"

if exist "PDF검증시스템_v1.0.zip" (
    echo ✅ ZIP 파일 생성 완료: PDF검증시스템_v1.0.zip
    echo.
    echo 🚀 배포 준비 완료!
    echo    사용자에게 PDF검증시스템_v1.0.zip 파일을 전달하세요.
) else (
    echo ⚠️ ZIP 파일 생성 실패. 수동으로 압축해주세요.
)

echo.
choice /c YN /m "배포 폴더를 열어보시겠습니까?"
if errorlevel 2 goto :end
explorer "release_package"

:end
pause
goto :eof

REM 시작 스크립트 생성 함수
:create_start_scripts

REM 메인 시작 스크립트
echo @echo off > "release_package\PDF 검증 시스템 시작.bat"
echo title PDF 검증 시스템 >> "release_package\PDF 검증 시스템 시작.bat"
echo echo. >> "release_package\PDF 검증 시스템 시작.bat"
echo echo ======================================== >> "release_package\PDF 검증 시스템 시작.bat"
echo echo    PDF 양식 검증 시스템 v1.0 >> "release_package\PDF 검증 시스템 시작.bat"
echo echo ======================================== >> "release_package\PDF 검증 시스템 시작.bat"
echo echo. >> "release_package\PDF 검증 시스템 시작.bat"
echo echo 🚀 PDF 검증 시스템을 시작합니다... >> "release_package\PDF 검증 시스템 시작.bat"
echo start "" "PDF_검증_시스템.exe" >> "release_package\PDF 검증 시스템 시작.bat"

REM ROI 도구 시작 스크립트
echo @echo off > "release_package\1단계_영역선택.bat"
echo title 영역 선택 도구 >> "release_package\1단계_영역선택.bat"
echo echo. >> "release_package\1단계_영역선택.bat"
echo echo ======================================== >> "release_package\1단계_영역선택.bat"
echo echo    1단계: 검증 영역 선택 >> "release_package\1단계_영역선택.bat"
echo echo ======================================== >> "release_package\1단계_영역선택.bat"
echo echo. >> "release_package\1단계_영역선택.bat"
echo echo 🎯 영역 선택 도구를 시작합니다... >> "release_package\1단계_영역선택.bat"
echo echo    빈 PDF 양식을 열고 검증할 영역을 설정하세요. >> "release_package\1단계_영역선택.bat"
echo echo. >> "release_package\1단계_영역선택.bat"
echo start "" "영역_선택_도구.exe" >> "release_package\1단계_영역선택.bat"

REM PDF 검증 도구 시작 스크립트
echo @echo off > "release_package\2단계_PDF검증.bat"
echo title PDF 검증 도구 >> "release_package\2단계_PDF검증.bat"
echo echo. >> "release_package\2단계_PDF검증.bat"
echo echo ======================================== >> "release_package\2단계_PDF검증.bat"
echo echo    2단계: PDF 양식 검증 >> "release_package\2단계_PDF검증.bat"
echo echo ======================================== >> "release_package\2단계_PDF검증.bat"
echo echo. >> "release_package\2단계_PDF검증.bat"
echo echo 📊 PDF 검증 도구를 시작합니다... >> "release_package\2단계_PDF검증.bat"
echo echo    작성된 PDF 양식을 검증하세요. >> "release_package\2단계_PDF검증.bat"
echo echo. >> "release_package\2단계_PDF검증.bat"
echo start "" "PDF_검증_도구.exe" >> "release_package\2단계_PDF검증.bat"

goto :eof

REM 사용자 가이드 생성 함수
:create_user_guide
echo PDF 양식 검증 시스템 사용 가이드 > "release_package\docs\사용법.txt"
echo ================================== >> "release_package\docs\사용법.txt"
echo. >> "release_package\docs\사용법.txt"
echo 🎯 이 프로그램은 PDF 양식이 올바르게 작성되었는지 자동으로 검증합니다. >> "release_package\docs\사용법.txt"
echo. >> "release_package\docs\사용법.txt"
echo 📋 사용 순서: >> "release_package\docs\사용법.txt"
echo. >> "release_package\docs\사용법.txt"
echo 1단계: 템플릿 생성 (처음 한 번만) >> "release_package\docs\사용법.txt"
echo    • "1단계_영역선택.bat" 실행 >> "release_package\docs\사용법.txt"
echo    • 빈 PDF 양식 파일 열기 >> "release_package\docs\사용법.txt"
echo    • 마우스로 검증할 영역 드래그하여 선택 >> "release_package\docs\사용법.txt"
echo    • 각 영역마다 이름과 검증 방법 설정 >> "release_package\docs\사용법.txt"
echo      - OCR: 텍스트 검증 (이름, 주소, 전화번호 등) >> "release_package\docs\사용법.txt"
echo      - Contour: 도형 검증 (서명, 체크박스, 도장 등) >> "release_package\docs\사용법.txt"
echo    • 템플릿 이름을 정하고 저장 >> "release_package\docs\사용법.txt"
echo. >> "release_package\docs\사용법.txt"
echo 2단계: PDF 검증 (매번 사용) >> "release_package\docs\사용법.txt"
echo    • "2단계_PDF검증.bat" 실행 >> "release_package\docs\사용법.txt"
echo    • 만든 템플릿 선택 >> "release_package\docs\사용법.txt"
echo    • 검증할 PDF 파일 선택 (작성된 양식) >> "release_package\docs\사용법.txt"
echo    • "검증 실행" 버튼 클릭 >> "release_package\docs\사용법.txt"
echo    • 결과 확인 및 문제가 있으면 주석 PDF 저장 >> "release_package\docs\사용법.txt"
echo. >> "release_package\docs\사용법.txt"
echo 📁 폴더 구조: >> "release_package\docs\사용법.txt"
echo    • templates: PDF 템플릿 파일들 >> "release_package\docs\사용법.txt"
echo    • output: 검증 결과 파일들 >> "release_package\docs\사용법.txt"
echo    • docs: 문서들 >> "release_package\docs\사용법.txt"
echo. >> "release_package\docs\사용법.txt"
echo 🔧 임계값 설정 가이드: >> "release_package\docs\사용법.txt"
echo    OCR (텍스트 검증): >> "release_package\docs\사용법.txt"
echo    • 이름: 2-3 (짧은 이름) >> "release_package\docs\사용법.txt"
echo    • 전화번호: 8-11 (하이픈 포함) >> "release_package\docs\사용법.txt"
echo    • 주소: 10-20 (상세 주소) >> "release_package\docs\사용법.txt"
echo. >> "release_package\docs\사용법.txt"
echo    Contour (도형 검증): >> "release_package\docs\사용법.txt"
echo    • 체크박스: 200-500 >> "release_package\docs\사용법.txt"
echo    • 서명: 800-1500 >> "release_package\docs\사용법.txt"
echo    • 도장: 2000-5000 >> "release_package\docs\사용법.txt"
echo. >> "release_package\docs\사용법.txt"
echo ❓ 문제 해결: >> "release_package\docs\사용법.txt"
echo    • 프로그램이 실행되지 않으면 Windows 10/11인지 확인 >> "release_package\docs\사용법.txt"
echo    • OCR 인식이 안 되면 이미지 품질 확인 >> "release_package\docs\사용법.txt"
echo    • 모든 필드가 "Empty"로 나오면 임계값을 낮게 설정 >> "release_package\docs\사용법.txt"

goto :eof

REM README 생성 함수
:create_readme
echo PDF Form Validation System v1.0 > "release_package\README.txt"
echo ================================== >> "release_package\README.txt"
echo. >> "release_package\README.txt"
echo Professional PDF form validation tool for Windows >> "release_package\README.txt"
echo. >> "release_package\README.txt"
echo Quick Start: >> "release_package\README.txt"
echo 1. Run "PDF 검증 시스템 시작.bat" >> "release_package\README.txt"
echo 2. Follow the on-screen instructions >> "release_package\README.txt"
echo. >> "release_package\README.txt"
echo System Requirements: >> "release_package\README.txt"
echo - Windows 10/11 >> "release_package\README.txt"
echo - No additional installation required >> "release_package\README.txt"
echo. >> "release_package\README.txt"
echo For detailed instructions, see docs/사용법.txt >> "release_package\README.txt"

goto :eof
