"""
개발 환경에서 테스트용으로 빠른 실행파일 생성
배포용이 아닌 로컬 테스트 목적
"""

import subprocess
import sys
from pathlib import Path

def quick_build():
    """빠른 테스트용 빌드"""
    project_root = Path(__file__).parent
    
    print("⚡ 빠른 테스트용 빌드 시작...")
    
    try:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--noconsole",
            "--name", "보험서류검증시스템_테스트",
            "enhanced_launcher.py"
        ]
        
        subprocess.run(cmd, check=True)
        
        exe_file = project_root / "dist" / "보험서류검증시스템_테스트.exe"
        if exe_file.exists():
            print(f"✅ 테스트용 실행파일 생성: {exe_file}")
            print("⚠️  이 파일은 테스트 목적으로만 사용하세요.")
            return True
        else:
            print("❌ 실행파일 생성 실패")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        return False

if __name__ == "__main__":
    quick_build()
