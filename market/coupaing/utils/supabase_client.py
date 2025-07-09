import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일의 경로를 프로젝트 루트 기준으로 설정합니다.
# __file__는 현재 파일의 경로입니다.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

def get_supabase_client() -> Client:
    """
    환경 변수에서 Supabase URL과 서비스 키를 읽어
    Supabase 클라이언트 객체를 생성하고 반환합니다.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY가 .env 파일에 설정되어야 합니다.")

    return create_client(supabase_url, supabase_key)

# 다른 파일에서 임포트하여 사용할 수 있도록 단일 클라이언트 인스턴스를 생성합니다.
supabase_client = get_supabase_client()
