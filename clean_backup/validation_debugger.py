#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
디버깅 강화 모듈
PDF 검증 실패 원인을 상세히 분석하고 저장
"""

import os
import json
import cv2
import numpy as np
import fitz
import pytesseract
from datetime import datetime
from PIL import Image

class ValidationDebugger:
    def __init__(self, template_data, pdf_path):
        self.template_data = template_data
        self.pdf_path = pdf_path
        self.debug_data = {}
        
        # 디버깅 폴더 구조 생성
        self.setup_debug_folders()
    
    def setup_debug_folders(self):
        """디버깅 폴더 구조 생성"""
        # templates.json에서 템플릿 이름 추출
        template_name = None
        try:
            with open('templates.json', 'r', encoding='utf-8') as f:
                templates = json.load(f)
                for name, data in templates.items():
                    if data.get('original_pdf_path') == self.template_data.get('original_pdf_path'):
                        template_name = name
                        break
        except:
            template_name = "unknown_template"
        
        if not template_name:
            template_name = "unknown_template"
        
        # 보험사 추출 (경로에서)
        company = "unknown_company"
        if 'original_pdf_path' in self.template_data:
            path_parts = self.template_data['original_pdf_path'].split('/')
            for part in path_parts:
                if part in ['삼성화재', 'DB손해보험', '현대해상', 'KB손해보험', '메리츠화재']:
                    company = part
                    break
        
        # 디버깅 폴더 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        
        self.debug_base_dir = f"output/{company}/{template_name}/fail"
        self.debug_session_dir = f"{self.debug_base_dir}/{pdf_name}_{timestamp}"
        
        # 폴더 생성
        os.makedirs(self.debug_session_dir, exist_ok=True)
        os.makedirs(f"{self.debug_session_dir}/roi_images", exist_ok=True)
        os.makedirs(f"{self.debug_session_dir}/debug_data", exist_ok=True)
        
        print(f"[DEBUG] 디버깅 폴더 생성: {self.debug_session_dir}")
    
    def analyze_roi_failure(self, roi_name, roi_data, template_doc, validate_doc):
        """ROI 실패 원인 상세 분석"""
        page_num = roi_data['page']
        coords = roi_data['coords']
        method = roi_data['method']
        threshold = roi_data['threshold']
        
        debug_info = {
            'roi_name': roi_name,
            'method': method,
            'threshold': threshold,
            'page': page_num,
            'coords': coords,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # ROI 영역 이미지 추출
            template_img = self.extract_roi_image(template_doc, page_num, coords)
            validate_img = self.extract_roi_image(validate_doc, page_num, coords)
            
            # 이미지 저장
            template_path = f"{self.debug_session_dir}/roi_images/{roi_name}_template.png"
            validate_path = f"{self.debug_session_dir}/roi_images/{roi_name}_validate.png"
            
            cv2.imwrite(template_path, cv2.cvtColor(template_img, cv2.COLOR_RGB2BGR))
            cv2.imwrite(validate_path, cv2.cvtColor(validate_img, cv2.COLOR_RGB2BGR))
            
            debug_info['template_image'] = template_path
            debug_info['validate_image'] = validate_path
            
            # 방법별 상세 분석
            if method == 'ocr':
                debug_info.update(self.analyze_ocr_failure(template_img, validate_img, threshold))
            else:  # contour
                debug_info.update(self.analyze_contour_failure(template_img, validate_img, threshold))
            
            # SSIM 분석 (공통)
            debug_info.update(self.analyze_ssim(template_img, validate_img))
            
            return debug_info
            
        except Exception as e:
            debug_info['error'] = str(e)
            return debug_info
    
    def analyze_ocr_failure(self, template_img, validate_img, threshold):
        """OCR 실패 상세 분석"""
        ocr_debug = {}
        
        try:
            # 텍스트 추출
            template_text = pytesseract.image_to_string(template_img, lang='kor+eng').strip()
            validate_text = pytesseract.image_to_string(validate_img, lang='kor+eng').strip()
            
            # 텍스트 정리
            clean_template = template_text.replace(' ', '').replace('\n', '')
            clean_validate = validate_text.replace(' ', '').replace('\n', '')
            
            ocr_debug.update({
                'template_text': template_text,
                'validate_text': validate_text,
                'template_length': len(clean_template),
                'validate_length': len(clean_validate),
                'text_difference': len(clean_validate) - len(clean_template),
                'threshold_required': threshold,
                'threshold_met': (len(clean_validate) - len(clean_template)) >= threshold
            })
            
            # OCR 신뢰도 분석
            template_data = pytesseract.image_to_data(template_img, lang='kor+eng', output_type=pytesseract.Output.DICT)
            validate_data = pytesseract.image_to_data(validate_img, lang='kor+eng', output_type=pytesseract.Output.DICT)
            
            template_confidences = [int(conf) for conf in template_data['conf'] if int(conf) > 0]
            validate_confidences = [int(conf) for conf in validate_data['conf'] if int(conf) > 0]
            
            ocr_debug.update({
                'template_avg_confidence': np.mean(template_confidences) if template_confidences else 0,
                'validate_avg_confidence': np.mean(validate_confidences) if validate_confidences else 0,
                'template_words_detected': len([w for w in template_data['text'] if w.strip()]),
                'validate_words_detected': len([w for w in validate_data['text'] if w.strip()])
            })
            
        except Exception as e:
            ocr_debug['ocr_error'] = str(e)
        
        return ocr_debug
    
    def analyze_contour_failure(self, template_img, validate_img, threshold):
        """Contour 실패 상세 분석"""
        contour_debug = {}
        
        try:
            # 그레이스케일 변환
            template_gray = cv2.cvtColor(template_img, cv2.COLOR_RGB2GRAY)
            validate_gray = cv2.cvtColor(validate_img, cv2.COLOR_RGB2GRAY)
            
            # 차이 계산
            diff = cv2.absdiff(template_gray, validate_gray)
            
            # 여러 임계값으로 테스트
            thresholds_to_test = [20, 30, 40, 50]
            contour_analysis = {}
            
            for thresh_val in thresholds_to_test:
                _, binary = cv2.threshold(diff, thresh_val, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                total_area = sum(cv2.contourArea(c) for c in contours)
                
                contour_analysis[f'threshold_{thresh_val}'] = {
                    'contours_count': len(contours),
                    'total_area': int(total_area),
                    'largest_contour': int(max([cv2.contourArea(c) for c in contours])) if contours else 0
                }
            
            contour_debug.update({
                'threshold_analysis': contour_analysis,
                'required_threshold': threshold,
                'recommendation': self.recommend_contour_threshold(contour_analysis, threshold)
            })
            
            # 차이 이미지 저장
            diff_path = f"{self.debug_session_dir}/roi_images/{self.current_roi}_diff.png"
            cv2.imwrite(diff_path, diff)
            contour_debug['diff_image'] = diff_path
            
        except Exception as e:
            contour_debug['contour_error'] = str(e)
        
        return contour_debug
    
    def analyze_ssim(self, template_img, validate_img):
        """SSIM 분석"""
        ssim_debug = {}
        
        try:
            from skimage.metrics import structural_similarity as ssim
            
            # 그레이스케일 변환
            template_gray = cv2.cvtColor(template_img, cv2.COLOR_RGB2GRAY)
            validate_gray = cv2.cvtColor(validate_img, cv2.COLOR_RGB2GRAY)
            
            # 크기 맞추기
            if template_gray.shape != validate_gray.shape:
                validate_gray = cv2.resize(validate_gray, (template_gray.shape[1], template_gray.shape[0]))
            
            # SSIM 계산
            ssim_score = ssim(template_gray, validate_gray)
            
            ssim_debug.update({
                'ssim_score': float(ssim_score),
                'similarity_percentage': float(ssim_score * 100),
                'is_too_similar': ssim_score > 0.995,  # 현재 임계값
                'recommended_threshold': 0.98 if ssim_score > 0.995 else 0.99
            })
            
        except Exception as e:
            ssim_debug['ssim_error'] = str(e)
        
        return ssim_debug
    
    def recommend_contour_threshold(self, analysis, current_threshold):
        """Contour 임계값 추천"""
        recommendations = []
        
        # 가장 적절한 임계값 찾기
        best_threshold = None
        for thresh_name, data in analysis.items():
            area = data['total_area']
            if area > 0:
                if not best_threshold or abs(area - current_threshold) < abs(analysis[best_threshold]['total_area'] - current_threshold):
                    best_threshold = thresh_name
        
        if best_threshold:
            recommended_area = analysis[best_threshold]['total_area']
            if recommended_area > current_threshold:
                recommendations.append(f"임계값을 {recommended_area}로 낮추는 것을 고려해보세요")
            elif recommended_area < current_threshold * 0.5:
                recommendations.append(f"임계값을 {recommended_area}로 높이는 것을 고려해보세요")
        
        return recommendations
    
    def extract_roi_image(self, doc, page_num, coords):
        """ROI 이미지 추출"""
        page = doc[page_num]
        rect = fitz.Rect(coords)
        
        # 고해상도로 추출
        mat = fitz.Matrix(3, 3)
        pix = page.get_pixmap(matrix=mat, clip=rect)
        
        # numpy 배열로 변환
        img_data = np.frombuffer(pix.samples, dtype=np.uint8)
        img_array = img_data.reshape(pix.height, pix.width, pix.n)
        
        # RGB로 변환
        if pix.n == 4:  # RGBA
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        elif pix.n == 1:  # Grayscale
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        
        return img_array
    
    def save_debug_report(self, all_results):
        """전체 디버깅 리포트 저장"""
        # JSON 리포트 생성
        debug_report = {
            'validation_session': {
                'pdf_path': self.pdf_path,
                'template_data': self.template_data,
                'timestamp': datetime.now().isoformat(),
                'total_rois': len(self.template_data['rois']),
                'failed_rois': len([r for r in all_results if not r.get('passed', False)])
            },
            'roi_analysis': self.debug_data,
            'recommendations': self.generate_recommendations(all_results)
        }
        
        # JSON 파일 저장
        report_path = f"{self.debug_session_dir}/debug_data/validation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(debug_report, f, ensure_ascii=False, indent=2)
        
        # 간단한 텍스트 리포트도 생성
        text_report_path = f"{self.debug_session_dir}/debug_data/summary.txt"
        self.create_text_summary(debug_report, text_report_path)
        
        return self.debug_session_dir
    
    def generate_recommendations(self, all_results):
        """개선 권장사항 생성"""
        recommendations = []
        
        failed_count = len([r for r in all_results if not r.get('passed', False)])
        total_count = len(all_results)
        
        if failed_count == total_count:
            recommendations.append("⚠️ 모든 ROI가 실패했습니다. SSIM 임계값을 0.98로 낮춰보세요.")
        elif failed_count > total_count * 0.7:
            recommendations.append("⚠️ 대부분의 ROI가 실패했습니다. 전반적인 임계값 조정이 필요합니다.")
        
        # ROI별 권장사항
        for roi_name, debug_data in self.debug_data.items():
            if 'ssim_score' in debug_data and debug_data['ssim_score'] > 0.995:
                recommendations.append(f"🔧 {roi_name}: SSIM이 너무 높음 ({debug_data['ssim_score']:.4f}). 임계값을 0.98로 조정 권장")
            
            if 'threshold_analysis' in debug_data:
                analysis = debug_data['threshold_analysis']
                for thresh, data in analysis.items():
                    if data['total_area'] > 0:
                        recommendations.append(f"💡 {roi_name}: {thresh}에서 면적 {data['total_area']} 감지됨")
        
        return recommendations
    
    def create_text_summary(self, debug_report, file_path):
        """텍스트 요약 리포트 생성"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=== PDF 검증 디버깅 리포트 ===\n\n")
            f.write(f"검증 시간: {debug_report['validation_session']['timestamp']}\n")
            f.write(f"PDF 파일: {os.path.basename(debug_report['validation_session']['pdf_path'])}\n")
            f.write(f"총 ROI 수: {debug_report['validation_session']['total_rois']}\n")
            f.write(f"실패 ROI 수: {debug_report['validation_session']['failed_rois']}\n\n")
            
            f.write("=== ROI별 상세 분석 ===\n\n")
            for roi_name, debug_data in debug_report['roi_analysis'].items():
                f.write(f"ROI: {roi_name}\n")
                f.write(f"  방법: {debug_data.get('method', 'Unknown')}\n")
                f.write(f"  임계값: {debug_data.get('threshold', 'Unknown')}\n")
                
                if 'ssim_score' in debug_data:
                    f.write(f"  SSIM 점수: {debug_data['ssim_score']:.4f}\n")
                
                if 'template_text' in debug_data:
                    f.write(f"  템플릿 텍스트: '{debug_data['template_text'][:50]}...'\n")
                    f.write(f"  검증 텍스트: '{debug_data['validate_text'][:50]}...'\n")
                    f.write(f"  텍스트 길이 차이: {debug_data['text_difference']}\n")
                
                if 'threshold_analysis' in debug_data:
                    f.write("  Contour 분석:\n")
                    for thresh, data in debug_data['threshold_analysis'].items():
                        f.write(f"    {thresh}: 면적 {data['total_area']}, 개수 {data['contours_count']}\n")
                
                f.write("\n")
            
            f.write("=== 권장사항 ===\n\n")
            for i, rec in enumerate(debug_report['recommendations'], 1):
                f.write(f"{i}. {rec}\n")

