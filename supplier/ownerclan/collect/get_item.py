import os
import requests
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import argparse

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

def get_ownerclan_item(item_key: str):
    """오너클랜 API를 통해 단일 상품 정보를 조회합니다."""
    if not OWNERCLAN_API_TOKEN:
        raise ValueError("OWNERCLAN_API_TOKEN이 설정되지 않았습니다.")

    query = f'''
    query getItemData {{ 
      item(key: "{item_key}") {{ 
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
        category {{ 
          key 
          name 
          fullName 
        }} 
        shippingFee 
        shippingType 
        images(size: large) 
        status 
        options {{ 
          optionAttributes {{ 
            name 
            value 
          }} 
          price 
          quantity 
        }} 
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
    '''

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OWNERCLAN_API_TOKEN}"
    }

    try:
        response = requests.post(OWNERCLAN_API_URL, json={'query': query}, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Error: {data['errors']}")
            return None
        return data.get('data', {}).get('item')
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return None

def transform_data_for_supabase(item_data: dict):
    """Supabase에 저장하기 위해 데이터를 변환합니다."""
    if not item_data:
        return None

    # Unix timestamp(초 단위)를 ISO 8601 형식의 문자열로 변환
    if 'createdAt' in item_data and item_data['createdAt'] is not None:
        item_data['createdAt'] = datetime.fromtimestamp(item_data['createdAt']).isoformat()
    if 'updatedAt' in item_data and item_data['updatedAt'] is not None:
        item_data['updatedAt'] = datetime.fromtimestamp(item_data['updatedAt']).isoformat()

    # lastSyncedAt 필드 추가
    item_data['lastSyncedAt'] = datetime.now().isoformat()

    return item_data

def save_item_to_supabase(item_data: dict):
    """변환된 상품 데이터를 Supabase에 저장합니다."""
    if not supabase or not item_data:
        print("Supabase 클라이언트가 초기화되지 않았거나 데이터가 없습니다.")
        return None

    try:
        # 'key'를 기준으로 이미 데이터가 있으면 업데이트, 없으면 삽입 (upsert)
        data, count = supabase.table('ownerclan_items').upsert(item_data, on_conflict='key').execute()
        print(f"성공적으로 Supabase에 저장/업데이트되었습니다. {count}개 항목 처리.")
        return data
    except Exception as e:
        print(f"Supabase 저장 중 오류 발생: {e}")
        return None

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='오너클랜에서 상품 정보를 가져와 Supabase에 저장합니다.')
    parser.add_argument('item_key', type=str, help='조회할 상품의 오너클랜 key')
    args = parser.parse_args()

    print(f"{args.item_key} 상품 정보 조회를 시작합니다...")
    raw_item_data = get_ownerclan_item(args.item_key)

    if raw_item_data:
        print("API에서 데이터 수신 성공. Supabase 저장을 위해 데이터 변환 중...")
        transformed_data = transform_data_for_supabase(raw_item_data)
        if transformed_data:
            save_item_to_supabase(transformed_data)
    else:
        print("API로부터 데이터를 가져오지 못했습니다.")

if __name__ == "__main__":
    if not all([OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
        print("오류: .env 파일에 필요한 환경변수(OWNERCLAN_API_TOKEN, SUPABASE_URL, SUPABASE_KEY)가 모두 설정되어 있는지 확인해주세요.")
    else:
        main()
