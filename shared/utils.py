"""
Utility Functions
공통 유틸리티 함수들
"""
import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import time

from shared.constants import *
from shared.types import *
from shared.exceptions import *


class FileUtils:
    """파일 관련 유틸리티"""
    
    @staticmethod
    def ensure_directory(path: FilePath) -> Path:
        """디렉토리 존재 확인 및 생성"""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    
    @staticmethod
    def get_file_size_mb(file_path: FilePath) -> float:
        """파일 크기 (MB) 반환"""
        return Path(file_path).stat().st_size / (1024 * 1024)
    
    @staticmethod
    def is_pdf_file(file_path: FilePath) -> bool:
        """PDF 파일 여부 확인"""
        return Path(file_path).suffix.lower() == PDF_EXTENSION
    
    @staticmethod
    def get_relative_path(file_path: FilePath, base_path: FilePath) -> str:
        """상대 경로 반환"""
        try:
            return str(Path(file_path).relative_to(base_path))
        except ValueError:
            return str(file_path)
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """안전한 파일명 생성 (특수문자 제거)"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    @staticmethod
    def backup_file(file_path: FilePath, backup_dir: Optional[FilePath] = None) -> Path:
        """파일 백업"""
        original = Path(file_path)
        if not original.exists():
            raise DocumentNotFoundError(str(file_path))
        
        backup_dir = backup_dir or original.parent / "backups"
        FileUtils.ensure_directory(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{BACKUP_PREFIX}{original.stem}_{timestamp}{original.suffix}"
        backup_path = Path(backup_dir) / backup_name
        
        import shutil
        shutil.copy2(original, backup_path)
        return backup_path


class JSONUtils:
    """JSON 관련 유틸리티"""
    
    @staticmethod
    def load_json(file_path: FilePath, encoding: str = 'utf-8') -> Dict[str, Any]:
        """JSON 파일 로드"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except FileNotFoundError:
            raise DocumentNotFoundError(str(file_path))
        except json.JSONDecodeError as e:
            raise DataIntegrityError(f"JSON 파싱 오류: {e}")
    
    @staticmethod
    def save_json(data: Dict[str, Any], file_path: FilePath, encoding: str = 'utf-8', indent: int = 2) -> None:
        """JSON 파일 저장"""
        try:
            FileUtils.ensure_directory(Path(file_path).parent)
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
        except Exception as e:
            raise DataPersistenceError("저장", str(e))
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], required_keys: List[str]) -> bool:
        """JSON 스키마 검증"""
        return all(key in data for key in required_keys)


class HashUtils:
    """해시 관련 유틸리티"""
    
    @staticmethod
    def calculate_file_hash(file_path: FilePath, algorithm: str = 'md5') -> str:
        """파일 해시 계산"""
        hash_obj = hashlib.new(algorithm)
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except FileNotFoundError:
            raise DocumentNotFoundError(str(file_path))
    
    @staticmethod
    def calculate_string_hash(text: str, algorithm: str = 'md5') -> str:
        """문자열 해시 계산"""
        return hashlib.new(algorithm, text.encode('utf-8')).hexdigest()


class TimeUtils:
    """시간 관련 유틸리티"""
    
    @staticmethod
    def get_timestamp() -> str:
        """현재 타임스탬프 (ISO 형식)"""
        return datetime.now().isoformat()
    
    @staticmethod
    def get_timestamp_filename() -> str:
        """파일명용 타임스탬프"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """초를 사람이 읽기 쉬운 형태로 변환"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.0f}s"
    
    @staticmethod
    def is_expired(timestamp: datetime, ttl_seconds: int) -> bool:
        """TTL 기반 만료 여부 확인"""
        expiry_time = timestamp + timedelta(seconds=ttl_seconds)
        return datetime.now() > expiry_time


class ValidationUtils:
    """검증 관련 유틸리티"""
    
    @staticmethod
    def validate_coordinates(coords: Coordinates) -> bool:
        """좌표 유효성 검사"""
        if not coords or len(coords) != 4:
            return False
        
        x1, y1, x2, y2 = coords
        
        # 좌표값이 숫자인지 확인
        if not all(isinstance(c, (int, float)) for c in coords):
            return False
        
        # 좌표값이 양수인지 확인
        if not all(c >= 0 for c in coords):
            return False
        
        # 면적이 양수인지 확인
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return width > MIN_ROI_SIZE and height > MIN_ROI_SIZE
    
    @staticmethod
    def normalize_coordinates(coords: Coordinates) -> Coordinates:
        """좌표 정규화 (좌상단, 우하단 순으로)"""
        x1, y1, x2, y2 = coords
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    
    @staticmethod
    def calculate_area(coords: Coordinates) -> float:
        """좌표로부터 면적 계산"""
        x1, y1, x2, y2 = coords
        return abs((x2 - x1) * (y2 - y1))
    
    @staticmethod
    def calculate_center(coords: Coordinates) -> Point:
        """좌표로부터 중심점 계산"""
        x1, y1, x2, y2 = coords
        return ((x1 + x2) / 2, (y1 + y2) / 2)


class StringUtils:
    """문자열 관련 유틸리티"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """텍스트 정리 (공백, 특수문자 제거)"""
        import re
        return re.sub(r'[\s\W_]+', '', text)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """텍스트 자르기"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    @staticmethod
    def generate_unique_name(base_name: str, existing_names: List[str]) -> str:
        """중복되지 않는 이름 생성"""
        if base_name not in existing_names:
            return base_name
        
        counter = 1
        while f"{base_name}_{counter}" in existing_names:
            counter += 1
        
        return f"{base_name}_{counter}"


class LoggingUtils:
    """로깅 관련 유틸리티"""
    
    @staticmethod
    def setup_logger(name: str, level: LogLevel = logging.INFO, 
                    log_file: Optional[FilePath] = None) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 핸들러가 이미 있으면 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 파일 핸들러 (옵션)
        if log_file:
            FileUtils.ensure_directory(Path(log_file).parent)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger


class PerformanceUtils:
    """성능 관련 유틸리티"""
    
    @staticmethod
    def measure_time(func):
        """함수 실행 시간 측정 데코레이터"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                print(f"{func.__name__} 실행 시간: {TimeUtils.format_duration(execution_time)}")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"{func.__name__} 실행 시간 (오류): {TimeUtils.format_duration(execution_time)}")
                raise
        return wrapper
    
    @staticmethod
    def get_memory_usage() -> float:
        """현재 메모리 사용량 (MB) 반환"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    @staticmethod
    def check_memory_warning() -> bool:
        """메모리 사용량 경고 확인"""
        current_usage = PerformanceUtils.get_memory_usage()
        return current_usage > MEMORY_WARNING_THRESHOLD_MB


class ConfigUtils:
    """설정 관련 유틸리티"""
    
    @staticmethod
    def load_config(config_file: FilePath = "config.json") -> ConfigDict:
        """설정 파일 로드"""
        if not Path(config_file).exists():
            return {}
        return JSONUtils.load_json(config_file)
    
    @staticmethod
    def save_config(config: ConfigDict, config_file: FilePath = "config.json") -> None:
        """설정 파일 저장"""
        JSONUtils.save_json(config, config_file)
    
    @staticmethod
    def get_config_value(config: ConfigDict, key: str, default: Any = None) -> Any:
        """설정값 조회 (중첩 키 지원)"""
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
