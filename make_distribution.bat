@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ╔══════════════════════════════════════════════╗
echo ║           PDF 검증 시스템 배포 도구          ║
echo ║            사용자 배포판 생성기              ║
echo ╚══════════════════════════════════════════════╝
echo.

REM 가상환경 확인 및 활성화
if exist "venv\Scripts\activate.bat" (
    echo [1/6] 가상환경 활성화...
    call venv\Scripts\activate.bat
) else if exist "pdf_env\Scripts\activate.bat" (
    call pdf_env\Scripts\activate.bat
) else (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo    먼저 one_click_setup.bat을 실행하세요.
    pause
    exit /b 1
)

REM PyInstaller 설치
echo [2/6] PyInstaller 준비...
pip install pyinstaller >nul 2>&1

REM 빌드 환경 정리
echo [3/6] 빌드 환경 정리...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist" rmdir /s /q "dist" >nul 2>&1  
if exist "사용자배포판" rmdir /s /q "사용자배포판" >nul 2>&1

REM EXE 파일 빌드
echo [4/6] 실행 파일 빌드 중... (잠시 기다려주세요)

REM 메인 시스템 빌드 (콘솔 포함으로 에러 확인 가능)
pyinstaller --onefile ^
    --name "PDF검증시스템" ^
    --distpath "dist" ^
    --add-data "src;src" ^
    --add-data "templates.json;." ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.scrolledtext" ^
    --exclude-module "matplotlib" ^
    run.py >nul 2>&1

REM ROI 도구 빌드
pyinstaller --onefile --windowed ^
    --name "영역선택도구" ^
    --distpath "dist" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.simpledialog" ^
    src/roi_selector.py >nul 2>&1

REM PDF 검증 도구 빌드  
pyinstaller --onefile --windowed ^
    --name "PDF검증도구" ^
    --distpath "dist" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.scrolledtext" ^
    src/pdf_validator_gui.py >nul 2>&1

REM 배포 패키지 구성
echo [5/6] 배포 패키지 구성...
mkdir "사용자배포판"
mkdir "사용자배포판\templates"
mkdir "사용자배포판\output"

REM 실행 파일 복사
copy "dist\PDF검증시스템.exe" "사용자배포판\" >nul 2>&1
copy "dist\영역선택도구.exe" "사용자배포판\" >nul 2>&1  
copy "dist\PDF검증도구.exe" "사용자배포판\" >nul 2>&1

REM 기본 파일들 복사
copy "templates.json" "사용자배포판\" >nul 2>&1
if exist "templates\*.pdf" copy "templates\*.pdf" "사용자배포판\templates\" >nul 2>&1

REM 사용자용 실행 스크립트 생성
echo [6/6] 사용자 가이드 생성...

REM 메인 시작 스크립트
echo @echo off > "사용자배포판\📋 PDF 검증 시스템.bat"
echo echo. >> "사용자배포판\📋 PDF 검증 시스템.bat"
echo echo ======================================== >> "사용자배포판\📋 PDF 검증 시스템.bat"
echo echo       PDF 양식 검증 시스템 v1.0 >> "사용자배포판\📋 PDF 검증 시스템.bat"
echo echo ======================================== >> "사용자배포판\📋 PDF 검증 시스템.bat"
echo echo. >> "사용자배포판\📋 PDF 검증 시스템.bat"
echo echo 🚀 PDF 검증 시스템을 시작합니다... >> "사용자배포판\📋 PDF 검증 시스템.bat"
echo echo. >> "사용자배포판\📋 PDF 검증 시스템.bat"
echo "PDF검증시스템.exe" >> "사용자배포판\📋 PDF 검증 시스템.bat"
echo pause >> "사용자배포판\📋 PDF 검증 시스템.bat"

REM 1단계 스크립트
echo @echo off > "사용자배포판\🎯 1단계_영역선택.bat"
echo echo. >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo ======================================== >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo     1단계: 검증할 영역 선택하기 >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo ======================================== >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo. >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo 📖 사용법: >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo   1. 빈 PDF 양식 파일을 준비하세요 >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo   2. 마우스로 검증할 영역을 드래그하세요 >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo   3. 각 영역의 이름과 검증방법을 설정하세요 >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo   4. 템플릿 이름을 정하고 저장하세요 >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo. >> "사용자배포판\🎯 1단계_영역선택.bat"
echo echo 🎯 영역 선택 도구를 시작합니다... >> "사용자배포판\🎯 1단계_영역선택.bat"
echo "영역선택도구.exe" >> "사용자배포판\🎯 1단계_영역선택.bat"

