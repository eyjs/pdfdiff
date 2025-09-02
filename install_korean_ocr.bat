@echo off
chcp 65001 >nul
echo 🔧 Tesseract 한글 OCR 설정 스크립트
echo ========================================
echo.

echo 📁 현재 경로: %CD%
echo.

REM 필요한 폴더 확인
if not exist "vendor\tesseract\tessdata" (
    echo ❌ vendor\tesseract\tessdata 폴더를 찾을 수 없습니다.
    echo    올바른 경로에서 실행하고 있는지 확인하세요.
    pause
    exit /b 1
)

echo ✅ tessdata 폴더 확인됨: %CD%\vendor\tesseract\tessdata
echo.

REM 이미 파일이 있는지 확인
set "NEED_DOWNLOAD=0"

if not exist "vendor\tesseract\tessdata\eng.traineddata" (
    echo ❌ 영어 언어팩이 없습니다.
    set "NEED_DOWNLOAD=1"
) else (
    echo ✅ 영어 언어팩 존재함
)

if not exist "vendor\tesseract\tessdata\kor.traineddata" (
    echo ❌ 한글 언어팩이 없습니다.
    set "NEED_DOWNLOAD=1"
) else (
    echo ✅ 한글 언어팩 존재함
)

if "%NEED_DOWNLOAD%"=="0" (
    echo.
    echo 🎉 모든 언어팩이 이미 설치되어 있습니다!
    echo    바로 프로그램을 사용하실 수 있습니다.
    echo.
    pause
    exit /b 0
)

echo.
echo 🔽 필요한 언어팩을 다운로드합니다...
echo.

REM Python 스크립트 실행
if exist "setup_tesseract_korean.py" (
    echo Python 자동 설치 스크립트를 실행합니다...
    python setup_tesseract_korean.py
    
    REM 결과 확인
    if exist "vendor\tesseract\tessdata\eng.traineddata" (
        if exist "vendor\tesseract\tessdata\kor.traineddata" (
            echo.
            echo ✅ 자동 설치가 완료되었습니다!
            goto :success
        )
    )
    echo.
    echo ⚠️ 자동 설치에 문제가 있었습니다. 수동 방법을 시도합니다...
)

echo.
echo 📋 수동 설치 안내:
echo ========================================
echo 1. 다음 링크들을 브라우저에서 열어주세요:
echo.
echo 영어 언어팩:
echo https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata
echo.
echo 한글 언어팩:
echo https://github.com/tesseract-ocr/tessdata/raw/main/kor.traineddata
echo.
echo 2. 다운로드한 파일들을 다음 폴더에 저장하세요:
echo %CD%\vendor\tesseract\tessdata\
echo.
echo 3. 파일명이 정확한지 확인하세요:
echo    - eng.traineddata
echo    - kor.traineddata
echo.

REM 수동 설치 대기
echo 수동 설치를 완료한 후 아무 키나 누르세요...
pause >nul

REM 수동 설치 확인
if exist "vendor\tesseract\tessdata\eng.traineddata" (
    if exist "vendor\tesseract\tessdata\kor.traineddata" (
        goto :success
    )
)

echo.
echo ❌ 여전히 언어팩을 찾을 수 없습니다.
echo    파일명과 경로를 다시 확인해주세요.
echo.
goto :manual_check

:success
echo.
echo 🎉 설치 완료!
echo ========================================
echo.
echo 설치된 파일들:
for %%f in (vendor\tesseract\tessdata\*.traineddata) do (
    echo   ✅ %%~nxf
)
echo.
echo 이제 enhanced_launcher.py를 실행하여
echo 한글 OCR 기능을 사용하실 수 있습니다!
echo.
pause
exit /b 0

:manual_check
echo 📋 설치 확인:
echo ========================================
echo 다음 파일들이 존재해야 합니다:
echo.
echo 📁 %CD%\vendor\tesseract\tessdata\
if exist "vendor\tesseract\tessdata\eng.traineddata" (
    echo   ✅ eng.traineddata
) else (
    echo   ❌ eng.traineddata ^(없음^)
)

if exist "vendor\tesseract\tessdata\kor.traineddata" (
    echo   ✅ kor.traineddata
) else (
    echo   ❌ kor.traineddata ^(없음^)
)
echo.
echo 문제가 지속되면 개발팀에 문의하세요.
echo.
pause
