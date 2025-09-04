"""
Type Definitions
타입 힌트와 커스텀 타입 정의
"""
from typing import TypeVar, Generic, Union, Tuple, List, Dict, Any, Optional, Callable
from pathlib import Path

# 기본 타입 별칭
FilePath = Union[str, Path]
Coordinates = Tuple[float, float, float, float]  # [x1, y1, x2, y2]
Point = Tuple[float, float]  # (x, y)
Size = Tuple[int, int]  # (width, height)
RGB = Tuple[int, int, int]  # (r, g, b)
RGBA = Tuple[int, int, int, int]  # (r, g, b, a)

# 검증 관련 타입
ValidationResult = Dict[str, Any]
ROIData = Dict[str, Any]
TemplateData = Dict[str, Any]
DebugInfo = Dict[str, Any]

# 콜백 타입
ProgressCallback = Callable[[str, int, int], None]  # (message, current, total)
ValidationCallback = Callable[[ValidationResult], None]
ErrorCallback = Callable[[Exception], None]

# 설정 타입
ConfigDict = Dict[str, Any]
DatabaseConfig = Dict[str, str]
UIConfig = Dict[str, Union[int, str, bool]]

# 제네릭 타입
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Repository 관련 타입
EntityId = Union[str, int]
QueryFilter = Dict[str, Any]
SortOrder = Dict[str, str]  # {"field": "asc|desc"}

# 이미지 처리 관련 타입
ImageArray = Any  # numpy.ndarray (순환 참조 방지)
ImageData = Union[bytes, ImageArray]
ProcessingParameters = Dict[str, Union[int, float, str]]

# 비동기 관련 타입
AsyncCallback = Callable[..., Any]
TaskResult = Union[Any, Exception]

# 통계 관련 타입
StatisticsData = Dict[str, Union[int, float, str]]
MetricsData = Dict[str, float]

# 이벤트 관련 타입
EventData = Dict[str, Any]
EventHandler = Callable[[EventData], None]

# 로깅 관련 타입
LogLevel = Union[str, int]
LogMessage = str

# 네트워크 관련 타입 (미래 확장용)
URLString = str
HeaderDict = Dict[str, str]
QueryParams = Dict[str, Union[str, int]]

# 파일 처리 관련 타입
FileMetadata = Dict[str, Union[str, int, float]]
FileContent = Union[str, bytes]
FileInfo = Tuple[FilePath, int, str]  # (path, size, modified_date)

# 인터페이스 관련 타입 (Protocol 대신 사용)
ServiceInterface = Any
RepositoryInterface = Any
ControllerInterface = Any

# 에러 처리 관련 타입
ErrorCode = str
ErrorDetails = Dict[str, Any]
ValidationError = Tuple[str, str]  # (field, message)

# 캐시 관련 타입
CacheKey = str
CacheValue = Any
CacheEntry = Tuple[CacheValue, float]  # (value, timestamp)

# 보안 관련 타입 (미래 확장용)
Token = str
Permissions = List[str]
UserContext = Dict[str, Any]

# 국제화 관련 타입
LanguageCode = str  # "ko", "en", etc.
TranslationKey = str
TranslationDict = Dict[LanguageCode, str]

# 플러그인 관련 타입 (미래 확장용)
PluginName = str
PluginConfig = Dict[str, Any]
PluginMetadata = Dict[str, str]
