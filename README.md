# PDF Validator System v3.0 - Clean Architecture

## 🎯 **프로젝트 개요**

보험서류 자동 검증 시스템이 **클린 아키텍처**로 전면 리팩토링되었습니다. 기존 기능은 유지하면서 코드 구조를 대폭 개선하여 유지보수성과 확장성을 크게 향상시켰습니다.

## 🏗️ **새로운 아키텍처**

### 클린 아키텍처 원칙 적용
```
📱 Presentation Layer (app/)
    ↓ depends on
🎮 Application Layer (controllers/)
    ↓ depends on
🧠 Domain Layer (domain/)
    ↑ implements
🔧 Infrastructure Layer (infrastructure/)
```

### 디렉토리 구조
```
pdfdiff/
├── main.py                      # 🚀 메인 진입점
├── app/                         # 📱 Presentation Layer
│   ├── gui/                     # UI 컴포넌트
│   │   ├── main_window.py       # 메인 윈도우
│   │   └── components/          # 재사용 UI 컴포넌트
│   └── controllers/             # 🎮 Application Controllers
│       ├── template_controller.py
│       └── validation_controller.py
├── domain/                      # 🧠 Domain Layer (Business Logic)
│   ├── entities/                # 핵심 엔티티
│   │   ├── roi.py
│   │   ├── template.py
│   │   ├── document.py
│   │   └── validation_result.py
│   ├── services/                # 도메인 서비스
│   │   ├── template_service.py
│   │   └── validation_service.py
│   └── repositories/            # 리포지토리 인터페이스
│       ├── template_repository.py
│       ├── document_repository.py
│       └── validation_repository.py
├── infrastructure/              # 🔧 Infrastructure Layer
│   ├── repositories/            # 리포지토리 구현체
│   │   ├── json_template_repository.py
│   │   └── file_document_repository.py
│   ├── services/               # 외부 서비스 래퍼
│   │   ├── pdf_service.py
│   │   ├── ocr_service.py
│   │   └── cv_service.py
│   └── config/                 # 설정 관리
│       └── settings.py
├── shared/                      # 🛠️ 공통 유틸리티
│   ├── exceptions.py           # 커스텀 예외
│   ├── constants.py            # 상수
│   ├── types.py               # 타입 정의
│   └── utils.py               # 공통 유틸리티
├── tests/                       # 🧪 테스트
│   ├── unit/
│   └── integration/
├── resources/                   # 📦 리소스
│   └── vendor/tesseract/        # OCR 엔진
├── clean_backup/                # 🗂️ 기존 코드 백업
└── requirements.txt
```

## 🚀 **실행 방법**

### 1. 기본 실행
```bash
python main.py
```

### 2. 디버그 모드
```bash
python main.py --debug
```

### 3. 버전 확인
```bash
python main.py --version
```

## 📋 **주요 개선사항**

### ✨ **아키텍처 개선**
- **의존성 역전**: 상위 계층이 하위 계층에 의존하지 않음
- **관심사 분리**: UI, 비즈니스 로직, 데이터 접근이 명확히 분리
- **단일 책임**: 각 클래스가 하나의 명확한 책임만 가짐
- **확장성**: 새로운 기능 추가가 용이한 구조

### 🧹 **코드 정리**
- **불필요한 파일 제거**: 중복, 임시, 테스트 파일들을 백업 폴더로 이동
- **명확한 네이밍**: 파일과 클래스 이름이 역할을 명확히 표현
- **일관된 구조**: 모든 모듈이 동일한 패턴을 따름

### 🔧 **개발자 경험 개선**
- **타입 힌트**: 모든 함수와 클래스에 타입 정보 추가
- **예외 처리**: 커스텀 예외 클래스로 명확한 오류 처리
- **로깅 시스템**: 체계적인 로깅 및 디버깅 지원
- **설정 관리**: 중앙화된 설정 관리 시스템

## 🎯 **핵심 컴포넌트**

### Domain Entities
- **ROI**: 검증 영역 정보 (좌표, 검증방식, 임계값)
- **Template**: ROI 집합 및 메타데이터
- **Document**: PDF 문서 정보
- **ValidationResult**: 검증 결과 및 통계

### Domain Services  
- **TemplateService**: 템플릿 생성, 수정, 검증
- **ValidationService**: PDF 검증 로직 및 결과 분석

### Controllers
- **TemplateController**: 템플릿 관리 UI 제어
- **ValidationController**: 검증 프로세스 제어

## 🛠️ **설치 및 설정**

