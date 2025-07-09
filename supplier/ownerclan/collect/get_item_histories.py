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

def get_item_histories(first: int = 100, date_from: int = None, kind: str = None, item_key: str = None):
    """오너클랜 API를 통해 상품 변경 이력을 조회하고 페이지네이션을 처리합니다."""
    if not OWNERCLAN_API_TOKEN:
        raise ValueError("OWNERCLAN_API_TOKEN이 설정되지 않았습니다.")

    all_histories = []
    has_next_page = True
    after_cursor = None
    total_fetched = 0

    while has_next_page and (total_fetched < first):
        batch_size = min(first - total_fetched, 1000)

        # GraphQL 쿼리 동적 생성
        params = f'first: {batch_size}'
        if after_cursor:
            params += f', after: "{after_cursor}"'
        if date_from:
            params += f', dateFrom: {date_from}'
        if kind:
            params += f', kind: {kind}' # kind는 Enum 타입이므로 ""를 붙이지 않음
        if item_key:
            params += f', itemKey: "{item_key}"'
        
        query = f'''
        query getItemHistories {{
          itemHistories({params}) {{
            pageInfo {{
              hasNextPage
              startCursor
              endCursor
            }}
            edges {{
              node {{
                itemKey
                kind
                title
                valueBefore
                valueAfter
                createdAt
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
            print(f"Fetching {batch_size} histories after cursor: {after_cursor}...")
            response = requests.post(OWNERCLAN_API_URL, json={'query': query}, headers=headers)
            response.raise_for_status()
            data = response.json()

            if 'errors' in data:
                print(f"GraphQL Error: {data['errors']}")
                break

            result = data.get('data', {}).get('itemHistories', {})
            edges = result.get('edges', [])
            page_info = result.get('pageInfo', {})

            if not edges:
                print("No more histories found.")
                break

            histories = [edge['node'] for edge in edges]
            all_histories.extend(histories)
            total_fetched += len(histories)

            has_next_page = page_info.get('hasNextPage', False)
            after_cursor = page_info.get('endCursor')

            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            break

    return all_histories

def transform_and_save_histories(histories: list):
    """데이터 리스트를 변환하고 Supabase에 저장합니다."""
    if not supabase or not histories:
        print("Supabase 클라이언트가 초기화되지 않았거나 데이터가 없습니다.")
        return

    transformed_histories = []
    for history in histories:
        if 'createdAt' in history and history['createdAt'] is not None:
            history['createdAt'] = datetime.fromtimestamp(history['createdAt'], tz=timezone.utc).isoformat()
        history['lastSyncedAt'] = datetime.now(timezone.utc).isoformat()
        transformed_histories.append(history)

    print(f"Transform completed. Inserting {len(transformed_histories)} histories to Supabase...")
    try:
        # 이력 데이터는 insert 사용
        data, count = supabase.table('ownerclan_item_histories').insert(transformed_histories).execute()
        print(f"성공적으로 Supabase에 저장되었습니다. {count}개 항목 처리.")
    except Exception as e:
        print(f"Supabase 저장 중 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='오너클랜에서 상품 변경 이력을 가져와 Supabase에 저장합니다.')
    parser.add_argument('--first', type=int, default=100, help='가져올 이력의 최대 개수')
    parser.add_argument('--date-from', type=int, help='조회 시작 시점 (Unix timestamp)')
    parser.add_argument('--kind', type=str, choices=['soldout', 'discontinued', 'restocked'], help='조회할 이력의 종류')
    parser.add_argument('--item-key', type=str, help='특정 상품의 이력만 조회할 경우 사용')
    args = parser.parse_args()

    print(f"총 {args.first}개의 상품 변경 이력 조회를 시작합니다.")
    all_histories = get_item_histories(first=args.first, date_from=args.date_from, kind=args.kind, item_key=args.item_key)

    if all_histories:
        print(f"총 {len(all_histories)}개의 이력 정보를 API로부터 수신했습니다.")
        transform_and_save_histories(all_histories)
    else:
        print("API로부터 데이터를 가져오지 못했습니다.")

if __name__ == "__main__":
    if not all([OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        print("오류: .env 파일에 필요한 환경변수(OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY)가 모두 설정되어 있는지 확인해주세요.")
    else:
        main()
