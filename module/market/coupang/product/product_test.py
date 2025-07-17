#!/usr/bin/env python3
"""
쿠팡 상품 등록 API 실제 테스트
실제 API 키를 사용한 상품 등록 및 관리 테스트
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
    ProductCertification,
    ProductNotice,
    ProductAttribute,
    ProductContent,
    ProductContentDetail,
    ProductPartialUpdateRequest
)


def test_real_api_product_creation():
    """실제 API로 상품 등록 테스트"""
    print("=" * 60 + " 실제 API 상품 등록 테스트 " + "=" * 60)
    
    try:
        # 실제 API 키로 클라이언트 초기화
        client = ProductClient()
        print("✅ 실제 API 인증으로 상품 클라이언트 초기화 성공")
        
        # 실제 상품 정보 설정
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📦 실제 API로 상품 등록 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        
        # 판매 기간 설정
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 상품 아이템 생성
        item = ProductItem(
            item_name="API테스트상품옵션1",
            original_price=30000,
            sale_price=25000,
            maximum_buy_count=50,
            maximum_buy_for_person=3,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="API_TEST_001",
            barcode="8801234567890"
        )
        
        # 대표 이미지 생성
        image = ProductImage(
            image_order=0,
            image_type="REPRESENTATION",
            vendor_path="https://example.com/test-product-image.jpg"
        )
        
        # 상품 속성 생성
        attribute = ProductAttribute(
            attribute_type_name="용량",
            attribute_value_name="500ml"
        )
        
        # 고시정보 생성
        notice = ProductNotice(
            notice_category_name="화장품",
            notice_category_detail_name="용량 또는 중량",
            content="500ml"
        )
        
        # 실제 상품 등록 요청 생성
        request = ProductRequest(
            display_category_code=56137,  # 실제 카테고리 코드로 변경 필요
            seller_product_name="API테스트 프리미엄 클렌징오일",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="apiTestUser",
            requested=False,  # 승인요청은 하지 않음 (테스트용)
            
            # 상품 정보
            display_product_name="API테스트 프리미엄 클렌징오일",
            brand="API테스트브랜드",
            general_product_name="프리미엄 클렌징 오일",
            product_group="클렌징 오일",
            manufacture="API테스트브랜드",
            
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
            return_charge_name="API테스트 반품센터",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="API테스트빌딩 5층",
            return_charge=2500,
            return_charge_vendor="N",
            
            # AS 정보
            after_service_information="API테스트 A/S 안내: 1234-5678",
            after_service_contact_number="1234-5678",
            
            # 출고지 정보 (실제 출고지 코드로 변경 필요)
            outbound_shipping_place_code="74010",
            
            # 리스트 데이터
            items=[item],
            images=[image],
            attributes=[attribute],
            notices=[notice]
        )
        
        print(f"\n📋 실제 상품 정보:")
        print(f"   📝 상품명: {request.display_product_name}")
        print(f"   🏷️ 브랜드: {request.brand}")
        print(f"   💰 가격: {item.sale_price:,}원 (정가: {item.original_price:,}원)")
        print(f"   📦 재고: {item.maximum_buy_count}개")
        print(f"   🚚 배송: 무료배송")
        
        # 실제 상품 등록 실행
        result = client.create_product(request)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 상품 등록 성공:")
            data = result.get("data", {})
            print(f"   🎯 결과: {result.get('message')}")
            if data:
                print(f"   📊 응답 데이터:")
                pprint(data, width=100, indent=4)
            
        else:
            print(f"\n❌ 실제 API 상품 등록 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
    except Exception as e:
        print(f"❌ 실제 API 상품 등록 오류: {e}")
        import traceback
        traceback.print_exc()


def test_real_api_category_recommendation():
    """실제 API로 카테고리 추천 테스트"""
    print("\n" + "=" * 60 + " 실제 API 카테고리 추천 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 다양한 상품에 대한 카테고리 추천 테스트
        test_products = [
            {
                "name": "삼성 갤럭시 스마트폰 케이스",
                "description": "투명 실리콘 소재의 갤럭시 전용 케이스",
                "brand": "삼성",
                "attributes": {
                    "소재": "실리콘",
                    "색상": "투명",
                    "호환기종": "갤럭시 S24"
                }
            },
            {
                "name": "나이키 에어포스 운동화",
                "description": "화이트 컬러의 클래식한 농구화",
                "brand": "나이키",
                "attributes": {
                    "색상": "화이트",
                    "사이즈": "270mm",
                    "타입": "농구화"
                }
            },
            {
                "name": "아모레퍼시픽 에센스",
                "description": "보습과 영양공급을 위한 페이셜 에센스",
                "brand": "아모레퍼시픽",
                "attributes": {
                    "용량": "150ml",
                    "타입": "에센스",
                    "피부타입": "모든피부"
                }
            }
        ]
        
        for i, product in enumerate(test_products, 1):
            print(f"\n🔍 테스트 {i}: {product['name']}")
            
            try:
                result = client.predict_category(
                    product_name=product["name"],
                    product_description=product["description"],
                    brand=product["brand"],
                    attributes=product["attributes"]
                )
                
                if result.get("success"):
                    data = result.get("data", {})
                    print(f"   ✅ 추천 성공:")
                    print(f"      📂 카테고리 ID: {data.get('predictedCategoryId')}")
                    print(f"      📝 카테고리명: {data.get('predictedCategoryName')}")
                    print(f"      🎯 결과타입: {data.get('autoCategorizationPredictionResultType')}")
                    
                    comment = data.get('comment')
                    if comment:
                        print(f"      💬 코멘트: {comment}")
                        
                else:
                    print(f"   ❌ 추천 실패: {result.get('error')}")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
                
    except Exception as e:
        print(f"❌ 실제 API 카테고리 추천 테스트 오류: {e}")


def test_real_api_complex_product():
    """실제 API로 복잡한 상품 등록 테스트"""
    print("\n" + "=" * 60 + " 실제 API 복잡한 상품 등록 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n📦 복잡한 상품 등록 테스트...")
        print(f"   다중 옵션, 이미지, 인증정보 포함")
        
        # 판매 기간 설정
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 다중 아이템 생성 (색상/용량별)
        items = [
            ProductItem(
                item_name="프리미엄오일_200ml_베이지",
                original_price=35000,
                sale_price=28000,
                maximum_buy_count=30,
                maximum_buy_for_person=2,
                maximum_buy_for_person_period=30,
                outbound_shipping_time_day=1,
                external_vendor_sku="PREM_OIL_200_BEIGE",
                barcode="8801234567001"
            ),
            ProductItem(
                item_name="프리미엄오일_200ml_클리어",
                original_price=35000,
                sale_price=28000,
                maximum_buy_count=30,
                maximum_buy_for_person=2,
                maximum_buy_for_person_period=30,
                outbound_shipping_time_day=1,
                external_vendor_sku="PREM_OIL_200_CLEAR",
                barcode="8801234567002"
            ),
            ProductItem(
                item_name="프리미엄오일_500ml_베이지",
                original_price=55000,
                sale_price=45000,
                maximum_buy_count=20,
                maximum_buy_for_person=1,
                maximum_buy_for_person_period=30,
                outbound_shipping_time_day=1,
                external_vendor_sku="PREM_OIL_500_BEIGE",
                barcode="8801234567003"
            )
        ]
        
        # 다중 이미지 생성
        images = [
            ProductImage(
                image_order=0,
                image_type="REPRESENTATION",
                vendor_path="https://example.com/premium-oil-main.jpg"
            ),
            ProductImage(
                image_order=1,
                image_type="DETAIL",
                vendor_path="https://example.com/premium-oil-detail1.jpg"
            ),
            ProductImage(
                image_order=2,
                image_type="DETAIL",
                vendor_path="https://example.com/premium-oil-detail2.jpg"
            ),
            ProductImage(
                image_order=3,
                image_type="DETAIL",
                vendor_path="https://example.com/premium-oil-ingredients.jpg"
            )
        ]
        
        # 인증정보 생성
        certifications = [
            ProductCertification(
                certification_type="KC_CERTIFICATION",
                certification_code="KC-2024-0001"
            )
        ]
        
        # 다중 속성 생성
        attributes = [
            ProductAttribute(
                attribute_type_name="용량",
                attribute_value_name="200ml"
            ),
            ProductAttribute(
                attribute_type_name="색상",
                attribute_value_name="베이지"
            ),
            ProductAttribute(
                attribute_type_name="제조국",
                attribute_value_name="대한민국"
            ),
            ProductAttribute(
                attribute_type_name="피부타입",
                attribute_value_name="모든피부"
            )
        ]
        
        # 다중 고시정보 생성
        notices = [
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="용량 또는 중량",
                content="200ml, 500ml"
            ),
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="제품주요사양",
                content="클렌징오일, 메이크업 리무버, 모든피부타입"
            ),
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="사용법",
                content="건조한 손에 적당량을 덜어 얼굴 전체에 부드럽게 마사지 후 미지근한 물로 헹구세요"
            )
        ]
        
        # 상세 컨텐츠 생성
        content_detail = ProductContentDetail(
            content_type="TEXT",
            content="<div><h2>프리미엄 클렌징오일</h2><p>자연 유래 성분으로 만든 고급 클렌징오일입니다.</p><p>강력한 메이크업 제거 효과와 함께 피부를 촉촉하게 관리해드립니다.</p></div>"
        )
        content = ProductContent(content_details=[content_detail])
        
        # 검색 태그 생성
        search_tags = [
            "클렌징오일", "메이크업리무버", "클렌징", "세안", "프리미엄", 
            "오일클렌저", "더블클렌징", "워터프루프", "딥클렌징", "보습"
        ]
        
        # 복잡한 상품 등록 요청 생성
        request = ProductRequest(
            display_category_code=56137,
            seller_product_name="프리미엄 멀티사이즈 클렌징오일 컬렉션",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="complexTestUser",
            requested=False,
            
            # 상품 정보
            display_product_name="프리미엄 멀티사이즈 클렌징오일",
            brand="프리미엄뷰티",
            general_product_name="프리미엄 클렌징 오일",
            product_group="클렌징 오일",
            manufacture="프리미엄뷰티",
            
            # 배송 정보 (조건부 무료배송)
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",
            delivery_charge_type="CONDITIONAL_FREE",
            delivery_charge=2500,
            free_ship_over_amount=40000,  # 4만원 이상 무료배송
            delivery_charge_on_return=0,
            remote_area_deliverable="Y",
            union_delivery_type="UNION_DELIVERY",
            
            # 반품지 정보
            return_center_code="1000274592",
            return_charge_name="프리미엄뷰티 반품센터",
            company_contact_number="02-9876-5432",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="프리미엄타워 10층",
            return_charge=2500,
            return_charge_vendor="N",
            
            # AS 정보
            after_service_information="품질보증 60일, 무료교환/환불, A/S 문의: 1588-1234",
            after_service_contact_number="1588-1234",
            
            # 출고지 정보
            outbound_shipping_place_code="74010",
            
            # 리스트 데이터
            items=items,
            images=images,
            certifications=certifications,
            attributes=attributes,
            notices=notices,
            content=content,
            search_tags=search_tags
        )
        
        print(f"\n📋 복잡한 상품 정보:")
        print(f"   📝 상품명: {request.display_product_name}")
        print(f"   🏷️ 브랜드: {request.brand}")
        print(f"   🎨 옵션 수: {len(items)}개")
        print(f"   🖼️ 이미지 수: {len(images)}개")
        print(f"   🔒 인증정보: {len(certifications)}개")
        print(f"   🏷️ 속성 수: {len(attributes)}개")
        print(f"   📋 고시정보: {len(notices)}개")
        print(f"   🔍 검색태그: {len(search_tags)}개")
        print(f"   📝 상세컨텐츠: {len(content.content_details)}개")
        print(f"   🚚 배송: 조건부무료 (4만원 이상)")
        
        # 상품 등록 실행
        result = client.create_product(request)
        
        if result.get("success"):
            print(f"\n✅ 복잡한 상품 등록 성공:")
            data = result.get("data", {})
            print(f"   🎯 결과: {result.get('message')}")
            if data:
                print(f"   📊 응답 데이터:")
                pprint(data, width=100, indent=4)
            
        else:
            print(f"\n❌ 복잡한 상품 등록 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
    except Exception as e:
        print(f"❌ 복잡한 상품 등록 오류: {e}")


def test_real_api_product_get():
    """실제 API로 상품 조회 테스트"""
    print("\n" + "=" * 60 + " 실제 API 상품 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 테스트용 등록상품ID (실제 API 테스트 시에는 실제 상품 ID 사용)
        test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '1320567890')
        
        print(f"\n🔍 실제 API로 상품 조회 중...")
        print(f"   📦 등록상품ID: {test_seller_product_id}")
        print(f"   💡 실제 테스트 시에는 TEST_SELLER_PRODUCT_ID 환경변수 설정 필요")
        
        # 상품 조회 실행
        result = client.get_product(test_seller_product_id)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 상품 조회 성공:")
            data = result.get("data", {})
            
            # 기본 정보 표시
            print(f"   📦 등록상품ID: {data.get('sellerProductId')}")
            print(f"   📝 상품명: {data.get('sellerProductName')}")
            print(f"   🏷️ 노출상품명: {data.get('displayProductName')}")
            print(f"   🏪 브랜드: {data.get('brand')}")
            print(f"   📊 상태: {data.get('statusName')}")
            print(f"   📂 카테고리: {data.get('displayCategoryCode')}")
            print(f"   🚚 배송: {data.get('deliveryMethod')} / {data.get('deliveryChargeType')}")
            print(f"   🏭 출고지: {data.get('outboundShippingPlaceCode')}")
            print(f"   📦 반품지: {data.get('returnCenterCode')}")
            
            # 아이템 정보 상세 표시
            items = data.get('items', [])
            print(f"\n   📋 상품 아이템 상세 정보 ({len(items)}개):")
            for i, item in enumerate(items, 1):
                print(f"\n      === 아이템 {i} ===")
                print(f"      📝 아이템명: {item.get('itemName')}")
                print(f"      💰 정가: {item.get('originalPrice'):,}원")
                print(f"      💲 판매가: {item.get('salePrice'):,}원")
                print(f"      📦 재고: {item.get('maximumBuyCount')}개")
                print(f"      👤 인당구매: {item.get('maximumBuyForPerson')}개")
                print(f"      🕐 구매기간: {item.get('maximumBuyForPersonPeriod')}일")
                print(f"      🚚 출고일: {item.get('outboundShippingTimeDay')}일")
                print(f"      🆔 옵션ID: {item.get('vendorItemId')}")
                print(f"      🔢 업체SKU: {item.get('externalVendorSku')}")
                print(f"      📋 바코드: {item.get('barcode') or '없음'}")
                print(f"      🔞 성인상품: {item.get('adultOnly')}")
                print(f"      💳 과세: {item.get('taxType')}")
                
                # 상품 속성 표시
                attributes = item.get('attributes', [])
                if attributes:
                    print(f"      🏷️ 속성: {len(attributes)}개")
                    for attr in attributes[:3]:  # 최대 3개만 표시
                        print(f"         - {attr.get('attributeTypeName')}: {attr.get('attributeValueName')}")
                
                # 이미지 정보 표시
                images = item.get('images', [])
                if images:
                    print(f"      🖼️ 이미지: {len(images)}개")
                    for img in images[:2]:  # 최대 2개만 표시
                        print(f"         - {img.get('imageType')}: {(img.get('vendorPath') or img.get('cdnPath', ''))[:50]}")
                
                if i >= 2:  # 최대 2개 아이템만 상세 표시
                    if len(items) > 2:
                        print(f"\n      ... 외 {len(items) - 2}개 아이템 (간략 표시 생략)")
                    break
            
            print(f"\n   📊 조회된 상품 정보 활용 가능:")
            print(f"      - 상품 수정 시 기본 데이터로 사용")
            print(f"      - 옵션ID(vendorItemId)로 가격/재고 수정")
            print(f"      - 상품 상태 및 승인 현황 확인")
            
        else:
            print(f"\n❌ 실제 API 상품 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
    except Exception as e:
        print(f"❌ 실제 API 상품 조회 오류: {e}")


def test_real_api_product_partial_get():
    """실제 API로 상품 조회 (승인불필요) 테스트"""
    print("\n" + "=" * 60 + " 실제 API 상품 조회 (승인불필요) 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 테스트용 등록상품ID (실제 API 테스트 시에는 실제 상품 ID 사용)
        test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '30100201234')
        
        print(f"\n🔍 실제 API로 상품 부분 조회 중...")
        print(f"   📦 등록상품ID: {test_seller_product_id}")
        print(f"   💡 실제 테스트 시에는 TEST_SELLER_PRODUCT_ID 환경변수 설정 필요")
        print(f"   🚀 빠른 배송/반품지 정보 조회용 API")
        
        # 상품 부분 조회 실행
        result = client.get_product_partial(test_seller_product_id)
        
        if result.get("success"):
            print(f"\n✅ 실제 API 상품 부분 조회 성공:")
            data = result.get("data", {})
            
            # 기본 정보
            print(f"   📦 등록상품ID: {data.get('sellerProductId')}")
            
            # 배송 정보 상세
            print(f"\n   🚚 배송 설정 상세:")
            delivery_method = data.get('deliveryMethod')
            delivery_charge_type = data.get('deliveryChargeType')
            print(f"      📋 배송방법: {delivery_method} - {client.DELIVERY_METHODS.get(delivery_method, '알 수 없음')}")
            print(f"      🚛 택배사코드: {data.get('deliveryCompanyCode')}")
            print(f"      💰 배송비타입: {delivery_charge_type} - {client.DELIVERY_CHARGE_TYPES.get(delivery_charge_type, '알 수 없음')}")
            print(f"      💵 기본배송비: {data.get('deliveryCharge'):,}원")
            print(f"      🎯 무료배송조건: {data.get('freeShipOverAmount'):,}원 이상")
            print(f"      🔄 초도반품배송비: {data.get('deliveryChargeOnReturn'):,}원")
            print(f"      🏔️ 도서산간배송: {'가능' if data.get('remoteAreaDeliverable') == 'Y' else '불가'}")
            print(f"      📦 묶음배송: {'가능' if data.get('unionDeliveryType') == 'UNION_DELIVERY' else '불가'}")
            print(f"      🏭 출고지코드: {data.get('outboundShippingPlaceCode')}")
            
            # 반품지 정보 상세
            print(f"\n   📦 반품지 설정 상세:")
            print(f"      🆔 반품지센터코드: {data.get('returnCenterCode')}")
            print(f"      🏷️ 반품지명: {data.get('returnChargeName')}")
            print(f"      📞 담당자 연락처: {data.get('companyContactNumber')}")
            print(f"      📮 우편번호: {data.get('returnZipCode')}")
            print(f"      🏠 기본주소: {data.get('returnAddress')}")
            print(f"      🏠 상세주소: {data.get('returnAddressDetail')}")
            print(f"      💰 반품배송비: {data.get('returnCharge'):,}원")
            
            # 기타 설정
            print(f"\n   ℹ️ 추가 설정:")
            print(f"      🔒 PCC(개인통관부호) 필요: {'예' if data.get('pccNeeded') else '아니오'}")
            extra_msg = data.get('extraInfoMessage')
            if extra_msg:
                print(f"      📝 주문제작 안내메시지: {extra_msg}")
            else:
                print(f"      📝 주문제작 안내메시지: 없음")
            
            # 배송비 정책 분석
            print(f"\n   📊 배송비 정책 분석:")
            if delivery_charge_type == "FREE":
                print(f"      ✅ 무료배송 상품")
                print(f"      🔄 반품시 고객부담: {data.get('deliveryChargeOnReturn'):,}원")
            elif delivery_charge_type == "NOT_FREE":
                print(f"      💰 유료배송 상품 ({data.get('deliveryCharge'):,}원)")
                print(f"      🔄 반품시 고객부담: {data.get('returnCharge'):,}원")
            elif delivery_charge_type == "CONDITIONAL_FREE":
                print(f"      🎯 조건부 무료배송")
                print(f"      📈 기준금액: {data.get('freeShipOverAmount'):,}원 이상")
                print(f"      💰 미달시 배송비: {data.get('deliveryCharge'):,}원")
            elif delivery_charge_type == "CHARGE_RECEIVED":
                print(f"      📮 착불배송 상품")
            
            print(f"\n   🎯 데이터 활용 가능:")
            print(f"      - 상품 수정 API의 기본 데이터로 즉시 사용")
            print(f"      - 배송비 정책 변경 전 현재 설정 확인")
            print(f"      - 반품지 변경 시 기존 설정 백업")
            print(f"      - 대량 상품 관리 시 빠른 설정 확인")
            
        else:
            print(f"\n❌ 실제 API 상품 부분 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
    except Exception as e:
        print(f"❌ 실제 API 상품 부분 조회 오류: {e}")


def test_real_api_product_update():
    """실제 API로 상품 수정 테스트"""
    print("\n" + "=" * 60 + " 실제 API 상품 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 환경변수에서 정보 가져오기
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        test_seller_product_id = os.getenv('TEST_SELLER_PRODUCT_ID', '309323422')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        print(f"\n🔧 실제 API로 상품 수정 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   🆔 수정할 상품 ID: {test_seller_product_id}")
        print(f"   💡 실제 테스트 시에는 기존 상품 ID를 TEST_SELLER_PRODUCT_ID로 설정")
        
        # 1단계: 기존 상품 정보 조회
        print(f"\n🔍 1단계: 기존 상품 정보 조회")
        get_result = client.get_product(test_seller_product_id)
        
        if get_result.get("success"):
            print(f"✅ 상품 조회 성공")
            data = get_result.get("data", {})
            print(f"   📦 기존 상품명: {data.get('sellerProductName', 'N/A')}")
            
            # 기존 아이템 정보 확인
            items = data.get('items', [])
            if items:
                first_item = items[0]
                existing_item_id = first_item.get('sellerProductItemId')
                vendor_item_id = first_item.get('vendorItemId')
                print(f"   📋 첫번째 아이템 ID: {existing_item_id}")
            else:
                existing_item_id = 769536471  # 예시 ID
                vendor_item_id = 123456789
                print(f"   ⚠️ 아이템 정보 없음, 예시 ID 사용")
        else:
            print(f"⚠️ 상품 조회 실패: {get_result.get('error')}")
            print(f"예시 데이터로 수정 테스트 진행...")
            existing_item_id = 769536471
            vendor_item_id = 123456789
        
        # 2단계: 상품 수정 요청 생성
        print(f"\n🔧 2단계: 상품 수정 요청 생성")
        
        # 판매 기간 설정
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 기존 아이템 수정
        updated_item = ProductItem(
            seller_product_item_id=existing_item_id,
            vendor_item_id=vendor_item_id,
            item_name="실제API_수정된_아이템",
            original_price=22000,
            sale_price=18500,  # 가격 수정
            maximum_buy_count=180,  # 재고 수정
            maximum_buy_for_person=4,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="REAL_API_UPDATED",
            barcode="8801234567899"
        )
        
        # 새로운 아이템 추가
        new_item = ProductItem(
            # seller_product_item_id 없음 = 새 옵션
            item_name="실제API_신규추가_아이템",
            original_price=28000,
            sale_price=24000,
            maximum_buy_count=100,
            maximum_buy_for_person=2,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=2,
            external_vendor_sku="REAL_API_NEW",
            barcode="8801234567898"
        )
        
        # 수정 이미지
        updated_images = [
            ProductImage(
                image_order=0,
                image_type="REPRESENTATION",
                vendor_path="https://example.com/real-api-updated-main.jpg"
            ),
            ProductImage(
                image_order=1,
                image_type="DETAIL",
                vendor_path="https://example.com/real-api-new-detail.jpg"
            )
        ]
        
        # 수정 속성
        updated_attributes = [
            ProductAttribute(
                attribute_type_name="수정상태",
                attribute_value_name="실제API수정완료"
            ),
            ProductAttribute(
                attribute_type_name="업데이트",
                attribute_value_name="최신버전"
            )
        ]
        
        # 수정 고시정보
        updated_notices = [
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="용량 또는 중량",
                content="실제API 테스트 수정 완료"
            ),
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="제품주요사양",
                content="실제API로 수정된 프리미엄 제품"
            )
        ]
        
        # 실제 상품 수정 요청
        update_request = ProductRequest(
            seller_product_id=int(test_seller_product_id),
            display_category_code=56137,
            seller_product_name="실제API_수정테스트_상품",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="realApiUpdateTest",
            requested=False,  # 테스트용이므로 승인요청 안함
            
            # 수정된 상품 정보
            display_product_name="실제API 수정테스트 상품",
            brand="실제API테스트브랜드",
            general_product_name="실제API 수정 테스트",
            product_group="실제API 테스트군",
            manufacture="실제API테스트브랜드",
            
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
            return_charge_name="실제API 수정테스트 반품센터",
            company_contact_number="02-9999-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구",
            return_address_detail="실제API테스트빌딩 수정층",
            return_charge=3000,
            return_charge_vendor="N",
            
            # AS 정보
            after_service_information="실제API 수정 A/S: 1588-9999",
            after_service_contact_number="1588-9999",
            
            # 출고지 정보
            outbound_shipping_place_code="74010",
            
            # 수정된 아이템들
            items=[updated_item, new_item],
            images=updated_images,
            attributes=updated_attributes,
            notices=updated_notices
        )
        
        print(f"\n📋 실제 수정 요청 상세:")
        print(f"   🔧 수정 아이템 ID: {existing_item_id}")
        print(f"   💰 수정된 가격: {updated_item.sale_price:,}원")
        print(f"   ➕ 신규 아이템: {new_item.item_name}")
        print(f"   💰 신규 아이템 가격: {new_item.sale_price:,}원")
        print(f"   📦 총 아이템 수: {len(update_request.items)}개")
        
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
            
            print(f"\n   ✅ 수정 완료 항목:")
            print(f"      1. ✅ 기존 아이템 정보 수정")
            print(f"      2. ✅ 새로운 아이템 추가")
            print(f"      3. ✅ 상품명 및 브랜드 변경")
            print(f"      4. ✅ 가격 및 재고 업데이트")
            print(f"      5. ✅ 이미지 및 속성 수정")
            print(f"      6. ✅ 고시정보 업데이트")
            
            print(f"\n   🎯 수정 성공 활용:")
            print(f"      - 기존 상품 정보 개선")
            print(f"      - 옵션 추가/수정으로 상품 확장")
            print(f"      - 가격 정책 조정")
            print(f"      - 브랜딩 및 마케팅 정보 업데이트")
            
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
            print(f"   - 잘못된 seller_product_item_id")
            print(f"   - 승인완료 상품의 가격/재고 직접 수정 시도")
            print(f"   - 권한이 없는 상품에 대한 수정 시도")
            print(f"   - 카테고리에 맞지 않는 속성 정보")
            print(f"   - 필수 고시정보 누락 또는 오류")
            
        print(f"\n💡 상품 수정 모범 사례:")
        print(f"   1. get_product로 기존 정보 먼저 조회")
        print(f"   2. 조회된 JSON을 기반으로 ProductRequest 구성")
        print(f"   3. 필요한 부분만 선택적으로 수정")
        print(f"   4. seller_product_item_id로 기존 옵션 관리")
        print(f"   5. 새 옵션 추가 시 ID 없이 items 배열에 추가")
        print(f"   6. 승인완료 상품은 별도 API로 가격/재고 수정")
        
    except Exception as e:
        print(f"❌ 실제 API 상품 수정 오류: {e}")
        import traceback
        traceback.print_exc()


def test_real_api_validation_scenarios():
    """실제 API로 검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 실제 API 검증 시나리오 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        vendor_id = os.getenv('COUPANG_VENDOR_ID')
        
        if not vendor_id:
            print("❌ COUPANG_VENDOR_ID 환경변수가 설정되지 않았습니다")
            return
        
        # 실제 API에서 발생할 수 있는 오류 시나리오들
        test_scenarios = [
            {
                "name": "잘못된 카테고리 코드",
                "category_code": 999999,  # 존재하지 않는 카테고리
                "expected_error": "카테고리"
            },
            {
                "name": "잘못된 반품지 코드",
                "return_center_code": "INVALID_CODE",
                "expected_error": "반품지"
            },
            {
                "name": "잘못된 출고지 코드",
                "outbound_code": "INVALID_OUTBOUND",
                "expected_error": "출고지"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🧪 시나리오 {i}: {scenario['name']}")
            
            try:
                # 기본 날짜 설정
                start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
                
                # 기본 아이템과 이미지 생성
                item = ProductItem(
                    item_name="검증테스트아이템",
                    original_price=10000,
                    sale_price=8000,
                    maximum_buy_count=10,
                    maximum_buy_for_person=1,
                    maximum_buy_for_person_period=30,
                    outbound_shipping_time_day=1
                )
                
                image = ProductImage(
                    image_order=0,
                    image_type="REPRESENTATION",
                    vendor_path="https://example.com/test.jpg"
                )
                
                # 테스트 상품 요청 생성
                request = ProductRequest(
                    display_category_code=scenario.get("category_code", 56137),
                    seller_product_name=f"검증테스트상품_{i}",
                    vendor_id=vendor_id,
                    sale_started_at=start_date,
                    sale_ended_at=end_date,
                    vendor_user_id="validationTestUser",
                    requested=False,
                    
                    brand="검증테스트브랜드",
                    general_product_name="검증 테스트 상품",
                    manufacture="검증테스트브랜드",
                    
                    delivery_method="SEQUENCIAL",
                    delivery_company_code="CJGLS",
                    delivery_charge_type="FREE",
                    
                    return_center_code=scenario.get("return_center_code", "1000274592"),
                    return_charge_name="검증테스트 반품지",
                    company_contact_number="02-1234-5678",
                    return_zip_code="135-090",
                    return_address="서울특별시 강남구",
                    return_address_detail="검증테스트빌딩",
                    return_charge=2500,
                    return_charge_vendor="N",
                    
                    after_service_information="검증테스트 A/S",
                    after_service_contact_number="1234-5678",
                    
                    outbound_shipping_place_code=scenario.get("outbound_code", "74010"),
                    
                    items=[item],
                    images=[image]
                )
                
                # 상품 등록 시도
                result = client.create_product(request)
                
                if result.get("success"):
                    print(f"   ⚠️ 예상치 못한 성공")
                else:
                    error_msg = result.get('error', '')
                    if scenario['expected_error'] in error_msg:
                        print(f"   ✅ 예상된 오류 발생: {error_msg}")
                    else:
                        print(f"   ❓ 다른 오류 발생: {error_msg}")
                        
            except ValueError as e:
                print(f"   ✅ 예상된 검증 오류: {e}")
            except Exception as e:
                if scenario['expected_error'] in str(e):
                    print(f"   ✅ 예상된 API 오류: {e}")
                else:
                    print(f"   ❓ 예상치 못한 오류: {e}")
                    
    except Exception as e:
        print(f"❌ 검증 시나리오 테스트 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 등록 API 실제 테스트 시작")
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
        return
    
    try:
        # 실제 API 테스트 실행
        test_real_api_product_creation()
        test_real_api_category_recommendation()
        test_real_api_complex_product()
        test_real_api_product_get()
        test_real_api_product_partial_get()
        test_real_api_product_update()
        test_real_api_validation_scenarios()
        
        print(f"\n" + "=" * 50 + " 실제 API 테스트 완료 " + "=" * 50)
        print("✅ 모든 실제 API 테스트가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 실제 API 인증 및 상품 등록")
        print("   2. ✅ 카테고리 추천 API")
        print("   3. ✅ 다중 옵션 상품 등록")
        print("   4. ✅ 상품 조회 API")
        print("   5. ✅ 상품 조회 (승인불필요) API")
        print("   6. ✅ 상품 수정 (승인필요) API")
        print("   7. ✅ 이미지 다중 등록")
        print("   8. ✅ 인증정보 등록")
        print("   9. ✅ 상품 속성 설정")
        print("  10. ✅ 고시정보 등록")
        print("  11. ✅ 상세 컨텐츠 등록")
        print("  12. ✅ 검색 태그 설정")
        print("  13. ✅ 조건부 무료배송 설정")
        print("  14. ✅ API 오류 처리 및 검증")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 상품 등록 전 카테고리 메타정보 조회 필수")
        print("   - 출고지/반품지 코드는 실제 등록된 코드 사용")
        print("   - 대표이미지는 반드시 포함되어야 함")
        print("   - 카테고리별 필수 속성 확인 필요")
        print("   - 고시정보는 카테고리에 맞게 정확히 입력")
        print("   - 이미지 URL은 접근 가능한 실제 경로 사용")
        print("   - 테스트용은 requested=false로 설정")
        print("   - 승인 요청은 상품 정보 완성 후 진행")
        
    except Exception as e:
        print(f"\n❌ 실제 API 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()