### 1. Python 환경 준비
```bash
# Python 3.8+ 필요
python --version

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. Tesseract OCR 설정
- `resources/vendor/tesseract/` 폴더에 Tesseract 실행파일 배치
- `resources/vendor/tesseract/tessdata/` 폴더에 언어팩 배치
  - eng.traineddata (영어)
  - kor.traineddata (한글)

### 4. 실행
```bash
python main.py
```

## 📖 **사용 가이드**

### 1단계: 템플릿 생성
1. 메인 화면에서 "📝 템플릿 생성 및 편집" 클릭
2. 원본 PDF 선택 및 템플릿 이름 입력
3. 검증할 영역(ROI) 드래그로 지정
4. 검증 방식 선택 (OCR/Contour)
5. 템플릿 저장

### 2단계: 서류 검증
1. 메인 화면에서 "🔍 서류 검증 실행" 클릭
2. 저장된 템플릿 선택
3. 검증할 PDF 파일 또는 폴더 선택
4. 검증 실행 및 결과 확인

## 🧪 **테스트**

### 단위 테스트 실행
```bash
python -m pytest tests/unit/ -v
```

### 통합 테스트 실행
```bash
python -m pytest tests/integration/ -v
```

### 전체 테스트 실행
```bash
python -m pytest -v
```

## 🔧 **개발 가이드**

### 새로운 기능 추가 시
1. **Domain Layer**에 엔티티/서비스 추가
2. **Infrastructure Layer**에 구현체 추가
3. **Application Layer**에 컨트롤러 로직 추가
4. **Presentation Layer**에 UI 컴포넌트 추가

### 코드 스타일
- **타입 힌트** 필수 사용
- **docstring** 작성 권장
- **예외 처리** 명확히 구현
- **로깅** 적절히 활용

### 디버깅
- `--debug` 플래그로 상세 로그 확인
- `settings.json`에서 디버그 설정 조정
- `logs/` 폴더의 로그 파일 확인

## 🚀 **확장 계획**

### Phase 1: 핵심 기능 완성 ✅
- 클린 아키텍처 적용
- 기존 기능 마이그레이션
- 테스트 코드 작성

### Phase 2: 고급 기능
- [ ] 웹 인터페이스 (FastAPI + React)
- [ ] 데이터베이스 지원 (SQLite/PostgreSQL)
- [ ] 배치 처리 스케줄러
- [ ] REST API 제공

### Phase 3: AI 강화
- [ ] 머신러닝 기반 ROI 자동 감지
- [ ] 딥러닝 OCR 엔진 통합
- [ ] 이상 탐지 알고리즘

### Phase 4: 엔터프라이즈
- [ ] 사용자 권한 관리
- [ ] 감사 로그 시스템
- [ ] 클러스터 배포 지원
- [ ] 모니터링 대시보드

## 🏆 **품질 지표**

### 코드 품질
- **순환 복잡도**: < 10
- **코드 중복**: < 5%
- **테스트 커버리지**: > 80%
- **타입 커버리지**: > 95%

### 성능 지표
- **단일 PDF 검증**: < 5초
- **메모리 사용량**: < 500MB
- **동시 처리**: 최대 5개 PDF
- **응답 시간**: < 1초 (UI)

## 🤝 **기여 가이드**

1. **포크 및 브랜치 생성**
2. **기능 구현 및 테스트**
3. **코드 리뷰 요청**
4. **문서 업데이트**

## 📞 **지원 및 문의**

- **이슈 트래커**: GitHub Issues
- **문서**: 프로젝트 Wiki
- **이메일**: dev-team@company.com

## 📄 **라이선스**

Copyright (c) 2025 PDF Validator System
All Rights Reserved

---

## 🔄 **마이그레이션 가이드**

### v2.0 → v3.0 변경사항

#### 파일 위치 변경
```
[기존] enhanced_launcher.py → [신규] main.py
[기존] src/template_manager.py → [신규] app/controllers/template_controller.py
[기존] src/pdf_validator_gui.py → [신규] app/controllers/validation_controller.py
```

#### API 변경사항
```python
# 기존 방식
from src.template_manager import TemplateManager

# 새로운 방식
from app.controllers.template_controller import TemplateController
```

#### 설정 파일 변경
- `templates.json` → 동일 (호환성 유지)
- 새로 추가: `settings.json` (애플리케이션 설정)

### 기존 템플릿 데이터 호환성
모든 기존 템플릿은 그대로 사용 가능합니다. 추가 마이그레이션 작업이 필요하지 않습니다.

---

**🎉 PDF Validator System v3.0이 더욱 강력하고 유지보수 가능한 시스템으로 업그레이드되었습니다!**
