@echo off
chcp 65001 >nul
title PDF Diff 프로젝트 - 한번에 설정하기

echo.
echo  ┌────────────────────────────────────────────────┐
echo  │        PDF Diff 프로젝트 통합 설정 도구        │
echo  │                   Ver 1.0                      │
echo  └────────────────────────────────────────────────┘
echo.

echo 🚀 PDF 서류 검증 시스템을 설정합니다...
echo.

REM 현재 디렉토리 확인
echo 📁 현재 경로: %CD%
echo.

REM 1. 필수 폴더 생성
echo 🔧 1단계: 필수 폴더 생성 중...
if not exist "templates" mkdir templates
if not exist "output" mkdir output
if not exist "input" mkdir input
echo    ✅ 폴더 구조 생성 완료

REM 2. Python 가상환경 확인 (선택사항)
echo.
echo 🐍 2단계: Python 환경 확인 중...

python --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ Python이 설치되지 않았거나 PATH에 등록되지 않았습니다.
    echo    Python 3.8+ 설치 후 다시 실행하세요.
    pause
    exit /b 1
) else (
    echo    ✅ Python 설치 확인됨
)

REM 3. 의존성 패키지 설치
echo.
echo 📦 3단계: 필수 패키지 설치 중...
echo    pip install -r requirements.txt 실행...

pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo    ⚠️ 일부 패키지 설치에서 경고가 있었을 수 있습니다.
    echo    하지만 진행을 계속합니다...
) else (
    echo    ✅ 패키지 설치 완료
)

REM 4. Tesseract 한글 언어팩 설치
echo.
echo 🔤 4단계: 한글 OCR 언어팩 설치 중...

REM tessdata 폴더 확인
if not exist "vendor\tesseract\tessdata" (
    echo    ❌ vendor\tesseract\tessdata 폴더를 찾을 수 없습니다.
    echo    프로젝트 구조를 확인하세요.
    pause
    exit /b 1
)

REM 언어팩 파일 존재 확인
set "NEEDS_INSTALL=0"
if not exist "vendor\tesseract\tessdata\eng.traineddata" set "NEEDS_INSTALL=1"
if not exist "vendor\tesseract\tessdata\kor.traineddata" set "NEEDS_INSTALL=1"

if "%NEEDS_INSTALL%"=="1" (
    echo    언어팩이 필요합니다. 자동 설치를 시도합니다...
    
    REM Python 자동 설치 스크립트 실행
    if exist "setup_tesseract_korean.py" (
        echo    Python 스크립트로 다운로드 중...
        python setup_tesseract_korean.py --quiet
    ) else (
        echo    ⚠️ 자동 설치 스크립트를 찾을 수 없습니다.
        echo    수동 설치가 필요합니다.
        goto :manual_install
    )
    
    REM 설치 결과 확인
    if exist "vendor\tesseract\tessdata\eng.traineddata" (
        if exist "vendor\tesseract\tessdata\kor.traineddata" (
            echo    ✅ 언어팩 자동 설치 완료
        ) else (
            goto :manual_install
        )
    ) else (
        goto :manual_install
    )
) else (
    echo    ✅ 언어팩이 이미 설치되어 있습니다.
)

goto :test_installation

:manual_install
echo    📋 수동 설치 안내:
echo    다음 링크에서 파일을 다운로드하여 vendor\tesseract\tessdata\ 폴더에 저장하세요:
echo.
echo    • 영어: https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata
echo    • 한글: https://github.com/tesseract-ocr/tessdata/raw/main/kor.traineddata
echo.
echo    다운로드 완료 후 아무 키나 누르세요...
pause >nul

:test_installation
REM 5. 설치 확인 테스트
echo.
echo 🧪 5단계: 설치 검증 중...

if exist "check_tesseract.py" (
    echo    설치 상태를 확인합니다...
    python check_tesseract.py --quiet
    if errorlevel 1 (
        echo    ⚠️ 일부 확인에서 문제가 발견되었습니다.
        echo    하지만 기본 기능은 사용 가능할 수 있습니다.
    ) else (
        echo    ✅ 모든 검증 통과
    )
) else (
    echo    ⚠️ 검증 스크립트를 찾을 수 없습니다. 수동 확인하세요.
)

REM 6. 완료 및 실행 안내
echo.
echo  ┌────────────────────────────────────────────────┐
echo  │                🎉 설정 완료!                   │
echo  └────────────────────────────────────────────────┘
echo.
echo 📋 설치된 구성 요소:
echo    ✅ Python 패키지들
echo    ✅ 프로젝트 폴더 구조
echo    ✅ Tesseract 한글 OCR
echo.
echo 🚀 이제 다음 명령으로 프로그램을 시작할 수 있습니다:
echo.
echo    python enhanced_launcher.py
echo.
echo ──────────────────────────────────────────────────
echo 📖 사용법:
echo    1. "템플릿 생성 및 편집" - PDF에서 검증할 영역 설정
echo    2. "검증 도구 실행" - 실제 서류 검증
echo.
echo 💡 문제가 발생하면:
echo    • check_tesseract.py - OCR 상태 확인
echo    • README.md - 상세 매뉴얼 참조
echo ──────────────────────────────────────────────────
echo.

REM 바로 실행 옵션 제공
echo 바로 프로그램을 실행하시겠습니까? (Y/N):
set /p choice="선택: "

if /i "%choice%"=="Y" (
    echo.
    echo 🚀 프로그램을 시작합니다...
    python enhanced_launcher.py
) else (
    echo.
    echo 설정이 완료되었습니다. 언제든 'python enhanced_launcher.py'로 실행하세요.
    pause
)
