#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 양식 검증 시스템 실행 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def run_roi_selector():
    """ROI 선택 도구 실행"""
    try:
        from roi_selector import main
        print("ROI 선택 도구를 시작합니다...")
        main()
    except ImportError as e:
        print(f"모듈 로드 실패: {e}")
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")

def run_pdf_validator():
    """PDF 검증 도구 실행"""
    try:
        from pdf_validator_gui import main
        print("PDF 검증 도구를 시작합니다...")
        main()
    except ImportError as e:
        print(f"모듈 로드 실패: {e}")
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("PDF 양식 검증 시스템")
    print("=" * 60)
    print("1. ROI 선택 도구 (템플릿 생성)")
    print("2. PDF 검증 도구 (양식 검증)")
    print("3. 종료")
    print("=" * 60)
    
    while True:
        try:
            choice = input("실행할 프로그램을 선택하세요 (1-3): ").strip()
            
            if choice == "1":
                run_roi_selector()
            elif choice == "2":
                run_pdf_validator()
            elif choice == "3":
                print("프로그램을 종료합니다.")
                break
            else:
                print("올바른 번호를 입력해주세요 (1-3)")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
