#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 검증 시스템 프로젝트 검증 도구
현재 프로젝트 구조와 구현 상태를 체크합니다.
"""

import os
import sys
import importlib.util

class ProjectValidator:
    def __init__(self, project_path):
        self.project_path = project_path
        self.issues = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
    
    def check_file_exists(self, file_path, description):
        """파일 존재 여부 확인"""
        self.total_checks += 1
        full_path = os.path.join(self.project_path, file_path)
        
        if os.path.exists(full_path):
            print(f"✅ {description}: {file_path}")
            self.success_count += 1
            return True
        else:
            print(f"❌ {description}: {file_path} - 누락")
            self.issues.append(f"{description} 파일 누락: {file_path}")
            return False
    
    def check_directory_exists(self, dir_path, description):
        """디렉토리 존재 여부 확인"""
        self.total_checks += 1
        full_path = os.path.join(self.project_path, dir_path)
        
        if os.path.isdir(full_path):
            print(f"✅ {description}: {dir_path}/")
            self.success_count += 1
            return True
        else:
            print(f"❌ {description}: {dir_path}/ - 누락")
            self.issues.append(f"{description} 디렉토리 누락: {dir_path}")
            return False
    
    def check_python_syntax(self, file_path, description):
        """Python 파일 구문 확인"""
        self.total_checks += 1
        full_path = os.path.join(self.project_path, file_path)
        
        if not os.path.exists(full_path):
            return False
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                compile(f.read(), full_path, 'exec')
            print(f"✅ {description} 구문 검사 통과")
            self.success_count += 1
            return True
        except SyntaxError as e:
            print(f"❌ {description} 구문 오류: {e}")
            self.issues.append(f"{description} 구문 오류: {str(e)}")
            return False
        except Exception as e:
            print(f"⚠️ {description} 검사 실패: {e}")
            self.warnings.append(f"{description} 검사 실패: {str(e)}")
            return False
    
    def check_imports(self, file_path, required_imports, description):
        """필수 import 확인"""
        self.total_checks += 1
        full_path = os.path.join(self.project_path, file_path)
        
        if not os.path.exists(full_path):
            return False
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            missing_imports = []
            for imp in required_imports:
                if f"import {imp}" not in content and f"from {imp}" not in content:
                    missing_imports.append(imp)
            
            if not missing_imports:
                print(f"✅ {description} 필수 import 확인 완료")
                self.success_count += 1
                return True
            else:
                print(f"⚠️ {description} 누락된 import: {', '.join(missing_imports)}")
                self.warnings.append(f"{description} 누락된 import: {', '.join(missing_imports)}")
                return False
                
        except Exception as e:
            print(f"❌ {description} import 검사 실패: {e}")
            self.issues.append(f"{description} import 검사 실패: {str(e)}")
            return False
    
    def validate_project(self):
        """전체 프로젝트 검증"""
        print("🔍 PDF 검증 시스템 프로젝트 검증을 시작합니다...\n")
        
        # 1. 기본 구조 확인
        print("📁 프로젝트 구조 확인:")
        self.check_directory_exists("src", "소스 코드 디렉토리")
        self.check_directory_exists("templates", "템플릿 디렉토리")
        
        # 2. 핵심 파일 확인
        print("\n📄 핵심 파일 확인:")
        self.check_file_exists("run.py", "메인 실행 스크립트")
        self.check_file_exists("requirements.txt", "패키지 의존성 파일")
        self.check_file_exists("README.md", "프로젝트 문서")
        self.check_file_exists("templates.json", "템플릿 설정 파일")
        
        # 3. 소스 코드 파일 확인
        print("\n🐍 소스 코드 파일 확인:")
        self.check_file_exists("src/roi_selector.py", "ROI 선택 도구")
        self.check_file_exists("src/pdf_validator_gui.py", "PDF 검증 도구")
        
        # 4. 유틸리티 파일 확인
        print("\n🛠️ 유틸리티 파일 확인:")
        self.check_file_exists("one_click_setup.bat", "Windows 자동 설치 스크립트")
        self.check_file_exists("quick_guide.py", "빠른 시작 가이드")
        self.check_file_exists("test_mode.py", "테스트 모드")
        
        # 5. Python 구문 검사
        print("\n🔧 Python 파일 구문 검사:")
        self.check_python_syntax("run.py", "메인 실행 스크립트")
        self.check_python_syntax("src/roi_selector.py", "ROI 선택 도구")
        self.check_python_syntax("src/pdf_validator_gui.py", "PDF 검증 도구")
        self.check_python_syntax("quick_guide.py", "빠른 시작 가이드")
        self.check_python_syntax("test_mode.py", "테스트 모드")
        
        # 6. 필수 import 확인
        print("\n📦 필수 라이브러리 import 확인:")
        self.check_imports("src/roi_selector.py", 
                          ["tkinter", "fitz", "PIL", "cv2", "numpy"], 
                          "ROI 선택 도구")
        self.check_imports("src/pdf_validator_gui.py", 
                          ["tkinter", "fitz", "cv2", "numpy", "pytesseract", "skimage"], 
                          "PDF 검증 도구")
        
        # 결과 출력
        self.print_summary()
    
    def print_summary(self):
        """검증 결과 요약 출력"""
        print("\n" + "="*60)
        print("📊 프로젝트 검증 결과 요약")
        print("="*60)
        
        success_rate = (self.success_count / self.total_checks) * 100 if self.total_checks > 0 else 0
        
        print(f"✅ 성공: {self.success_count}/{self.total_checks} ({success_rate:.1f}%)")
        
        if self.issues:
            print(f"❌ 오류: {len(self.issues)}개")
            for issue in self.issues:
                print(f"   • {issue}")
        
        if self.warnings:
            print(f"⚠️ 경고: {len(self.warnings)}개")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        print("\n" + "="*60)
        
        if success_rate >= 90:
            print("🎉 프로젝트가 올바르게 구현되었습니다!")
            print("   • one_click_setup.bat 또는 python run.py로 실행 가능")
        elif success_rate >= 70:
            print("⚠️ 프로젝트가 대부분 구현되었지만 몇 가지 문제가 있습니다.")
            print("   • 위의 오류들을 수정하면 정상 실행 가능")
        else:
            print("❌ 프로젝트에 중요한 구성 요소가 누락되었습니다.")
            print("   • 오류들을 먼저 수정해주세요")

def main():
    """메인 함수"""
    # 현재 디렉토리 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"검증 대상 디렉토리: {current_dir}")
    print()
    
    # 프로젝트 검증 실행
    validator = ProjectValidator(current_dir)
    validator.validate_project()
    
    input("\n검증 완료. Enter를 눌러 종료하세요...")

if __name__ == "__main__":
    main()
