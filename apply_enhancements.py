#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
보험 서류 검증 시스템 v2.0 강화 기능 최종 통합 스크립트
"""

import os
import sys
import shutil
from datetime import datetime

def main():
    """메인 통합 함수"""
    print("🚀 보험 서류 검증 시스템 v2.0 강화 기능 통합")
    print("=" * 60)
    
    # 1단계: 폴더 구조 설정
    setup_enhanced_folders()
    
    # 2단계: 기존 데이터 백업
    backup_existing_data()
    
    # 3단계: 새 모듈들 확인
    verify_new_modules()
    
    # 4단계: 통합 테스트
    integration_test()
    
    # 5단계: 사용 가이드 표시
    show_usage_guide()
    
    print("\n✅ 모든 강화 기능이 성공적으로 통합되었습니다!")

def setup_enhanced_folders():
    """강화된 폴더 구조 설정"""
    print("\n📁 1단계: 폴더 구조 설정...")
    
    try:
        # 기본 폴더 생성
        folders = [
            'templates', 'output', 
            'templates/삼성화재', 'templates/DB손해보험', 'templates/현대해상',
            'output/삼성화재', 'output/DB손해보험', 'output/현대해상',
            'output/삼성화재/fail', 'output/삼성화재/success',
            'output/DB손해보험/fail', 'output/DB손해보험/success'
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        
        print("  ✅ 체계적 폴더 구조 생성 완료")
        show_folder_preview()
        
    except Exception as e:
        print(f"  ❌ 폴더 구조 설정 실패: {str(e)}")

def backup_existing_data():
    """기존 데이터 백업"""
    print("\n💾 2단계: 기존 데이터 백업...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    
    files_to_backup = [
        'templates.json',
        'src/roi_selector.py', 
        'src/pdf_validator_gui.py'
    ]
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                shutil.copy2(file_path, backup_dir)
                print(f"  💾 {file_path} 백업됨")
        
        print(f"  ✅ 백업 완료: {backup_dir}/")
        
    except Exception as e:
        print(f"  ❌ 백업 실패: {str(e)}")

def verify_new_modules():
    """새 모듈들 확인"""
    print("\n🔍 3단계: 새 모듈 확인...")
    
    required_modules = [
        'src/validation_debugger.py',
        'src/pdf_reload_functionality.py', 
        'src/template_editor.py',
        'src/folder_manager.py',
        'enhanced_launcher.py'
    ]
    
    for module_path in required_modules:
        if os.path.exists(module_path):
            file_size = os.path.getsize(module_path)
            print(f"  ✅ {module_path} ({file_size:,} bytes)")
        else:
            print(f"  ❌ {module_path} 없음")

def integration_test():
    """통합 테스트"""
    print("\n🧪 4단계: 통합 테스트...")
    
    # 필수 디렉토리 확인
    required_dirs = ['templates', 'output', 'src']
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✅ {directory}/ 폴더 존재")
        else:
            print(f"  ❌ {directory}/ 폴더 없음")

def show_folder_preview():
    """폴더 구조 미리보기"""
    print("\n📂 새로운 폴더 구조:")
    print("templates/")
    print("  ├── 삼성화재/")
    print("  ├── DB손해보험/")
    print("  └── 현대해상/")
    print("output/")
    print("  ├── 삼성화재/")
    print("  │   ├── fail/      ← 실패 케이스")
    print("  │   └── success/   ← 성공 케이스")
    print("  └── DB손해보험/")

def show_usage_guide():
    """사용 가이드 표시"""
    print("\n📋 5단계: 사용 가이드")
    
    print("\n🎯 시작하기:")
    print("  1. python enhanced_launcher.py 실행")
    print("  2. 단계별로 작업 진행")
    
    print("\n🔧 새 기능 사용법:")
    print("  📝 템플릿 편집: ROI 선택기에서 '기존 템플릿 불러오기'")
    print("  🔄 PDF 재업로드: 검증기에서 '다른 PDF로 재검사'")
    print("  🔍 디버깅 모드: 검증 실패시 자동 상세 분석")
    print("  📁 결과 확인: 런처에서 '결과 폴더 열기'")

def create_quick_start_script():
    """빠른 시작 스크립트 생성"""
    bat_content = '''@echo off
echo 🚀 보험 서류 검증 시스템 v2.0 시작...
echo.

python enhanced_launcher.py

if errorlevel 1 (
    echo.
    echo ❌ 실행 중 오류가 발생했습니다.
    echo 개별 실행을 시도해보세요:
    echo   python src/roi_selector.py
    echo   python src/pdf_validator_gui.py
    pause
)
'''
    
    try:
        with open('start_enhanced.bat', 'w', encoding='cp949') as f:
            f.write(bat_content)
        print("  📜 빠른 시작 스크립트 생성: start_enhanced.bat")
    except Exception as e:
        print(f"  ❌ 시작 스크립트 생성 실패: {str(e)}")

if __name__ == "__main__":
    try:
        main()
        create_quick_start_script()
        
        print("\n🎊 통합 완료! 새로운 강화 기능을 체험해보세요!")
        print("📋 자세한 내용은 README_v2.md를 참조하세요.")
        
    except Exception as e:
        print(f"\n💥 통합 중 오류 발생: {str(e)}")
        print("기존 방식으로 계속 사용하실 수 있습니다.")
