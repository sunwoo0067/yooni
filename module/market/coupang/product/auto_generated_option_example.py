#!/usr/bin/env python3
"""
쿠팡 자동생성옵션 활성화/비활성화 API 사용 예제
개별 옵션 상품과 전체 상품에 대한 자동생성옵션 제어 방법을 보여줍니다
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


def test_vendor_item_auto_generated_option():
    """개별 벤더아이템 자동생성옵션 활성화/비활성화 테스트"""
    print("=" * 60 + " 개별 벤더아이템 자동생성옵션 제어 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 예시 벤더아이템ID (실제 값으로 변경 필요)
        vendor_item_id = 3000000000  # 실제 벤더아이템ID로 변경 필요
        
        print(f"\n📋 개별 벤더아이템 자동생성옵션 제어...")
        print(f"   🆔 벤더아이템ID: {vendor_item_id}")
        print(f"   📝 목적: 조건에 맞는 옵션 자동생성 활성화/비활성화")
        
        # 1. 자동생성옵션 활성화 테스트
        print(f"\n" + "=" * 50 + " 자동생성옵션 활성화 " + "=" * 50)
        print(f"   🔗 API: POST /v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{vendor_item_id}/auto-generated/opt-in")
        
        print(f"\n📤 자동생성옵션 활성화 요청 중...")
        result_enable = client.enable_vendor_item_auto_generated_option(vendor_item_id)
        
        if result_enable.get("success"):
            print(f"\n✅ 자동생성옵션 활성화 성공!")
            
            vendor_item_id_result = result_enable.get("vendor_item_id")
            message = result_enable.get("message", "")
            data = result_enable.get("data", "")
            is_processing = result_enable.get("processing", False)
            
            print(f"\n📊 활성화 결과:")
            print(f"   🆔 벤더아이템ID: {vendor_item_id_result}")
            print(f"   📝 메시지: {message}")
            print(f"   📊 데이터: {data}")
            print(f"   🔄 처리 상태: {'처리 중' if is_processing else '완료'}")
            
            if is_processing:
                print(f"\n⏳ 자동생성옵션 활성화가 처리 중입니다")
                print(f"   📢 처리 완료까지 시간이 소요될 수 있습니다")
                print(f"   🔍 상품 관리 페이지에서 진행 상황을 확인해주세요")
            
            print(f"\n💡 자동생성옵션 활성화 후 예상 효과:")
            print("   1. 📦 조건에 맞는 번들 상품 자동 생성")
            print("   2. 📈 판매 기회 확대")
            print("   3. 🎯 고객 선택권 증가")
            print("   4. 💰 매출 증대 기회")
            
            print(f"\n🔍 자동생성 조건:")
            print("   - 📦 기준 상품의 수량에 따른 배수 옵션")
            print("   - 💰 기준 가격의 배수 가격 설정")
            print("   - 🎯 고객 수요가 높은 조합 우선")
            print("   - ✅ 쿠팡 정책에 부합하는 옵션만 생성")
            
        else:
            print(f"\n❌ 자동생성옵션 활성화 실패:")
            print(f"   🚨 오류: {result_enable.get('error')}")
            print(f"   📊 코드: {result_enable.get('code')}")
            
            # 오류별 해결 방법
            error_message = result_enable.get('error', '').lower()
            print(f"\n💡 해결 방법:")
            if 'system exception' in error_message:
                print("   1. 시스템 일시적 오류 - 잠시 후 재시도")
                print("   2. 네트워크 연결 상태 확인")
            else:
                print("   1. 벤더아이템ID 확인")
                print("   2. 상품이 승인 완료 상태인지 확인")
                print("   3. 자동생성 가능한 조건인지 확인")
        
        # 활성화 성공 시에만 비활성화 테스트 진행
        if result_enable.get("success"):
            # 잠시 대기
            import time
            time.sleep(3)
            
            # 2. 자동생성옵션 비활성화 테스트
            print(f"\n" + "=" * 50 + " 자동생성옵션 비활성화 " + "=" * 50)
            print(f"   🔗 API: POST /v2/providers/seller_api/apis/api/v1/marketplace/vendor-items/{vendor_item_id}/auto-generated/opt-out")
            
            print(f"\n📤 자동생성옵션 비활성화 요청 중...")
            result_disable = client.disable_vendor_item_auto_generated_option(vendor_item_id)
            
            if result_disable.get("success"):
                print(f"\n✅ 자동생성옵션 비활성화 성공!")
                
                vendor_item_id_result = result_disable.get("vendor_item_id")
                message = result_disable.get("message", "")
                data = result_disable.get("data", "")
                is_processing = result_disable.get("processing", False)
                
                print(f"\n📊 비활성화 결과:")
                print(f"   🆔 벤더아이템ID: {vendor_item_id_result}")
                print(f"   📝 메시지: {message}")
                print(f"   📊 데이터: {data}")
                print(f"   🔄 처리 상태: {'처리 중' if is_processing else '완료'}")
                
                print(f"\n💡 자동생성옵션 비활성화 후 주의사항:")
                print("   1. ⏹️ 더 이상 새로운 옵션이 자동 생성되지 않음")
                print("   2. 📦 기존 자동 생성된 옵션은 유지됨")
                print("   3. 🔄 판매 중지를 원한다면 별도 설정 필요")
                print("   4. 📈 매출 기회 감소 가능성")
                
            else:
                print(f"\n❌ 자동생성옵션 비활성화 실패:")
                print(f"   🚨 오류: {result_disable.get('error')}")
                print(f"   📊 코드: {result_disable.get('code')}")
            
            # 개별 옵션 제어 결과 요약
            print(f"\n📊 개별 옵션 제어 결과 요약:")
            print(f"   ✅ 활성화: {'성공' if result_enable.get('success') else '실패'}")
            print(f"   ⏹️ 비활성화: {'성공' if result_disable.get('success') else '실패'}")
        
    except Exception as e:
        print(f"❌ 개별 벤더아이템 자동생성옵션 제어 오류: {e}")
        import traceback
        traceback.print_exc()


def test_seller_auto_generated_option():
    """전체 상품 자동생성옵션 활성화/비활성화 테스트"""
    print("\n" + "=" * 60 + " 전체 상품 자동생성옵션 제어 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        print(f"\n📋 전체 상품 자동생성옵션 제어...")
        print(f"   🎯 범위: 판매자의 모든 등록 상품")
        print(f"   📝 목적: 조건에 맞는 전체 상품에 대한 자동생성 활성화/비활성화")
        
        # 1. 전체 상품 자동생성옵션 활성화 테스트
        print(f"\n" + "=" * 50 + " 전체 상품 자동생성옵션 활성화 " + "=" * 50)
        print(f"   🔗 API: POST /v2/providers/seller_api/apis/api/v1/marketplace/seller/auto-generated/opt-in")
        
        print(f"\n📤 전체 상품 자동생성옵션 활성화 요청 중...")
        result_enable_all = client.enable_seller_auto_generated_option()
        
        if result_enable_all.get("success"):
            print(f"\n✅ 전체 상품 자동생성옵션 활성화 성공!")
            
            message = result_enable_all.get("message", "")
            data = result_enable_all.get("data", "")
            is_processing = result_enable_all.get("processing", False)
            
            print(f"\n📊 활성화 결과:")
            print(f"   📝 메시지: {message}")
            print(f"   📊 데이터: {data}")
            print(f"   🔄 처리 상태: {'처리 중' if is_processing else '완료'}")
            
            if is_processing:
                print(f"\n⏳ 전체 상품 자동생성옵션 활성화가 처리 중입니다")
                print(f"   📢 대량 처리로 인해 완료까지 시간이 소요됩니다")
                print(f"   🔍 각 상품별 진행 상황을 주기적으로 확인해주세요")
            
            print(f"\n💡 전체 상품 자동생성옵션 활성화 효과:")
            print("   1. 🚀 전체 상품 포트폴리오 확장")
            print("   2. 📈 매출 기회 극대화")
            print("   3. 🎯 고객 만족도 향상")
            print("   4. 💰 수익성 증대")
            print("   5. 🔄 운영 효율성 개선")
            
            print(f"\n📊 예상 영향 범위:")
            print("   - 📦 조건에 맞는 모든 상품에 자동 옵션 생성")
            print("   - 🎯 카테고리별 최적화된 옵션 조합")
            print("   - 💰 가격 경쟁력 있는 번들 상품")
            print("   - 📈 검색 노출 기회 증가")
            
        else:
            print(f"\n❌ 전체 상품 자동생성옵션 활성화 실패:")
            print(f"   🚨 오류: {result_enable_all.get('error')}")
            print(f"   📊 코드: {result_enable_all.get('code')}")
            
            # 오류별 해결 방법
            error_message = result_enable_all.get('error', '').lower()
            print(f"\n💡 해결 방법:")
            if 'system exception' in error_message:
                print("   1. 시스템 일시적 오류 - 잠시 후 재시도")
                print("   2. 서버 과부하 가능성 - 시간대 변경 후 재시도")
            else:
                print("   1. 판매자 계정 상태 확인")
                print("   2. 등록된 상품이 있는지 확인")
                print("   3. API 권한 확인")
        
        # 활성화 성공 시에만 비활성화 테스트 진행
        if result_enable_all.get("success"):
            # 잠시 대기
            import time
            time.sleep(5)
            
            # 2. 전체 상품 자동생성옵션 비활성화 테스트
            print(f"\n" + "=" * 50 + " 전체 상품 자동생성옵션 비활성화 " + "=" * 50)
            print(f"   🔗 API: POST /v2/providers/seller_api/apis/api/v1/marketplace/seller/auto-generated/opt-out")
            
            print(f"\n📤 전체 상품 자동생성옵션 비활성화 요청 중...")
            result_disable_all = client.disable_seller_auto_generated_option()
            
            if result_disable_all.get("success"):
                print(f"\n✅ 전체 상품 자동생성옵션 비활성화 성공!")
                
                message = result_disable_all.get("message", "")
                data = result_disable_all.get("data", "")
                is_processing = result_disable_all.get("processing", False)
                
                print(f"\n📊 비활성화 결과:")
                print(f"   📝 메시지: {message}")
                print(f"   📊 데이터: {data}")
                print(f"   🔄 처리 상태: {'처리 중' if is_processing else '완료'}")
                
                print(f"\n💡 전체 상품 자동생성옵션 비활성화 후 주의사항:")
                print("   1. ⏹️ 모든 상품의 새로운 자동 옵션 생성 중단")
                print("   2. 📦 기존 자동 생성된 옵션들은 그대로 유지")
                print("   3. 🔄 개별 상품별 판매 중지는 별도 설정")
                print("   4. 📉 매출 기회 감소 가능성")
                print("   5. 🎯 수동 옵션 관리 필요")
                
            else:
                print(f"\n❌ 전체 상품 자동생성옵션 비활성화 실패:")
                print(f"   🚨 오류: {result_disable_all.get('error')}")
                print(f"   📊 코드: {result_disable_all.get('code')}")
            
            # 전체 상품 제어 결과 요약
            print(f"\n📊 전체 상품 제어 결과 요약:")
            print(f"   ✅ 활성화: {'성공' if result_enable_all.get('success') else '실패'}")
            print(f"   ⏹️ 비활성화: {'성공' if result_disable_all.get('success') else '실패'}")
        
    except Exception as e:
        print(f"❌ 전체 상품 자동생성옵션 제어 오류: {e}")


def test_auto_generated_option_strategy():
    """자동생성옵션 전략 시나리오 테스트"""
    print("\n" + "=" * 60 + " 자동생성옵션 전략 시나리오 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        print(f"\n📋 자동생성옵션 활용 전략 시나리오...")
        print(f"   🎯 목적: 다양한 상황별 최적 활용 방안")
        
        # 시나리오 1: 신규 상품 런칭
        print(f"\n" + "=" * 40 + " 시나리오 1: 신규 상품 런칭 " + "=" * 40)
        print(f"📈 상황: 새로운 상품을 출시하여 시장 반응 테스트")
        print(f"🎯 전략:")
        print(f"   1. 🚀 전체 상품 자동생성옵션 활성화")
        print(f"      - 시장 반응 빠른 파악")
        print(f"      - 다양한 옵션으로 고객 선택권 제공")
        print(f"   2. 📊 초기 데이터 수집 후 개별 최적화")
        print(f"      - 성과 좋은 상품만 개별 관리")
        print(f"      - 성과 낮은 상품은 비활성화")
        
        # 시나리오 2: 성수기 대응
        print(f"\n" + "=" * 40 + " 시나리오 2: 성수기 대응 " + "=" * 40)
        print(f"📈 상황: 명절/할인시즌 등 매출 극대화 필요")
        print(f"🎯 전략:")
        print(f"   1. 📦 인기 상품 개별 자동생성옵션 활성화")
        print(f"      - 선별적 옵션 확장")
        print(f"      - 재고 회전율 고려")
        print(f"   2. 💰 가격 경쟁력 있는 번들 상품 집중")
        print(f"      - 고객 구매 유도")
        print(f"      - 객단가 상승 효과")
        
        # 시나리오 3: 재고 최적화
        print(f"\n" + "=" * 40 + " 시나리오 3: 재고 최적화 " + "=" * 40)
        print(f"📈 상황: 과다 재고 또는 재고 부족 상황")
        print(f"🎯 전략:")
        print(f"   1. 📦 과다 재고 상품:")
        print(f"      - 자동생성옵션 활성화로 판매 채널 확대")
        print(f"      - 번들 상품으로 재고 소진 가속화")
        print(f"   2. 🔄 재고 부족 상품:")
        print(f"      - 자동생성옵션 비활성화")
        print(f"      - 기본 옵션만 유지하여 재고 효율성 확보")
        
        # 시나리오 4: 경쟁 대응
        print(f"\n" + "=" * 40 + " 시나리오 4: 경쟁 대응 " + "=" * 40)
        print(f"📈 상황: 경쟁사 대비 차별화 필요")
        print(f"🎯 전략:")
        print(f"   1. 🎯 차별화 상품 자동생성옵션 활성화")
        print(f"      - 독특한 번들 조합 제공")
        print(f"      - 고객 선택의 폭 확대")
        print(f"   2. 💰 가격 경쟁력 확보")
        print(f"      - 다양한 가격대 옵션 제공")
        print(f"      - 고객층별 맞춤 상품")
        
        print(f"\n💡 자동생성옵션 활용 베스트 프랙티스:")
        print(f"   1. 📊 데이터 기반 의사결정")
        print(f"      - 성과 지표 정기 모니터링")
        print(f"      - A/B 테스트를 통한 최적화")
        print(f"   2. 🔄 주기적 검토 및 조정")
        print(f"      - 월별/분기별 전략 재검토")
        print(f"      - 시장 변화에 따른 유연한 대응")
        print(f"   3. 🎯 선택과 집중")
        print(f"      - 전체 활성화 vs 개별 관리 균형")
        print(f"      - 핵심 상품 집중 관리")
        print(f"   4. 📈 성과 측정")
        print(f"      - 매출 증가율 추적")
        print(f"      - 고객 만족도 모니터링")
        
    except Exception as e:
        print(f"❌ 자동생성옵션 전략 시나리오 테스트 오류: {e}")


def test_validation_scenarios():
    """자동생성옵션 API 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 자동생성옵션 API 검증 테스트 " + "=" * 60)
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 벤더아이템ID 검증 테스트
    print(f"\n🆔 벤더아이템ID 검증 테스트:")
    
    test_vendor_item_ids = [
        (None, "None 값"),
        (0, "0 값"),
        (-123, "음수 값"),
        ("abc", "문자열"),
        (3000000000, "정상값")
    ]
    
    for vendor_item_id, description in test_vendor_item_ids:
        try:
            if vendor_item_id is not None:
                validate_vendor_item_id(vendor_item_id)
            else:
                # None 값은 별도 처리
                raise ValueError("벤더아이템ID(vendor_item_id)는 필수입니다")
            print(f"   ✅ {description} ({vendor_item_id}): 검증 통과")
        except ValueError as e:
            print(f"   ❌ {description} ({vendor_item_id}): {e}")
        except Exception as e:
            print(f"   ⚠️  {description} ({vendor_item_id}): 예상치 못한 오류 - {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 자동생성옵션 활성화/비활성화 API 예제 시작")
    print("=" * 120)
    
    try:
        # 개별 벤더아이템 자동생성옵션 제어 테스트
        test_vendor_item_auto_generated_option()
        
        # 전체 상품 자동생성옵션 제어 테스트
        test_seller_auto_generated_option()
        
        # 자동생성옵션 전략 시나리오 테스트
        test_auto_generated_option_strategy()
        
        # 검증 시나리오 테스트
        test_validation_scenarios()
        
        print(f"\n" + "=" * 50 + " 자동생성옵션 API 예제 완료 " + "=" * 50)
        print("✅ 모든 자동생성옵션 API 예제가 완료되었습니다!")
        
        print(f"\n🎉 구현된 API들:")
        print("   1. ✅ 개별 상품 자동생성옵션 활성화 (POST /vendor-items/{vendorItemId}/auto-generated/opt-in)")
        print("   2. ✅ 개별 상품 자동생성옵션 비활성화 (POST /vendor-items/{vendorItemId}/auto-generated/opt-out)")
        print("   3. ✅ 전체 상품 자동생성옵션 활성화 (POST /seller/auto-generated/opt-in)")
        print("   4. ✅ 전체 상품 자동생성옵션 비활성화 (POST /seller/auto-generated/opt-out)")
        
        print(f"\n💡 자동생성옵션 API 주요 특징:")
        print("   - 개별 상품과 전체 상품 단위 제어")
        print("   - 조건에 맞는 옵션 자동 생성")
        print("   - SUCCESS/PROCESSING/FAILED 상태 지원")
        print("   - 기존 자동생성 옵션 유지")
        print("   - 실시간 활성화/비활성화")
        
        print(f"\n📊 활용 방안:")
        print("   🚀 시장 확장: 다양한 옵션으로 판매 기회 증대")
        print("   🎯 고객 만족: 선택의 폭 확대")
        print("   💰 매출 증대: 번들 상품을 통한 객단가 상승")
        print("   📈 운영 효율: 자동화를 통한 관리 부담 감소")
        print("   🔄 전략적 제어: 상황별 유연한 옵션 관리")
        
    except Exception as e:
        print(f"\n❌ 자동생성옵션 API 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()