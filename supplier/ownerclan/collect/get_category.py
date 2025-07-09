import os
import requests
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
import argparse
import time

# .env 파일에서 환경 변수 로드
load_dotenv()

# --- 환경 변수 설정 ---
OWNERCLAN_API_URL = "https://api-sandbox.ownerclan.com/v1/graphql"
OWNERCLAN_API_TOKEN = os.getenv("OWNERCLAN_API_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- Supabase 클라이언트 초기화 ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

def get_category_data(key: str, first: int = 100, after: str = None):
    """오너클랜 API를 통해 카테고리 정보와 하위 카테고리 목록을 조회합니다."""
    if not OWNERCLAN_API_TOKEN:
        raise ValueError("OWNERCLAN_API_TOKEN이 설정되지 않았습니다.")

    after_clause = f', after: "{after}"' if after else ""

    query = f'''
    query getCategoryData {{
      category(key: "{key}") {{
        key
        id
        name
        fullName
        attributes
        parent {{ key }}
        descendants(first: {first}{after_clause}) {{
          pageInfo {{
            hasNextPage
            endCursor
          }}
          edges {{
            node {{
              key
              id
              name
              fullName
              attributes
              parent {{ key }}
            }}
          }}
        }}
      }}
    }}
    '''

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OWNERCLAN_API_TOKEN}"
    }

    try:
        response = requests.post(OWNERCLAN_API_URL, json={'query': query}, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Error: {data['errors']}")
            return None
        return data.get('data', {}).get('category')
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return None

def save_categories_to_db(categories: list):
    """카테고리 데이터 리스트를 Supabase에 일괄 저장합니다."""
    if not supabase or not categories:
        return

    transformed_data = []
    for cat in categories:
        transformed_data.append({
            'key': cat.get('key'),
            'id': cat.get('id'),
            'name': cat.get('name'),
            'fullName': cat.get('fullName'),
            'attributes': cat.get('attributes'),
            'parentKey': cat.get('parent', {}).get('key') if cat.get('parent') else None,
            'lastSyncedAt': datetime.now(timezone.utc).isoformat()
        })
    
    try:
        data, count = supabase.table('ownerclan_categories').upsert(transformed_data, on_conflict='key').execute()
        print(f"Saved/Updated {len(transformed_data)} categories.")
    except Exception as e:
        print(f"Supabase 저장 중 오류 발생: {e}")

def sync_all_descendants(start_key: str):
    """특정 카테고리부터 시작하여 모든 하위 카테고리를 동기화합니다."""
    print(f"Starting sync for all descendants of category key: {start_key}")
    has_next_page = True
    cursor = None
    total_synced = 0

    while has_next_page:
        print(f"Fetching descendants... (After cursor: {cursor})")
        category_data = get_category_data(start_key, after=cursor)

        if not category_data:
            print("Failed to fetch category data. Aborting.")
            break

        # 시작 카테고리 정보 저장 (루프 첫 실행 시)
        if cursor is None:
            save_categories_to_db([category_data])
            total_synced += 1

        descendants_connection = category_data.get('descendants', {})
        descendants = [edge['node'] for edge in descendants_connection.get('edges', [])]
        
        if descendants:
            save_categories_to_db(descendants)
            total_synced += len(descendants)
        
        page_info = descendants_connection.get('pageInfo', {})
        has_next_page = page_info.get('hasNextPage', False)
        cursor = page_info.get('endCursor')

        if not has_next_page:
            print("No more pages. Sync complete.")
        else:
            time.sleep(1) # API 요청 간 짧은 딜레이
            
    print(f"\nTotal categories synced: {total_synced}")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='오너클랜 카테고리 정보를 가져와 Supabase에 저장합니다.')
    parser.add_argument('key', type=str, help='조회를 시작할 카테고리 key. (모든 카테고리 동기화는 \'00000000\' 사용)')
    args = parser.parse_args()

    sync_all_descendants(args.key)

if __name__ == "__main__":
    if not all([OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        print("오류: .env 파일에 필요한 환경변수(OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY)가 모두 설정되어 있는지 확인해주세요.")
    else:
        main()
