📦 PDF 검증 시스템 - 사용자 배포 가이드
이 문서는 개발 환경이 없는 일반 사용자에게 프로그램을 배포하기 위해, 모든 의존성(Tesseract OCR 포함)이 포함된 단일 실행 패키지를 만드는 과정을 안내합니다.

🎯 배포 목표
사용자는 Python이나 Tesseract OCR을 별도로 설치할 필요 없이, 압축 해제 후 .bat 파일을 더블클릭하는 것만으로 프로그램을 즉시 사용할 수 있어야 합니다.

🚀 배포 과정 (3단계)
1단계: Tesseract OCR 엔진 준비 (최초 1회)
배포판에 Tesseract 엔진을 포함시키기 위해, 실행 파일들을 프로젝트 폴더로 가져옵니다.

Tesseract 포터블 버전 다운로드:

Tesseract 포터블 다운로드 링크로 이동하여 tesseract-5.x.x-x64.zip 파일을 다운로드합니다.

프로젝트 폴더에 압축 해제:

프로젝트 루트에 vendor라는 새 폴더를 만듭니다.

그 안에 tesseract라는 폴더를 다시 만듭니다. (vendor/tesseract)

다운로드한 zip 파일의 내용물(tesseract.exe, tessdata 폴더 등)을 모두 이 vendor/tesseract 폴더 안으로 복사합니다.

최종 폴더 구조:

pdfdiff/
├── vendor/
│ └── tesseract/
│ ├── tesseract.exe
│ ├── tessdata/
│ └── ... (각종 dll 파일들)
└── src/
└── ...

2단계: Python 코드 수정 (최초 1회)
src/pdf_validator_gui.py 파일 최상단에 아래 코드를 추가하여, 프로그램이 내장된 Tesseract를 사용하도록 경로를 지정합니다.

# src/pdf_validator_gui.py 상단

import pytesseract
import sys
import os

# PyInstaller로 빌드된 .exe 환경인지 확인

if getattr(sys, 'frozen', False): # .exe 파일일 경우, tesseract.exe의 경로를 프로그램 내부 폴더로 지정
application_path = os.path.dirname(sys.executable)
tesseract_path = os.path.join(application_path, 'tesseract', 'tesseract.exe')
if os.path.exists(tesseract_path):
pytesseract.pytesseract.tesseract_cmd = tesseract_path

3단계: 원클릭 배포판 생성 (배포 시마다 실행)
프로젝트 루트 폴더에 있는 create_release.bat 파일을 실행합니다.

.\create_release.bat

이 스크립트는 다음 작업을 자동으로 수행합니다:

PyInstaller를 사용하여 enhanced_launcher.py와 각 도구를 .exe 파일로 빌드합니다.

빌드 과정에서 vendor/tesseract 폴더를 통째로 포함시킵니다.

release 폴더를 생성하고, 실행 파일, templates.json, 빈 input/output 폴더 등 사용자에게 필요한 모든 파일을 정리하여 복사합니다.

최종적으로 PDF_Validator_v1.0.zip과 같은 배포용 압축 파일을 생성합니다.

🚚 최종 전달
생성된 .zip 파일을 사용자에게 전달하고, 압축 해제 후 PDF 검증 시스템 시작.bat 파일을 실행하도록 안내하면 됩니다.
