# -*- coding: utf-8 -*-
"""
Ownerclan의 '주문 취소 요청' API를 호출하는 스크립트입니다.
배송 준비중(preparing) 상태인 주문의 취소를 요청합니다.
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

# 주문 취소 요청을 위한 GraphQL mutation 쿼리입니다.
REQUEST_CANCELLATION_MUTATION = """
mutation RequestOrderCancellation($key: ID!, $input: RequestOrderCancellationInput!) {
    requestOrderCancellation(key: $key, input: $input) {
        key
        id
        products {
            quantity
            price
            shippingType
            itemKey
            productName
            itemOptionInfo {
                optionAttributes {
                    name
                    value
                }
                price
            }
            trackingNumber
            shippingCompanyCode
            shippingCompanyName
            shippedDate
            additionalAttributes {
                key
                value
            }
            taxFree
            sellerNote
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
"""

def request_order_cancellation(order_key: str, reason: str) -> dict:
    """
    주어진 주문 key에 해당하는 주문의 취소를 요청합니다.

    Args:
        order_key: 취소 요청할 주문의 코드.
        reason: 취소 요청 사유.

    Returns:
        API 응답을 JSON 형식으로 반환합니다.
    """
    print("인증 토큰을 발급받는 중입니다...")
    token = get_ownerclan_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    variables = {
        "key": order_key,
        "input": {
            "cancelReason": reason
        }
    }

    payload = {
        "operationName": "RequestOrderCancellation",
        "query": REQUEST_CANCELLATION_MUTATION,
        "variables": variables
    }

    print(f"{GRAPHQL_URL} 에 주문 취소 요청을 보냅니다...")
    response = requests.post(GRAPHQL_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킵니다.

    return response.json()

def main():
    """
    스크립트의 메인 실행 함수입니다.
    """
    parser = argparse.ArgumentParser(description="Ownerclan 주문 취소를 요청합니다.")
    parser.add_argument("--key", type=str, required=True, help="취소 요청할 주문의 key입니다.")
    parser.add_argument("--reason", type=str, required=True, help="주문 취소 요청 사유입니다.")
    args = parser.parse_args()

    try:
        result = request_order_cancellation(args.key, args.reason)
        print("\n--- API 응답 ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생: {http_err}")
        print(f"응답 내용: {http_err.response.text}")
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")

if __name__ == "__main__":
    main()
