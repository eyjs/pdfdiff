#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
폴더 구조 관리자 - 완전 구현
"""

import os
import json
import shutil
from datetime import datetime

class FolderManager:
    def __init__(self, base_path="."):
        self.base_path = base_path
        self.templates_dir = os.path.join(base_path, "templates")
        self.output_dir = os.path.join(base_path, "output")
    
    def setup_folder_structure(self):
        """표준 폴더 구조 생성"""
        print("📁 폴더 구조 설정 중...")
        
        # 기본 폴더
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 보험사 폴더
        companies = ['삼성화재', 'DB손해보험', '현대해상', 'KB손해보험', '메리츠화재']
        
        for company in companies:
            # templates/보험사명/
            company_template = os.path.join(self.templates_dir, company)
            os.makedirs(company_template, exist_ok=True)
            
            # output/보험사명/
            company_output = os.path.join(self.output_dir, company)
            os.makedirs(company_output, exist_ok=True)
            
            # output/보험사명/fail/
            fail_dir = os.path.join(company_output, "fail")
            os.makedirs(fail_dir, exist_ok=True)
            
            # output/보험사명/success/
            success_dir = os.path.join(company_output, "success")
            os.makedirs(success_dir, exist_ok=True)
        
        print("✅ 폴더 구조 완료")
    
    def get_output_path(self, company_name, template_name, result_type="fail"):
        """적절한 결과 저장 경로 반환"""
        base_dir = os.path.join(self.output_dir, company_name)
        
        if template_name:
            template_dir = os.path.join(base_dir, template_name)
            os.makedirs(template_dir, exist_ok=True)
            
            result_dir = os.path.join(template_dir, result_type)
            os.makedirs(result_dir, exist_ok=True)
            return result_dir
        else:
            result_dir = os.path.join(base_dir, result_type)
            os.makedirs(result_dir, exist_ok=True)
            return result_dir
    
    def save_result_with_structure(self, company_name, template_name, pdf_path, results, annotated_doc=None):
        """새 폴더 구조로 결과 저장"""
        try:
            # 성공/실패 판단
            failed_count = len([r for r in results if r.get('status') != 'OK'])
            result_type = "fail" if failed_count > 0 else "success"
            
            # 저장 경로
            output_dir = self.get_output_path(company_name, template_name, result_type)
            
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            
            # 주석 PDF 저장
            if annotated_doc:
                pdf_filename = f"{pdf_name}_검증결과_{timestamp}.pdf"
                pdf_output_path = os.path.join(output_dir, pdf_filename)
                annotated_doc.save(pdf_output_path)
                print(f"📄 결과 PDF 저장: {pdf_output_path}")
            
            # JSON 결과 저장
            json_filename = f"{pdf_name}_결과_{timestamp}.json"
            json_output_path = os.path.join(output_dir, json_filename)
            
            result_data = {
                'timestamp': timestamp,
                'company': company_name,
                'template': template_name,
                'pdf_path': pdf_path,
                'result_type': result_type,
                'results': results,
                'summary': {
                    'total': len(results),
                    'failed': failed_count,
                    'success_rate': round(((len(results) - failed_count) / len(results)) * 100, 1) if results else 0
                }
            }
            
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            print(f"📊 결과 데이터 저장: {json_output_path}")
            
            return {
                'pdf_path': pdf_output_path if annotated_doc else None,
                'json_path': json_output_path,
                'output_dir': output_dir
            }
            
        except Exception as e:
            print(f"❌ 결과 저장 실패: {str(e)}")
            return None

# 전역 인스턴스
folder_manager = FolderManager()

def init_enhanced_folders():
    """강화된 폴더 구조 초기화"""
    folder_manager.setup_folder_structure()
    print("🎯 새 폴더 구조:")
    print("templates/")
    print("  ├── 삼성화재/")
    print("  ├── DB손해보험/")
    print("  └── ...")
    print("output/")
    print("  ├── 삼성화재/")
    print("  │   ├── 템플릿명1/")
    print("  │   │   ├── fail/      ← 실패 케이스")
    print("  │   │   └── success/   ← 성공 케이스")
    print("  │   └── 템플릿명2/")
    print("  └── DB손해보험/")

if __name__ == "__main__":
    init_enhanced_folders()
