# -*- coding: utf-8 -*-
"""Ownerclan의 여러 주문 내역을 조회하는 스크립트.

이 스크립트는 Ownerclan의 GraphQL API를 사용하여 주문 목록을 조회합니다.
다양한 검색 조건과 페이지네이션을 지원하여 특정 조건에 맞는 주문들을 필터링하고,
결과를 JSON 형식으로 출력합니다.

주요 기능:
- 날짜 범위, 주문 상태, 판매자 메모 등 다양한 조건으로 주문 검색
- 페이지네이션(cursor-based)을 통한 데이터 조회
- 명령줄 인자를 통한 동적 쿼리 생성

사용 예시:
# 지난 7일간의 '결제완료' 상태인 주문 5개를 조회
python supplier/ownerclan/list_orders.py --status PAYMENT_COMPLETED --first 5 --dateFrom $(date -d '-7 days' +%Y-%m-%dT%H:%M:%S)

# 특정 cursor 이후의 주문 10개를 조회
python supplier/ownerclan/list_orders.py --after "some_cursor_value" --first 10
"""

import argparse
import json
import os
from datetime import datetime
import sys
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# 현재 스크립트의 경로를 기준으로 프로젝트 루트 경로를 추가합니다.
# 이렇게 하면 다른 위치에서 스크립트를 실행해도 모듈을 올바르게 임포트할 수 있습니다.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from supplier.ownerclan.utils.auth import get_ownerclan_token

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- Constants ---
GRAPHQL_URL = "https://api.ownerclan.com/v1/graphql"

# 복수 주문 조회를 위한 GraphQL 쿼리 템플릿입니다.
ORDERS_QUERY_TEMPLATE = """
query {
  allOrders {
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    edges {
      cursor
      node {
        key
        id
        products {
          quantity
          price
          shippingType
          itemKey
          itemOptionInfo {
            optionAttributes {
              name
              value
            }
            price
          }
          trackingNumber
          shippingCompanyCode
          shippedDate
          additionalAttributes {
            key
            value
          }
          taxFree
        }
        status
        shippingInfo {
          sender {
            name
            phoneNumber
            email
          }
          recipient {
            name
            phoneNumber
            destinationAddress {
              addr1
              addr2
              postalCode
            }
          }
          shippingFee
        }
        createdAt
        updatedAt
        note
        ordererNote
        sellerNote
        isBeingMediated
        adjustments {
          reason
          price
          taxFree
        }
        transactions {
          key
          id
          kind
          status
          amount {
            currency
            value
          }
          createdAt
          updatedAt
          closedAt
          note
        }
      }
    }
  }
}
"""

# --- Functions ---

