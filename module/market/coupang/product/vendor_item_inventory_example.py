#!/usr/bin/env python3
"""
쿠팡 벤더아이템 재고/가격/상태 조회 API 사용 예제
vendorItemId로 아이템의 재고수량, 판매가격, 판매상태를 조회하는 방법을 보여줍니다
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
    validate_vendor_item_id
)


def test_basic_vendor_item_inventory():
    """기본적인 벤더아이템 재고/가격/상태 조회 테스트"""
    print("=" * 60 + " 기본 벤더아이템 재고/가격/상태 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 예시 벤더아이템ID (실제 아이템 ID로 변경 필요)
        vendor_item_id = 3000000000  # 실제 벤더아이템ID로 변경 필요
        
        print(f"\n📋 벤더아이템 재고/가격/상태 조회 중...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{vendor_item_id}/inventories")
        
        # 벤더아이템 재고/가격/상태 조회 실행
        print(f"\n📤 벤더아이템 재고/가격/상태 조회 요청 중...")
        result = client.get_vendor_item_inventory(vendor_item_id)
        
        if result.get("success"):
            print(f"\n✅ 벤더아이템 재고/가격/상태 조회 성공!")
            
            # 기본 정보 표시
            data = result.get("data", {})
            vendor_item_id_result = result.get("vendor_item_id")
            seller_item_id = result.get("seller_item_id")
            amount_in_stock = result.get("amount_in_stock")
            sale_price = result.get("sale_price")
            on_sale = result.get("on_sale")
            
            print(f"\n📊 아이템 정보:")
            print(f"   🆔 벤더아이템ID: {vendor_item_id_result}")
            print(f"   🆔 셀러아이템ID: {seller_item_id}")
            print(f"   📦 잔여수량: {amount_in_stock}개")
            print(f"   💰 판매가격: {sale_price:,}원")
            print(f"   🔄 판매상태: {'판매중' if on_sale else '판매중지'}")
            
            # 재고 상태 분석
            print(f"\n📈 재고 상태 분석:")
            
            # 재고 수준 분석
            if amount_in_stock == 0:
                stock_level = "품절"
                stock_emoji = "❌"
                stock_alert = "긴급: 재고 보충 필요"
            elif amount_in_stock <= 5:
                stock_level = "부족"
                stock_emoji = "⚠️"
                stock_alert = "주의: 재고 부족"
            elif amount_in_stock <= 20:
                stock_level = "보통"
                stock_emoji = "⚡"
                stock_alert = "정보: 재고 관리 필요"
            else:
                stock_level = "충분"
                stock_emoji = "✅"
                stock_alert = "양호: 재고 충분"
            
            print(f"   {stock_emoji} 재고 수준: {stock_level}")
            print(f"   📢 알림: {stock_alert}")
            
            # 판매 상태 분석
            print(f"\n🔄 판매 상태 분석:")
            if on_sale:
                if amount_in_stock > 0:
                    sale_status = "정상 판매 중"
                    sale_emoji = "✅"
                    sale_alert = "활성: 정상 판매 진행 중"
                else:
                    sale_status = "품절 상태"
                    sale_emoji = "❌"
                    sale_alert = "긴급: 재고 없음으로 실제 판매 불가"
            else:
                sale_status = "판매 중지"
                sale_emoji = "⏸️"
                sale_alert = "정보: 판매가 중지된 상태"
            
            print(f"   {sale_emoji} 판매 상태: {sale_status}")
            print(f"   📢 알림: {sale_alert}")
            
            # 가격 분석
            print(f"\n💰 가격 정보:")
            print(f"   💲 현재 판매가: {sale_price:,}원")
            
            # 가격대별 분석
            if sale_price < 10000:
                price_category = "저가"
            elif sale_price < 50000:
                price_category = "중가"
            elif sale_price < 100000:
                price_category = "고가"
            else:
                price_category = "프리미엄"
            
            print(f"   🏷️ 가격대: {price_category}")
            
            # 재고 가치 계산
            if amount_in_stock > 0 and sale_price > 0:
                total_stock_value = amount_in_stock * sale_price
                print(f"   💎 재고 총 가치: {total_stock_value:,}원")
            
            # 종합 상태 평가
            print(f"\n🎯 종합 상태 평가:")
            
            # 상태 점수 계산
            status_score = 0
            
            if on_sale:
                status_score += 50  # 판매 중이면 50점
            
            if amount_in_stock > 20:
                status_score += 40  # 재고 충분하면 40점
            elif amount_in_stock > 5:
                status_score += 25  # 재고 보통이면 25점
            elif amount_in_stock > 0:
                status_score += 10  # 재고 적으면 10점
            # 품절이면 0점
            
            if sale_price > 0:
                status_score += 10  # 가격이 설정되어 있으면 10점
            
            # 종합 평가
            if status_score >= 90:
                overall_status = "우수"
                overall_emoji = "🟢"
                overall_message = "모든 지표가 양호합니다"
            elif status_score >= 70:
                overall_status = "양호"
                overall_emoji = "🟡"
                overall_message = "일부 개선이 필요합니다"
            elif status_score >= 50:
                overall_status = "보통"
                overall_emoji = "🟠"
                overall_message = "여러 개선사항이 있습니다"
            else:
                overall_status = "개선 필요"
                overall_emoji = "🔴"
                overall_message = "즉시 조치가 필요합니다"
            
            print(f"   {overall_emoji} 종합 상태: {overall_status} ({status_score}/100점)")
            print(f"   📝 평가: {overall_message}")
            
            # 권장 액션
            print(f"\n💡 권장 액션:")
            actions = []
            
            if amount_in_stock == 0:
                actions.append("🔄 재고 즉시 보충")
            elif amount_in_stock <= 5:
                actions.append("📦 재고 추가 주문")
            
            if not on_sale and amount_in_stock > 0:
                actions.append("▶️ 판매 재개 검토")
            
            if on_sale and amount_in_stock == 0:
                actions.append("⏸️ 임시 판매 중지 검토")
            
            if sale_price == 0:
                actions.append("💰 판매가격 설정")
            
            if not actions:
                actions.append("✅ 현재 상태 양호, 지속 모니터링")
            
            for i, action in enumerate(actions, 1):
                print(f"   {i}. {action}")
            
        else:
            print(f"\n❌ 벤더아이템 재고/가격/상태 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
            
            # 일반적인 오류 해결 방법 제시
            error_message = result.get('error', '').lower()
            print(f"\n💡 해결 방법:")
            if '유효한 옵션이 없습니다' in error_message or 'invalid' in error_message:
                print("   1. 벤더아이템ID가 올바른지 확인")
                print("   2. 해당 아이템이 삭제되었는지 확인")
                print("   3. 다른 벤더아이템ID로 재시도")
            else:
                print("   1. 네트워크 연결 상태 확인")
                print("   2. API 키 및 권한 확인")
                print("   3. 잠시 후 재시도")
            
    except Exception as e:
        print(f"❌ 벤더아이템 재고/가격/상태 조회 오류: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_vendor_items():
    """여러 벤더아이템의 재고/가격/상태 일괄 조회 테스트"""
    print("\n" + "=" * 60 + " 여러 벤더아이템 일괄 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 비교할 벤더아이템ID들 (실제 아이템 ID로 변경 필요)
        vendor_item_ids = [3000000000, 3000000001, 3000000002]
        
        print(f"\n🔄 여러 벤더아이템 일괄 조회")
        print(f"   📦 비교 대상: {len(vendor_item_ids)}개 아이템")
        print(f"   📝 목적: 아이템별 재고/가격/상태 비교")
        
        item_results = {}
        
        # 각 벤더아이템별로 조회
        for i, vendor_item_id in enumerate(vendor_item_ids, 1):
            print(f"\n📦 아이템 {i} (ID: {vendor_item_id}) 조회 중...")
            
            result = client.get_vendor_item_inventory(vendor_item_id)
            
            if result.get("success"):
                item_results[vendor_item_id] = result
                amount_in_stock = result.get("amount_in_stock", 0)
                sale_price = result.get("sale_price", 0)
                on_sale = result.get("on_sale", False)
                
                print(f"   ✅ 아이템 {i} 조회 성공")
                print(f"      📦 재고: {amount_in_stock}개")
                print(f"      💰 가격: {sale_price:,}원")
                print(f"      🔄 판매: {'중' if on_sale else '중지'}")
            else:
                print(f"   ❌ 아이템 {i} 조회 실패: {result.get('error')}")
                item_results[vendor_item_id] = None
        
        # 아이템별 비교 분석
        if any(item_results.values()):
            print(f"\n📊 벤더아이템별 비교 분석:")
            
            # 각 아이템의 요약 정보
            print(f"\n📋 아이템별 요약:")
            total_stock = 0
            total_value = 0
            active_items = 0
            
            for vendor_item_id, result in item_results.items():
                if result:
                    amount_in_stock = result.get("amount_in_stock", 0)
                    sale_price = result.get("sale_price", 0)
                    on_sale = result.get("on_sale", False)
                    
                    status_icon = "✅" if on_sale and amount_in_stock > 0 else "⚠️" if on_sale else "⏸️"
                    print(f"   {status_icon} ID {vendor_item_id}: {amount_in_stock}개, {sale_price:,}원, {'판매중' if on_sale else '중지'}")
                    
                    total_stock += amount_in_stock
                    total_value += amount_in_stock * sale_price
                    if on_sale and amount_in_stock > 0:
                        active_items += 1
                else:
                    print(f"   ❌ ID {vendor_item_id}: 조회 실패")
            
            # 전체 통계
            print(f"\n📈 전체 통계:")
            print(f"   📦 총 재고량: {total_stock}개")
            print(f"   💎 총 재고 가치: {total_value:,}원")
            print(f"   ✅ 활성 아이템: {active_items}개")
            print(f"   📊 전체 아이템: {len(vendor_item_ids)}개")
            
            # 재고 분포 분석
            stock_distribution = {}
            for result in item_results.values():
                if result:
                    amount_in_stock = result.get("amount_in_stock", 0)
                    if amount_in_stock == 0:
                        category = "품절"
                    elif amount_in_stock <= 5:
                        category = "부족"
                    elif amount_in_stock <= 20:
                        category = "보통"
                    else:
                        category = "충분"
                    
                    stock_distribution[category] = stock_distribution.get(category, 0) + 1
            
            print(f"\n📊 재고 수준 분포:")
            for category, count in stock_distribution.items():
                percentage = (count / len([r for r in item_results.values() if r])) * 100
                print(f"   📦 {category}: {count}개 ({percentage:.1f}%)")
            
            # 가격 분석
            prices = [result.get("sale_price", 0) for result in item_results.values() if result]
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                
                print(f"\n💰 가격 분석:")
                print(f"   📊 평균 가격: {avg_price:,.0f}원")
                print(f"   🔽 최저 가격: {min_price:,}원")
                print(f"   🔺 최고 가격: {max_price:,}원")
            
            print(f"\n💡 일괄 조회 활용:")
            print("   📊 포트폴리오 관리: 전체 아이템 현황 파악")
            print("   🔍 재고 모니터링: 품절/부족 아이템 식별")
            print("   📈 성과 분석: 아이템별 가치 및 판매 현황")
            print("   ⚡ 효율성: 여러 아이템 동시 모니터링")
        
    except Exception as e:
        print(f"❌ 여러 벤더아이템 일괄 조회 오류: {e}")


def test_vendor_item_validation():
    """벤더아이템ID 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 벤더아이템ID 검증 테스트 " + "=" * 60)
    
    client = ProductClient()
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "None 값",
            "vendor_item_id": None,
            "expected_error": "필수입니다"
        },
        {
            "name": "0 값",
            "vendor_item_id": 0,
            "expected_error": "0보다 큰"
        },
        {
            "name": "음수 값",
            "vendor_item_id": -123,
            "expected_error": "0보다 큰"
        },
        {
            "name": "문자열 (숫자)",
            "vendor_item_id": "3000000000",
            "expected_error": None  # 변환되어 통과해야 함
        },
        {
            "name": "문자열 (비숫자)",
            "vendor_item_id": "abc123",
            "expected_error": "숫자여야"
        },
        {
            "name": "너무 큰 수",
            "vendor_item_id": 99999999999999,  # 14자리
            "expected_error": "유효 범위"
        },
        {
            "name": "유효한 벤더아이템ID",
            "vendor_item_id": 3000000000,
            "expected_error": None  # 오류 없음
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 {i}: {test_case['name']}")
        vendor_item_id = test_case['vendor_item_id']
        expected_error = test_case['expected_error']
        
        try:
            validate_vendor_item_id(vendor_item_id)
            
            if expected_error is None:
                print(f"   ✅ 예상대로 검증 통과")
            else:
                print(f"   ⚠️ 예상과 다르게 검증 통과 (검증 로직 확인 필요)")
                
        except ValueError as e:
            if expected_error and expected_error in str(e):
                print(f"   ✅ 예상대로 검증 실패: {e}")
            else:
                print(f"   ⚠️ 예상과 다른 검증 오류: {e}")
        except Exception as e:
            print(f"   ❌ 예상치 못한 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 벤더아이템 재고/가격/상태 조회 API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 벤더아이템 재고/가격/상태 조회 테스트
        test_basic_vendor_item_inventory()
        
        # 여러 벤더아이템 일괄 조회 테스트
        test_multiple_vendor_items()
        
        # 검증 시나리오 테스트
        test_vendor_item_validation()
        
        print(f"\n" + "=" * 50 + " 벤더아이템 재고/가격/상태 조회 예제 완료 " + "=" * 50)
        print("✅ 모든 벤더아이템 재고/가격/상태 조회 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 재고/가격/상태 조회")
        print("   2. ✅ 여러 아이템 일괄 조회")
        print("   3. ✅ 재고 수준 분석")
        print("   4. ✅ 판매 상태 분석")
        print("   5. ✅ 가격 정보 분석")
        print("   6. ✅ 종합 상태 평가")
        print("   7. ✅ 벤더아이템ID 검증")
        
        print(f"\n💡 벤더아이템 재고/가격/상태 조회 주요 특징:")
        print("   - 벤더아이템ID 기반 정확한 재고 정보")
        print("   - 실시간 재고수량/판매가격/판매상태 제공")
        print("   - 재고 수준별 상태 분석")
        print("   - 판매 활성화 여부 확인")
        print("   - 재고 가치 계산")
        
        print(f"\n📊 활용 방안:")
        print("   📦 재고 관리: 실시간 재고 수준 모니터링")
        print("   💰 가격 관리: 현재 판매가격 확인")
        print("   🔄 판매 관리: 판매 활성화 상태 추적")
        print("   📈 성과 분석: 아이템별 재고 가치 계산")
        print("   🚨 알림 시스템: 품절/부족 상품 자동 감지")
        print("   📊 대시보드: 전체 아이템 현황 통합 관리")
        
    except Exception as e:
        print(f"\n❌ 벤더아이템 재고/가격/상태 조회 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()