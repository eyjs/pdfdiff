import tkinter as tk
import sys
import os

# 프로젝트의 루트 디렉토리를 Python 경로에 추가합니다.
# 이렇게 하면 app, domain, infrastructure 등 다른 폴더에 있는 모듈을
# 'from app.gui...' 와 같은 절대 경로로 가져올 수 있습니다.
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.gui.main_window import MainWindow
from app.controllers.main_controller import MainController

def main():
    """
    애플리케이션의 시작점 (Composition Root).
    모든 최상위 구성요소를 조립하고 GUI 메인 루프를 시작합니다.
    """
    # 1. 애플리케이션의 메인 윈도우(Tkinter 루트) 생성
    root = tk.Tk()

    # 2. 메인 컨트롤러 생성.
    #    MainController는 다른 기능 창들(템플릿 편집기, 검증 도구)을
    #    열어주는 '지휘자' 역할을 담당합니다.
    main_controller = MainController(root)

    # 3. 메인 뷰(View) 생성.
    #    MainWindow는 사용자가 가장 처음 보게 될 메뉴 화면이며,
    #    모든 사용자 요청(버튼 클릭 등)을 MainController에 전달합니다.
    app = MainWindow(root, main_controller)

    # 4. Tkinter 이벤트 루프를 시작하여 사용자 입력을 기다립니다.
    root.mainloop()

if __name__ == "__main__":
    main()

