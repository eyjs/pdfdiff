# PDF Validator System v3.0

## 📖 개요

PDF 문서의 특정 영역(ROI)을 자동으로 검증하는 Python 기반 GUI 애플리케이션입니다.  
보험서류 등의 기입 여부를 OCR과 이미지 비교를 통해 자동 검증합니다.

## 🚀 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 실행
python main.py
```

## 🏗️ 프로젝트 구조

```
pdfdiff/
├── main.py                    # 애플리케이션 진입점
├── app/                       # 프레젠테이션 계층 (GUI)
├── domain/                    # 도메인 계층 (비즈니스 로직)
├── infrastructure/            # 인프라 계층 (외부 연동)
├── shared/                    # 공통 유틸리티
├── resources/                 # Tesseract OCR 리소스
├── templates.json             # 템플릿 데이터
└── settings.json              # 애플리케이션 설정
```

## ⚙️ 주요 기능

### 📝 템플릿 생성
- PDF에서 검증할 영역(ROI) 지정
- OCR/윤곽선/이미지 비교 방식 선택
- 자동 앵커 영역 생성으로 정확도 향상

### 🔍 문서 검증  
- 개별 파일 또는 일괄 처리
- 실시간 진행률 표시
- 검증 결과 리포트 생성

## 🔧 기술 스택

- **GUI**: Tkinter
- **PDF 처리**: PyMuPDF (1.26.4)
- **OCR**: Tesseract + pytesseract (0.3.10)
- **이미지 처리**: OpenCV (4.8.1.78)
- **아키텍처**: Clean Architecture 패턴

## ⚙️ Tesseract 설정

1. `resources/vendor/tesseract/` 폴더에 `tesseract.exe` 배치
2. `tessdata/` 폴더에 언어 데이터 파일 배치:
   - `kor.traineddata` (한글)
   - `eng.traineddata` (영어)

## 🎮 사용법

### 1단계: 템플릿 생성
1. "템플릿 생성 및 편집" 클릭
2. 원본 PDF 선택
3. 검증할 영역을 마우스로 드래그
4. 검증 방식 선택 (OCR/윤곽선/이미지)
5. 템플릿 저장

### 2단계: 문서 검증
1. "서류 검증 실행" 클릭  
2. 저장된 템플릿 선택
3. 검증할 PDF 파일들 선택
4. 검증 실행 및 결과 확인

## 🔧 설정 파일

### settings.json
```json
{
  "tesseract": {
    "executable_path": "resources/vendor/tesseract/tesseract.exe",
    "languages": "kor+eng",
    "confidence_threshold": 60
  },
  "validation": {
    "default_ssim_threshold": 0.99,
    "max_processing_time": 300
  }
}
```

## 🧪 테스트

```bash
# 단위 테스트
python -m pytest tests/unit/ -v

# 통합 테스트
python -m pytest tests/integration/ -v
```

## 🔧 문제 해결

**Tesseract 오류 시:**
- `tesseract.exe` 파일 경로 확인
- 언어 데이터 파일 존재 확인
- `settings.json`에서 경로 설정 확인

**메모리 부족 시:**
- `settings.json`에서 `max_concurrent_validations` 값 감소
- 대용량 PDF 파일은 분할 처리

## 📈 성능 지표

- **검증 속도**: 단일 PDF 3-5초
- **정확도**: 95% 이상 (깔끔한 문서 기준)
- **지원 형식**: PDF
- **동시 처리**: 최대 5개 파일

## 📄 라이선스

Copyright (c) 2025 PDF Validator System - All Rights Reserved
