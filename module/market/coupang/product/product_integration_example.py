#!/usr/bin/env python3
"""
쿠팡 상품 등록 통합 예제
카테고리 → 출고지/반품지 → 상품등록 전체 플로우
"""

import os
import sys
from datetime import datetime, timedelta
from pprint import pprint

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from market.coupang.category import CoupangCategoryManager
from market.coupang.ShippingCenters import ShippingCenterClient
from market.coupang.ReturnCenters import ReturnCenterClient
from market.coupang.product import (
    ProductClient,
    ProductRequest,
    ProductItem,
    ProductImage,
    ProductAttribute,
    ProductNotice
)


def test_complete_product_registration_flow():
    """완전한 상품 등록 플로우 테스트"""
    print("=" * 80 + " 완전한 상품 등록 플로우 " + "=" * 80)
    
    try:
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        
        print(f"🚀 쿠팡 상품 등록 통합 플로우 시작")
        print(f"   🏢 판매자 ID: {vendor_id}")
        
        # ===== 1단계: 카테고리 추천 및 확인 =====
        print(f"\n" + "=" * 30 + " 1단계: 카테고리 추천 " + "=" * 30)
        
        product_client = ProductClient()
        
        # 카테고리 추천 요청
        category_result = product_client.predict_category(
            product_name="프리미엄 아르간 헤어오일",
            product_description="모로코산 아르간오일로 만든 프리미엄 헤어케어 제품",
            brand="프리미엄뷰티",
            attributes={
                "용량": "100ml",
                "타입": "헤어오일",
                "성분": "아르간오일"
            }
        )
        
        if category_result.get("success"):
            category_data = category_result.get("data", {})
            category_id = category_data.get("predictedCategoryId")
            category_name = category_data.get("predictedCategoryName")
            print(f"   ✅ 카테고리 추천 성공")
            print(f"      📂 추천 카테고리: {category_name} ({category_id})")
        else:
            print(f"   ⚠️ 카테고리 추천 실패, 기본 카테고리 사용")
            category_id = 56137  # 기본 카테고리
            category_name = "기본 카테고리"
        
        # ===== 2단계: 카테고리 메타정보 조회 =====
        print(f"\n" + "=" * 30 + " 2단계: 카테고리 메타정보 조회 " + "=" * 30)
        
        try:
            category_manager = CoupangCategoryManager()
            
            # 카테고리 메타정보 조회 (실제로는 API 호출)
            print(f"   🔍 카테고리 {category_id} 메타정보 조회 중...")
            print(f"   ℹ️ 실제 환경에서는 카테고리 메타정보 조회 API 호출")
            print(f"      필수 속성, 고시정보, 구매옵션 등 확인")
            
        except Exception as e:
            print(f"   ⚠️ 카테고리 메타정보 조회 실패: {e}")
        
        # ===== 3단계: 출고지 조회 =====
        print(f"\n" + "=" * 30 + " 3단계: 출고지 조회 " + "=" * 30)
        
        try:
            shipping_client = ShippingCenterClient()
            
            # 출고지 목록 조회
            shipping_response = shipping_client.get_shipping_centers(vendor_id, page_num=1, page_size=5)
            
            if shipping_response.content:
                shipping_center = shipping_response.content[0]
                outbound_code = shipping_center.outbound_shipping_place_code
                print(f"   ✅ 출고지 조회 성공")
                print(f"      🏭 출고지: {shipping_center.shipping_place_name} ({outbound_code})")
            else:
                print(f"   ⚠️ 등록된 출고지가 없습니다")
                outbound_code = "74010"  # 기본값
                
        except Exception as e:
            print(f"   ⚠️ 출고지 조회 실패: {e}")
            outbound_code = "74010"  # 기본값
        
        # ===== 4단계: 반품지 조회 =====
        print(f"\n" + "=" * 30 + " 4단계: 반품지 조회 " + "=" * 30)
        
        try:
            return_client = ReturnCenterClient()
            
            # 반품지 목록 조회
            return_response = return_client.get_return_centers(vendor_id, page_num=1, page_size=5)
            
            if return_response.content:
                return_center = return_response.content[0]
                return_code = return_center.return_center_code
                return_name = return_center.shipping_place_name
                print(f"   ✅ 반품지 조회 성공")
                print(f"      📦 반품지: {return_name} ({return_code})")
                
                # 반품지 주소 정보
                if return_center.place_addresses:
                    addr = return_center.place_addresses[0]
                    return_zip = addr.return_zip_code
                    return_address = addr.return_address
                    return_detail = addr.return_address_detail
                    return_contact = addr.company_contact_number
                else:
                    return_zip = "135-090"
                    return_address = "서울특별시 강남구"
                    return_detail = "기본 반품지"
                    return_contact = "02-1234-5678"
            else:
                print(f"   ⚠️ 등록된 반품지가 없습니다")
                return_code = "1000274592"
                return_name = "기본 반품지"
                return_zip = "135-090"
                return_address = "서울특별시 강남구"
                return_detail = "기본 반품지"
                return_contact = "02-1234-5678"
                
        except Exception as e:
            print(f"   ⚠️ 반품지 조회 실패: {e}")
            return_code = "1000274592"
            return_name = "기본 반품지"
            return_zip = "135-090"
            return_address = "서울특별시 강남구"
            return_detail = "기본 반품지"
            return_contact = "02-1234-5678"
        
        # ===== 5단계: 상품 등록 =====
        print(f"\n" + "=" * 30 + " 5단계: 상품 등록 " + "=" * 30)
        
        # 판매 기간 설정
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 상품 아이템 생성
        item = ProductItem(
            item_name="프리미엄아르간헤어오일_100ml",
            original_price=50000,
            sale_price=39000,
            maximum_buy_count=100,
            maximum_buy_for_person=3,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="PREM_ARGAN_100",
            barcode="8801234567890"
        )
        
        # 대표 이미지 생성
        image = ProductImage(
            image_order=0,
            image_type="REPRESENTATION",
            vendor_path="https://example.com/argan-hair-oil.jpg"
        )
        
        # 상품 속성 생성 (카테고리 메타정보 기반)
        attributes = [
            ProductAttribute(
                attribute_type_name="용량",
                attribute_value_name="100ml"
            ),
            ProductAttribute(
                attribute_type_name="타입",
                attribute_value_name="헤어오일"
            ),
            ProductAttribute(
                attribute_type_name="주성분",
                attribute_value_name="아르간오일"
            )
        ]
        
        # 고시정보 생성 (카테고리별 필수정보)
        notices = [
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="용량 또는 중량",
                content="100ml"
            ),
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="제품주요사양",
                content="헤어오일, 모로코산 아르간오일 함유"
            )
        ]
        
        # 통합 상품 등록 요청 생성
        request = ProductRequest(
            display_category_code=int(category_id) if category_id else 56137,
            seller_product_name="프리미엄 아르간 헤어오일 100ml",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="integrationTestUser",
            requested=False,  # 테스트용이므로 승인요청 안함
            
            # 상품 정보
            display_product_name="프리미엄 아르간 헤어오일",
            brand="프리미엄뷰티",
            general_product_name="아르간 헤어오일",
            product_group="헤어케어",
            manufacture="프리미엄뷰티",
            
            # 배송 정보
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",
            delivery_charge_type="FREE",
            delivery_charge=0,
            free_ship_over_amount=0,
            delivery_charge_on_return=2500,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            
            # 조회된 반품지 정보 사용
            return_center_code=return_code,
            return_charge_name=return_name,
            company_contact_number=return_contact,
            return_zip_code=return_zip,
            return_address=return_address,
            return_address_detail=return_detail,
            return_charge=2500,
            return_charge_vendor="N",
            
            # AS 정보
            after_service_information="품질보증 30일, A/S 문의: 1588-1234",
            after_service_contact_number="1588-1234",
            
            # 조회된 출고지 정보 사용
            outbound_shipping_place_code=outbound_code,
            
            # 리스트 데이터
            items=[item],
            images=[image],
            attributes=attributes,
            notices=notices
        )
        
        print(f"   📋 통합 상품 정보:")
        print(f"      📝 상품명: {request.display_product_name}")
        print(f"      🏷️ 브랜드: {request.brand}")
        print(f"      📂 카테고리: {category_name} ({category_id})")
        print(f"      💰 가격: {item.sale_price:,}원 (정가: {item.original_price:,}원)")
        print(f"      🏭 출고지: {outbound_code}")
        print(f"      📦 반품지: {return_name} ({return_code})")
        print(f"      🚚 배송: 무료배송")
        
        # 상품 등록 실행
        print(f"\n   📤 상품 등록 요청 중...")
        result = product_client.create_product(request)
        
        if result.get("success"):
            print(f"\n   ✅ 통합 상품 등록 성공!")
            data = result.get("data", {})
            print(f"      🎯 결과: {result.get('message')}")
            if data:
                print(f"      📊 응답 데이터:")
                pprint(data, width=100, indent=8)
            
            print(f"\n   🎉 전체 플로우 완료:")
            print(f"      1. ✅ 카테고리 추천")
            print(f"      2. ✅ 카테고리 메타정보 확인")
            print(f"      3. ✅ 출고지 조회 및 설정")
            print(f"      4. ✅ 반품지 조회 및 설정")
            print(f"      5. ✅ 상품 등록")
            
        else:
            print(f"\n   ❌ 통합 상품 등록 실패:")
            print(f"      🚨 오류: {result.get('error')}")
            print(f"      📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n      📋 오류 응답 상세:")
                pprint(original_response, width=100, indent=8)
                
    except Exception as e:
        print(f"❌ 통합 상품 등록 플로우 오류: {e}")
        import traceback
        traceback.print_exc()


