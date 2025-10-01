import tkinter as tk
import sys
import os
import logging

# 프로젝트의 루트 디렉토리를 Python 경로에 추가합니다.
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.gui.main_window import MainWindow
from app.controllers.main_controller import MainController
from shared.utils import LoggingUtils, get_base_path

from app.gui.main_window import MainWindow
from app.controllers.main_controller import MainController
from shared.utils import LoggingUtils, get_base_path

def setup_logging():
    """애플리케이션 전역 로거를 설정합니다."""
    log_dir = get_base_path() / "output" / "debug"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    
    # 모든 로그를 파일에 기록하도록 루트 로거를 설정합니다.
    # 이렇게 하면 EasyOCR 같은 라이브러리의 출력도 캡처할 수 있습니다.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        filename=str(log_file),
        filemode='w', # 프로그램을 실행할 때마다 새 로그 파일 생성
        encoding='utf-8'
    )
    
    # 콘솔에도 로그를 출력하기 위한 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    logging.info("========================================")
    logging.info("Logging setup complete. Application starting.")
    logging.info(f"Log file at: {log_file}")
    logging.info("========================================")

def main():
    """
    애플리케이션의 시작점 (Composition Root).
    모든 최상위 구성요소를 조립하고 GUI 메인 루프를 시작합니다.
    """
    # 1. 로깅 설정
    setup_logging()

    # 2. 애플리케이션의 메인 윈도우(Tkinter 루트) 생성
    root = tk.Tk()

    # 3. 메인 컨트롤러 생성.
    main_controller = MainController(root)

    # 4. 메인 뷰(View) 생성.
    app = MainWindow(root, main_controller)

    # 5. Tkinter 이벤트 루프를 시작하여 사용자 입력을 기다립니다.
    root.mainloop()

if __name__ == "__main__":
    main()