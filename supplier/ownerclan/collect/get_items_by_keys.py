import os
import requests
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
import argparse
import json

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

def get_items_by_keys_batch(keys: list):
    """오너클랜 API를 통해 key 리스트로 상품 정보를 조회합니다."""
    if not OWNERCLAN_API_TOKEN:
        raise ValueError("OWNERCLAN_API_TOKEN이 설정되지 않았습니다.")
    
    # keys 리스트를 JSON 문자열 형식으로 변환
    keys_json_string = json.dumps(keys)

    query = f'''
    query ItemsByKeys {{
      itemsByKeys(keys: {keys_json_string}) {{
        createdAt
        updatedAt
        key
        name
        model
        production
        origin
        price
        category {{ key name }}
        content
        shippingFee
        status
        options {{ optionAttributes {{ name value }} price quantity key }}
        taxFree
        returnable
        images(size: large)
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
            return []
        return data.get('data', {}).get('itemsByKeys', [])
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return []

def transform_and_save_items(items: list):
    """데이터 리스트를 변환하고 Supabase에 일괄 저장합니다."""
    if not supabase or not items:
        print("Supabase 클라이언트가 초기화되지 않았거나 데이터가 없습니다.")
        return

    transformed_items = []
    for item in items:
        if item.get('createdAt'):
            item['createdAt'] = datetime.fromtimestamp(item['createdAt'], tz=timezone.utc).isoformat()
        if item.get('updatedAt'):
            item['updatedAt'] = datetime.fromtimestamp(item['updatedAt'], tz=timezone.utc).isoformat()
        item['lastSyncedAt'] = datetime.now(timezone.utc).isoformat()
        transformed_items.append(item)

    print(f"Transform completed. Upserting {len(transformed_items)} items to Supabase...")
    try:
        data, count = supabase.table('ownerclan_items').upsert(transformed_items, on_conflict='key').execute()
        print(f"성공적으로 Supabase에 저장/업데이트되었습니다. {count}개 항목 처리.")
    except Exception as e:
        print(f"Supabase 저장 중 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='오너클랜에서 여러 상품 키로 정보를 가져와 Supabase에 저장합니다.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--keys', nargs='+', help='조회할 상품 key 리스트 (공백으로 구분)')
    group.add_argument('--from-file', type=str, help='상품 key 리스트가 포함된 텍스트 파일 경로 (한 줄에 key 하나씩)')
    
    args = parser.parse_args()

    item_keys = []
    if args.keys:
        item_keys = args.keys
    elif args.from_file:
        try:
            with open(args.from_file, 'r') as f:
                item_keys = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다 - {args.from_file}")
            return

    if not item_keys:
        print("조회할 상품 key가 없습니다.")
        return

    print(f"총 {len(item_keys)}개의 상품 정보 조회를 시작합니다.")

    # API는 최대 5000개까지 처리 가능하므로, 리스트를 5000개씩 나눔
    batch_size = 5000
    for i in range(0, len(item_keys), batch_size):
        batch_keys = item_keys[i:i + batch_size]
        print(f"\nProcessing batch {i // batch_size + 1}: {len(batch_keys)} keys...")
        items_data = get_items_by_keys_batch(batch_keys)
        
        if items_data:
            print(f"API로부터 {len(items_data)}개의 상품 정보를 수신했습니다.")
            transform_and_save_items(items_data)
        else:
            print("해당 배치에서 API로부터 데이터를 가져오지 못했습니다.")

if __name__ == "__main__":
    if not all([OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        print("오류: .env 파일에 필요한 환경변수(OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY)가 모두 설정되어 있는지 확인해주세요.")
    else:
        main()