# PDF 검증 GUI에 통합할 디버깅 함수들
def enhanced_validation_with_debug(validator_instance, filled_pdf_path):
    """강화된 검증 + 디버깅"""
    
    # 디버거 초기화
    debugger = ValidationDebugger(validator_instance.template_data, filled_pdf_path)
    
    # 원본 검증 실행
    try:
        original_doc = fitz.open(validator_instance.original_pdf_path)
        filled_doc = fitz.open(filled_pdf_path)
        
        validation_results = []
        debug_results = []
        
        for field_name, roi_info in validator_instance.rois.items():
            # 기본 검증
            result = validator_instance._validate_single_roi(original_doc, filled_doc, field_name, roi_info)
            validation_results.append(result)
            
            # 실패한 경우 상세 디버깅
            if result.get('status') != 'OK':
                debugger.current_roi = field_name
                debug_info = debugger.analyze_roi_failure(field_name, roi_info, original_doc, filled_doc)
                debugger.debug_data[field_name] = debug_info
                debug_results.append(debug_info)
        
        # 디버깅 리포트 저장
        if debug_results:  # 실패가 있는 경우만
            debug_folder = debugger.save_debug_report(validation_results)
            print(f"[DEBUG] 실패 분석 저장됨: {debug_folder}")
        
        original_doc.close()
        filled_doc.close()
        
        return validation_results, debug_results
        
    except Exception as e:
        print(f"[ERROR] 디버깅 검증 실패: {str(e)}")
        return [], []

