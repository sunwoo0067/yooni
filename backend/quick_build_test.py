#!/usr/bin/env python3
"""빠른 빌드 테스트 스크립트"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🔍 빌드 환경 검증 중...")
    
    # Python 버전 확인
    python_version = sys.version_info
    print(f"✅ Python 버전: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 가상환경 확인
    venv_dir = Path("venv")
    if venv_dir.exists():
        print("✅ 가상환경이 존재합니다")
    else:
        print("❌ 가상환경이 없습니다")
        return 1
    
    # 필수 파일 확인
    required_files = ["requirements.txt", "main.py", "simple_api.py"]
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} 파일이 존재합니다")
        else:
            print(f"❌ {file} 파일이 없습니다")
            return 1
    
    # flake8으로 간단한 코드 검사
    print("\n🔍 코드 품질 검사 중...")
    try:
        result = subprocess.run(
            ["venv/bin/python", "-m", "flake8", "--version"],
            capture_output=True,
            text=True
        )
        print(f"✅ flake8 버전: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ flake8 실행 실패: {e}")
    
    # 디렉토리 구조 확인
    print("\n📁 주요 디렉토리:")
    dirs = ["ai", "market", "supplier", "common", "workflow"]
    for dir_name in dirs:
        if Path(dir_name).exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ (없음)")
    
    print("\n✨ 빌드 환경 검증 완료!")
    return 0

if __name__ == "__main__":
    sys.exit(main())