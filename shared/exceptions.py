"""
Custom Exceptions
애플리케이션별 예외 클래스들
"""


class PDFValidatorException(Exception):
    """PDF 검증 시스템의 기본 예외"""
    pass


class TemplateException(PDFValidatorException):
    """템플릿 관련 예외"""
    pass


class TemplateNotFoundError(TemplateException):
    """템플릿을 찾을 수 없음"""
    
    def __init__(self, template_name: str):
        super().__init__(f"템플릿 '{template_name}'을 찾을 수 없습니다")
        self.template_name = template_name


class TemplateAlreadyExistsError(TemplateException):
    """템플릿이 이미 존재함"""
    
    def __init__(self, template_name: str):
        super().__init__(f"템플릿 '{template_name}'이 이미 존재합니다")
        self.template_name = template_name


class InvalidTemplateError(TemplateException):
    """유효하지 않은 템플릿"""
    
    def __init__(self, template_name: str, reason: str):
        super().__init__(f"템플릿 '{template_name}'이 유효하지 않습니다: {reason}")
        self.template_name = template_name
        self.reason = reason


class DocumentException(PDFValidatorException):
    """문서 관련 예외"""
    pass


class DocumentNotFoundError(DocumentException):
    """문서를 찾을 수 없음"""
    
    def __init__(self, file_path: str):
        super().__init__(f"문서 '{file_path}'를 찾을 수 없습니다")
        self.file_path = file_path


class InvalidDocumentError(DocumentException):
    """유효하지 않은 문서"""
    
    def __init__(self, file_path: str, reason: str):
        super().__init__(f"문서 '{file_path}'가 유효하지 않습니다: {reason}")
        self.file_path = file_path
        self.reason = reason


class DocumentCorruptedError(DocumentException):
    """손상된 문서"""
    
    def __init__(self, file_path: str):
        super().__init__(f"문서 '{file_path}'가 손상되었습니다")
        self.file_path = file_path


class ValidationException(PDFValidatorException):
    """검증 관련 예외"""
    pass


class ValidationConfigError(ValidationException):
    """검증 설정 오류"""
    
    def __init__(self, message: str):
        super().__init__(f"검증 설정 오류: {message}")


class ValidationProcessError(ValidationException):
    """검증 처리 오류"""
    
    def __init__(self, roi_name: str, message: str):
        super().__init__(f"ROI '{roi_name}' 검증 오류: {message}")
        self.roi_name = roi_name


class ROIException(PDFValidatorException):
    """ROI 관련 예외"""
    pass


class InvalidROIError(ROIException):
    """유효하지 않은 ROI"""
    
    def __init__(self, roi_name: str, reason: str):
        super().__init__(f"ROI '{roi_name}'이 유효하지 않습니다: {reason}")
        self.roi_name = roi_name
        self.reason = reason


class ROINotFoundError(ROIException):
    """ROI를 찾을 수 없음"""
    
    def __init__(self, roi_name: str):
        super().__init__(f"ROI '{roi_name}'을 찾을 수 없습니다")
        self.roi_name = roi_name


class ServiceException(PDFValidatorException):
    """서비스 관련 예외"""
    pass


class OCRServiceError(ServiceException):
    """OCR 서비스 오류"""
    
    def __init__(self, message: str):
        super().__init__(f"OCR 서비스 오류: {message}")


class PDFServiceError(ServiceException):
    """PDF 서비스 오류"""
    
    def __init__(self, message: str):
        super().__init__(f"PDF 서비스 오류: {message}")


class ComputerVisionServiceError(ServiceException):
    """컴퓨터 비전 서비스 오류"""
    
    def __init__(self, message: str):
        super().__init__(f"컴퓨터 비전 서비스 오류: {message}")


class RepositoryException(PDFValidatorException):
    """저장소 관련 예외"""
    pass


class DataPersistenceError(RepositoryException):
    """데이터 저장 오류"""
    
    def __init__(self, operation: str, details: str = ""):
        message = f"데이터 {operation} 실패"
        if details:
            message += f": {details}"
        super().__init__(message)
        self.operation = operation


class DataIntegrityError(RepositoryException):
    """데이터 무결성 오류"""
    
    def __init__(self, message: str):
        super().__init__(f"데이터 무결성 오류: {message}")


class ConfigurationException(PDFValidatorException):
    """설정 관련 예외"""
    pass


class MissingConfigurationError(ConfigurationException):
    """필수 설정 누락"""
    
    def __init__(self, config_key: str):
        super().__init__(f"필수 설정 '{config_key}'가 누락되었습니다")
        self.config_key = config_key


class InvalidConfigurationError(ConfigurationException):
    """잘못된 설정"""
    
    def __init__(self, config_key: str, reason: str):
        super().__init__(f"설정 '{config_key}'가 잘못되었습니다: {reason}")
        self.config_key = config_key
        self.reason = reason
