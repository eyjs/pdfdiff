import sys
import os
import subprocess
import shutil
import importlib

# --- 검사 설정 (최신 버전 기준) ---
REQUIRED_LIBRARIES = [
    "fitz",
    "cv2",
    "skimage",
    "PIL",
    "pytesseract",
    "numpy"
]

REQUIRED_FILES = [
    "enhanced_launcher.py",
    "templates.json",
    "src/template_manager.py", #<-- roi_selector.py 에서 변경
    "src/pdf_validator_gui.py"
]

REQUIRED_FOLDERS = [
    "src",
    "templates",
    "output",
    "input"
]

class SystemCheck:
    """
    PDF 검증 시스템의 실행 환경과 의존성을 검사하는 클래스입니다.
    """
    def __init__(self):
        self.passed = 0
        self.failed = 0
        print("="*60)
        print("🚀 PDF 검증 시스템 환경 및 의존성 검사를 시작합니다.")
        print("="*60)

    def check(self, title, func):
        """검사 항목을 실행하고 성공/실패를 카운트합니다."""
        print(f"\n--- {title} ---")
        if func():
            self.passed += 1
        else:
            self.failed += 1

    def run(self):
        """모든 검사를 순차적으로 실행합니다."""
        self.check("Python 라이브러리 설치 확인", self.check_libraries)
        self.check("Tesseract OCR 엔진 확인", self.check_tesseract)
        self.check("핵심 파일 및 폴더 구조 확인", self.check_structure)
        self.summary()

    def check_libraries(self):
        """requirements.txt에 명시된 라이브러리들이 설치되었는지 확인합니다."""
        all_found = True
        for lib in REQUIRED_LIBRARIES:
            try:
                lib_to_import = 'fitz' if lib == 'PyMuPDF' else lib
                importlib.import_module(lib_to_import)
                print(f"  ✅ [성공] '{lib}' 라이브러리가 설치되어 있습니다.")
            except ImportError:
                print(f"  ❌ [실패] '{lib}' 라이브러리가 설치되지 않았습니다.")
                print(f"     -> 해결 방법: 터미널에서 'pip install -r requirements.txt'를 실행하세요.")
                all_found = False
        return all_found

    def check_tesseract(self):
        """
        Tesseract OCR 엔진이 사용 가능한지 확인합니다.
        1순위: 프로젝트 내장(vendor) Tesseract (배포용)
        2순위: 시스템 PATH에 설치된 Tesseract (개발용)
        """
        # 1순위: 프로젝트 내장 Tesseract 확인
        bundled_path = os.path.join("vendor", "tesseract", "tesseract.exe")
        if os.path.exists(bundled_path):
            print(f"  ✅ [성공] 프로젝트 내장 Tesseract 엔진을 찾았습니다: ({bundled_path})")
            print("     -> 프로그램이 이 버전을 우선적으로 사용합니다. (권장)")
            return True

        # 2순위: 시스템 PATH 확인
        system_path = shutil.which("tesseract")
        if system_path:
            print(f"  ⚠️ [경고] 시스템 PATH에 설치된 Tesseract를 찾았습니다: ({system_path})")
            print("     -> 개발 환경에서는 작동하지만, 다른 PC에서는 작동하지 않을 수 있습니다.")
            print("     -> 배포를 위해서는 프로젝트 내에 Tesseract를 포함시키는 것을 권장합니다.")
            return True

        # Tesseract를 찾지 못한 경우
        print("  ❌ [실패] Tesseract OCR 엔진을 시스템에서 찾을 수 없습니다.")
        print("     -> 원인: Tesseract는 C++ 프로그램이므로 'pip'로 설치할 수 없습니다.")
        print("     -> 해결 방법 1 (권장): DEPLOYMENT_GUIDE.md의 '1단계'를 따라 vendor/tesseract 폴더를 구성하세요.")
        print("     -> 해결 방법 2 (개발용): Tesseract를 PC에 직접 설치하고 시스템 PATH에 추가하세요.")
        return False

    def check_structure(self):
        """프로젝트 실행에 필요한 파일과 폴더가 모두 존재하는지 확인합니다."""
        all_found = True
        for file in REQUIRED_FILES:
            if not os.path.exists(file):
                print(f"  ❌ [실패] 필수 파일이 없습니다: {file}")
                all_found = False
            else:
                 print(f"  ✅ [성공] 필수 파일 확인: {file}")

        for folder in REQUIRED_FOLDERS:
            if not os.path.isdir(folder):
                print(f"  ❌ [실패] 필수 폴더가 없습니다: {folder}")
                all_found = False
            else:
                 print(f"  ✅ [성공] 필수 폴더 확인: {folder}")
        return all_found

    def summary(self):
        """모든 검사 결과를 요약하여 보여줍니다."""
        print("\n" + "="*60)
        print("📊 검사 결과 요약")
        print("="*60)
        print(f"  - 통과: {self.passed} 개")
        print(f"  - 실패: {self.failed} 개")
        print("-" * 60)
        if self.failed == 0:
            print("🎉 축하합니다! 모든 필수 요구사항이 충족되었습니다.")
            print("   이제 'python enhanced_launcher.py'를 실행하여 프로그램을 시작할 수 있습니다.")
        else:
            print("🔥 몇 가지 문제가 발견되었습니다. 위의 [실패] 항목을 먼저 해결해주세요.")
        print("="*60)

if __name__ == "__main__":
    check = SystemCheck()
    check.run()

