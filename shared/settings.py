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
    from shared.utils import ConfigUtils
    from shared.exceptions import *
except ImportError:
    # 모듈 경로 문제 해결
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from shared.constants import *
    from shared.utils import ConfigUtils
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


class Settings:
    """애플리케이션 전역 설정 관리자"""

    def __init__(self, config_file: str = "settings.json"):
        self.base_dir = self._get_application_path()
        self.config_file = Path(self.base_dir) / config_file

        # 기본 설정 인스턴스
        self.tesseract = TesseractSettings()
        self.ui = UISettings()
        self.validation = ValidationSettings()
        self.storage = StorageSettings()

        # 저장소 경로 동적 설정
        self.storage.templates_file = str(Path(self.base_dir) / DEFAULT_TEMPLATE_FILE)

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
            self._update_from_dict(self.storage, config.get("storage", {}))

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

        tesseract_dir = Path(self.base_dir) / self.storage.resources_directory / "vendor" / "tesseract"

        exe_path = tesseract_dir / TESSERACT_EXECUTABLE
        tessdata_path = tesseract_dir / TESSDATA_SUBDIR

        if exe_path.exists():
            self.tesseract.executable_path = str(exe_path.absolute())

        if tessdata_path.exists() and tessdata_path.is_dir():
            self.tesseract.tessdata_path = str(tessdata_path.absolute())

        if self.tesseract.is_configured():
            self.save()

    def _get_application_path(self) -> str:
        """
        애플리케이션의 루트 경로를 반환합니다.
        """
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            # 수정: settings.py의 새 위치(config/)에 맞게 경로 계산 수정
            return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 전역 설정 인스턴스 생성
settings = Settings()