def list_orders(token: str, **kwargs) -> dict:
    """GraphQL API를 호출하여 주문 목록을 조회합니다."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 쿼리 인자를 생성합니다.
    # 예: {'first': 10, 'status': 'PAYMENT_COMPLETED'} -> 'first: 10, status: PAYMENT_COMPLETED'
    args_list = []
    for k, v in kwargs.items():
        if v is None:
            continue
        # 문자열 값은 따옴표로 감싸줍니다.
        if isinstance(v, str):
            args_list.append(f'{k}: "{v}"')
        # 그 외의 값(Int 등)은 그대로 사용합니다.
        else:
            args_list.append(f'{k}: {v}')
    args_str = ", ".join(args_list)

    # 인자가 있는 경우, 쿼리에 동적으로 추가합니다.
    if args_str:
        final_query = ORDERS_QUERY_TEMPLATE.replace("allOrders", f"allOrders({args_str})")
    else:
        final_query = ORDERS_QUERY_TEMPLATE

    response = requests.get(GRAPHQL_URL, params={"query": final_query}, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def save_orders_to_supabase(supabase: Client, orders: list[dict]):
    """
    조회된 주문 목록을 Supabase 데이터베이스에 'upsert'합니다.
    테이블 스키마가 데이터 타입을 직접 처리하므로 별도의 변환이 필요 없습니다.
    """
    if not orders:
        print("저장할 주문이 없습니다.")
        return

    processed_orders = []
    for order in orders:
        processed_order = order.copy()
        for key in ['createdAt', 'updatedAt']:
            if key in processed_order and processed_order[key] is not None:
                try:
                    # Unix 타임스탬프(밀리초)를 ISO 8601 형식으로 변환합니다.
                    processed_order[key] = datetime.fromtimestamp(processed_order[key] / 1000).isoformat()
                except (ValueError, TypeError):
                    processed_order[key] = None # 변환 실패 시 NULL로 처리
        processed_orders.append(processed_order)

    print(f"\n총 {len(processed_orders)}개의 주문을 Supabase('ownerclan_orders' 테이블)에 저장합니다...")

    try:
        # 'key'를 기준으로 데이터를 일괄적으로 upsert합니다.
        data, count = supabase.table('ownerclan_orders').upsert(processed_orders).execute()

        if data and len(data[1]) > 0:
            print(f"성공적으로 {len(data[1])}개의 주문을 저장/업데이트했습니다.")
        else:
            print("변경된 데이터가 없습니다.")

    except Exception as e:
        print(f"Supabase 저장 중 오류 발생: {e}")


def main():
    """명령줄 인자를 파싱하고 주문 조회 함수를 실행합니다."""
    parser = argparse.ArgumentParser(description="오너클랜에서 여러 주문 내역을 조회합니다.")
    
    # Pagination 인수
    parser.add_argument("--after", type=str, help="이 cursor 값 이후의 주문만 조회합니다.")
    parser.add_argument("--first", type=int, help="조회할 주문의 최대 개수입니다.")

    # Search 인수
    parser.add_argument("--dateFrom", type=str, help="주문 생성일 시작 (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--dateTo", type=str, help="주문 생성일 종료 (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--note", type=str, help="원장주문코드(note)에 포함된 값으로 검색합니다.")
    parser.add_argument("--sellerNote", type=str, help="주문 관리 코드(sellerNote)에 포함된 값으로 검색합니다.")
    parser.add_argument("--status", type=str, help="특정 주문 상태의 주문만 조회합니다.")
    parser.add_argument("--shippedAfter", type=str, help="송장 입력일 시작 (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--shippedBefore", type=str, help="송장 입력일 종료 (YYYY-MM-DDTHH:MM:SS)")

    args = parser.parse_args()

    # 인자에서 None 값을 제거하여 kwargs를 생성합니다.
    kwargs = {k: v for k, v in vars(args).items() if v is not None}

    # 날짜 범위 기본값 설정 (명시되지 않은 경우, 최근 90일)
    if 'dateFrom' not in kwargs and 'dateTo' not in kwargs and 'note' not in kwargs and 'sellerNote' not in kwargs:
        now = datetime.now()
        kwargs['dateTo'] = now.isoformat()
        kwargs['dateFrom'] = (now - timedelta(days=90)).isoformat()

    try:
        print("1. Obtaining authentication token...")
        token = get_ownerclan_token()
        print("   -> Token obtained successfully.")

        print(f"\n2. Fetching orders with parameters: {kwargs}...")
        # Supabase 클라이언트 초기화
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            print("오류: SUPABASE_URL 또는 SUPABASE_ANON_KEY가 .env 파일에 설정되지 않았습니다.")
            sys.exit(1)

        supabase: Client = create_client(supabase_url, supabase_key)

        data = list_orders(token, **kwargs)
        print("   -> Data fetched successfully.")

        print("\n3. API Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 조회된 주문을 Supabase에 저장
        if data and 'data' in data and 'allOrders' in data['data'] and 'edges' in data['data']['allOrders']:
            order_edges = data['data']['allOrders']['edges']
            # 실제 주문 데이터는 'node' 키에 들어있으므로, node 리스트를 추출합니다.
            order_nodes = [item['node'] for item in order_edges if 'node' in item]
            save_orders_to_supabase(supabase, order_nodes)
        else:
            print("API 응답에서 주문 데이터를 찾을 수 없거나, 조회된 주문이 없습니다.")

    except requests.exceptions.HTTPError as e:
        print(f"\nAn HTTP error occurred: {e}")
        print(f"Response body: {e.response.text}")
    except KeyError as e:
        print(f"\nAn error occurred while parsing the response: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
