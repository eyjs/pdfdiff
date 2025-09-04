"""
Constants
시스템 전체에서 사용되는 상수들
"""

# 파일 관련 상수
DEFAULT_TEMPLATE_FILE = "templates.json"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_INPUT_DIR = "input"
DEFAULT_RESOURCES_DIR = "resources"

# PDF 관련 상수
PDF_EXTENSION = ".pdf"
SUPPORTED_EXTENSIONS = [PDF_EXTENSION]
MAX_PDF_SIZE_MB = 50  # 최대 PDF 파일 크기 (MB)
DEFAULT_PDF_DPI = 150  # PDF 렌더링 DPI
HIGH_QUALITY_DPI = 300

# ROI 관련 상수
MIN_ROI_SIZE = 10  # 최소 ROI 크기 (픽셀)
MAX_ROI_SIZE = 5000  # 최대 ROI 크기 (픽셀)
DEFAULT_OCR_THRESHOLD = 3  # OCR 기본 임계값
DEFAULT_CONTOUR_THRESHOLD = 100  # Contour 기본 임계값

# 검증 관련 상수
MAX_PROCESSING_TIME = 300  # 최대 처리 시간 (초)
DEFAULT_SSIM_THRESHOLD = 0.99  # SSIM 임계값
LAYOUT_DETECTION_SCALE = 2.0  # 레이아웃 감지용 스케일

# OCR 관련 상수
OCR_LANGUAGES = "kor+eng"  # 지원 언어
OCR_CONFIG_DEFAULT = r"--oem 3 --psm 6"
OCR_CONFIG_SINGLE_WORD = r"--oem 3 --psm 8"
OCR_CONFIDENCE_THRESHOLD = 60  # OCR 신뢰도 임계값

# 컴퓨터 비전 상수
FEATURE_DETECTORS = ["AKAZE", "ORB", "SIFT"]  # 특징점 검출기
MIN_MATCH_COUNT = 10  # 최소 매칭 점수
RANSAC_THRESHOLD = 5.0  # RANSAC 임계값
TEMPLATE_MATCH_THRESHOLD = 0.55  # 템플릿 매칭 임계값

# UI 관련 상수
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# 색상 상수 (RGB)
COLOR_ROI_OCR = (0, 0, 255)  # 파란색
COLOR_ROI_CONTOUR = (255, 0, 0)  # 빨간색
COLOR_ANCHOR = (0, 255, 255)  # 청록색
COLOR_SUCCESS = (0, 255, 0)  # 녹색
COLOR_FAILURE = (255, 165, 0)  # 주황색
COLOR_ERROR = (255, 0, 0)  # 빨간색

# 로깅 관련 상수
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 캐시 관련 상수
CACHE_MAX_SIZE = 100  # 최대 캐시 크기
CACHE_TTL_SECONDS = 3600  # 캐시 TTL (1시간)

# 성능 관련 상수
MAX_CONCURRENT_VALIDATIONS = 5  # 최대 동시 검증 수
MEMORY_WARNING_THRESHOLD_MB = 1000  # 메모리 경고 임계값 (MB)

# 파일 이름 패턴
RESULT_FILE_PATTERN = "result_{document_name}_{timestamp}.json"
DEBUG_FILE_PATTERN = "debug_{document_name}_{timestamp}.json"
ANNOTATED_PDF_PATTERN = "annotated_{document_name}_{timestamp}.pdf"

# 디렉토리 구조
COMPANY_FOLDERS = [
    "삼성화재", 
    "DB손해보험", 
    "현대해상", 
    "KB손해보험", 
    "메리츠화재"
]

# 결과 분류
RESULT_TYPES = ["success", "fail"]

# 버전 정보
VERSION = "2.0.0"
APPLICATION_NAME = "PDF Validator System"

# 백업 관련 상수
AUTO_BACKUP_ENABLED = True
BACKUP_RETENTION_DAYS = 30
BACKUP_PREFIX = "backup_"

# 지원하는 이미지 포맷
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]

# 통계 관련 상수
STATISTICS_REFRESH_INTERVAL = 300  # 5분
RECENT_RESULTS_LIMIT = 50

# 에러 재시도 관련
MAX_RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 1

# Tesseract 관련
TESSERACT_EXECUTABLE = "tesseract.exe"
TESSDATA_SUBDIR = "tessdata"
REQUIRED_LANGUAGES = ["eng", "kor"]
