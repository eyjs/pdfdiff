"""
Application Settings
애플리케이션 설정 관리
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from shared.constants import *
from shared.utils import ConfigUtils, FileUtils
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
    templates_file: str = DEFAULT_TEMPLATE_FILE
    output_directory: str = DEFAULT_OUTPUT_DIR
    input_directory: str = DEFAULT_INPUT_DIR
    resources_directory: str = DEFAULT_RESOURCES_DIR
    auto_backup: bool = AUTO_BACKUP_ENABLED
    backup_retention_days: int = BACKUP_RETENTION_DAYS


class Settings:
    """애플리케이션 전역 설정 관리자"""
    
    def __init__(self, config_file: str = "settings.json"):
        self.config_file = Path(config_file)
        
        # 기본 설정 인스턴스
        self.tesseract = TesseractSettings()
        self.ui = UISettings()
        self.validation = ValidationSettings()
        self.storage = StorageSettings()
        
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
            
            config = ConfigUtils.load_config(self.config_file)
            
            # Tesseract 설정
            if "tesseract" in config:
                t_config = config["tesseract"]
                self.tesseract.executable_path = t_config.get("executable_path", "")
                self.tesseract.tessdata_path = t_config.get("tessdata_path", "")
                self.tesseract.languages = t_config.get("languages", OCR_LANGUAGES)
                self.tesseract.config_default = t_config.get("config_default", OCR_CONFIG_DEFAULT)
                self.tesseract.config_single_word = t_config.get("config_single_word", OCR_CONFIG_SINGLE_WORD)
                self.tesseract.confidence_threshold = t_config.get("confidence_threshold", OCR_CONFIDENCE_THRESHOLD)
            
            # UI 설정
            if "ui" in config:
                ui_config = config["ui"]
                self.ui.window_width = ui_config.get("window_width", DEFAULT_WINDOW_WIDTH)
                self.ui.window_height = ui_config.get("window_height", DEFAULT_WINDOW_HEIGHT)
                self.ui.min_window_width = ui_config.get("min_window_width", MIN_WINDOW_WIDTH)
                self.ui.min_window_height = ui_config.get("min_window_height", MIN_WINDOW_HEIGHT)
                self.ui.remember_window_size = ui_config.get("remember_window_size", True)
                self.ui.theme = ui_config.get("theme", "default")
                self.ui.language = ui_config.get("language", "ko")
            
            # 검증 설정
            if "validation" in config:
                v_config = config["validation"]
                self.validation.max_processing_time = v_config.get("max_processing_time", MAX_PROCESSING_TIME)
                self.validation.default_ssim_threshold = v_config.get("default_ssim_threshold", DEFAULT_SSIM_THRESHOLD)
                self.validation.layout_detection_scale = v_config.get("layout_detection_scale", LAYOUT_DETECTION_SCALE)
                self.validation.max_concurrent_validations = v_config.get("max_concurrent_validations", MAX_CONCURRENT_VALIDATIONS)
                self.validation.enable_debug_mode = v_config.get("enable_debug_mode", False)
                self.validation.save_debug_images = v_config.get("save_debug_images", True)
            
            # 저장소 설정
            if "storage" in config:
                s_config = config["storage"]
                self.storage.templates_file = s_config.get("templates_file", DEFAULT_TEMPLATE_FILE)
                self.storage.output_directory = s_config.get("output_directory", DEFAULT_OUTPUT_DIR)
                self.storage.input_directory = s_config.get("input_directory", DEFAULT_INPUT_DIR)
                self.storage.resources_directory = s_config.get("resources_directory", DEFAULT_RESOURCES_DIR)
                self.storage.auto_backup = s_config.get("auto_backup", AUTO_BACKUP_ENABLED)
                self.storage.backup_retention_days = s_config.get("backup_retention_days", BACKUP_RETENTION_DAYS)
            
            # 기타 설정
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
                "tesseract": {
                    "executable_path": self.tesseract.executable_path,
                    "tessdata_path": self.tesseract.tessdata_path,
                    "languages": self.tesseract.languages,
                    "config_default": self.tesseract.config_default,
                    "config_single_word": self.tesseract.config_single_word,
                    "confidence_threshold": self.tesseract.confidence_threshold
                },
                "ui": {
                    "window_width": self.ui.window_width,
                    "window_height": self.ui.window_height,
                    "min_window_width": self.ui.min_window_width,
                    "min_window_height": self.ui.min_window_height,
                    "remember_window_size": self.ui.remember_window_size,
                    "theme": self.ui.theme,
                    "language": self.ui.language
                },
                "validation": {
                    "max_processing_time": self.validation.max_processing_time,
                    "default_ssim_threshold": self.validation.default_ssim_threshold,
                    "layout_detection_scale": self.validation.layout_detection_scale,
                    "max_concurrent_validations": self.validation.max_concurrent_validations,
                    "enable_debug_mode": self.validation.enable_debug_mode,
                    "save_debug_images": self.validation.save_debug_images
                },
                "storage": {
                    "templates_file": self.storage.templates_file,
                    "output_directory": self.storage.output_directory,
                    "input_directory": self.storage.input_directory,
                    "resources_directory": self.storage.resources_directory,
                    "auto_backup": self.storage.auto_backup,
                    "backup_retention_days": self.storage.backup_retention_days
                }
            }
            
            ConfigUtils.save_config(config, self.config_file)
        except Exception as e:
            raise ConfigurationException(f"설정 저장 실패: {str(e)}")
    
    def _setup_tesseract(self) -> None:
        """Tesseract 자동 설정"""
        # 이미 설정되어 있으면 검증만
        if self.tesseract.is_configured():
            return
        
        # 자동 경로 탐지
        application_path = self._get_application_path()
        
        # 경로 후보들
        tesseract_candidates = [
            Path(application_path) / "resources" / "vendor" / "tesseract" / TESSERACT_EXECUTABLE,
            Path(application_path) / "vendor" / "tesseract" / TESSERACT_EXECUTABLE,
            Path("resources") / "vendor" / "tesseract" / TESSERACT_EXECUTABLE,
            Path("vendor") / "tesseract" / TESSERACT_EXECUTABLE
        ]
        
        tessdata_candidates = [
            Path(application_path) / "resources" / "vendor" / "tesseract" / TESSDATA_SUBDIR,
            Path(application_path) / "vendor" / "tesseract" / TESSDATA_SUBDIR,
            Path("resources") / "vendor" / "tesseract" / TESSDATA_SUBDIR,
            Path("vendor") / "tesseract" / TESSDATA_SUBDIR
        ]
        
        # Tesseract 실행파일 찾기
        for candidate in tesseract_candidates:
            if candidate.exists():
                self.tesseract.executable_path = str(candidate.absolute())
                break
        
        # Tessdata 폴더 찾기
        for candidate in tessdata_candidates:
            if candidate.exists() and candidate.is_dir():
                self.tesseract.tessdata_path = str(candidate.absolute())
                break
        
        # 언어팩 확인
        if self.tesseract.tessdata_path:
            tessdata_path = Path(self.tesseract.tessdata_path)
            missing_languages = []
            
            for lang in REQUIRED_LANGUAGES:
                lang_file = tessdata_path / f"{lang}.traineddata"
                if not lang_file.exists():
                    missing_languages.append(lang)
            
            if missing_languages:
                print(f"⚠️ 누락된 언어팩: {', '.join(missing_languages)}")
    
    def _get_application_path(self) -> str:
        """애플리케이션 경로 반환"""
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 경우
            return os.path.dirname(sys.executable)
        else:
            # 개발 환경
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    def validate(self) -> Dict[str, list]:
        """설정 유효성 검사"""
        warnings = []
        errors = []
        
        # Tesseract 설정 검증
        if not self.tesseract.is_configured():
            errors.append("Tesseract OCR이 설정되지 않았습니다")
        
        # 디렉토리 존재 확인
        required_dirs = [
            self.storage.output_directory,
            self.storage.input_directory,
            self.storage.resources_directory
        ]
        
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                warnings.append(f"디렉토리가 존재하지 않습니다: {dir_path}")
        
        # 템플릿 파일 확인
        if not Path(self.storage.templates_file).exists():
            warnings.append(f"템플릿 파일이 존재하지 않습니다: {self.storage.templates_file}")
        
        # UI 설정 검증
        if self.ui.window_width < self.ui.min_window_width:
            errors.append("창 너비가 최소값보다 작습니다")
        
        if self.ui.window_height < self.ui.min_window_height:
            errors.append("창 높이가 최소값보다 작습니다")
        
        return {
            "errors": errors,
            "warnings": warnings
        }
    
    def reset_to_defaults(self) -> None:
        """기본값으로 재설정"""
        self.tesseract = TesseractSettings()
        self.ui = UISettings()
        self.validation = ValidationSettings()
        self.storage = StorageSettings()
        self.debug_enabled = False
        self.log_level = "INFO"
        
        # Tesseract 재설정
        self._setup_tesseract()
    
    def get_summary(self) -> Dict[str, Any]:
        """설정 요약 정보"""
        return {
            "version": self.version,
            "tesseract_configured": self.tesseract.is_configured(),
            "tesseract_executable": self.tesseract.executable_path,
            "tessdata_path": self.tesseract.tessdata_path,
            "debug_enabled": self.debug_enabled,
            "templates_file": self.storage.templates_file,
            "output_directory": self.storage.output_directory,
            "ui_settings": {
                "window_size": f"{self.ui.window_width}x{self.ui.window_height}",
                "theme": self.ui.theme,
                "language": self.ui.language
            }
        }


# 전역 설정 인스턴스
settings = Settings()