REM 2단계 스크립트
echo @echo off > "사용자배포판\📊 2단계_PDF검증.bat"
echo echo. >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo ======================================== >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo      2단계: PDF 양식 검증하기 >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo ======================================== >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo. >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo 📖 사용법: >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo   1. 1단계에서 만든 템플릿을 선택하세요 >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo   2. 검증할 작성된 PDF 파일을 선택하세요 >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo   3. 검증 실행 버튼을 클릭하세요 >> "사용자배로판\📊 2단계_PDF검증.bat"
echo echo   4. 결과를 확인하고 필요시 주석 PDF를 저장하세요 >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo. >> "사용자배포판\📊 2단계_PDF검증.bat"
echo echo 📊 PDF 검증 도구를 시작합니다... >> "사용자배포판\📊 2단계_PDF검증.bat"
echo "PDF검증도구.exe" >> "사용자배포판\📊 2단계_PDF검증.bat"

REM 사용법 안내서 생성
echo PDF 검증 시스템 사용 안내서 > "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo ======================= >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo. >> "사용자배로판\📖 사용법을_먼저_읽어주세요.txt"
echo 안녕하세요! PDF 검증 시스템에 오신 것을 환영합니다. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo 🎯 이 프로그램의 목적: >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo   PDF 양식이 제대로 작성되었는지 자동으로 확인해드립니다. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo   예: 이름이 써져 있는지, 서명이 되어 있는지, 체크박스가 체크되었는지 등 >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo 📝 사용 순서: >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo   1단계 (처음 한 번만): 🎯 1단계_영역선택.bat >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo      • 빈 양식 PDF를 열어서 >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo      • 확인하고 싶은 부분(이름, 서명, 체크박스 등)을 마우스로 드래그 >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo      • 각 영역마다 이름 지어주고 저장 >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo   2단계 (매번 사용): 📊 2단계_PDF검증.bat >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo      • 1단계에서 만든 템플릿 선택 >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo      • 검증하고 싶은 작성된 PDF 선택 >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo      • 검증 결과 확인 >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo 💡 팁: >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo   • 처음 사용자는 "📋 PDF 검증 시스템.bat"을 먼저 실행해보세요! >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo   • 문제가 발견되면 output 폴더에 주석이 달린 PDF가 자동 저장됩니다. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"
echo ❓ 문의사항이 있으시면 개발자에게 연락주세요. >> "사용자배포판\📖 사용법을_먼저_읽어주세요.txt"

REM ZIP 파일 생성
powershell -Command "Compress-Archive -Path '사용자배포판\*' -DestinationPath 'PDF검증시스템_배포판.zip' -Force" >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════╗
echo ║                🎉 배포 완료!                ║  
echo ╚══════════════════════════════════════════════╝
echo.
echo 📦 생성된 파일:
echo   • 사용자배포판\ (폴더)
echo   • PDF검증시스템_배포판.zip ⭐ (배포용)
echo.
echo 📊 패키지 정보:
for /f %%i in ('powershell "(Get-ChildItem 사용자배포판 -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"') do echo   크기: 약 %%i MB
dir "사용자배포판" | find "File(s)"
echo.
echo 🚀 배포 방법:
echo   1. PDF검증시스템_배포판.zip 파일을 사용자에게 전달
echo   2. 사용자는 압축 해제 후 "📋 PDF 검증 시스템.bat" 실행
echo.
echo 📋 사용자 안내사항:
echo   • Windows 10/11에서만 동작합니다
echo   • 설치 과정이 없어 바로 사용 가능합니다  
echo   • 바이러스 백신에서 오탐지할 수 있으니 예외 처리 안내
echo.

choice /c YN /m "배포 폴더를 지금 열어보시겠습니까?"
if errorlevel 2 goto :end
explorer "사용자배포판"

:end
pause
