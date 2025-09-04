"""
PDF Validator System - Main Entry Point
애플리케이션 메인 진입점
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.config.settings import settings
from shared.utils import LoggingUtils, FileUtils
from shared.exceptions import *
from shared.constants import APPLICATION_NAME, VERSION


def setup_application():
    """애플리케이션 초기 설정"""
    try:
        # 로거 설정
        logger = LoggingUtils.setup_logger(
            APPLICATION_NAME, 
            level=settings.log_level,
            log_file="logs/app.log" if settings.debug_enabled else None
        )
        
        logger.info(f"{APPLICATION_NAME} v{VERSION} 시작")
        
        # 필수 디렉토리 생성
        required_dirs = [
            settings.storage.output_directory,
            settings.storage.input_directory,
            "logs"
        ]
        
        for dir_path in required_dirs:
            FileUtils.ensure_directory(dir_path)
            logger.debug(f"디렉토리 확인/생성: {dir_path}")
        
        # 설정 검증
        validation_result = settings.validate()
        
        if validation_result["errors"]:
            logger.error("설정 오류 발견:")
            for error in validation_result["errors"]:
                logger.error(f"  - {error}")
            return False
        
        if validation_result["warnings"]:
            logger.warning("설정 경고:")
            for warning in validation_result["warnings"]:
                logger.warning(f"  - {warning}")
        
        logger.info("애플리케이션 초기화 완료")
        return True
        
    except Exception as e:
        print(f"애플리케이션 초기화 실패: {e}")
        return False


def main():
    """메인 함수"""
    try:
        # 애플리케이션 초기 설정
        if not setup_application():
            print("애플리케이션 초기화에 실패했습니다.")
            sys.exit(1)
        
        # GUI 애플리케이션 시작
        import tkinter as tk
        from app.gui.main_window import MainWindow
        
        # Tkinter 루트 윈도우 생성
        root = tk.Tk()
        
        # 메인 윈도우 생성 및 실행
        app = MainWindow(root)
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")
        
        # 디버그 모드에서는 전체 스택 트레이스 출력
        if settings.debug_enabled:
            import traceback
            traceback.print_exc()
        
        sys.exit(1)


def show_version():
    """버전 정보 출력"""
    print(f"{APPLICATION_NAME} v{VERSION}")
    print("PDF 문서 검증 자동화 시스템")
    print("Copyright (c) 2025")


def show_help():
    """도움말 출력"""
    show_version()
    print("\n사용법:")
    print("  python main.py              - GUI 모드로 실행")
    print("  python main.py --version    - 버전 정보 출력")
    print("  python main.py --help       - 이 도움말 출력")
    print("  python main.py --debug      - 디버그 모드로 실행")
    print("\n설정 파일: settings.json")
    print("템플릿 파일: templates.json")


if __name__ == "__main__":
    # 명령행 인자 처리
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--version', '-v']:
            show_version()
            sys.exit(0)
        elif arg in ['--help', '-h']:
            show_help()
            sys.exit(0)
        elif arg in ['--debug', '-d']:
            settings.debug_enabled = True
            settings.log_level = "DEBUG"
            print("디버그 모드 활성화")
        else:
            print(f"알 수 없는 인자: {sys.argv[1]}")
            print("사용 가능한 옵션을 보려면 --help를 사용하세요.")
            sys.exit(1)
    
    # 메인 프로그램 실행
    main()
