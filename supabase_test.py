import os
from dotenv import load_dotenv
from supabase import create_client, Client
import sys

# .env에서 환경변수 로드
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("[ERROR] .env에 SUPABASE_URL, SUPABASE_ANON_KEY가 모두 설정되어야 합니다.")
    sys.exit(1)

# Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# 예시: test_table의 모든 row 조회 (테이블명은 원하는 대로 수정)
def fetch_all_rows():
    response = supabase.table("test_table").select("*").execute()
    print("[조회 결과]")
    print(response.data)

if __name__ == "__main__":
    print("Supabase 연결 테스트 및 예시 테이블 조회")
    fetch_all_rows() 