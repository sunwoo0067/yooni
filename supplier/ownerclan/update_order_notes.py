# -*- coding: utf-8 -*-
"""
Ownerclan의 '주문 메모 업데이트' API를 호출하는 스크립트입니다.
기존 주문의 원장주문코드(note)와 주문관리메모(sellerNote)를 업데이트합니다.
"""

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

# 프로젝트 루트 디렉터리를 sys.path에 추가합니다.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from supplier.ownerclan.utils.auth import get_ownerclan_token

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# Ownerclan GraphQL API 엔드포인트입니다.
GRAPHQL_URL = "https://api.ownerclan.com/v1/graphql"

# 주문 메모 업데이트를 위한 GraphQL mutation 쿼리 템플릿입니다.
# 주문 key는 동적으로 삽입됩니다.
UPDATE_ORDER_NOTES_MUTATION_TEMPLATE = """
mutation UpdateOrderNotes($input: OrderUpdateNotesInput!) {{
    updateOrderNotes(key: \"{order_key}\", input: $input) {{
        key
        id
        products {{
            quantity
            price
            shippingType
            itemKey
            productName
            itemOptionInfo {{
                optionAttributes {{
                    name
                    value
                }}
                price
            }}
            trackingNumber
            shippingCompanyCode
            shippingCompanyName
            shippedDate
            additionalAttributes {{
                key
                value
            }}
            taxFree
            sellerNote
        }}
        status
        shippingInfo {{
            sender {{
                name
                phoneNumber
                email
            }}
            recipient {{
                name
                phoneNumber
                destinationAddress {{
                    addr1
                    addr2
                    postalCode
                }}
            }}
            shippingFee
        }}
        createdAt
        updatedAt
        note
        ordererNote
        sellerNote
        isBeingMediated
        adjustments {{
            reason
            price
            taxFree
        }}
        transactions {{
            key
            id
            kind
            status
            amount {{
                currency
                value
            }}
            createdAt
            updatedAt
            closedAt
            note
        }}
    }}
}}
"""

def update_order_notes(order_key: str, note: str | None = None, seller_note: str | None = None) -> dict:
    """
    주어진 주문 key에 대해 메모를 업데이트합니다.

    Args:
        order_key: 메모를 수정할 주문의 코드.
        note: 수정할 원장주문코드.
        seller_note: 수정할 주문관리메모.

    Returns:
        API 응답을 JSON 형식으로 반환합니다.
    """
    if not note and not seller_note:
        raise ValueError("적어도 note 또는 seller_note 중 하나는 제공되어야 합니다.")

    print("인증 토큰을 발급받는 중입니다...")
    token = get_ownerclan_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    input_variables = {}
    if note:
        input_variables['note'] = note
    if seller_note:
        # API 명세에 따라 sellerNotes는 배열 형태여야 합니다.
        input_variables['sellerNotes'] = [{'sellerNote': seller_note}]

    # 템플릿에 주문 key를 삽입하여 최종 쿼리를 완성합니다.
    final_query = UPDATE_ORDER_NOTES_MUTATION_TEMPLATE.format(order_key=order_key)

    payload = {
        "operationName": "UpdateOrderNotes",
        "query": final_query,
        "variables": {"input": input_variables}
    }

    print(f"{GRAPHQL_URL} 에 주문 메모 업데이트를 요청합니다...")
    response = requests.post(GRAPHQL_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킵니다.

    return response.json()

def main():
    """
    스크립트의 메인 실행 함수입니다.
    """
    parser = argparse.ArgumentParser(description="Ownerclan 주문의 메모를 업데이트합니다.")
    parser.add_argument("--key", type=str, required=True, help="메모를 수정할 주문의 key입니다.")
    parser.add_argument("--note", type=str, help="새로운 원장주문코드(note)입니다.")
    parser.add_argument("--seller-note", type=str, help="새로운 주문관리메모(sellerNote)입니다.")
    args = parser.parse_args()

    try:
        result = update_order_notes(args.key, args.note, args.seller_note)
        print("\n--- API 응답 ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생: {http_err}")
        print(f"응답 내용: {http_err.response.text}")
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")

if __name__ == "__main__":
    main()
