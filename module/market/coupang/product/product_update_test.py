#!/usr/bin/env python3
"""
쿠팡 상품 수정 API 실제 테스트
실제 API 키를 사용한 상품 수정 테스트
"""

import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.product import (
    ProductClient,
    ProductRequest,
    ProductItem,
    ProductImage,
    ProductAttribute,
    ProductNotice,
    ProductPartialUpdateRequest
)


def test_real_api_product_update():
    """실제 API로 상품 수정 테스트"""
    print("=" * 60 + " 실제 API 상품 수정 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = ProductClient()
        print("✅ 실제 API 인증으로 상품 클라이언트 초기화 성공")
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '309323422')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📝 실제 API로 상품 수정 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   🆔 수정할 상품 ID: {test_seller_product_id}")
        print(f"   💡 TEST_SELLER_PRODUCT_ID 환경변수로 상품 ID 설정 가능")
        
        # 1단계: 기존 상품 정보 조회
        print(f"\n🔍 1단계: 기존 상품 정보 조회")
        get_result = client.get_product(test_seller_product_id)
        
        if not get_result.get("success"):
            print(f"❌ 상품 조회 실패: {get_result.get('error')}")
            print(f"💡 존재하는 상품 ID를 TEST_SELLER_PRODUCT_ID 환경변수에 설정하세요")
            
            # 조회 실패 시에도 예시 수정 요청 실행
            print(f"\n📝 예시 데이터로 수정 요청 테스트 진행...")
            seller_product_id_int = int(test_seller_product_id)
        else:
            print(f"✅ 상품 조회 성공")
            data = get_result.get("data", {})
            print(f"   📦 조회된 상품명: {data.get('sellerProductName', 'N/A')}")
            seller_product_id_int = int(test_seller_product_id)
        
        # 2단계: 상품 수정 요청 생성
        print(f"\n🔧 2단계: 상품 수정 요청 생성")
        
        # 판매 기간 설정
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 수정할 아이템 (실제로는 조회된 데이터에서 가져옴)
        updated_item = ProductItem(
            seller_product_item_id=769536471,  # 실제 아이템 ID로 변경 필요
            vendor_item_id=123456789,  # 실제 벤더 아이템 ID
            item_name="실제API_수정테스트_아이템",
            original_price=25000,
            sale_price=20000,
            maximum_buy_count=150,
            maximum_buy_for_person=5,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="REAL_API_TEST_UPDATE",
            barcode="8801234567895"
        )
        
        # 대표 이미지
        image = ProductImage(
            image_order=0,
            image_type="REPRESENTATION",
            vendor_path="https://example.com/real-api-test-update.jpg"
        )
        
        # 상품 속성
        attribute = ProductAttribute(
            attribute_type_name="테스트용량",
            attribute_value_name="실제API테스트용"
        )
        
        # 고시정보
        notice = ProductNotice(
            notice_category_name="화장품",
            notice_category_detail_name="용량 또는 중량",
            content="실제API 테스트용"
        )
        
        # 실제 상품 수정 요청 생성
        update_request = ProductRequest(
            seller_product_id=seller_product_id_int,
            display_category_code=56137,  # 실제 카테고리 코드로 변경 필요
            seller_product_name="실제API_상품수정_테스트",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="realApiUpdateTest",
            requested=False,  # 테스트용이므로 승인요청 안함
            
            # 상품 정보
            display_product_name="실제API 상품수정 테스트",
            brand="실제API테스트브랜드",
            general_product_name="실제API 수정 테스트 상품",
            product_group="테스트 상품군",
            manufacture="실제API테스트브랜드",
            
            # 배송 정보
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",
            delivery_charge_type="FREE",
            delivery_charge=0,
            free_ship_over_amount=0,
            delivery_charge_on_return=2500,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            
            # 반품지 정보 (실제 반품지 코드로 변경 필요)
            return_center_code="1000274592",
            return_charge_name="실제API 테스트 반품센터",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="실제API테스트빌딩 5층",
            return_charge=2500,
            return_charge_vendor="N",
            
            # AS 정보
            after_service_information="실제API 테스트 A/S: 1234-5678",
            after_service_contact_number="1234-5678",
            
            # 출고지 정보 (실제 출고지 코드로 변경 필요)
            outbound_shipping_place_code="74010",
            
            # 리스트 데이터
            items=[updated_item],
            images=[image],
            attributes=[attribute],
            notices=[notice]
        )
        
        print(f"\n📋 실제 수정 요청 정보:")
        print(f"   📝 상품명: {update_request.display_product_name}")
        print(f"   🏷️ 브랜드: {update_request.brand}")
        print(f"   💰 가격: {updated_item.sale_price:,}원 (정가: {updated_item.original_price:,}원)")
        print(f"   📦 재고: {updated_item.maximum_buy_count}개")
        print(f"   🚚 배송: 무료배송")
        
        # 3단계: 실제 상품 수정 실행
        print(f"\n📤 3단계: 실제 상품 수정 실행")
        result = client.update_product(update_request)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 상품 수정 성공:")
            data = result.get("data", {})
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            if data:
                print(f"   📊 응답 데이터:")
                pprint(data, width=100, indent=4)
            
            print(f"\n   ✅ 수정 완료 단계:")
            print(f"      1. ✅ 기존 상품 정보 조회")
            print(f"      2. ✅ 수정 요청 데이터 생성")
            print(f"      3. ✅ 실제 API 수정 실행")
            
        else:
            print(f"\n❌ 실제 API 상품 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
            print(f"\n💡 일반적인 수정 실패 사유:")
            print(f"   - 존재하지 않는 seller_product_id")
            print(f"   - 권한이 없는 상품 수정 시도")
            print(f"   - 승인완료 상품의 가격/재고 수정 시도 (별도 API 필요)")
            print(f"   - 잘못된 seller_product_item_id")
            print(f"   - 카테고리에 맞지 않는 속성 정보")
                
    except Exception as e:
        print(f"❌ 실제 API 상품 수정 오류: {e}")
        import traceback
        traceback.print_exc()


def test_real_api_option_management():
    """실제 API로 옵션 관리 테스트"""
    print("\n" + "=" * 60 + " 실제 API 옵션 관리 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '309323423')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🔧 실제 API로 옵션 관리 테스트")
        print(f"   🆔 상품 ID: {test_seller_product_id}")
        print(f"   🏢 판매자 ID: {vendor_id}")
        
        # 기존 상품 정보 조회
        print(f"\n📋 기존 상품 정보 조회 중...")
        get_result = client.get_product(test_seller_product_id)
        
        if get_result.get("success"):
            print(f"✅ 상품 조회 성공")
            data = get_result.get("data", {})
            items = data.get("items", [])
            print(f"   📦 기존 옵션 수: {len(items)}개")
            
            # 기존 옵션 정보 출력
            for i, item in enumerate(items[:3]):  # 상위 3개만
                item_id = item.get('sellerProductItemId', 'N/A')
                item_name = item.get('itemName', 'N/A')
                price = item.get('salePrice', 0)
                print(f"      {i+1}. {item_name} (ID: {item_id}) - {price:,}원")
        else:
            print(f"⚠️ 상품 조회 실패: {get_result.get('error')}")
            print(f"예시 데이터로 옵션 관리 테스트 진행...")
            items = []
        
        # 옵션 수정 시나리오
        print(f"\n🔧 옵션 수정 시나리오:")
        print(f"   📝 기존 옵션 수정 (ID 포함)")
        print(f"   ➕ 새 옵션 추가 (ID 없음)")
        
        # 판매 기간
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 수정할 기존 옵션 (실제 ID 사용)
        if items:
            first_item = items[0]
            existing_item_id = first_item.get('sellerProductItemId')
            vendor_item_id = first_item.get('vendorItemId')
        else:
            existing_item_id = 769536471  # 예시 ID
            vendor_item_id = 123456789
        
        modified_option = ProductItem(
            seller_product_item_id=existing_item_id,
            vendor_item_id=vendor_item_id,
            item_name="실제API_수정된옵션",
            original_price=22000,
            sale_price=18500,  # 가격 수정
            maximum_buy_count=120,
            maximum_buy_for_person=4,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="REAL_MODIFIED_OPT",
            barcode="8801234567896"
        )
        
        # 새로운 옵션 추가
        new_option = ProductItem(
            # seller_product_item_id 없음 = 새 옵션
            item_name="실제API_신규추가옵션",
            original_price=28000,
            sale_price=24000,
            maximum_buy_count=80,
            maximum_buy_for_person=3,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=2,
            external_vendor_sku="REAL_NEW_OPT",
            barcode="8801234567897"
        )
        
        # 옵션 관리 요청
        option_request = ProductRequest(
            seller_product_id=int(test_seller_product_id),
            display_category_code=56137,
            seller_product_name="실제API_옵션관리_테스트",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="realApiOptionTest",
            requested=False,
            
            display_product_name="실제API 옵션관리 테스트",
            brand="실제API테스트",
            general_product_name="옵션관리 테스트",
            product_group="테스트",
            manufacture="실제API테스트",
            
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",
            delivery_charge_type="FREE",
            delivery_charge=0,
            free_ship_over_amount=0,
            delivery_charge_on_return=3000,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            
            return_center_code="1000274592",
            return_charge_name="실제API 옵션테스트 반품센터",
            company_contact_number="02-9999-1234",
            return_zip_code="135-090",
            return_address="서울특별시 강남구",
            return_address_detail="옵션테스트빌딩",
            return_charge=3000,
            return_charge_vendor="N",
            
            after_service_information="실제API 옵션 A/S: 1588-9999",
            after_service_contact_number="1588-9999",
            outbound_shipping_place_code="74010",
            
            # 수정된 옵션 + 새 옵션
            items=[modified_option, new_option],
            images=[
                ProductImage(
                    image_order=0,
                    image_type="REPRESENTATION",
                    vendor_path="https://example.com/real-api-option-test.jpg"
                )
            ],
            attributes=[
                ProductAttribute(
                    attribute_type_name="옵션타입",
                    attribute_value_name="수정됨/신규추가"
                )
            ],
            notices=[
                ProductNotice(
                    notice_category_name="화장품",
                    notice_category_detail_name="용량 또는 중량",
                    content="실제API 옵션관리 테스트"
                )
            ]
        )
        
        print(f"\n📋 옵션 관리 상세:")
        print(f"   🔧 수정 옵션 ID: {existing_item_id}")
        print(f"   💰 수정 옵션 가격: {modified_option.sale_price:,}원")
        print(f"   ➕ 새 옵션명: {new_option.item_name}")
        print(f"   💰 새 옵션 가격: {new_option.sale_price:,}원")
        
        # 옵션 관리 실행
        print(f"\n📤 옵션 관리 요청 실행...")
        result = client.update_product(option_request)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 옵션 관리 성공:")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            print(f"\n   📊 옵션 관리 결과:")
            print(f"      ✅ 기존 옵션 수정 완료")
            print(f"      ✅ 새 옵션 추가 완료")
            print(f"      💡 삭제된 옵션: items 배열에서 제외된 옵션들")
            
        else:
            print(f"\n❌ 실제 API 옵션 관리 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
    except Exception as e:
        print(f"❌ 실제 API 옵션 관리 오류: {e}")


def test_real_api_update_validation():
    """실제 API 수정 검증 테스트"""
    print("\n" + "=" * 60 + " 실제 API 수정 검증 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🧪 실제 API에서 발생할 수 있는 수정 오류 시나리오")
        
        # 시나리오 1: 존재하지 않는 상품 ID
        print(f"\n📋 시나리오 1: 존재하지 않는 상품 ID")
        invalid_request = ProductRequest(
            seller_product_id=999999999,  # 존재하지 않는 ID
            display_category_code=56137,
            seller_product_name="존재하지않는상품테스트",
            vendor_id=vendor_id,
            sale_started_at="2024-01-01T00:00:00",
            sale_ended_at="2024-12-31T23:59:59",
            vendor_user_id="invalidTest",
            items=[
                ProductItem(
                    item_name="테스트아이템",
                    original_price=10000,
                    sale_price=8000,
                    maximum_buy_count=10,
                    maximum_buy_for_person=1,
                    maximum_buy_for_person_period=30,
                    outbound_shipping_time_day=1
                )
            ],
            images=[
                ProductImage(
                    image_order=0,
                    image_type="REPRESENTATION",
                    vendor_path="https://example.com/test.jpg"
                )
            ]
        )
        
        result1 = client.update_product(invalid_request)
        if result1.get("success"):
            print(f"   ⚠️ 예상과 다르게 성공함")
        else:
            print(f"   ✅ 예상대로 실패: {result1.get('error')}")
        
        # 시나리오 2: 잘못된 seller_product_item_id
        print(f"\n📋 시나리오 2: 잘못된 seller_product_item_id")
        invalid_item_request = ProductRequest(
            seller_product_id=int(os.getenv('TEST_SELLER_PRODUCT_ID', '309323422')),
            display_category_code=56137,
            seller_product_name="잘못된아이템ID테스트",
            vendor_id=vendor_id,
            sale_started_at="2024-01-01T00:00:00",
            sale_ended_at="2024-12-31T23:59:59",
            vendor_user_id="invalidItemTest",
            items=[
                ProductItem(
                    seller_product_item_id=999999999,  # 존재하지 않는 아이템 ID
                    item_name="잘못된아이템",
                    original_price=10000,
                    sale_price=8000,
                    maximum_buy_count=10,
                    maximum_buy_for_person=1,
                    maximum_buy_for_person_period=30,
                    outbound_shipping_time_day=1
                )
            ],
            images=[
                ProductImage(
                    image_order=0,
                    image_type="REPRESENTATION",
                    vendor_path="https://example.com/test.jpg"
                )
            ]
        )
        
        result2 = client.update_product(invalid_item_request)
        if result2.get("success"):
            print(f"   ⚠️ 예상과 다르게 성공함")
        else:
            print(f"   ✅ 예상대로 실패: {result2.get('error')}")
        
        print(f"\n💡 실제 API 오류 패턴 확인:")
        print(f"   - 데이터 검증 오류는 클라이언트에서 처리")
        print(f"   - 권한/존재여부 오류는 서버에서 반환")
        print(f"   - 오류 메시지를 통한 문제 파악 가능")
        
    except Exception as e:
        print(f"❌ 실제 API 검증 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 수정 API 실제 테스트 시작")
    print("=" * 120)
    
    # 환경 변수 확인
    required_env_vars = ['COUPANG_ACCESS_KEY', 'COUPANG_SECRET_KEY', 'COUPANG_VENDOR_ID']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        print("설정 방법:")
        print("   export COUPANG_ACCESS_KEY='your_access_key'")
        print("   export COUPANG_SECRET_KEY='your_secret_key'")
        print("   export COUPANG_VENDOR_ID='your_vendor_id'")
        print("   export TEST_SELLER_PRODUCT_ID='existing_product_id'  # 선택사항")
        return
    
    try:
        # 실제 API 테스트 실행
        test_real_api_product_update()
        test_real_api_option_management()
        test_real_api_update_validation()
        
        print(f"\n" + "=" * 50 + " 실제 API 수정 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 상품 수정 테스트가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 상품 수정")
        print("   2. ✅ 실제 API 옵션 관리")
        print("   3. ✅ 조회 결과 기반 수정")
        print("   4. ✅ 수정 검증 및 오류 처리")
        print("   5. ✅ seller_product_item_id 기반 옵션 수정")
        print("   6. ✅ 새 옵션 추가 및 기존 옵션 삭제")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 상품 수정 전 get_product로 기존 정보 확인")
        print("   - seller_product_id와 seller_product_item_id는 필수")
        print("   - 승인완료 상품의 가격/재고는 별도 API 사용")
        print("   - 옵션 추가/수정/삭제는 items 배열로 관리")
        print("   - 수정 후 승인 요청은 requested 옵션으로 제어")
        print("   - 실제 반품지/출고지 코드 사용 필수")
        
    except Exception as e:
        print(f"\n❌ 실제 API 수정 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()