def create_enhanced_annotated_pdf(original_path, filled_path, validation_results, debug_results, output_path):
    """강화된 주석 PDF 생성"""
    try:
        # 검증 결과를 기반으로 주석 PDF 생성
        doc = fitz.open(filled_path)
        
        for i, result in enumerate(validation_results):
            if result.get('status') != 'OK':
                page_num = result['page']
                coords = result['coords']
                field_name = result['field_name']
                
                page = doc[page_num]
                rect = fitz.Rect(coords)
                
                # 노란 형광펜
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors({"stroke": [1, 1, 0], "fill": [1, 1, 0]})
                highlight.set_opacity(0.4)
                highlight.update()
                
                # 상세 디버깅 정보 주석
                if i < len(debug_results):
                    debug_info = debug_results[i]
                    
                    # 주석 텍스트 구성
                    annotation_text = f"❌ {field_name}\n"
                    annotation_text += f"상태: {result.get('message', '검증 실패')}\n"
                    
                    if 'ssim_score' in debug_info:
                        annotation_text += f"유사도: {debug_info['ssim_score']:.4f}\n"
                    
                    if 'text_difference' in debug_info:
                        annotation_text += f"텍스트 차이: {debug_info['text_difference']}자\n"
                        annotation_text += f"필요: {debug_info['threshold_required']}자 이상\n"
                    
                    if 'threshold_analysis' in debug_info:
                        best_area = max([data['total_area'] for data in debug_info['threshold_analysis'].values()])
                        annotation_text += f"최대 감지 면적: {best_area}\n"
                        annotation_text += f"필요 면적: {debug_info['threshold']} 이상\n"
                    
                    # 텍스트 주석 추가
                    text_point = fitz.Point(coords[0], coords[1] - 10)
                    text_annot = page.add_text_annot(text_point, annotation_text)
                    text_annot.update()
        
        # 저장
        doc.save(output_path)
        doc.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 강화된 주석 PDF 생성 실패: {str(e)}")
        return False
