# PDF 서류 자동 검증 시스템

PDF 문서의 특정 영역(ROI)에 기입 여부를 자동으로 검증하는 Python GUI 애플리케이션입니다.

## 주요 기능

- **템플릿 생성**: PDF에서 검증할 영역을 마우스로 선택하고 저장
- **자동 검증**: OCR, 윤곽선 검출, 이미지 비교 방식 지원
- **일괄 처리**: 여러 PDF 파일을 한 번에 검증
- **결과 리포트**: 검증 결과를 자동으로 정리하여 출력

## 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. Tesseract 설정 (OCR 사용 시)
#    - resources/vendor/tesseract/ 폴더에 tesseract.exe 배치
#    - tessdata/ 폴더에 kor.traineddata, eng.traineddata 배치

# 3. 실행
python main.py
```

## 프로젝트 구조

```
pdfdiff/
├── main.py                 # 진입점
├── app/                    # GUI 및 컨트롤러
│   ├── gui/               # Tkinter 기반 UI
│   └── controllers/       # 비즈니스 로직 연결
├── domain/                 # 핵심 비즈니스 로직
│   ├── entities/          # 데이터 모델
│   ├── services/          # 검증 서비스
│   └── repositories/      # 데이터 저장소
├── infrastructure/         # 외부 시스템 연동
├── shared/                 # 공통 유틸리티
└── resources/              # Tesseract OCR 리소스
```

## 기술 스택

| 항목            | 기술                |
| --------------- | ------------------- |
| **아키텍처**    | Clean Architecture  |
| **GUI**         | Tkinter             |
| **PDF**         | PyMuPDF 1.26.4      |
| **OCR**         | Tesseract + EasyOCR |
| **이미지 처리** | OpenCV 4.8.1.78     |

## 사용 방법

### 1단계: 템플릿 생성

1. "템플릿 생성 및 편집" 클릭
2. 원본 PDF 선택
3. 검증할 영역을 마우스로 드래그하여 지정
4. 검증 방식 선택 (OCR/윤곽선/이미지 비교)
5. 템플릿 저장

### 2단계: 서류 검증

1. "서류 검증 실행" 클릭
2. 저장된 템플릿 선택
3. 검증할 PDF 파일들 선택
4. 검증 실행 및 결과 확인

## 설정

`settings.json` 파일에서 주요 설정을 변경할 수 있습니다:

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

## 문제 해결

**Tesseract 오류 발생 시**

- `tesseract.exe` 파일 경로 확인
- 언어 데이터 파일(`kor.traineddata`, `eng.traineddata`) 존재 확인

**메모리 부족 시**

- `settings.json`에서 동시 처리 파일 수 감소
- 대용량 PDF는 분할 처리

## 라이선스

Copyright (c) 2025 - All Rights Reserved
