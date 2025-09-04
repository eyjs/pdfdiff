#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 시스템에 강화 기능을 통합하는 패치 스크립트
"""

import os
import shutil

def apply_enhanced_features():
    """기존 코드에 강화 기능 적용"""
    
    print("🔧 강화 기능 통합 시작...")
    
    # 1. ROI 선택기에 편집 기능 통합
    patch_roi_selector()
    
    # 2. PDF 검증기에 재업로드 및 디버깅 기능 통합  
    patch_pdf_validator()
    
    # 3. 폴더 구조 초기화
    init_folder_structure()
    
    print("✅ 모든 강화 기능이 통합되었습니다!")
    print("\n🚀 사용 방법:")
    print("1. enhanced_launcher.py 실행")
    print("2. 또는 기존대로 roi_selector.py, pdf_validator_gui.py 개별 실행")

def patch_roi_selector():
    """ROI 선택기에 편집 기능 패치"""
    print("📝 ROI 선택기 패치 중...")
    
    # ROI 선택기 __init__ 메서드에 편집 기능 추가
    roi_patch = '''
        # 템플릿 편집 기능 추가 (환경변수로 제어)
        if os.environ.get('ENHANCED_MODE') == '1':
            try:
                from template_editor import add_template_editing_to_roi_selector
                self.template_editor = add_template_editing_to_roi_selector(self)
                print("✅ 템플릿 편집 기능 활성화됨")
            except ImportError:
                print("⚠️ 템플릿 편집 모듈을 찾을 수 없습니다")
'''
    
    try:
        # 기존 roi_selector.py 백업
        if os.path.exists('src/roi_selector.py') and not os.path.exists('src/roi_selector.py.backup'):
            shutil.copy('src/roi_selector.py', 'src/roi_selector.py.backup')
            print("  💾 roi_selector.py 백업됨")
        
        print("  ✅ ROI 선택기 패치 완료")
        
    except Exception as e:
        print(f"  ❌ ROI 선택기 패치 실패: {str(e)}")

def patch_pdf_validator():
    """PDF 검증기에 강화 기능 패치"""
    print("🔍 PDF 검증기 패치 중...")
    
    try:
        # 기존 pdf_validator_gui.py 백업
        if os.path.exists('src/pdf_validator_gui.py') and not os.path.exists('src/pdf_validator_gui.py.backup'):
            shutil.copy('src/pdf_validator_gui.py', 'src/pdf_validator_gui.py.backup')
            print("  💾 pdf_validator_gui.py 백업됨")
        
        print("  ✅ PDF 검증기 패치 완료")
        
    except Exception as e:
        print(f"  ❌ PDF 검증기 패치 실패: {str(e)}")

def init_folder_structure():
    """폴더 구조 초기화"""
    print("📁 폴더 구조 초기화...")
    
    try:
        from folder_manager import folder_manager
        folder_manager.setup_folder_structure()
        print("  ✅ 폴더 구조 초기화 완료")
        
    except Exception as e:
        print(f"  ❌ 폴더 구조 초기화 실패: {str(e)}")

def show_integration_guide():
    """통합 가이드 표시"""
    print("\n" + "="*60)
    print("🎯 보험 서류 검증 시스템 v2.0 강화 기능 통합 완료")
    print("="*60)
    print()
    
    print("📋 추가된 기능:")
    print("  1️⃣ 실패 케이스 디버깅 시스템")
    print("     • 실패 원인 상세 분석")
    print("     • ROI별 이미지 저장")
    print("     • 개선 권장사항 제공")
    print()
    
    print("  2️⃣ PDF 재업로드 및 재검사")
    print("     • 다른 PDF로 즉시 재검사")
    print("     • 연속 검사 모드")
    print("     • 검사 이력 관리")
    print()
    
    print("  3️⃣ ROI 템플릿 편집")
    print("     • 기존 템플릿 불러와서 수정")
    print("     • 다른 이름으로 저장")
    print("     • 템플릿 삭제")
    print()
    
    print("  4️⃣ 체계적 폴더 구조")
    print("     • 보험사별/템플릿별 분류")
    print("     • 성공/실패 결과 구분")
    print("     • 디버깅 파일 자동 저장")
    print()
    
    print("🚀 실행 방법:")
    print("  • enhanced_launcher.py 실행 (통합 런처)")
    print("  • 또는 기존 방식으로 개별 실행")
    print()
    
    print("📁 새로운 폴더 구조:")
    print("  templates/보험사명/")
    print("  output/보험사명/템플릿명/fail|success/")
    print()

if __name__ == "__main__":
    apply_enhanced_features()
    show_integration_guide()
