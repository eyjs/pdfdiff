# EasyOCR 내장형 설치 가이드

## 개요

이 가이드는 EasyOCR 모델을 애플리케이션에 내장하여 인터넷 연결 없이도 사용할 수 있도록 번들링하는 방법을 설명합니다.

## 내장형 EasyOCR의 장점

- ✅ **오프라인 동작**: 인터넷 연결 없이 OCR 사용 가능
- ✅ **빠른 초기화**: 모델 다운로드 시간 없음
- ✅ **배포 편의성**: 설치된 시스템에서 바로 동작
- ✅ **높은 한글 정확도**: Tesseract보다 우수한 한글 인식

## 설치 방법

### 자동 설치 (권장)

```bash
# 프로젝트 루트에서 실행
setup_bundled_easyocr.bat
```

### 수동 설치

```bash
# 1. EasyOCR 패키지 설치
venv\Scripts\activate.bat
pip install easyocr==1.7.1 torch torchvision

# 2. 모델 다운로드
python resources\vendor\easyocr\bundle_models.py

# 3. 설치 확인
python -c "from infrastructure.services.easyocr_service import EasyOCRService; print('설치 완료!')"
```

## 디렉토리 구조

설치 후 다음과 같은 구조가 생성됩니다:

```
resources/vendor/easyocr/
├── bundle_models.py          # 모델 다운로드 스크립트
├── model_config.py          # 모델 설정 파일 (자동 생성)
└── models/
    ├── korean_g2.pth        # 한글 인식 모델 (~85MB)
    ├── english_g2.pth       # 영어 인식 모델 (~45MB)
    └── craft_mlt_25k.pth    # 텍스트 감지 모델 (~67MB)
```

## 사용법

### 기본 사용

내장형 EasyOCR이 설치되면 애플리케이션에서 자동으로 사용됩니다:

```python
# MainController에서 자동으로 초기화
ocr_service = ComparativeOCRService(tesseract_service)
```

### 비교 OCR 로그 예시

```
[INFO] 내장형 EasyOCR + Tesseract 비교 서비스 초기화 중...
[INFO] ✅ 내장 EasyOCR 초기화 완료 (소요시간: 3.2초)
[INFO] Tesseract: '통합안진단비 특정소액암진단비' (시간: 0.8초)
[INFO] 내장 EasyOCR: '통합암진단비 특정소액암진단비' (시간: 2.1초)
[INFO] ✅ 선택: EASYOCR - '통합암진단비 특정소액암진단비' (점수: 0.87)
```

## 성능 비교

| OCR 엔진 | 한글 정확도 | 처리 속도 | 메모리 사용 |
|----------|-------------|-----------|-------------|
| Tesseract | ~75% | 0.5-1초 | ~50MB |
| EasyOCR | ~90% | 2-4초 | ~200MB |
| 비교 모드 | **~92%** | 2-5초 | ~250MB |

## 문제 해결

### 1. 모델 다운로드 실패

```bash
# 네트워크 문제 시 수동 다운로드
# https://github.com/JaidedAI/EasyOCR/releases/download/v1.6.0/ 에서 직접 다운로드
# resources/vendor/easyocr/models/ 폴더에 배치
```

### 2. 메모리 부족

```python
# easyocr_service.py에서 배치 크기 조정
batch_size=1  # 기본값, 메모리 부족 시 유지
```

### 3. PyTorch 설치 오류

```bash
# CPU 전용 PyTorch 설치
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

## 배포 시 주의사항

### PyInstaller 번들링

```python
# build_user_release.bat에 추가할 항목
--add-data "resources/vendor/easyocr;resources/vendor/easyocr"
```

### 용량 최적화

- 전체 EasyOCR 모델: ~200MB
- 압축 후 배포 파일: +150MB 증가 예상
- 필요 시 한글 모델만 포함하여 용량 절약 가능

## 라이선스

- EasyOCR: Apache 2.0 License
- PyTorch: BSD License
- 내장 모델들: 각 모델의 라이선스를 따름

---

더 자세한 내용은 EasyOCR 공식 문서를 참조하세요: https://github.com/JaidedAI/EasyOCR
