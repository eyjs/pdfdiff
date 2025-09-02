# run.py (최종 수정 버전)

import sys
import os

# 현재 디렉토리의 'src' 폴더를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def run_template_manager():
    """1단계: ROI 템플릿 관리 도구 실행"""
    try:
        # [수정] roi_selector 대신 template_manager를 호출합니다.
        from template_manager import main
        print("1단계: ROI 템플릿 관리 도구를 시작합니다...")
        main()
    except ImportError as e:
        print(f"모듈 로드 실패: {e}")
        print("src 폴더에 template_manager.py 파일이 있는지 확인해주세요.")
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")

def run_pdf_validator():
    """2단계: PDF 검증 도구 실행"""
    try:
        # pdf_validator_gui는 그대로 유지합니다.
        from pdf_validator_gui import main
        print("2단계: PDF 검증 도구를 시작합니다...")
        main()
    except ImportError as e:
        print(f"모듈 로드 실패: {e}")
        print("src 폴더에 pdf_validator_gui.py 파일이 있는지 확인해주세요.")
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("PDF 양식 검증 시스템")
    print("=" * 60)
    print("1. 템플릿 관리 도구 (ROI 생성 및 편집)")
    print("2. PDF 검증 도구 (양식 검증)")
    print("3. 종료")
    print("=" * 60)

    while True:
        try:
            choice = input("실행할 프로그램을 선택하세요 (1-3): ").strip()

            if choice == "1":
                # [수정] 새로운 함수를 호출합니다.
                run_template_manager()
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