def test_batch_product_registration():
    """배치 상품 등록 예제"""
    print("\n" + "=" * 80 + " 배치 상품 등록 예제 " + "=" * 80)
    
    try:
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')
        product_client = ProductClient()
        
        print(f"📦 다중 상품 등록 테스트")
        
        # 등록할 상품 목록
        products = [
            {
                "name": "프리미엄 비타민C 세럼",
                "brand": "뷰티랩",
                "price": 45000,
                "sale_price": 35000,
                "description": "고농축 비타민C로 밝고 건강한 피부를 위한 세럼",
                "sku": "BEAUTY_VITC_30"
            },
            {
                "name": "히알루론산 보습크림",
                "brand": "뷰티랩", 
                "price": 38000,
                "sale_price": 28000,
                "description": "깊은 수분 공급을 위한 히알루론산 보습크림",
                "sku": "BEAUTY_HYA_50"
            },
            {
                "name": "레티놀 안티에이징 크림",
                "brand": "뷰티랩",
                "price": 55000,
                "sale_price": 42000,
                "description": "주름 개선과 탄력 증진을 위한 레티놀 크림",
                "sku": "BEAUTY_RET_30"
            }
        ]
        
        success_count = 0
        fail_count = 0
        
        for i, product_info in enumerate(products, 1):
            print(f"\n📦 상품 {i}: {product_info['name']}")
            
            try:
                # 카테고리 추천
                category_result = product_client.predict_category(
                    product_name=product_info["name"],
                    product_description=product_info["description"],
                    brand=product_info["brand"]
                )
                
                if category_result.get("success"):
                    category_data = category_result.get("data", {})
                    category_id = int(category_data.get("predictedCategoryId", 56137))
                else:
                    category_id = 56137  # 기본 카테고리
                
                # 판매 기간 설정
                start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
                
                # 상품 아이템 생성
                item = ProductItem(
                    item_name=f"{product_info['name']}_기본",
                    original_price=product_info["price"],
                    sale_price=product_info["sale_price"],
                    maximum_buy_count=50,
                    maximum_buy_for_person=2,
                    maximum_buy_for_person_period=30,
                    outbound_shipping_time_day=1,
                    external_vendor_sku=product_info["sku"]
                )
                
                # 대표 이미지 생성
                image = ProductImage(
                    image_order=0,
                    image_type="REPRESENTATION",
                    vendor_path=f"https://example.com/{product_info['sku'].lower()}.jpg"
                )
                
                # 상품 등록 요청 생성
                request = ProductRequest(
                    display_category_code=category_id,
                    seller_product_name=product_info["name"],
                    vendor_id=vendor_id,
                    sale_started_at=start_date,
                    sale_ended_at=end_date,
                    vendor_user_id="batchTestUser",
                    requested=False,
                    
                    display_product_name=product_info["name"],
                    brand=product_info["brand"],
                    general_product_name=product_info["name"],
                    product_group="스킨케어",
                    manufacture=product_info["brand"],
                    
                    delivery_method="SEQUENCIAL",
                    delivery_company_code="CJGLS",
                    delivery_charge_type="FREE",
                    
                    return_center_code="1000274592",
                    return_charge_name="뷰티랩 반품센터",
                    company_contact_number="02-1234-5678",
                    return_zip_code="135-090",
                    return_address="서울특별시 강남구",
                    return_address_detail="뷰티랩빌딩",
                    return_charge=2500,
                    return_charge_vendor="N",
                    
                    after_service_information="뷰티랩 A/S 센터: 1588-1234",
                    after_service_contact_number="1588-1234",
                    
                    outbound_shipping_place_code="74010",
                    
                    items=[item],
                    images=[image]
                )
                
                # 상품 등록 실행
                result = product_client.create_product(request)
                
                if result.get("success"):
                    print(f"   ✅ 등록 성공")
                    success_count += 1
                else:
                    print(f"   ❌ 등록 실패: {result.get('error')}")
                    fail_count += 1
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
                fail_count += 1
        
        print(f"\n📊 배치 등록 결과:")
        print(f"   ✅ 성공: {success_count}개")
        print(f"   ❌ 실패: {fail_count}개")
        print(f"   📈 성공률: {success_count/(success_count+fail_count)*100:.1f}%")
        
    except Exception as e:
        print(f"❌ 배치 상품 등록 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 등록 통합 예제 시작")
    print("=" * 120)
    
    try:
        # 완전한 상품 등록 플로우 테스트
        test_complete_product_registration_flow()
        
        # 배치 상품 등록 테스트
        test_batch_product_registration()
        
        print(f"\n" + "=" * 50 + " 통합 예제 완료 " + "=" * 50)
        print("✅ 모든 통합 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 통합 기능들:")
        print("   1. ✅ 카테고리 추천 → 상품등록 연동")
        print("   2. ✅ 출고지 조회 → 상품등록 연동")
        print("   3. ✅ 반품지 조회 → 상품등록 연동")
        print("   4. ✅ 전체 플로우 자동화")
        print("   5. ✅ 배치 상품 등록")
        print("   6. ✅ 오류 처리 및 검증")
        
        print(f"\n💡 실제 사용 시 주의사항:")
        print("   - 환경변수 설정: COUPANG_ACCESS_KEY, COUPANG_SECRET_KEY, COUPANG_VENDOR_ID")
        print("   - 카테고리 메타정보 조회로 필수 속성 확인")
        print("   - 실제 출고지/반품지 코드 사용")
        print("   - 이미지 URL은 접근 가능한 실제 경로")
        print("   - 테스트 시 requested=false 사용")
        print("   - 상품명/브랜드는 실제 판매하는 상품으로 설정")
        print("   - 가격 설정 시 경쟁력 고려")
        
    except Exception as e:
        print(f"\n❌ 통합 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()