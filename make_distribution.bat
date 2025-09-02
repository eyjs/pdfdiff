@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ╔══════════════════════════════════════════════╗
echo ║           PDF 검증 시스템 배포 도구          ║
echo ║            v2.0 사용자 배포판 생성기         ║
echo ╚══════════════════════════════════════════════╝
echo.

REM --- 가상환경 확인 및 활성화 ---
if exist "venv\Scripts\activate.bat" (
    echo [1/6] 가상환경 활성화...
    call venv\Scripts\activate.bat
) else (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo    먼저 one_click_setup.bat을 실행하여 개발 환경을 설정하세요.
    pause
    exit /b 1
)

REM --- PyInstaller 설치 ---
echo [2/6] PyInstaller 준비...
pip install pyinstaller >nul 2>&1

REM --- 빌드 환경 정리 ---
echo [3/6] 이전 빌드 환경 정리...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "사용자배포판" rmdir /s /q "사용자배포판" >nul 2>&1

REM --- EXE 파일 빌드 ---
echo [4/6] 실행 파일 빌드 중... (시간이 다소 소요될 수 있습니다)

REM 통합 런처 빌드 (콘솔 기반)
pyinstaller --onefile ^
    --name "PDF검증_통합런처" ^
    --distpath "dist" ^
    --add-data "src;src" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    enhanced_launcher.py >nul 2>&1

REM 1단계: 템플릿 설정 도구 빌드 (GUI)
pyinstaller --onefile --windowed ^
    --name "템플릿_설정도구" ^
    --distpath "dist" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.simpledialog" ^
    src/roi_selector.py >nul 2>&1

REM 2단계: 서류 검증 도구 빌드 (GUI)
pyinstaller --onefile --windowed ^
    --name "서류_검증도구" ^
    --distpath "dist" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.scrolledtext" ^
    src/pdf_validator_gui.py >nul 2>&1

REM --- 배포 패키지 구성 ---
echo [5/6] 배포 패키지 구성...
mkdir "사용자배포판"
mkdir "사용자배포판\templates"
mkdir "사용자배포판\output"

REM 실행 파일 복사
copy "dist\PDF검증_통합런처.exe" "사용자배포판\" >nul 2>&1
copy "dist\템플릿_설정도구.exe" "사용자배포판\" >nul 2>&1
copy "dist\서류_검증도구.exe" "사용자배포판\" >nul 2>&1

REM 기본 템플릿 폴더/파일 복사
if exist "templates" xcopy "templates" "사용자배포판\templates" /E /I /Y >nul 2>&1

REM --- 사용자 가이드 생성 ---
echo [6/6] 사용자 가이드 및 실행 스크립트 생성...

REM 메인 시작 스크립트
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo.
    echo ========================================
    echo       PDF 보험 서류 검증 시스템 v2.0
    echo ========================================
    echo.
    echo 🚀 통합 런처를 시작합니다...
    echo    메뉴에서 원하는 작업을 선택하세요.
    echo.
    echo "PDF검증_통합런처.exe"
    echo pause
) > "사용자배포판\✅ (시작) 통합 런처 실행.bat"

REM 1단계 스크립트
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo.
    echo ========================================
    echo      1단계: 템플릿 설정하기
    echo ========================================
    echo.
    echo 🎯 템플릿 설정 도구를 직접 실행합니다...
    echo "템플릿_설정도구.exe"
) > "사용자배포판\1단계_템플릿_설정.bat"

REM 2단계 스크립트
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo.
    echo ========================================
    echo      2단계: PDF 서류 검증하기
    echo ========================================
    echo.
    echo 📊 서류 검증 도구를 직접 실행합니다...
    echo "서류_검증도구.exe"
) > "사용자배포판\2단계_서류_검증.bat"

REM 사용법 안내서 생성
(
    echo 안녕하세요! PDF 보험 서류 검증 시스템 v2.0입니다.
    echo.
    echo ■ 이 프로그램은 무엇인가요?
    echo   PDF 보험 서류가 양식에 맞게 잘 작성되었는지 자동으로 검사하고,
    echo   문제가 있는 부분을 찾아주는 품질 관리 도구입니다.
    echo.
    echo ■ 어떻게 사용하나요?
    echo   가장 쉬운 방법은 '✅ (시작) 통합 런처 실행.bat' 파일을 실행하는 것입니다.
    echo   실행하면 나타나는 메뉴에서 원하는 작업을 선택하여 진행할 수 있습니다.
    echo.
    echo   [주요 기능]
    echo.
    echo   1. 템플릿 설정 (처음 한 번 또는 양식 변경 시)
    echo      - 원본 PDF 양식을 불러와 이름, 서명, 체크박스 등 검증할 영역을 지정하고 저장합니다.
    echo      - '1단계_템플릿_설정.bat'으로 직접 실행할 수도 있습니다.
    echo.
    echo   2. 서류 검증 (반복 사용)
    echo      - 위에서 만든 템플릿과 검증할 PDF 파일을 선택한 후 검증을 실행합니다.
    echo      - '2단계_서류_검증.bat'으로 직접 실행할 수도 있습니다.
    echo.
    echo ■ 결과는 어디에 저장되나요?
    echo   - 검증 결과(성공/실패)는 'output' 폴더 안에 보험사별, 템플릿별로 자동 분류되어 저장됩니다.
    echo.
    echo ■ 문의사항이 있으시면 개발자에게 연락주세요.
) > "사용자배포판\📖 사용법.txt"

REM --- 최종 정리 ---
powershell -Command "Compress-Archive -Path '사용자배포판\*' -DestinationPath 'PDF검증시스템_배포판_v2.0.zip' -Force" >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════╗
echo ║                🎉 배포 완료!                 ║
echo ╚══════════════════════════════════════════════╝
echo.
echo 📦 생성된 파일:
echo   - 사용자배포판\ (폴더)
echo   - PDF검증시스템_배포판_v2.0.zip ⭐ (이 파일을 사용자에게 전달하세요)
echo.
echo 🚀 배포 방법:
echo   1. PDF검증시스템_배포판_v2.0.zip 파일을 사용자에게 전달
echo   2. 사용자는 압축 해제 후 '✅ (시작) 통합 런처 실행.bat'을 실행
echo.
choice /c YN /m "배포 폴더를 지금 열어보시겠습니까?"
if errorlevel 2 goto :end
explorer "사용자배포판"

:end
pause