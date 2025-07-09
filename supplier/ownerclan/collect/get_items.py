import os
import requests
from datetime import datetime
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

def get_all_ownerclan_items(first: int = 100, min_price: int = None, max_price: int = None, search: str = None):
    """오너클랜 API를 통해 여러 상품 정보를 조회하고 페이지네이션을 처리합니다."""
    if not OWNERCLAN_API_TOKEN:
        raise ValueError("OWNERCLAN_API_TOKEN이 설정되지 않았습니다.")

    all_items = []
    has_next_page = True
    after_cursor = None
    total_fetched = 0

    while has_next_page and (total_fetched < first):
        # 한 번에 가져올 아이템 수 결정 (최대 1000개, 남은 아이템 수 고려)
        batch_size = min(first - total_fetched, 1000)
        
        # GraphQL 쿼리 동적 생성
        params = f'first: {batch_size}'
        if after_cursor:
            params += f', after: "{after_cursor}"'
        if min_price is not None:
            params += f', minPrice: {min_price}'
        if max_price is not None:
            params += f', maxPrice: {max_price}'
        if search:
            params += f', search: "{search}"'

        query = f'''
        query getAllItemsData {{
          allItems({params}) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}
            edges {{
              node {{
                createdAt
                updatedAt
                key
                name
                model
                production
                origin
                price
                pricePolicy
                fixedPrice
                category {{ key name fullName }}
                shippingFee
                shippingType
                images(size: large)
                status
                options {{ optionAttributes {{ name value }} price quantity }}
                taxFree
                adultOnly
                returnable
                guaranteedShippingPeriod
                openmarketSellable
                boxQuantity
                attributes
                returnCriteria
                metadata
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
            print(f"Fetching {batch_size} items after cursor: {after_cursor}...")
            response = requests.post(OWNERCLAN_API_URL, json={'query': query}, headers=headers)
            response.raise_for_status()
            data = response.json()

            if 'errors' in data:
                print(f"GraphQL Error: {data['errors']}")
                break

            result = data.get('data', {}).get('allItems', {})
            edges = result.get('edges', [])
            page_info = result.get('pageInfo', {})

            if not edges:
                print("No more items found.")
                break

            # node만 추출하여 리스트에 추가
            items = [edge['node'] for edge in edges]
            all_items.extend(items)
            total_fetched += len(items)

            has_next_page = page_info.get('hasNextPage', False)
            after_cursor = page_info.get('endCursor')

            # API 속도 제한을 피하기 위해 약간의 딜레이 추가
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            break

    return all_items

def transform_and_save_batch(items: list):
    """데이터 리스트를 변환하고 Supabase에 일괄 저장합니다."""
    if not supabase or not items:
        print("Supabase 클라이언트가 초기화되지 않았거나 데이터가 없습니다.")
        return

    transformed_items = []
    for item in items:
        # Unix timestamp를 ISO 8601 형식으로 변환
        if 'createdAt' in item and item['createdAt'] is not None:
            item['createdAt'] = datetime.fromtimestamp(item['createdAt']).isoformat()
        if 'updatedAt' in item and item['updatedAt'] is not None:
            item['updatedAt'] = datetime.fromtimestamp(item['updatedAt']).isoformat()
        item['lastSyncedAt'] = datetime.now().isoformat()
        transformed_items.append(item)

    print(f"Transform completed. Upserting {len(transformed_items)} items to Supabase...")
    try:
        data, count = supabase.table('ownerclan_items').upsert(transformed_items, on_conflict='key').execute()
        print(f"성공적으로 Supabase에 저장/업데이트되었습니다. {count}개 항목 처리.")
    except Exception as e:
        print(f"Supabase 저장 중 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='오너클랜에서 여러 상품 정보를 가져와 Supabase에 저장합니다.')
    parser.add_argument('--first', type=int, default=100, help='가져올 상품의 최대 개수')
    parser.add_argument('--min_price', type=int, help='검색할 상품의 최저 가격')
    parser.add_argument('--max_price', type=int, help='검색할 상품의 최고 가격')
    parser.add_argument('--search', type=str, help='검색어')
    args = parser.parse_args()

    print(f"총 {args.first}개의 상품 정보 조회를 시작합니다.")
    all_items = get_all_ownerclan_items(first=args.first, min_price=args.min_price, max_price=args.max_price, search=args.search)

    if all_items:
        print(f"총 {len(all_items)}개의 상품 정보를 API로부터 수신했습니다.")
        transform_and_save_batch(all_items)
    else:
        print("API로부터 데이터를 가져오지 못했습니다.")

if __name__ == "__main__":
    if not all([OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        print("오류: .env 파일에 필요한 환경변수(OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY)가 모두 설정되어 있는지 확인해주세요.")
    else:
        main()
