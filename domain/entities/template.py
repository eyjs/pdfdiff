"""
Template Entity
PDF 검증을 위한 템플릿 정보
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

from domain.entities.roi import ROI


@dataclass
class Template:
    """
    PDF 검증 템플릿
    
    Attributes:
        name: 템플릿 이름
        original_pdf_path: 원본 PDF 파일 경로
        rois: ROI 딕셔너리 {roi_name: ROI}
        description: 템플릿 설명
        created_at: 생성일시
        updated_at: 수정일시
    """
    name: str
    original_pdf_path: str
    rois: Dict[str, ROI] = field(default_factory=dict)
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.name.strip():
            raise ValueError("템플릿 이름은 필수입니다")
        
        if not self.original_pdf_path.strip():
            raise ValueError("원본 PDF 경로는 필수입니다")
    
    def add_roi(self, roi: ROI) -> None:
        """ROI 추가"""
        if roi.name in self.rois:
            raise ValueError(f"ROI '{roi.name}'이 이미 존재합니다")
        
        self.rois[roi.name] = roi
    
    def remove_roi(self, roi_name: str) -> bool:
        """ROI 제거"""
        if roi_name in self.rois:
            del self.rois[roi_name]
            return True
        return False
    
    def get_roi(self, roi_name: str) -> Optional[ROI]:
        """ROI 조회"""
        return self.rois.get(roi_name)
    
    def get_rois_by_page(self, page: int) -> List[ROI]:
        """특정 페이지의 ROI들 반환"""
        return [roi for roi in self.rois.values() if roi.page == page]
    
    def get_total_pages(self) -> int:
        """사용된 페이지 수 반환"""
        if not self.rois:
            return 0
        return max(roi.page for roi in self.rois.values()) + 1
    
    def get_roi_count(self) -> int:
        """총 ROI 개수"""
        return len(self.rois)
    
    def get_anchored_roi_count(self) -> int:
        """앵커가 있는 ROI 개수"""
        return sum(1 for roi in self.rois.values() if roi.has_anchor())
    
    @property
    def pdf_path_exists(self) -> bool:
        """원본 PDF 파일 존재 여부"""
        return Path(self.original_pdf_path).exists()
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (저장용)"""
        return {
            "original_pdf_path": self.original_pdf_path,
            "rois": {name: roi.to_dict() for name, roi in self.rois.items()},
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'Template':
        """딕셔너리에서 템플릿 생성"""
        rois = {}
        for roi_name, roi_data in data.get("rois", {}).items():
            rois[roi_name] = ROI.from_dict(roi_name, roi_data)
        
        return cls(
            name=name,
            original_pdf_path=data["original_pdf_path"],
            rois=rois,
            description=data.get("description"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
