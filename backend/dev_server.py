#!/usr/bin/env python3
"""
개발용 서버 - 자동 재시작 기능 포함
"""
import os
import sys
import subprocess
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 가상환경 확인
venv_dir = Path("venv")
if not venv_dir.exists():
    print("❌ 가상환경이 없습니다. 먼저 'python3 -m venv venv'를 실행하세요.")
    sys.exit(1)

# uvicorn이 설치되어 있는지 확인
try:
    import uvicorn
except ImportError:
    print("⚠️  uvicorn이 설치되지 않았습니다. 설치 중...")
    subprocess.run([str(venv_dir / "bin" / "pip"), "install", "uvicorn[standard]"])
    import uvicorn

if __name__ == "__main__":
    # 개발 환경 설정
    os.environ["ENVIRONMENT"] = "development"
    
    # 실행할 앱 선택
    app_choice = input("실행할 앱을 선택하세요:\n1) simple_api (포트 8003)\n2) main (포트 8000)\n선택 [1-2]: ")
    
    if app_choice == "1":
        app_module = "simple_api:app"
        port = 8003
        print("🚀 Simple API 개발 서버를 시작합니다...")
    elif app_choice == "2":
        app_module = "main:app"
        port = 8000
        print("🚀 Main API 개발 서버를 시작합니다...")
    else:
        print("❌ 잘못된 선택입니다.")
        sys.exit(1)
    
    # uvicorn 실행 (자동 재시작 포함)
    uvicorn.run(
        app_module,
        host="0.0.0.0",
        port=port,
        reload=True,  # 코드 변경 시 자동 재시작
        reload_dirs=[".", "ai", "market", "supplier", "workflow"],  # 감시할 디렉토리
        log_level="info",
        access_log=True,
        use_colors=True,
        # 개발 환경에서 유용한 설정
        reload_delay=0.25,  # 재시작 지연 시간 (초)
        reload_includes=["*.py", "*.json"],  # 감시할 파일 패턴
        reload_excludes=["__pycache__", "*.pyc", "logs/*", "data/*"],  # 제외할 패턴
    )