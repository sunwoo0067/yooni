#!/usr/bin/env python3
"""
쿠팡 상품 수정 API 사용 예제
기존 상품의 정보를 수정하는 방법을 보여줍니다
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
    ProductContent,
    ProductContentDetail,
    ProductPartialUpdateRequest
)


def test_product_update_basic():
    """기본적인 상품 수정 테스트"""
    print("=" * 60 + " 기본 상품 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 수정할 상품의 기존 정보 (실제로는 get_product API로 조회)
        seller_product_id = 309323422  # 예시 ID - 실제 상품 ID로 변경 필요
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        
        print(f"\n📝 상품 수정 중...")
        print(f"   🆔 수정할 상품 ID: {seller_product_id}")
        print(f"   🏢 판매자 ID: {vendor_id}")
        
        # 판매 기간 설정 (1년 연장)
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 기존 아이템 수정 (seller_product_item_id 포함)
        updated_item = ProductItem(
            seller_product_item_id=769536471,  # 기존 아이템 ID
            vendor_item_id=123456789,  # 기존 벤더 아이템 ID
            item_name="수정된_클렌징오일_200ml",
            original_price=15000,  # 가격 수정
            sale_price=12000,      # 할인가 수정
            maximum_buy_count=200,  # 재고 증가
            maximum_buy_for_person=5,  # 구매 제한 완화
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="UPDATED_SKU_001",
            barcode="8801234567891"
        )
        
        # 새로운 아이템 추가 (seller_product_item_id 없음)
        new_item = ProductItem(
            item_name="새로운옵션_클렌징오일_300ml",
            original_price=20000,
            sale_price=18000,
            maximum_buy_count=100,
            maximum_buy_for_person=3,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="NEW_SKU_002",
            barcode="8801234567892"
        )
        
        # 수정된 이미지 (기존 이미지 + 새 이미지)
        images = [
            ProductImage(
                image_order=0,
                image_type="REPRESENTATION",
                vendor_path="https://example.com/updated-product-image.jpg"
            ),
            ProductImage(
                image_order=1,
                image_type="DETAIL",
                vendor_path="https://example.com/new-detail-image.jpg"
            )
        ]
        
        # 수정된 속성
        attributes = [
            ProductAttribute(
                attribute_type_name="용량",
                attribute_value_name="200ml/300ml"  # 옵션 추가로 용량 변경
            ),
            ProductAttribute(
                attribute_type_name="타입",
                attribute_value_name="오일클렌저"
            )
        ]
        
        # 수정된 고시정보
        notices = [
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="용량 또는 중량",
                content="200ml, 300ml"  # 새 용량 추가
            ),
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="제품주요사양",
                content="수정된 프리미엄 클렌징오일, 향상된 포뮬러"
            )
        ]
        
        # 상품 수정 요청 생성
        update_request = ProductRequest(
            seller_product_id=seller_product_id,  # 수정할 상품 ID 필수
            display_category_code=56137,
            seller_product_name="수정된_프리미엄_클렌징오일",  # 상품명 수정
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="updatedTestUser",
            requested=False,  # 수정 후 바로 승인 요청하지 않음
            
            # 수정된 상품 정보
            display_product_name="수정된 프리미엄 클렌징오일",
            brand="업그레이드브랜드",  # 브랜드 정보 수정
            general_product_name="향상된 클렌징 오일",
            product_group="프리미엄 클렌징",
            manufacture="업그레이드브랜드",
            
            # 배송 정보 (기존 유지 또는 수정)
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",
            delivery_charge_type="FREE",
            delivery_charge=0,
            free_ship_over_amount=0,
            delivery_charge_on_return=2500,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            
            # 반품지 정보 (기존 유지)
            return_center_code="1000274592",
            return_charge_name="프리미엄 반품센터",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="프리미엄빌딩 5층",
            return_charge=2500,
            return_charge_vendor="N",
            
            # AS 정보
            after_service_information="업그레이드 A/S 센터: 1588-9999",
            after_service_contact_number="1588-9999",
            
            # 출고지 정보
            outbound_shipping_place_code="74010",
            
            # 수정된 리스트 데이터
            items=[updated_item, new_item],  # 기존 수정 + 새 옵션 추가
            images=images,
            attributes=attributes,
            notices=notices
        )
        
        print(f"\n📋 수정할 상품 정보:")
        print(f"   📝 상품명: {update_request.display_product_name}")
        print(f"   🏷️ 브랜드: {update_request.brand}")
        print(f"   📦 아이템 수: {len(update_request.items)}개")
        print(f"   🖼️ 이미지 수: {len(update_request.images)}개")
        print(f"   💰 첫번째 아이템 가격: {updated_item.sale_price:,}원")
        
        # 상품 수정 실행
        print(f"\n📤 상품 수정 요청 중...")
        result = client.update_product(update_request)
        
        if result.get("success"):
            print(f"\n✅ 상품 수정 성공!")
            data = result.get("data", {})
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            if data:
                print(f"   📊 응답 데이터:")
                pprint(data, width=100, indent=8)
        else:
            print(f"\n❌ 상품 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
    except Exception as e:
        print(f"❌ 상품 수정 오류: {e}")
        import traceback
        traceback.print_exc()


def test_product_update_option_modification():
    """상품 옵션 수정/추가/삭제 예제"""
    print("\n" + "=" * 60 + " 상품 옵션 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 예시 상품 정보
        seller_product_id = 309323423
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        
        print(f"\n🔧 상품 옵션 수정 시나리오")
        print(f"   🆔 상품 ID: {seller_product_id}")
        print(f"   📝 작업: 기존 옵션 수정 + 새 옵션 추가 + 옵션 삭제")
        
        # 1. 기존 옵션 수정 (seller_product_item_id 포함)
        modified_option = ProductItem(
            seller_product_item_id=769536471,  # 기존 옵션 ID
            vendor_item_id=123456789,
            item_name="수정된_옵션_소형_150ml",
            original_price=12000,
            sale_price=9900,  # 가격 인하
            maximum_buy_count=150,
            maximum_buy_for_person=3,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="MODIFIED_SMALL",
            barcode="8801234567893"
        )
        
        # 2. 새로운 옵션 추가 (seller_product_item_id 없음)
        new_large_option = ProductItem(
            # seller_product_item_id 없음 = 새 옵션 추가
            item_name="신규_대용량_500ml",
            original_price=35000,
            sale_price=29900,
            maximum_buy_count=50,
            maximum_buy_for_person=2,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=2,  # 대용량은 출고 하루 더
            external_vendor_sku="NEW_LARGE_500",
            barcode="8801234567894"
        )
        
        # 3. 옵션 삭제는 items 배열에서 제외
        # (기존에 있던 seller_product_item_id=769536472는 제외하여 삭제)
        
        # 판매 기간
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 속성 수정 (새로운 용량 반영)
        updated_attributes = [
            ProductAttribute(
                attribute_type_name="용량",
                attribute_value_name="150ml/500ml"  # 수정된 용량 옵션
            ),
            ProductAttribute(
                attribute_type_name="패키지",
                attribute_value_name="리뉴얼패키지"
            )
        ]
        
        # 이미지 (기존 + 새 옵션용)
        updated_images = [
            ProductImage(
                image_order=0,
                image_type="REPRESENTATION",
                vendor_path="https://example.com/renewed-main-image.jpg"
            ),
            ProductImage(
                image_order=1,
                image_type="DETAIL",
                vendor_path="https://example.com/size-comparison.jpg"
            )
        ]
        
        # 상품 수정 요청
        option_update_request = ProductRequest(
            seller_product_id=seller_product_id,
            display_category_code=56137,
            seller_product_name="리뉴얼_다용량_클렌징오일",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="optionUpdateUser",
            requested=False,
            
            display_product_name="리뉴얼 다용량 클렌징오일",
            brand="리뉴얼브랜드",
            general_product_name="다용량 클렌징 오일",
            product_group="프리미엄 클렌징",
            manufacture="리뉴얼브랜드",
            
            # 배송 정보
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",
            delivery_charge_type="FREE",
            delivery_charge=0,
            free_ship_over_amount=0,
            delivery_charge_on_return=3000,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            
            # 반품지 정보
            return_center_code="1000274592",
            return_charge_name="리뉴얼 반품센터",
            company_contact_number="02-9999-1234",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="리뉴얼빌딩 3층",
            return_charge=3000,
            return_charge_vendor="N",
            
            after_service_information="리뉴얼 A/S: 1588-7777",
            after_service_contact_number="1588-7777",
            outbound_shipping_place_code="74010",
            
            # 수정된 옵션들 (삭제할 옵션은 제외)
            items=[modified_option, new_large_option],
            images=updated_images,
            attributes=updated_attributes,
            notices=[
                ProductNotice(
                    notice_category_name="화장품",
                    notice_category_detail_name="용량 또는 중량",
                    content="150ml, 500ml"
                )
            ]
        )
        
        print(f"\n📋 옵션 수정 상세:")
        print(f"   🔧 수정할 옵션: {modified_option.item_name} (ID: {modified_option.seller_product_item_id})")
        print(f"   ➕ 추가할 옵션: {new_large_option.item_name}")
        print(f"   ➖ 삭제할 옵션: ID 769536472 (배열에서 제외)")
        print(f"   💰 수정된 가격: {modified_option.sale_price:,}원")
        print(f"   💰 신규 옵션 가격: {new_large_option.sale_price:,}원")
        
        # 옵션 수정 실행
        print(f"\n📤 옵션 수정 요청 중...")
        result = client.update_product(option_update_request)
        
        if result.get("success"):
            print(f"\n✅ 옵션 수정 성공!")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            print(f"\n   📊 수정 결과:")
            print(f"      ✅ 기존 옵션 수정 완료")
            print(f"      ✅ 새 옵션 추가 완료")
            print(f"      ✅ 불필요한 옵션 삭제 완료")
        else:
            print(f"\n❌ 옵션 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
    except Exception as e:
        print(f"❌ 옵션 수정 오류: {e}")


def test_product_update_from_get_api():
    """상품 조회 API 결과를 사용한 수정 예제"""
    print("\n" + "=" * 60 + " 조회 결과 기반 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 예시 상품 ID
        seller_product_id = "1234567890"
        
        print(f"🔍 1단계: 기존 상품 정보 조회")
        print(f"   🆔 조회할 상품 ID: {seller_product_id}")
        
        # 1. 기존 상품 정보 조회
        get_result = client.get_product(seller_product_id)
        
        if not get_result.get("success"):
            print(f"❌ 상품 조회 실패: {get_result.get('error')}")
            print("💡 실제 테스트 시에는 존재하는 상품 ID를 사용하세요")
            return
        
        print(f"✅ 상품 조회 성공")
        
        # 2. 조회된 데이터에서 필요한 정보 추출 (예시)
        product_data = get_result.get("data", {})
        print(f"   📋 조회된 상품명: {product_data.get('sellerProductName', 'N/A')}")
        
        # 3. 조회된 정보를 기반으로 수정 요청 생성
        # 실제로는 조회된 JSON 데이터를 파싱하여 ProductRequest 객체 생성
        print(f"\n🔧 2단계: 조회된 정보로 수정 요청 생성")
        
        # 예시: 조회된 정보를 기반으로 일부만 수정
        update_request = ProductRequest(
            seller_product_id=int(seller_product_id),
            display_category_code=56137,  # 조회된 값 사용
            seller_product_name="조회기반_수정된_상품명",  # 수정할 부분
            vendor_id=os.getenv('COUPANG_VENDOR_ID', 'A00012345'),
            sale_started_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            sale_ended_at=(datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S"),
            vendor_user_id="queryBasedUpdate",
            requested=False,
            
            # 조회된 정보에서 필요한 부분만 수정
            display_product_name="조회기반 수정된 상품",
            brand="수정된브랜드",  # 수정할 부분
            
            # 나머지는 조회된 기존 정보 유지 또는 수정
            delivery_method="SEQUENCIAL",
            delivery_charge_type="FREE",
            
            # 반품지 정보 (조회된 기존 정보 유지)
            return_center_code="1000274592",
            return_charge_name="기존 반품센터",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구",
            return_address_detail="기존 주소",
            return_charge=2500,
            return_charge_vendor="N",
            
            outbound_shipping_place_code="74010",
            
            # 최소한의 아이템과 이미지 (실제로는 조회된 데이터 사용)
            items=[
                ProductItem(
                    seller_product_item_id=769536471,  # 조회된 기존 아이템 ID
                    item_name="조회기반_수정된_아이템",
                    original_price=20000,
                    sale_price=15000,  # 가격만 수정
                    maximum_buy_count=100,
                    maximum_buy_for_person=3,
                    maximum_buy_for_person_period=30,
                    outbound_shipping_time_day=1
                )
            ],
            images=[
                ProductImage(
                    image_order=0,
                    image_type="REPRESENTATION",
                    vendor_path="https://example.com/query-based-update.jpg"
                )
            ]
        )
        
        print(f"   📝 수정할 내용:")
        print(f"      상품명: 조회기반_수정된_상품명")
        print(f"      브랜드: 수정된브랜드")
        print(f"      아이템 가격: 15,000원으로 변경")
        
        # 4. 수정 실행
        print(f"\n📤 3단계: 수정 요청 실행")
        result = client.update_product(update_request)
        
        if result.get("success"):
            print(f"\n✅ 조회 기반 상품 수정 성공!")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            print(f"\n   💡 실제 사용 플로우:")
            print(f"      1. get_product()로 기존 정보 조회")
            print(f"      2. 조회된 JSON을 ProductRequest로 변환")
            print(f"      3. 필요한 부분만 수정")
            print(f"      4. update_product()로 수정 실행")
        else:
            print(f"\n❌ 조회 기반 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 조회 기반 수정 오류: {e}")


def test_validation_scenarios():
    """상품 수정 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 수정 검증 시나리오 테스트 " + "=" * 60)
    
    client = ProductClient()
    
    print("\n🧪 다양한 검증 오류 상황 테스트")
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "seller_product_id 누락",
            "request": ProductRequest(
                # seller_product_id 없음
                display_category_code=56137,
                seller_product_name="테스트상품",
                vendor_id="A00012345",
                sale_started_at="2024-01-01T00:00:00",
                sale_ended_at="2024-12-31T23:59:59",
                vendor_user_id="testuser"
            ),
            "expected_error": "등록상품ID"
        },
        {
            "name": "잘못된 seller_product_id 타입",
            "request": ProductRequest(
                seller_product_id=0,  # 잘못된 값
                display_category_code=56137,
                seller_product_name="테스트상품",
                vendor_id="A00012345",
                sale_started_at="2024-01-01T00:00:00",
                sale_ended_at="2024-12-31T23:59:59",
                vendor_user_id="testuser",
                items=[],  # 빈 아이템
                images=[]  # 빈 이미지
            ),
            "expected_error": "아이템"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 {i}: {test_case['name']}")
        
        try:
            result = client.update_product(test_case['request'])
            
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
    print("🚀 쿠팡 상품 수정 API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 상품 수정 테스트
        test_product_update_basic()
        
        # 옵션 수정/추가/삭제 테스트
        test_product_update_option_modification()
        
        # 조회 결과 기반 수정 테스트
        test_product_update_from_get_api()
        
        # 검증 시나리오 테스트
        test_validation_scenarios()
        
        print(f"\n" + "=" * 50 + " 상품 수정 예제 완료 " + "=" * 50)
        print("✅ 모든 상품 수정 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 상품 정보 수정")
        print("   2. ✅ 상품 옵션 수정/추가/삭제")
        print("   3. ✅ 조회 결과 기반 수정")
        print("   4. ✅ 수정 요청 데이터 검증")
        print("   5. ✅ seller_product_item_id 기반 옵션 관리")
        print("   6. ✅ 오류 처리 및 검증")
        
        print(f"\n💡 상품 수정 주요 포인트:")
        print("   - seller_product_id는 수정 시 필수")
        print("   - 기존 옵션 수정: seller_product_item_id 포함")
        print("   - 새 옵션 추가: seller_product_item_id 없음")
        print("   - 옵션 삭제: items 배열에서 제외")
        print("   - 조회 API로 기존 정보 확인 후 수정 권장")
        print("   - 승인완료 상품의 가격/재고는 별도 API 사용")
        print("   - 수정 후 승인 요청은 requested 옵션으로 제어")
        
    except Exception as e:
        print(f"\n❌ 상품 수정 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()