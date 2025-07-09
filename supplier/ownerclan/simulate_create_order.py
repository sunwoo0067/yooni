# -*- coding: utf-8 -*-
"""
Ownerclan의 '테스트 주문' (주문 생성 시뮬레이션) API를 호출하는 스크립트입니다.
실제 주문을 생성하지 않고, 예상되는 상품 금액과 배송비 정보를 조회합니다.
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

# 주문 생성 시뮬레이션을 위한 GraphQL mutation 쿼리입니다.
SIMULATE_CREATE_ORDER_MUTATION = """
mutation SimulateCreateOrder($input: OrderInput!) {
    simulateCreateOrder(input: $input) {
        itemAmounts {
            amount
            itemKey
        }
        shippingAmount
        extraShippingFeeExists
    }
}
"""

def simulate_create_order(input_data: dict) -> dict:
    """
    주어진 입력 데이터로 Ownerclan 주문 생성을 시뮬레이션합니다.

    Args:
        input_data: 주문 생성을 위한 데이터 (sender, recipient, products 등).

    Returns:
        API 응답을 JSON 형식으로 반환합니다.
    """
    print("인증 토큰을 발급받는 중입니다...")
    token = get_ownerclan_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "operationName": "SimulateCreateOrder",
        "query": SIMULATE_CREATE_ORDER_MUTATION,
        "variables": {"input": input_data}
    }

    print(f"{GRAPHQL_URL} 에 주문 생성 시뮬레이션을 요청합니다...")
    response = requests.post(GRAPHQL_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킵니다.

    return response.json()

def main():
    """
    스크립트의 메인 실행 함수입니다.
    명령줄 인자를 파싱하고, 시뮬레이션 함수를 호출합니다.
    """
    parser = argparse.ArgumentParser(description="Ownerclan 주문 생성을 시뮬레이션합니다.")
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="주문 정보가 담긴 JSON 파일의 경로입니다."
    )
    args = parser.parse_args()

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except FileNotFoundError:
        print(f"오류: 파일 '{args.input_file}'을(를) 찾을 수 없습니다.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"오류: 파일 '{args.input_file}'이(가) 올바른 JSON 형식이 아닙니다.")
        sys.exit(1)

    try:
        result = simulate_create_order(input_data)
        print("\n--- API 응답 ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생: {http_err}")
        print(f"응답 내용: {http_err.response.text}")
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")

if __name__ == "__main__":
    main()
