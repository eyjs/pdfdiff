"""
Validation Service
PDF 검증 도메인 서비스
"""
from typing import List, Optional, Dict, Any
import time
from datetime import datetime

from domain.entities.template import Template
from domain.entities.document import Document
from domain.entities.roi import ROI
from domain.entities.validation_result import ValidationResult, ROIValidationResult, ValidationStatus


class ValidationService:
    """검증 도메인 서비스"""
    
    def __init__(self):
        pass
    
    def validate_document(self, document: Document, template: Template) -> ValidationResult:
        """문서 검증 수행"""
        start_time = time.time()
        
        # 검증 결과 객체 생성
        result = ValidationResult(
            document=document,
            template_name=template.name,
            validated_at=datetime.now()
        )
        
        # ROI별 검증 수행
        for roi_name, roi in template.rois.items():
            roi_result = self._validate_single_roi(document, roi)
            result.add_roi_result(roi_result)
        
        # 총 처리 시간 계산
        result.total_processing_time = time.time() - start_time
        
        return result
    
    def _validate_single_roi(self, document: Document, roi: ROI) -> ROIValidationResult:
        """단일 ROI 검증"""
        start_time = time.time()
        
        try:
            # TODO: 실제 검증 로직은 Infrastructure 계층에서 구현
            # 여기서는 비즈니스 규칙만 정의
            
            # 기본 유효성 검사
            if not self._is_roi_valid(roi):
                return ROIValidationResult(
                    roi_name=roi.name,
                    status=ValidationStatus.ERROR,
                    message="ROI 정보가 유효하지 않습니다",
                    processing_time=time.time() - start_time
                )
            
            # 문서 유효성 검사
            if not document.exists or not document.is_pdf:
                return ROIValidationResult(
                    roi_name=roi.name,
                    status=ValidationStatus.ERROR,
                    message="문서가 유효하지 않습니다",
                    processing_time=time.time() - start_time
                )
            
            # 실제 검증은 Infrastructure의 PDF Service에서 수행
            # 여기서는 성공으로 가정
            return ROIValidationResult(
                roi_name=roi.name,
                status=ValidationStatus.OK,
                message="검증 완료",
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            return ROIValidationResult(
                roi_name=roi.name,
                status=ValidationStatus.ERROR,
                message=f"검증 중 오류 발생: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def _is_roi_valid(self, roi: ROI) -> bool:
        """ROI 유효성 검사"""
        # 좌표 유효성
        if not roi.coords or len(roi.coords) != 4:
            return False
        
        # 면적 유효성
        if roi.area <= 0:
            return False
        
        # 페이지 번호 유효성
        if roi.page < 0:
            return False
        
        # 임계값 유효성
        if roi.threshold < 0:
            return False
        
        return True
    
    def batch_validate_documents(self, documents: List[Document], template: Template) -> List[ValidationResult]:
        """다중 문서 일괄 검증"""
        results = []
        
        for document in documents:
            try:
                result = self.validate_document(document, template)
                results.append(result)
            except Exception as e:
                # 개별 문서 검증 실패 시 에러 결과 생성
                error_result = ValidationResult(
                    document=document,
                    template_name=template.name,
                    validated_at=datetime.now()
                )
                
                # 모든 ROI에 대해 에러 결과 추가
                for roi_name in template.rois.keys():
                    error_roi_result = ROIValidationResult(
                        roi_name=roi_name,
                        status=ValidationStatus.ERROR,
                        message=f"문서 처리 오류: {str(e)}"
                    )
                    error_result.add_roi_result(error_roi_result)
                
                results.append(error_result)
        
        return results
    
    def analyze_validation_results(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """검증 결과 통계 분석"""
        if not results:
            return {
                "total_documents": 0,
                "successful_documents": 0,
                "failed_documents": 0,
                "success_rate": 0.0,
                "total_rois": 0,
                "successful_rois": 0,
                "failed_rois": 0,
                "roi_success_rate": 0.0,
                "average_processing_time": 0.0,
                "common_failures": {}
            }
        
        total_documents = len(results)
        successful_documents = sum(1 for result in results if result.is_overall_success)
        failed_documents = total_documents - successful_documents
        
        total_rois = sum(result.total_count for result in results)
        successful_rois = sum(result.success_count for result in results)
        failed_rois = total_rois - successful_rois
        
        total_processing_time = sum(result.total_processing_time or 0 for result in results)
        average_processing_time = total_processing_time / total_documents if total_documents > 0 else 0
        
        # 공통 실패 패턴 분석
        failure_patterns = {}
        for result in results:
            for roi_result in result.roi_results:
                if roi_result.is_failure:
                    key = f"{roi_result.roi_name}_{roi_result.status.value}"
                    failure_patterns[key] = failure_patterns.get(key, 0) + 1
        
        # 가장 빈번한 실패 5개
        common_failures = dict(sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return {
            "total_documents": total_documents,
            "successful_documents": successful_documents,
            "failed_documents": failed_documents,
            "success_rate": round(successful_documents / total_documents * 100, 2) if total_documents > 0 else 0,
            "total_rois": total_rois,
            "successful_rois": successful_rois,
            "failed_rois": failed_rois,
            "roi_success_rate": round(successful_rois / total_rois * 100, 2) if total_rois > 0 else 0,
            "average_processing_time": round(average_processing_time, 3),
            "common_failures": common_failures
        }
    
    def get_validation_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """검증 결과 기반 개선 권장사항"""
        recommendations = []
        
        if not results:
            return recommendations
        
        analysis = self.analyze_validation_results(results)
        
        # 성공률 기반 권장사항
        if analysis["success_rate"] < 50:
            recommendations.append("⚠️ 전체 성공률이 50% 미만입니다. 템플릿 설정을 재검토하세요.")
        elif analysis["success_rate"] < 80:
            recommendations.append("📈 성공률을 높이기 위해 실패 패턴을 분석해보세요.")
        
        # ROI 성공률 기반 권장사항
        if analysis["roi_success_rate"] < 70:
            recommendations.append("🎯 개별 ROI 성공률이 낮습니다. ROI 설정과 임계값을 조정하세요.")
        
        # 처리 시간 기반 권장사항
        if analysis["average_processing_time"] > 10:
            recommendations.append("⏱️ 평균 처리 시간이 길습니다. 템플릿 복잡도를 검토하세요.")
        
        # 공통 실패 패턴 기반 권장사항
        common_failures = analysis["common_failures"]
        if common_failures:
            most_common = max(common_failures.items(), key=lambda x: x[1])
            roi_name, status = most_common[0].rsplit("_", 1)
            count = most_common[1]
            recommendations.append(f"🔍 '{roi_name}' ROI에서 {status} 오류가 {count}회 발생했습니다. 설정을 확인하세요.")
        
        return recommendations
