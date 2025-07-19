#!/usr/bin/env python3
"""
백엔드 빌드 스크립트
프로덕션 환경을 위한 백엔드 서비스 빌드 및 패키징
"""
import os
import sys
import shutil
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class BackendBuilder:
    def __init__(self, build_type: str = "prod", clean: bool = False, optimize: bool = True):
        self.build_type = build_type
        self.clean = clean
        self.optimize = optimize
        self.root_dir = Path(__file__).parent
        self.build_dir = self.root_dir / "build"
        self.dist_dir = self.root_dir / "dist"
        self.venv_dir = self.root_dir / "venv"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # 가상환경의 Python 실행 파일 경로
        if sys.platform == "win32":
            self.python_exe = self.venv_dir / "Scripts" / "python.exe"
            self.pip_exe = self.venv_dir / "Scripts" / "pip.exe"
        else:
            self.python_exe = self.venv_dir / "bin" / "python"
            self.pip_exe = self.venv_dir / "bin" / "pip"
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = {
            "INFO": "\033[0;32m",  # Green
            "WARN": "\033[1;33m",  # Yellow
            "ERROR": "\033[0;31m", # Red
            "DEBUG": "\033[0;34m"  # Blue
        }
        reset = "\033[0m"
        print(f"{color.get(level, '')}{timestamp} [{level}] {message}{reset}")
        
    def run_command(self, cmd: List[str], description: str) -> bool:
        """명령 실행 및 결과 확인"""
        self.log(f"실행 중: {description}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if result.stdout:
                self.log(result.stdout, "DEBUG")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"실패: {description}", "ERROR")
            self.log(f"에러: {e.stderr}", "ERROR")
            self.errors.append(f"{description}: {e.stderr}")
            return False
            
    def clean_build(self):
        """빌드 디렉토리 정리"""
        if self.clean:
            self.log("빌드 디렉토리 정리 중...")
            dirs_to_clean = [
                self.build_dir,
                self.dist_dir,
                self.root_dir / "__pycache__",
                self.root_dir / ".pytest_cache",
                self.root_dir / "htmlcov",
                self.root_dir / ".coverage"
            ]
            
            for dir_path in dirs_to_clean:
                if dir_path.exists():
                    if dir_path.is_dir():
                        shutil.rmtree(dir_path)
                    else:
                        dir_path.unlink()
                    self.log(f"삭제됨: {dir_path}")
                    
            # 모든 __pycache__ 디렉토리 삭제
            for pycache in self.root_dir.rglob("__pycache__"):
                shutil.rmtree(pycache)
                
    def check_environment(self):
        """환경 검증"""
        self.log("환경 검증 중...")
        
        # Python 버전 확인
        python_version = sys.version_info
        if python_version < (3, 11):
            self.errors.append(f"Python 3.11 이상이 필요합니다. 현재: {python_version}")
            return False
            
        # 가상환경 확인 및 생성
        if not self.venv_dir.exists():
            self.log("가상환경 생성 중...")
            self.run_command(
                [sys.executable, "-m", "venv", str(self.venv_dir)],
                "가상환경 생성"
            )
            
        # 가상환경 Python 실행 파일 확인
        if not self.python_exe.exists():
            self.errors.append(f"가상환경 Python을 찾을 수 없습니다: {self.python_exe}")
            return False
            
        # 필수 파일 확인
        required_files = ["requirements.txt", "main.py", "simple_api.py"]
        for file in required_files:
            if not (self.root_dir / file).exists():
                self.errors.append(f"필수 파일이 없습니다: {file}")
                return False
                
        return True
        
    def install_dependencies(self):
        """의존성 설치"""
        self.log("의존성 설치 중...")
        
        # pip 업그레이드
        self.run_command(
            [str(self.python_exe), "-m", "pip", "install", "--upgrade", "pip"],
            "pip 업그레이드"
        )
        
        # requirements.txt 설치
        if self.build_type == "prod":
            # 프로덕션 빌드: 정확한 버전만 설치
            self.run_command(
                [str(self.pip_exe), "install", "-r", "requirements.txt", "--no-deps"],
                "프로덕션 의존성 설치"
            )
        else:
            # 개발 빌드: 모든 의존성 설치
            self.run_command(
                [str(self.pip_exe), "install", "-r", "requirements.txt"],
                "개발 의존성 설치"
            )
            
    def run_tests(self):
        """테스트 실행"""
        if self.build_type != "prod":
            self.log("테스트 실행 중...")
            
            # pytest 실행
            test_result = self.run_command(
                [str(self.python_exe), "-m", "pytest", "-v", "--tb=short"],
                "단위 테스트"
            )
            
            if not test_result:
                self.warnings.append("일부 테스트가 실패했습니다")
                
    def check_code_quality(self):
        """코드 품질 검사"""
        self.log("코드 품질 검사 중...")
        
        # flake8 검사
        self.run_command(
            [str(self.python_exe), "-m", "flake8", ".", "--config=.flake8", "--statistics"],
            "코드 스타일 검사"
        )
        
        # 타입 체크 (mypy)
        if (self.root_dir / "mypy.ini").exists():
            self.run_command(
                [str(self.python_exe), "-m", "mypy", ".", "--ignore-missing-imports"],
                "타입 검사"
            )
            
    def optimize_code(self):
        """코드 최적화"""
        if self.optimize and self.build_type == "prod":
            self.log("코드 최적화 중...")
            
            # Python 파일 컴파일 (.pyc)
            import py_compile
            import compileall
            
            compileall.compile_dir(
                self.root_dir,
                force=True,
                optimize=2,  # -OO 최적화
                quiet=1
            )
            
    def create_package(self):
        """배포 패키지 생성"""
        self.log("배포 패키지 생성 중...")
        
        # dist 디렉토리 생성
        self.dist_dir.mkdir(exist_ok=True)
        
        # 필요한 파일 복사
        files_to_copy = [
            "main.py",
            "simple_api.py",
            "websocket_server.py",
            "workflow_api_server.py",
            "scheduler.py",
            "requirements.txt",
            "Dockerfile",
            ".env.example"
        ]
        
        directories_to_copy = [
            "ai",
            "api",
            "common",
            "core",
            "config",
            "database",
            "market",
            "supplier",
            "workflow",
            "services"
        ]
        
        # 파일 복사
        for file in files_to_copy:
            src = self.root_dir / file
            if src.exists():
                shutil.copy2(src, self.dist_dir / file)
                
        # 디렉토리 복사
        for directory in directories_to_copy:
            src = self.root_dir / directory
            if src.exists():
                dst = self.dist_dir / directory
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
                
    def generate_build_info(self):
        """빌드 정보 생성"""
        build_info = {
            "build_time": datetime.now().isoformat(),
            "build_type": self.build_type,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "errors": self.errors,
            "warnings": self.warnings,
            "optimized": self.optimize
        }
        
        with open(self.dist_dir / "build_info.json", "w") as f:
            json.dump(build_info, f, indent=2, ensure_ascii=False)
            
    def create_docker_build(self):
        """Docker 이미지 빌드"""
        if self.build_type == "prod":
            self.log("Docker 이미지 빌드 중...")
            
            docker_tag = f"yoonni-backend:{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.run_command(
                ["docker", "build", "-t", docker_tag, "-f", "Dockerfile", "."],
                f"Docker 이미지 빌드: {docker_tag}"
            )
            
    def generate_report(self):
        """빌드 리포트 생성"""
        self.log("\n" + "="*60)
        self.log("빌드 완료 리포트")
        self.log("="*60)
        
        self.log(f"빌드 타입: {self.build_type}")
        self.log(f"최적화: {'활성화' if self.optimize else '비활성화'}")
        self.log(f"출력 디렉토리: {self.dist_dir}")
        
        if self.errors:
            self.log(f"\n❌ 에러 ({len(self.errors)}개):", "ERROR")
            for error in self.errors:
                self.log(f"  - {error}", "ERROR")
        else:
            self.log("\n✅ 에러 없음", "INFO")
            
        if self.warnings:
            self.log(f"\n⚠️  경고 ({len(self.warnings)}개):", "WARN")
            for warning in self.warnings:
                self.log(f"  - {warning}", "WARN")
                
        self.log("\n빌드가 완료되었습니다!")
        
    def build(self):
        """전체 빌드 프로세스 실행"""
        start_time = time.time()
        
        try:
            # 1. 환경 검증
            if not self.check_environment():
                self.log("환경 검증 실패", "ERROR")
                return False
                
            # 2. 빌드 정리
            self.clean_build()
            
            # 3. 의존성 설치
            self.install_dependencies()
            
            # 4. 테스트 실행
            self.run_tests()
            
            # 5. 코드 품질 검사
            self.check_code_quality()
            
            # 6. 코드 최적화
            self.optimize_code()
            
            # 7. 패키지 생성
            self.create_package()
            
            # 8. 빌드 정보 생성
            self.generate_build_info()
            
            # 9. Docker 빌드 (선택적)
            if shutil.which("docker"):
                self.create_docker_build()
            else:
                self.warnings.append("Docker가 설치되지 않아 이미지 빌드를 건너뛰었습니다")
                
            # 10. 리포트 생성
            self.generate_report()
            
            elapsed_time = time.time() - start_time
            self.log(f"\n총 빌드 시간: {elapsed_time:.2f}초")
            
            return len(self.errors) == 0
            
        except Exception as e:
            self.log(f"빌드 중 예외 발생: {str(e)}", "ERROR")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="백엔드 빌드 스크립트")
    parser.add_argument("--type", choices=["dev", "prod", "test"], default="prod",
                        help="빌드 타입 (기본값: prod)")
    parser.add_argument("--clean", action="store_true",
                        help="빌드 전 정리")
    parser.add_argument("--no-optimize", action="store_true",
                        help="최적화 비활성화")
    parser.add_argument("--verbose", action="store_true",
                        help="상세 출력")
    
    args = parser.parse_args()
    
    builder = BackendBuilder(
        build_type=args.type,
        clean=args.clean,
        optimize=not args.no_optimize
    )
    
    success = builder.build()
    sys.exit(0 if success else 1)