"""
ROI (Region of Interest) Entity
검증 대상 영역을 나타내는 핵심 엔티티
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ValidationMethod(Enum):
    """검증 방식"""
    OCR = "ocr"
    CONTOUR = "contour"


@dataclass
class ROI:
    """
    PDF 문서 내 검증 대상 영역
    
    Attributes:
        name: ROI 식별 이름
        page: 페이지 번호 (0부터 시작)
        coords: [x1, y1, x2, y2] 좌표
        anchor_coords: 앵커 영역 좌표 (위치 추적용)
        method: 검증 방식 (OCR 또는 CONTOUR)
        threshold: 검증 임계값
    """
    name: str
    page: int
    coords: List[float]  # [x1, y1, x2, y2]
    method: ValidationMethod
    threshold: int
    anchor_coords: Optional[List[float]] = None  # [x1, y1, x2, y2]
    
    def __post_init__(self):
        """데이터 검증"""
        if len(self.coords) != 4:
            raise ValueError("좌표는 [x1, y1, x2, y2] 형식이어야 합니다")
        
        if self.anchor_coords and len(self.anchor_coords) != 4:
            raise ValueError("앵커 좌표는 [x1, y1, x2, y2] 형식이어야 합니다")
        
        if self.page < 0:
            raise ValueError("페이지 번호는 0 이상이어야 합니다")
        
        if self.threshold < 0:
            raise ValueError("임계값은 0 이상이어야 합니다")
    
    @property
    def width(self) -> float:
        """ROI 너비"""
        return abs(self.coords[2] - self.coords[0])
    
    @property
    def height(self) -> float:
        """ROI 높이"""
        return abs(self.coords[3] - self.coords[1])
    
    @property
    def area(self) -> float:
        """ROI 면적"""
        return self.width * self.height
    
    @property
    def center(self) -> tuple[float, float]:
        """ROI 중심점"""
        x = (self.coords[0] + self.coords[2]) / 2
        y = (self.coords[1] + self.coords[3]) / 2
        return (x, y)
    
    def has_anchor(self) -> bool:
        """앵커 여부 확인"""
        return self.anchor_coords is not None
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (저장용)"""
        result = {
            "page": self.page,
            "coords": self.coords,
            "method": self.method.value,
            "threshold": self.threshold
        }
        
        if self.anchor_coords:
            result["anchor_coords"] = self.anchor_coords
            
        return result
    
    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'ROI':
        """딕셔너리에서 ROI 생성"""
        return cls(
            name=name,
            page=data["page"],
            coords=data["coords"],
            method=ValidationMethod(data["method"]),
            threshold=data["threshold"],
            anchor_coords=data.get("anchor_coords")
        )
