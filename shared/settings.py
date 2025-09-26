"""
Application Settings
애플리케이션 설정 관리 (프로젝트 최상위 config 폴더용)
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# shared 폴더에 있는 상수와 유틸리티를 가져옵니다.
try:
    from shared.constants import *
    from shared.utils import ConfigUtils, get_base_path
    from shared.exceptions import *
except ImportError:
    # 모듈 경로 문제 해결
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from shared.constants import *
    from shared.utils import ConfigUtils, get_base_path
    from shared.exceptions import *


@dataclass
class TesseractSettings:
    """Tesseract OCR 설정"""
    executable_path: str = ""
    tessdata_path: str = ""
    languages: str = OCR_LANGUAGES
    config_default: str = OCR_CONFIG_DEFAULT
    config_single_word: str = OCR_CONFIG_SINGLE_WORD
    confidence_threshold: int = OCR_CONFIDENCE_THRESHOLD

    def is_configured(self) -> bool:
        """Tesseract 설정 여부 확인"""
        return (bool(self.executable_path) and
                Path(self.executable_path).exists() and
                bool(self.tessdata_path) and
                Path(self.tessdata_path).exists())


@dataclass
class UISettings:
    """UI 설정"""
    window_width: int = DEFAULT_WINDOW_WIDTH
    window_height: int = DEFAULT_WINDOW_HEIGHT
    min_window_width: int = MIN_WINDOW_WIDTH
    min_window_height: int = MIN_WINDOW_HEIGHT
    remember_window_size: bool = True
    theme: str = "default"
    language: str = "ko"


@dataclass
class ValidationSettings:
    """검증 설정"""
    max_processing_time: int = MAX_PROCESSING_TIME
    default_ssim_threshold: float = DEFAULT_SSIM_THRESHOLD
    layout_detection_scale: float = LAYOUT_DETECTION_SCALE
    max_concurrent_validations: int = MAX_CONCURRENT_VALIDATIONS
    enable_debug_mode: bool = False
    save_debug_images: bool = True


@dataclass
class StorageSettings:
    """저장소 설정"""
    templates_file: str = ""  # 동적으로 경로 설정
    output_directory: str = DEFAULT_OUTPUT_DIR
    input_directory: str = DEFAULT_INPUT_DIR
    resources_directory: str = DEFAULT_RESOURCES_DIR
    auto_backup: bool = AUTO_BACKUP_ENABLED
    backup_retention_days: int = BACKUP_RETENTION_DAYS


@dataclass
class OcrEngineSelectionSettings: # 새로운 dataclass 정의
    default_engine: str = "comparative"
    easyocr_gpu_enabled: bool = False

@dataclass
class EasyocrSettings:
    """EasyOCR 설정"""
    model_storage_directory: str = EASYOCR_MODEL_DIR

class Settings:
    """애플리케이션 전역 설정 관리자"""

    def __init__(self, config_file: str = "settings.json"):
        self.base_dir = get_base_path() # 공통 함수 사용
        self.config_file = self.base_dir / config_file

        # 기본 설정 인스턴스
        self.tesseract = TesseractSettings()
        self.ui = UISettings()
        self.validation = ValidationSettings()
        self.storage = StorageSettings()
        self.ocr_engine_selection = OcrEngineSelectionSettings() # 추가
        self.easyocr = EasyocrSettings() # 추가
        self.easyocr.model_storage_directory = str(self.base_dir / EASYOCR_MODEL_DIR) # EasyOCR 모델 경로 절대 경로로 설정

        # 저장소 경로 설정 (get_base_path가 환경에 맞는 루트를 반환)
        self.storage.templates_file = str(self.base_dir / DEFAULT_TEMPLATE_FILE)

        # 추가 설정
        self.debug_enabled = False
        self.log_level = "INFO"
        self.version = VERSION

        # 설정 로드
        self.load()

        # Tesseract 자동 설정
        self._setup_tesseract()

    def load(self) -> None:
        """설정 파일에서 로드"""
        try:
            if not self.config_file.exists():
                self.save()  # 기본 설정 저장
                return

            config = ConfigUtils.load_config(str(self.config_file))

            self._update_from_dict(self.tesseract, config.get("tesseract", {}))
            self._update_from_dict(self.ui, config.get("ui", {}))
            self._update_from_dict(self.validation, config.get("validation", {}))
            self._update_from_dict(self.ocr_engine_selection, config.get("ocr_engine_selection", {})) # 추가
            self._update_from_dict(self.easyocr, config.get("easyocr", {})) # 추가
            storage_config = config.get("storage", {})
            storage_config.pop('templates_file', None)  # 코드에서 설정한 경로를 유지하기 위해 파일 값 무시
            self._update_from_dict(self.storage, storage_config)

            self.debug_enabled = config.get("debug_enabled", False)
            self.log_level = config.get("log_level", "INFO")

        except Exception as e:
            raise ConfigurationException(f"설정 로드 실패: {str(e)}")

    def save(self) -> None:
        """설정을 파일에 저장"""
        try:
            config = {
                "version": self.version,
                "debug_enabled": self.debug_enabled,
                "log_level": self.log_level,
                "tesseract": self.tesseract.__dict__,
                "ui": self.ui.__dict__,
                "validation": self.validation.__dict__,
                "ocr_engine_selection": self.ocr_engine_selection.__dict__, # 추가
                "easyocr": self.easyocr.__dict__, # 추가
                "storage": self.storage.__dict__,
            }
            ConfigUtils.save_config(config, str(self.config_file))
        except Exception as e:
            raise ConfigurationException(f"설정 저장 실패: {str(e)}")

    def _update_from_dict(self, dataclass_instance, config_dict):
        """dict로부터 dataclass 인스턴스를 업데이트합니다."""
        for key, value in config_dict.items():
            if hasattr(dataclass_instance, key):
                setattr(dataclass_instance, key, value)

    def _setup_tesseract(self) -> None:
        """Tesseract 자동 설정"""
        if self.tesseract.is_configured():
            return

        # 이제 Tesseract 경로는 TesseractOcrService에서 중앙 관리하므로
        # 이 메소드는 settings.json에 경로가 수동으로 지정된 경우에만 사용되거나, 비워둘 수 있습니다.
        # 지금은 TesseractOcrService에 위임하므로 이 부분을 비워둡니다.
        pass

# 전역 설정 인스턴스 생성
settings = Settings()
