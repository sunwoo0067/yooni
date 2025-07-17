#!/usr/bin/env python3
"""
쿠팡 상품 상태변경이력 조회 API 사용 예제
등록상품ID로 상품의 상태변경이력을 조회하는 방법을 보여줍니다
"""

import os
import sys
from datetime import datetime
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.product import (
    ProductClient,
    ProductStatusHistoryParams
)


def test_basic_status_history():
    """기본적인 상품 상태변경이력 조회 테스트"""
    print("=" * 60 + " 기본 상품 상태변경이력 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 예시 등록상품ID (실제 상품 ID로 변경 필요)
        seller_product_id = 123456789  # 실제 등록상품ID로 변경 필요
        
        # 기본 조회 파라미터 설정
        history_params = ProductStatusHistoryParams(
            seller_product_id=seller_product_id,
            max_per_page=10  # 페이지당 10개씩
        )
        
        print(f"\n📋 상품 상태변경이력 조회 중...")
        print(f"   🆔 등록상품ID: {seller_product_id}")
        print(f"   📄 페이지당 건수: {history_params.max_per_page}개")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/{seller_product_id}/histories")
        
        # 상태변경이력 조회 실행
        print(f"\n📤 상태변경이력 조회 요청 중...")
        result = client.get_product_status_history(history_params)
        
        if result.get("success"):
            print(f"\n✅ 상품 상태변경이력 조회 성공!")
            
            # 기본 정보 표시
            data = result.get("data", [])
            next_token = result.get("next_token")
            has_next = result.get("has_next")
            
            print(f"\n📊 조회 결과 정보:")
            print(f"   📦 조회된 이력수: {len(data)}개")
            print(f"   🆔 등록상품ID: {result.get('seller_product_id')}")
            print(f"   ➡️ 다음 페이지: {'있음' if has_next else '없음'}")
            if next_token:
                print(f"   🔑 다음 페이지 토큰: {next_token}")
            
            # 상태변경이력 표시
            if data:
                print(f"\n📋 상품 상태변경이력:")
                for i, history in enumerate(data, 1):
                    status = history.get('status', 'N/A')
                    comment = history.get('comment', 'N/A')
                    created_by = history.get('createdBy', 'N/A')
                    created_at = history.get('createdAt', 'N/A')
                    
                    print(f"\n   {i}. 상태변경 이력:")
                    print(f"      📊 상태: {status}")
                    print(f"      💬 변경내용: {comment}")
                    print(f"      👤 변경자: {created_by}")
                    print(f"      📅 변경일시: {created_at}")
                
                # 상태변경 분석
                print(f"\n📈 상태변경 분석:")
                
                # 상태별 빈도
                status_count = {}
                for history in data:
                    status = history.get('status', 'Unknown')
                    status_count[status] = status_count.get(status, 0) + 1
                
                print(f"\n📊 상태별 변경 빈도:")
                for status, count in status_count.items():
                    percentage = (count / len(data)) * 100
                    print(f"   📊 {status}: {count}회 ({percentage:.1f}%)")
                
                # 변경자별 분석
                creator_count = {}
                for history in data:
                    creator = history.get('createdBy', 'Unknown')
                    creator_count[creator] = creator_count.get(creator, 0) + 1
                
                print(f"\n👤 변경자별 분석:")
                for creator, count in creator_count.items():
                    percentage = (count / len(data)) * 100
                    print(f"   👤 {creator}: {count}회 ({percentage:.1f}%)")
                
                # 최근 변경 상태
                if len(data) > 0:
                    latest_history = data[0]  # 첫 번째가 가장 최근
                    print(f"\n🔄 최근 상태변경:")
                    print(f"   📊 현재 상태: {latest_history.get('status', 'N/A')}")
                    print(f"   📅 마지막 변경: {latest_history.get('createdAt', 'N/A')}")
                    print(f"   👤 변경자: {latest_history.get('createdBy', 'N/A')}")
                    
                # 진행 단계 분석
                system_changes = sum(1 for h in data if h.get('createdBy') == '쿠팡 셀러 시스템')
                manual_changes = len(data) - system_changes
                
                print(f"\n🔄 처리 방식 분석:")
                print(f"   🤖 시스템 자동 처리: {system_changes}회")
                print(f"   👤 수동 처리: {manual_changes}회")
                
                if len(data) > 1:
                    print(f"   📈 전체 진행 단계: {len(data)}단계")
                    
            else:
                print(f"\n📭 해당 상품의 상태변경이력이 없습니다")
                print(f"💡 상품이 아직 등록되지 않았거나 ID가 잘못되었을 수 있습니다")
            
        else:
            print(f"\n❌ 상품 상태변경이력 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
            
    except Exception as e:
        print(f"❌ 상품 상태변경이력 조회 오류: {e}")
        import traceback
        traceback.print_exc()


def test_paginated_status_history():
    """페이징을 통한 전체 상태변경이력 조회 테스트"""
    print("\n" + "=" * 60 + " 페이징 상태변경이력 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        seller_product_id = 123456789  # 실제 등록상품ID로 변경 필요
        
        print(f"\n📄 페이징을 통한 전체 상태변경이력 조회")
        print(f"   🆔 등록상품ID: {seller_product_id}")
        print(f"   📝 방법: 여러 페이지를 순차적으로 조회")
        
        all_histories = []
        current_token = None
        page_num = 1
        max_pages = 5  # 테스트용으로 최대 5페이지만
        
        while page_num <= max_pages:
            print(f"\n📄 {page_num}페이지 조회 중...")
            
            # 페이지별 조회 파라미터
            history_params = ProductStatusHistoryParams(
                seller_product_id=seller_product_id,
                max_per_page=5,  # 테스트용으로 페이지당 5개
                next_token=current_token
            )
            
            # 페이지 조회
            result = client.get_product_status_history(history_params)
            
            if result.get("success"):
                data = result.get("data", [])
                next_token = result.get("next_token")
                
                print(f"   ✅ {page_num}페이지 조회 성공: {len(data)}개 이력")
                
                # 전체 목록에 추가
                all_histories.extend(data)
                
                # 페이지별 요약 정보 표시
                if data:
                    latest_status = data[0].get('status', 'N/A')
                    oldest_status = data[-1].get('status', 'N/A')
                    print(f"      📊 최신 상태: {latest_status}")
                    print(f"      📊 가장 오래된 상태: {oldest_status}")
                
                # 다음 페이지 확인
                if next_token:
                    print(f"   ➡️ 다음 페이지 토큰: {next_token}")
                    current_token = next_token
                    page_num += 1
                else:
                    print(f"   🏁 마지막 페이지입니다")
                    break
            else:
                print(f"   ❌ {page_num}페이지 조회 실패: {result.get('error')}")
                break
        
        # 전체 결과 분석
        print(f"\n📊 전체 페이징 조회 결과:")
        print(f"   📄 조회한 페이지 수: {page_num - 1}페이지")
        print(f"   📦 총 수집된 이력수: {len(all_histories)}개")
        
        if all_histories:
            # 전체 상태 변화 추적
            status_timeline = []
            for history in all_histories:
                status_timeline.append({
                    'status': history.get('status'),
                    'created_at': history.get('createdAt'),
                    'created_by': history.get('createdBy')
                })
            
            print(f"\n📈 전체 상태 변화 타임라인:")
            print(f"   🔄 총 상태변경 횟수: {len(status_timeline)}회")
            
            # 상태 진행 경로
            unique_statuses = []
            for history in reversed(all_histories):  # 시간순으로 정렬
                status = history.get('status')
                if not unique_statuses or unique_statuses[-1] != status:
                    unique_statuses.append(status)
            
            print(f"\n🛤️ 상태 진행 경로:")
            progress_path = " → ".join(unique_statuses)
            print(f"   📊 {progress_path}")
            
            # 처리 시간 분석
            if len(all_histories) >= 2:
                first_change = all_histories[-1].get('createdAt', '')  # 가장 오래된 변경
                last_change = all_histories[0].get('createdAt', '')   # 가장 최근 변경
                
                print(f"\n⏰ 처리 시간 분석:")
                print(f"   📅 최초 변경: {first_change}")
                print(f"   📅 최근 변경: {last_change}")
                
            print(f"\n💡 페이징 조회 활용법:")
            print(f"   📊 전체 이력: 상품의 완전한 진행 과정 파악")
            print(f"   🔍 패턴 분석: 상태변경 패턴 및 소요시간 분석")
            print(f"   📋 감사: 변경 이력 추적 및 감사")
        
    except Exception as e:
        print(f"❌ 페이징 상태변경이력 조회 오류: {e}")


def test_multiple_products_history():
    """여러 상품의 상태변경이력 비교 테스트"""
    print("\n" + "=" * 60 + " 여러 상품 상태변경이력 비교 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 비교할 상품들 (실제 상품 ID로 변경 필요)
        product_ids = [123456789, 123456790, 123456791]
        
        print(f"\n🔄 여러 상품 상태변경이력 비교")
        print(f"   📦 비교 대상: {len(product_ids)}개 상품")
        print(f"   📝 목적: 상품별 상태변경 패턴 비교")
        
        product_histories = {}
        
        # 각 상품별로 상태변경이력 조회
        for i, product_id in enumerate(product_ids, 1):
            print(f"\n📦 상품 {i} (ID: {product_id}) 조회 중...")
            
            history_params = ProductStatusHistoryParams(
                seller_product_id=product_id,
                max_per_page=20  # 충분한 이력 조회
            )
            
            result = client.get_product_status_history(history_params)
            
            if result.get("success"):
                data = result.get("data", [])
                product_histories[product_id] = data
                print(f"   ✅ 상품 {i} 조회 성공: {len(data)}개 이력")
                
                if data:
                    current_status = data[0].get('status', 'N/A')
                    print(f"      📊 현재 상태: {current_status}")
            else:
                print(f"   ❌ 상품 {i} 조회 실패: {result.get('error')}")
                product_histories[product_id] = []
        
        # 상품별 비교 분석
        if any(product_histories.values()):
            print(f"\n📊 상품별 상태변경이력 비교:")
            
            # 각 상품의 현재 상태
            print(f"\n📋 상품별 현재 상태:")
            for product_id, histories in product_histories.items():
                if histories:
                    current_status = histories[0].get('status', 'N/A')
                    total_changes = len(histories)
                    print(f"   🆔 상품 {product_id}: {current_status} ({total_changes}회 변경)")
                else:
                    print(f"   🆔 상품 {product_id}: 이력 없음")
            
            # 상태변경 횟수 비교
            change_counts = {pid: len(histories) for pid, histories in product_histories.items()}
            avg_changes = sum(change_counts.values()) / len(change_counts)
            
            print(f"\n📈 상태변경 활동 분석:")
            print(f"   📊 평균 변경 횟수: {avg_changes:.1f}회")
            
            most_active = max(change_counts.items(), key=lambda x: x[1])
            least_active = min(change_counts.items(), key=lambda x: x[1])
            
            print(f"   🔥 가장 활발한 상품: ID {most_active[0]} ({most_active[1]}회)")
            print(f"   😴 가장 조용한 상품: ID {least_active[0]} ({least_active[1]}회)")
            
            # 공통 상태변경 패턴
            all_statuses = set()
            for histories in product_histories.values():
                for history in histories:
                    all_statuses.add(history.get('status', ''))
            
            print(f"\n🛤️ 공통 상태 유형:")
            print(f"   📊 전체 상태 종류: {len(all_statuses)}개")
            print(f"   📋 상태 목록: {', '.join(sorted(all_statuses))}")
            
            print(f"\n💡 비교 분석 활용:")
            print(f"   📊 성과 비교: 상품별 진행 속도 비교")
            print(f"   🔍 문제 식별: 지연되는 상품 파악")
            print(f"   📈 패턴 분석: 일반적인 상태변경 경로 파악")
        
    except Exception as e:
        print(f"❌ 여러 상품 상태변경이력 비교 오류: {e}")


def test_status_history_validation():
    """상태변경이력 조회 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 상태변경이력 조회 검증 테스트 " + "=" * 60)
    
    client = ProductClient()
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "등록상품ID 누락",
            "params": ProductStatusHistoryParams(
                seller_product_id=0  # 잘못된 값
            ),
            "expected_error": "등록상품ID"
        },
        {
            "name": "음수 등록상품ID",
            "params": ProductStatusHistoryParams(
                seller_product_id=-123  # 음수
            ),
            "expected_error": "0보다 큰"
        },
        {
            "name": "잘못된 페이지 크기 (0)",
            "params": ProductStatusHistoryParams(
                seller_product_id=123456789,
                max_per_page=0  # 잘못된 값
            ),
            "expected_error": "페이지당 건수"
        },
        {
            "name": "잘못된 페이지 크기 (101)",
            "params": ProductStatusHistoryParams(
                seller_product_id=123456789,
                max_per_page=101  # 최대값 초과
            ),
            "expected_error": "페이지당 건수"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 {i}: {test_case['name']}")
        
        try:
            result = client.get_product_status_history(test_case['params'])
            
            if result.get("success"):
                print(f"   ⚠️ 예상과 다르게 성공함 (검증 로직 확인 필요)")
            else:
                print(f"   ✅ 예상대로 검증 실패: {result.get('error')}")
                
        except ValueError as e:
            expected = test_case.get('expected_error', '')
            if expected in str(e):
                print(f"   ✅ 예상대로 검증 오류: {e}")
            else:
                print(f"   ⚠️ 예상과 다른 검증 오류: {e}")
        except Exception as e:
            print(f"   ❌ 예상치 못한 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 상태변경이력 조회 API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 상태변경이력 조회 테스트
        test_basic_status_history()
        
        # 페이징 조회 테스트
        test_paginated_status_history()
        
        # 여러 상품 비교 테스트
        test_multiple_products_history()
        
        # 검증 시나리오 테스트
        test_status_history_validation()
        
        print(f"\n" + "=" * 50 + " 상태변경이력 조회 예제 완료 " + "=" * 50)
        print("✅ 모든 상품 상태변경이력 조회 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 상태변경이력 조회")
        print("   2. ✅ 페이징 기반 전체 이력 조회")
        print("   3. ✅ 여러 상품 이력 비교")
        print("   4. ✅ 상태변경 패턴 분석")
        print("   5. ✅ 진행 경로 추적")
        print("   6. ✅ 처리 시간 분석")
        print("   7. ✅ 검증 오류 처리")
        
        print(f"\n💡 상태변경이력 조회 주요 특징:")
        print("   - 등록상품ID 기반 정확한 이력 추적")
        print("   - 페이징 지원으로 대량 이력 조회 가능")
        print("   - 상태/변경자/변경시간 상세 정보 제공")
        print("   - 시스템/수동 변경 구분 가능")
        print("   - 실시간 상태변경 반영")
        
        print(f"\n📊 활용 방안:")
        print("   🔍 상태 추적: 상품 진행 상황 실시간 모니터링")
        print("   📊 패턴 분석: 상태변경 패턴 및 소요시간 분석")
        print("   🔄 프로세스 개선: 지연 구간 식별 및 최적화")
        print("   📋 감사: 변경 이력 추적 및 책임자 확인")
        print("   🚨 문제 해결: 상태변경 실패 원인 분석")
        
    except Exception as e:
        print(f"\n❌ 상품 상태변경이력 조회 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()