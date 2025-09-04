"""
Validation Result Entity
검증 결과를 나타내는 엔티티
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from domain.entities.roi import ROI
from domain.entities.document import Document


class ValidationStatus(Enum):
    """검증 상태"""
    OK = "OK"
    DEFICIENT = "DEFICIENT"
    ERROR = "ERROR"


@dataclass
class ROIValidationResult:
    """
    개별 ROI 검증 결과
    
    Attributes:
        roi_name: ROI 이름
        status: 검증 상태
        message: 검증 메시지
        details: 상세 정보
        processing_time: 처리 시간 (초)
    """
    roi_name: str
    status: ValidationStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    processing_time: Optional[float] = None
    
    @property
    def is_success(self) -> bool:
        """성공 여부"""
        return self.status == ValidationStatus.OK
    
    @property
    def is_failure(self) -> bool:
        """실패 여부"""
        return self.status in [ValidationStatus.DEFICIENT, ValidationStatus.ERROR]


@dataclass
class ValidationResult:
    """
    전체 문서 검증 결과
    
    Attributes:
        document: 검증 대상 문서
        template_name: 사용된 템플릿 이름
        roi_results: ROI별 검증 결과
        total_processing_time: 총 처리 시간
        validated_at: 검증 수행 시간
        debug_info: 디버깅 정보
    """
    document: Document
    template_name: str
    roi_results: List[ROIValidationResult] = field(default_factory=list)
    total_processing_time: Optional[float] = None
    validated_at: Optional[datetime] = None
    debug_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """기본값 설정"""
        if not self.validated_at:
            self.validated_at = datetime.now()
    
    @property
    def total_count(self) -> int:
        """총 ROI 개수"""
        return len(self.roi_results)
    
    @property
    def success_count(self) -> int:
        """성공한 ROI 개수"""
        return sum(1 for result in self.roi_results if result.is_success)
    
    @property
    def failure_count(self) -> int:
        """실패한 ROI 개수"""
        return sum(1 for result in self.roi_results if result.is_failure)
    
    @property
    def error_count(self) -> int:
        """에러가 발생한 ROI 개수"""
        return sum(1 for result in self.roi_results if result.status == ValidationStatus.ERROR)
    
    @property
    def deficient_count(self) -> int:
        """미비한 ROI 개수"""
        return sum(1 for result in self.roi_results if result.status == ValidationStatus.DEFICIENT)
    
    @property
    def success_rate(self) -> float:
        """성공률 (0.0 ~ 1.0)"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count
    
    @property
    def is_overall_success(self) -> bool:
        """전체 검증 성공 여부"""
        return self.failure_count == 0
    
    def get_failed_roi_names(self) -> List[str]:
        """실패한 ROI 이름들"""
        return [result.roi_name for result in self.roi_results if result.is_failure]
    
    def get_result_by_roi_name(self, roi_name: str) -> Optional[ROIValidationResult]:
        """ROI 이름으로 결과 조회"""
        for result in self.roi_results:
            if result.roi_name == roi_name:
                return result
        return None
    
    def add_roi_result(self, result: ROIValidationResult) -> None:
        """ROI 결과 추가"""
        self.roi_results.append(result)
    
    def get_summary(self) -> Dict[str, Any]:
        """검증 결과 요약"""
        return {
            "document_name": self.document.file_name,
            "template_name": self.template_name,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "error_count": self.error_count,
            "deficient_count": self.deficient_count,
            "success_rate": round(self.success_rate * 100, 1),
            "is_overall_success": self.is_overall_success,
            "processing_time": self.total_processing_time,
            "failed_rois": self.get_failed_roi_names()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """전체 결과를 딕셔너리로 변환"""
        return {
            "summary": self.get_summary(),
            "roi_results": [
                {
                    "roi_name": result.roi_name,
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "processing_time": result.processing_time
                }
                for result in self.roi_results
            ],
            "debug_info": self.debug_info
        }
