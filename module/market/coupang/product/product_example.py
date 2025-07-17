#!/usr/bin/env python3
"""
쿠팡 상품 등록 API 사용 예제
상품 등록 기능 테스트
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
    ProductRequiredDocument,
    ProductPartialUpdateRequest
)


def test_basic_product_creation():
    """기본적인 상품 등록 테스트"""
    print("=" * 60 + " 기본 상품 등록 테스트 " + "=" * 60)
    
    try:
        # 클라이언트 초기화
        client = ProductClient()
        print("✅ 쿠팡 상품 클라이언트 초기화 성공")
        
        # 기본 상품 정보 설정
        vendor_id = "A00012345"  # 실제 벤더 ID로 변경 필요
        category_code = 56137  # 예시 카테고리 코드
        
        print(f"\n📦 상품 등록 중...")
        print(f"   🏢 판매자 ID: {vendor_id}")
        print(f"   📂 카테고리: {category_code}")
        
        # 판매 기간 설정 (현재부터 1년)
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 상품 아이템 생성
        item = ProductItem(
            item_name="테스트상품옵션1",
            original_price=20000,
            sale_price=15000,
            maximum_buy_count=100,
            maximum_buy_for_person=5,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="TEST001",
            barcode="1234567890123"
        )
        
        # 대표 이미지 생성
        image = ProductImage(
            image_order=0,
            image_type="REPRESENTATION",
            vendor_path="https://example.com/product-image.jpg"
        )
        
        # 상품 속성 생성
        attribute = ProductAttribute(
            attribute_type_name="용량",
            attribute_value_name="200ml"
        )
        
        # 고시정보 생성
        notice = ProductNotice(
            notice_category_name="화장품",
            notice_category_detail_name="용량 또는 중량",
            content="200ml"
        )
        
        # 상품 등록 요청 생성
        request = ProductRequest(
            display_category_code=category_code,
            seller_product_name="테스트브랜드 솝베리클렌징오일",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="testuser",
            requested=False,  # 저장만 하고 승인요청은 하지 않음
            
            # 상품 정보
            display_product_name="테스트브랜드 솝베리클렌징오일",
            brand="테스트브랜드",
            general_product_name="솝베리 클렌징 오일",
            product_group="클렌징 오일",
            manufacture="테스트브랜드",
            
            # 배송 정보
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",
            delivery_charge_type="FREE",
            delivery_charge=0,
            free_ship_over_amount=0,
            delivery_charge_on_return=2500,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            
            # 반품지 정보
            return_center_code="1000274592",
            return_charge_name="테스트반품지",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="테스트주소지",
            return_charge=2500,
            return_charge_vendor="N",
            
            # AS 정보
            after_service_information="A/S안내1234-1234",
            after_service_contact_number="1234-1234",
            
            # 출고지 정보
            outbound_shipping_place_code="74010",
            
            # 리스트 데이터
            items=[item],
            images=[image],
            attributes=[attribute],
            notices=[notice]
        )
        
        print(f"\n📋 상품 정보:")
        print(f"   📝 상품명: {request.display_product_name}")
        print(f"   🏷️ 브랜드: {request.brand}")
        print(f"   💰 가격: {item.sale_price:,}원 (정가: {item.original_price:,}원)")
        print(f"   📦 재고: {item.maximum_buy_count}개")
        print(f"   🚚 배송: {client.DELIVERY_CHARGE_TYPES[request.delivery_charge_type]}")
        
        # 상품 등록 실행
        result = client.create_product(request)
        
        if result.get("success"):
            print(f"\n✅ 상품 등록 성공:")
            data = result.get("data", {})
            print(f"   🎯 결과: {result.get('message')}")
            if data:
                pprint(data, width=100, indent=4)
            
        else:
            print(f"\n❌ 상품 등록 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 오류 상세 정보
            original_response = result.get('originalResponse', {})
            if original_response:
                print(f"\n📋 오류 응답 상세:")
                pprint(original_response, width=100)
                
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 상품 등록 오류: {e}")


def test_category_recommendation():
    """카테고리 추천 테스트"""
    print("\n" + "=" * 60 + " 카테고리 추천 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        print(f"\n🔍 카테고리 추천 요청 중...")
        
        # 카테고리 추천 요청
        result = client.predict_category(
            product_name="코데즈컴바인 양트임싱글코트",
            product_description="모니터 해상도, 밝기, 컴퓨터 사양 등에 따라 실물과 약간의 색상차이가 있을 수 있습니다",
            brand="코데즈컴바인",
            attributes={
                "제품 소재": "모달:53.8 폴리:43.2 레이온:2.4 면:0.6",
                "색상": "베이지,네이비",
                "제조국": "한국"
            }
        )
        
        if result.get("success"):
            print(f"\n✅ 카테고리 추천 성공:")
            data = result.get("data", {})
            print(f"   🎯 추천 결과: {data.get('autoCategorizationPredictionResultType')}")
            print(f"   📂 카테고리 ID: {data.get('predictedCategoryId')}")
            print(f"   📝 카테고리명: {data.get('predictedCategoryName')}")
            
            comment = data.get('comment')
            if comment:
                print(f"   💬 코멘트: {comment}")
                
        else:
            print(f"\n❌ 카테고리 추천 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 카테고리 추천 오류: {e}")


def test_complex_product_creation():
    """복잡한 상품 등록 테스트 (다중 옵션, 이미지, 인증정보 포함)"""
    print("\n" + "=" * 60 + " 복잡한 상품 등록 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        vendor_id = "A00012345"
        category_code = 56137
        
        print(f"\n📦 복잡한 상품 등록 중...")
        print(f"   다중 옵션, 이미지, 인증정보 포함")
        
        # 판매 기간 설정
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 다중 아이템 생성 (색상별)
        items = [
            ProductItem(
                item_name="솝베리클렌징오일_베이지",
                original_price=25000,
                sale_price=20000,
                maximum_buy_count=50,
                maximum_buy_for_person=3,
                maximum_buy_for_person_period=30,
                outbound_shipping_time_day=1,
                external_vendor_sku="SOB001_BEIGE",
                barcode="1234567890001"
            ),
            ProductItem(
                item_name="솝베리클렌징오일_네이비",
                original_price=25000,
                sale_price=20000,
                maximum_buy_count=50,
                maximum_buy_for_person=3,
                maximum_buy_for_person_period=30,
                outbound_shipping_time_day=1,
                external_vendor_sku="SOB001_NAVY",
                barcode="1234567890002"
            )
        ]
        
        # 다중 이미지 생성
        images = [
            ProductImage(
                image_order=0,
                image_type="REPRESENTATION",
                vendor_path="https://example.com/product-main.jpg"
            ),
            ProductImage(
                image_order=1,
                image_type="DETAIL",
                vendor_path="https://example.com/product-detail1.jpg"
            ),
            ProductImage(
                image_order=2,
                image_type="DETAIL",
                vendor_path="https://example.com/product-detail2.jpg"
            )
        ]
        
        # 인증정보 생성
        certifications = [
            ProductCertification(
                certification_type="KC_CERTIFICATION",
                certification_code="KC-200-2002-22"
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
                attribute_value_name="한국"
            )
        ]
        
        # 다중 고시정보 생성
        notices = [
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="용량 또는 중량",
                content="200ml"
            ),
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="제품주요사양",
                content="클렌징오일, 메이크업 제거용"
            )
        ]
        
        # 상세 컨텐츠 생성
        content_detail = ProductContentDetail(
            content_type="TEXT",
            content="<div>프리미엄 솝베리 클렌징오일로 깔끔하게 메이크업을 제거하세요</div>"
        )
        content = ProductContent(content_details=[content_detail])
        
        # 검색 태그 생성
        search_tags = ["클렌징오일", "메이크업리무버", "솝베리", "클렌징", "세안"]
        
        # 복잡한 상품 등록 요청 생성
        request = ProductRequest(
            display_category_code=category_code,
            seller_product_name="프리미엄 솝베리 클렌징오일 세트",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="testuser",
            requested=False,
            
            # 상품 정보
            display_product_name="프리미엄 솝베리 클렌징오일",
            brand="프리미엄브랜드",
            general_product_name="솝베리 클렌징 오일",
            product_group="클렌징 오일",
            manufacture="프리미엄브랜드",
            
            # 배송 정보 (조건부 무료배송)
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",
            delivery_charge_type="CONDITIONAL_FREE",
            delivery_charge=2500,
            free_ship_over_amount=30000,  # 3만원 이상 무료배송
            delivery_charge_on_return=0,
            remote_area_deliverable="Y",  # 도서산간 배송 가능
            union_delivery_type="UNION_DELIVERY",
            
            # 반품지 정보
            return_center_code="1000274592",
            return_charge_name="프리미엄브랜드 반품센터",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="프리미엄빌딩 5층",
            return_charge=2500,
            return_charge_vendor="N",
            
            # AS 정보
            after_service_information="품질보증 30일, A/S 문의: 1234-5678",
            after_service_contact_number="1234-5678",
            
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
        print(f"   🚚 배송: 조건부무료 (3만원 이상)")
        
        # 상품 등록 실행
        result = client.create_product(request)
        
        if result.get("success"):
            print(f"\n✅ 복잡한 상품 등록 성공:")
            data = result.get("data", {})
            print(f"   🎯 결과: {result.get('message')}")
            if data:
                pprint(data, width=100, indent=4)
            
        else:
            print(f"\n❌ 복잡한 상품 등록 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
    except Exception as e:
        print(f"❌ 복잡한 상품 등록 오류: {e}")


def test_validation_scenarios():
    """검증 시나리오 테스트"""
    print("\n" + "=" * 60 + " 검증 시나리오 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 검증 시나리오들
        test_scenarios = [
            {
                "name": "카테고리 코드 누락",
                "request_data": {
                    "display_category_code": 0,  # 잘못된 카테고리
                    "seller_product_name": "테스트상품",
                    "vendor_id": "A00012345",
                    "vendor_user_id": "testuser"
                },
                "expected_error": "노출카테고리코드는 필수"
            },
            {
                "name": "상품명 누락",
                "request_data": {
                    "display_category_code": 56137,
                    "seller_product_name": "",  # 빈 상품명
                    "vendor_id": "A00012345",
                    "vendor_user_id": "testuser"
                },
                "expected_error": "등록상품명은 필수"
            },
            {
                "name": "아이템 누락",
                "request_data": {
                    "display_category_code": 56137,
                    "seller_product_name": "테스트상품",
                    "vendor_id": "A00012345",
                    "vendor_user_id": "testuser",
                    "items": []  # 빈 아이템 리스트
                },
                "expected_error": "최소 1개 이상의 아이템이 필요"
            },
            {
                "name": "대표이미지 누락",
                "request_data": {
                    "display_category_code": 56137,
                    "seller_product_name": "테스트상품",
                    "vendor_id": "A00012345",
                    "vendor_user_id": "testuser",
                    "items": [ProductItem(
                        item_name="테스트아이템",
                        original_price=10000,
                        sale_price=8000,
                        maximum_buy_count=10,
                        maximum_buy_for_person=1,
                        maximum_buy_for_person_period=30,
                        outbound_shipping_time_day=1
                    )],
                    "images": []  # 빈 이미지 리스트
                },
                "expected_error": "최소 1개 이상의 이미지가 필요"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🧪 시나리오 {i}: {scenario['name']}")
            
            try:
                # 기본 날짜 설정
                start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
                
                # 기본 요청 데이터 생성
                base_data = {
                    "sale_started_at": start_date,
                    "sale_ended_at": end_date
                }
                base_data.update(scenario["request_data"])
                
                # ProductRequest 생성 (부분적 데이터)
                request = ProductRequest(**base_data)
                
                # 상품 등록 시도
                result = client.create_product(request)
                print(f"   ⚠️ 예상치 못한 성공")
                
            except ValueError as e:
                if scenario['expected_error'] in str(e):
                    print(f"   ✅ 예상된 검증 오류: {e}")
                else:
                    print(f"   ❓ 다른 검증 오류: {e}")
            except Exception as e:
                print(f"   ❓ 예상치 못한 오류: {e}")
                
    except Exception as e:
        print(f"❌ 검증 시나리오 테스트 오류: {e}")


def test_product_get():
    """상품 조회 테스트"""
    print("\n" + "=" * 60 + " 상품 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 테스트용 등록상품ID (실제로는 상품 등록 후 반환된 ID 사용)
        test_seller_product_id = "1320567890"  # 예시 ID
        
        print(f"\n🔍 상품 조회 중...")
        print(f"   📦 등록상품ID: {test_seller_product_id}")
        
        # 상품 조회 실행
        result = client.get_product(test_seller_product_id)
        
        if result.get("success"):
            print(f"\n✅ 상품 조회 성공:")
            data = result.get("data", {})
            
            # 기본 정보 표시
            print(f"   📦 등록상품ID: {data.get('sellerProductId')}")
            print(f"   📝 상품명: {data.get('sellerProductName')}")
            print(f"   🏷️ 노출상품명: {data.get('displayProductName')}")
            print(f"   🏪 브랜드: {data.get('brand')}")
            print(f"   📊 상태: {data.get('statusName')}")
            print(f"   📂 카테고리코드: {data.get('displayCategoryCode')}")
            print(f"   🚚 배송방법: {data.get('deliveryMethod')}")
            print(f"   💰 배송비타입: {data.get('deliveryChargeType')}")
            
            # 아이템 정보 표시
            items = data.get('items', [])
            print(f"\n   📋 상품 아이템 정보 ({len(items)}개):")
            for i, item in enumerate(items[:3], 1):  # 최대 3개만 표시
                print(f"      {i}. {item.get('itemName')}")
                print(f"         💰 가격: {item.get('salePrice'):,}원")
                print(f"         📦 재고: {item.get('maximumBuyCount')}개")
                print(f"         🆔 옵션ID: {item.get('vendorItemId')}")
                if item.get('externalVendorSku'):
                    print(f"         🔢 SKU: {item.get('externalVendorSku')}")
            
            if len(items) > 3:
                print(f"      ... 외 {len(items) - 3}개 아이템")
                
            # 이미지 정보 표시 (첫 번째 아이템만)
            if items and items[0].get('images'):
                images = items[0]['images']
                print(f"\n   🖼️ 이미지 정보 ({len(images)}개):")
                for img in images[:2]:  # 최대 2개만 표시
                    print(f"      - {img.get('imageType')}: {img.get('imageOrder')}번째")
            
        else:
            print(f"\n❌ 상품 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 일반적인 오류 상황들
            error_msg = result.get('error', '')
            if "등록 또는 수정되고 있습니다" in error_msg:
                print(f"   💡 해결방법: 10분 후 다시 조회하세요")
            elif "다른 업체" in error_msg:
                print(f"   💡 해결방법: 본인 업체의 상품인지 확인하세요")
            elif "데이터가 없습니다" in error_msg:
                print(f"   💡 해결방법: 올바른 등록상품ID인지 확인하세요")
                
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 상품 조회 오류: {e}")


def test_product_partial_get():
    """상품 조회 (승인불필요) 테스트"""
    print("\n" + "=" * 60 + " 상품 조회 (승인불필요) 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 테스트용 등록상품ID (실제로는 상품 등록 후 반환된 ID 사용)
        test_seller_product_id = "30100201234"  # 예시 ID
        
        print(f"\n🔍 상품 부분 조회 중...")
        print(f"   📦 등록상품ID: {test_seller_product_id}")
        print(f"   💡 배송 및 반품지 정보를 빠르게 조회")
        
        # 상품 부분 조회 실행
        result = client.get_product_partial(test_seller_product_id)
        
        if result.get("success"):
            print(f"\n✅ 상품 부분 조회 성공:")
            data = result.get("data", {})
            
            # 기본 정보
            print(f"   📦 등록상품ID: {data.get('sellerProductId')}")
            
            # 배송 정보
            print(f"\n   🚚 배송 정보:")
            print(f"      📋 배송방법: {data.get('deliveryMethod')} ({client.DELIVERY_METHODS.get(data.get('deliveryMethod', ''), '알 수 없음')})")
            print(f"      🚛 택배사: {data.get('deliveryCompanyCode')}")
            print(f"      💰 배송비타입: {data.get('deliveryChargeType')} ({client.DELIVERY_CHARGE_TYPES.get(data.get('deliveryChargeType', ''), '알 수 없음')})")
            print(f"      💵 기본배송비: {data.get('deliveryCharge'):,}원")
            print(f"      🎯 무료배송조건: {data.get('freeShipOverAmount'):,}원 이상")
            print(f"      🔄 초도반품배송비: {data.get('deliveryChargeOnReturn'):,}원")
            print(f"      🏔️ 도서산간배송: {data.get('remoteAreaDeliverable')}")
            print(f"      📦 묶음배송: {data.get('unionDeliveryType')}")
            print(f"      🏭 출고지코드: {data.get('outboundShippingPlaceCode')}")
            
            # 반품지 정보
            print(f"\n   📦 반품지 정보:")
            print(f"      🆔 반품지코드: {data.get('returnCenterCode')}")
            print(f"      🏷️ 반품지명: {data.get('returnChargeName')}")
            print(f"      📞 연락처: {data.get('companyContactNumber')}")
            print(f"      📮 우편번호: {data.get('returnZipCode')}")
            print(f"      🏠 주소: {data.get('returnAddress')}")
            print(f"      🏠 상세주소: {data.get('returnAddressDetail')}")
            print(f"      💰 반품배송비: {data.get('returnCharge'):,}원")
            
            # 기타 정보
            print(f"\n   ℹ️ 기타 정보:")
            print(f"      🔒 PCC 필요: {data.get('pccNeeded')}")
            if data.get('extraInfoMessage'):
                print(f"      📝 안내메시지: {data.get('extraInfoMessage')}")
            
            print(f"\n   💡 활용 방법:")
            print(f"      - 상품 수정 API에서 이 정보를 기본값으로 사용")
            print(f"      - 배송비 정책 변경 시 현재 설정 확인")
            print(f"      - 반품지 정보 변경 시 기존 정보 참조")
            
        else:
            print(f"\n❌ 상품 부분 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 일반적인 오류 상황들
            error_msg = result.get('error', '')
            if "데이터가 없습니다" in error_msg:
                print(f"   💡 해결방법: 존재하는 상품의 sellerProductId인지 확인하세요")
                
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 상품 부분 조회 오류: {e}")


def test_product_update():
    """상품 수정 테스트"""
    print("\n" + "=" * 60 + " 상품 수정 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 수정할 상품 정보
        seller_product_id = 309323422  # 예시 ID
        vendor_id = "A00012345"
        
        print(f"\n🔧 상품 수정 기능 테스트")
        print(f"   🆔 수정할 상품 ID: {seller_product_id}")
        print(f"   💡 실제로는 get_product API로 기존 정보 조회 후 수정")
        
        # 판매 기간 설정 (1년 연장)
        start_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
        
        # 기존 아이템 수정 (seller_product_item_id 포함)
        updated_item = ProductItem(
            seller_product_item_id=769536471,  # 기존 아이템 ID
            vendor_item_id=123456789,
            item_name="수정된_클렌징오일_250ml",
            original_price=18000,  # 가격 수정
            sale_price=15000,
            maximum_buy_count=200,  # 재고 증가
            maximum_buy_for_person=5,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=1,
            external_vendor_sku="UPDATED_SKU_001",
            barcode="8801234567891"
        )
        
        # 새로운 아이템 추가 (seller_product_item_id 없음)
        new_item = ProductItem(
            # seller_product_item_id 없음 = 새 옵션 추가
            item_name="신규추가_대용량_500ml",
            original_price=30000,
            sale_price=25000,
            maximum_buy_count=100,
            maximum_buy_for_person=3,
            maximum_buy_for_person_period=30,
            outbound_shipping_time_day=2,
            external_vendor_sku="NEW_LARGE_001",
            barcode="8801234567892"
        )
        
        # 수정 이미지
        images = [
            ProductImage(
                image_order=0,
                image_type="REPRESENTATION",
                vendor_path="https://example.com/updated-main-image.jpg"
            ),
            ProductImage(
                image_order=1,
                image_type="DETAIL",
                vendor_path="https://example.com/new-detail-image.jpg"
            )
        ]
        
        # 수정 속성
        attributes = [
            ProductAttribute(
                attribute_type_name="용량",
                attribute_value_name="250ml/500ml"
            ),
            ProductAttribute(
                attribute_type_name="개선사항",
                attribute_value_name="향상된포뮬러"
            )
        ]
        
        # 수정 고시정보
        notices = [
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="용량 또는 중량",
                content="250ml, 500ml"
            ),
            ProductNotice(
                notice_category_name="화장품",
                notice_category_detail_name="제품주요사양",
                content="수정된 프리미엄 클렌징오일, 향상된 성분"
            )
        ]
        
        # 상품 수정 요청 생성
        update_request = ProductRequest(
            seller_product_id=seller_product_id,  # 수정 시 필수
            display_category_code=56137,
            seller_product_name="수정된_프리미엄_클렌징오일",
            vendor_id=vendor_id,
            sale_started_at=start_date,
            sale_ended_at=end_date,
            vendor_user_id="updateTestUser",
            requested=False,
            
            display_product_name="수정된 프리미엄 클렌징오일",
            brand="향상된브랜드",
            general_product_name="향상된 클렌징 오일",
            product_group="프리미엄 클렌징",
            manufacture="향상된브랜드",
            
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
            return_charge_name="향상된 반품센터",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구",
            return_address_detail="향상된빌딩 5층",
            return_charge=3000,
            return_charge_vendor="N",
            
            after_service_information="향상된 A/S: 1588-9999",
            after_service_contact_number="1588-9999",
            outbound_shipping_place_code="74010",
            
            # 수정된 데이터 (기존 + 신규)
            items=[updated_item, new_item],
            images=images,
            attributes=attributes,
            notices=notices
        )
        
        print(f"\n📋 수정 상세 정보:")
        print(f"   🔧 기존 옵션 수정: {updated_item.item_name} (ID: {updated_item.seller_product_item_id})")
        print(f"   ➕ 새 옵션 추가: {new_item.item_name}")
        print(f"   💰 수정된 가격: {updated_item.sale_price:,}원")
        print(f"   💰 신규 옵션 가격: {new_item.sale_price:,}원")
        print(f"   📦 총 옵션 수: {len(update_request.items)}개")
        
        # 상품 수정 실행
        print(f"\n📤 상품 수정 요청 중...")
        result = client.update_product(update_request)
        
        if result.get("success"):
            print(f"\n✅ 상품 수정 성공:")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            data = result.get("data", {})
            if data:
                print(f"   📊 응답 데이터: {data}")
                
            print(f"\n   💡 수정 완료 항목:")
            print(f"      ✅ 기존 옵션 정보 수정")
            print(f"      ✅ 새로운 옵션 추가")
            print(f"      ✅ 상품명 및 브랜드 변경")
            print(f"      ✅ 가격 및 재고 수정")
            print(f"      ✅ 이미지 및 속성 업데이트")
        else:
            print(f"\n❌ 상품 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 일반적인 수정 실패 사유
            print(f"\n   💡 일반적인 수정 실패 사유:")
            print(f"      - 존재하지 않는 seller_product_id")
            print(f"      - 잘못된 seller_product_item_id")
            print(f"      - 승인완료 상품의 가격/재고 수정 시도")
            print(f"      - 권한이 없는 상품 수정 시도")
        
        print(f"\n💡 상품 수정 주요 포인트:")
        print(f"   - seller_product_id는 수정 시 필수")
        print(f"   - 기존 옵션: seller_product_item_id 포함")
        print(f"   - 새 옵션: seller_product_item_id 없음")
        print(f"   - 옵션 삭제: items 배열에서 제외")
        print(f"   - get_product로 기존 정보 확인 후 수정 권장")
        
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 상품 수정 오류: {e}")


def test_product_approval():
    """상품 승인 요청 테스트"""
    print("\n" + "=" * 60 + " 상품 승인 요청 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 테스트용 등록상품ID (실제로는 상품 등록 후 반환된 ID 사용)
        test_seller_product_id = "1320567890"  # 예시 ID
        
        print(f"\n🔄 상품 승인 요청 중...")
        print(f"   📦 등록상품ID: {test_seller_product_id}")
        
        # 상품 승인 요청 실행
        result = client.approve_product(test_seller_product_id)
        
        if result.get("success"):
            print(f"\n✅ 상품 승인 요청 성공:")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   📦 승인요청 상품ID: {result.get('seller_product_id')}")
            
            data = result.get("data", {})
            if data:
                print(f"   📊 응답 데이터: {data}")
        else:
            print(f"\n❌ 상품 승인 요청 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 일반적인 오류 상황들
            error_msg = result.get('error', '')
            if "임시저장" in error_msg:
                print(f"   💡 해결방법: 상품이 '임시저장' 상태인지 확인하세요")
            elif "승인 요청 가능한 상태가 아닙니다" in error_msg:
                print(f"   💡 해결방법: 상품 상태를 확인하고 '임시저장' 상태에서만 승인요청 가능")
            elif "등록 또는 수정되고 있습니다" in error_msg:
                print(f"   💡 해결방법: 10분 후 다시 승인요청을 시도하세요")
                
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 상품 승인 요청 오류: {e}")


def test_supported_options():
    """지원 옵션 조회 테스트"""
    print("\n" + "=" * 60 + " 지원 옵션 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 지원 배송방법 조회
        delivery_methods = client.get_supported_delivery_methods()
        print(f"\n📋 지원 배송방법:")
        for code, name in delivery_methods.items():
            print(f"   - {code}: {name}")
        
        # 지원 배송비 종류 조회
        charge_types = client.get_supported_delivery_charge_types()
        print(f"\n💰 지원 배송비 종류:")
        for code, name in charge_types.items():
            print(f"   - {code}: {name}")
        
        # 지원 이미지 타입 조회
        image_types = client.get_supported_image_types()
        print(f"\n🖼️ 지원 이미지 타입:")
        for code, name in image_types.items():
            print(f"   - {code}: {name}")


def test_product_partial_update():
    """상품 부분 수정 (승인불필요) 테스트"""
    print("\n" + "=" * 60 + " 상품 부분 수정 (승인불필요) 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        # 수정할 상품 ID (실제 승인완료된 상품 ID로 변경 필요)
        seller_product_id = 309323422  # 예시 ID
        
        print(f"\n⚡ 상품 부분 수정 기능 테스트")
        print(f"   🆔 수정할 상품 ID: {seller_product_id}")
        print(f"   ✨ 특징: 승인 불필요, 배송/반품지만 수정")
        print(f"   🚀 장점: 빠른 물류 정보 변경")
        
        # 부분 수정 요청 생성
        partial_request = ProductPartialUpdateRequest(
            seller_product_id=seller_product_id,
            
            # 배송 정보 수정
            delivery_method="SEQUENCIAL",
            delivery_company_code="CJGLS",  # CJ대한통운
            delivery_charge_type="FREE",
            delivery_charge=0,
            delivery_charge_on_return=2500,
            free_ship_over_amount=0,
            remote_area_deliverable="N",
            union_delivery_type="UNION_DELIVERY",
            outbound_shipping_place_code="74010",
            outbound_shipping_time_day=1,
            
            # 반품지 정보 수정
            return_center_code="1000274592",
            return_charge_name="예제 반품센터",
            company_contact_number="02-1234-5678",
            return_zip_code="135-090",
            return_address="서울특별시 강남구 삼성동",
            return_address_detail="예제빌딩 5층",
            return_charge=2500,
            
            # 기타 정보
            extra_info_message="부분수정 예제로 변경됨",
            pcc_needed=False
        )
        
        print(f"\n📋 수정할 정보:")
        print(f"   🚚 배송: {partial_request.delivery_method} ({partial_request.delivery_company_code})")
        print(f"   💰 배송비: {partial_request.delivery_charge}원 ({partial_request.delivery_charge_type})")
        print(f"   📦 반품비: {partial_request.return_charge}원")
        print(f"   🏢 반품센터: {partial_request.return_charge_name}")
        print(f"   📞 연락처: {partial_request.company_contact_number}")
        print(f"   📅 출고일: {partial_request.outbound_shipping_time_day}일")
        print(f"   💬 안내: {partial_request.extra_info_message}")
        
        # 상품 부분 수정 실행
        print(f"\n📤 상품 부분 수정 요청 중...")
        result = client.update_product_partial(partial_request)
        
        if result.get("success"):
            print(f"\n✅ 상품 부분 수정 성공!")
            print(f"   🎯 결과: {result.get('message')}")
            print(f"   🆔 상품 ID: {result.get('seller_product_id')}")
            
            data = result.get("data", {})
            if data:
                print(f"   📊 응답 데이터:")
                pprint(data, width=100, indent=8)
                
            print(f"\n   ✨ 부분 수정의 장점:")
            print(f"      - 승인 과정 없이 즉시 반영")
            print(f"      - 배송/반품 정보만 빠르게 수정")
            print(f"      - 기존 상품 정보는 그대로 유지")
            print(f"      - 승인완료된 상품만 사용 가능")
        else:
            print(f"\n❌ 상품 부분 수정 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 일반적인 부분 수정 실패 사유
            print(f"\n   💡 일반적인 부분 수정 실패 사유:")
            print(f"      - 존재하지 않는 seller_product_id")
            print(f"      - 승인완료가 아닌 상품 (임시저장중, 승인대기중)")
            print(f"      - 권한이 없는 상품 수정 시도")
            print(f"      - 잘못된 반품센터/출고지 코드")
        
        print(f"\n💡 부분 수정 vs 전체 수정 비교:")
        print(f"   📝 전체 수정 (update_product):")
        print(f"      - 모든 상품 정보 수정 가능")
        print(f"      - 승인 과정 필요")
        print(f"      - 상품 상태에 따라 제한")
        print(f"   ⚡ 부분 수정 (update_product_partial):")
        print(f"      - 배송/반품지 정보만 수정")
        print(f"      - 승인 과정 불필요")
        print(f"      - 승인완료 상품만 가능")
        
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 상품 부분 수정 오류: {e}")
            
    except Exception as e:
        print(f"❌ 지원 옵션 조회 오류: {e}")


def test_inflow_status():
    """상품 등록 현황 조회 테스트"""
    print("\n" + "=" * 60 + " 상품 등록 현황 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        print(f"\n📊 상품 등록 현황 조회 기능 테스트")
        print(f"   📝 기능: 등록 가능한 상품수와 현재 등록된 상품수 조회")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/inflow-status")
        
        # 상품 등록 현황 조회 실행
        print(f"\n📤 상품 등록 현황 조회 요청 중...")
        result = client.get_inflow_status()
        
        if result.get("success"):
            print(f"\n✅ 상품 등록 현황 조회 성공!")
            
            # 기본 정보 표시
            vendor_id = result.get("vendor_id")
            restricted = result.get("restricted")
            registered_count = result.get("registered_count")
            permitted_count = result.get("permitted_count")
            
            print(f"\n📋 등록 현황 정보:")
            print(f"   🏢 판매자 ID: {vendor_id}")
            print(f"   📦 현재 등록된 상품수: {registered_count:,}개")
            
            if permitted_count is not None:
                print(f"   🎯 등록 가능한 최대 상품수: {permitted_count:,}개")
                remaining = permitted_count - registered_count
                usage_rate = (registered_count / permitted_count) * 100
                print(f"   ⚡ 추가 등록 가능한 상품수: {remaining:,}개")
                print(f"   📊 현재 사용률: {usage_rate:.1f}%")
            else:
                print(f"   🚀 등록 가능한 최대 상품수: 제한없음")
            
            # 등록 제한 상태
            print(f"\n🔐 상품 생성 제한 상태:")
            if restricted:
                print(f"   ❌ 제한됨: 현재 새로운 상품을 등록할 수 없습니다")
                print(f"   💡 조치: 쿠팡 담당자에게 문의 필요")
            else:
                print(f"   ✅ 허용됨: 새로운 상품을 등록할 수 있습니다")
            
            # 응답 데이터 표시
            data = result.get("data", {})
            if data:
                print(f"\n📊 응답 데이터:")
                pprint(data, width=100, indent=8)
            
            # 상태 분석
            print(f"\n📈 상태 분석:")
            if not restricted:
                if permitted_count is not None:
                    if usage_rate >= 90:
                        print(f"   🔴 주의: 등록 한도의 90% 이상 사용 중")
                    elif usage_rate >= 70:
                        print(f"   🟡 관리: 등록 한도의 70% 이상 사용 중")
                    else:
                        print(f"   🟢 여유: 등록 한도에 여유가 있음")
                else:
                    print(f"   🚀 최적: 무제한 등록 가능한 프리미엄 계정")
            else:
                print(f"   🚨 제한: 상품 등록이 차단된 상태")
                
        else:
            print(f"\n❌ 상품 등록 현황 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 일반적인 오류 상황들
            error_msg = result.get('error', '')
            if "권한" in error_msg or "인증" in error_msg:
                print(f"   💡 해결방법: API 키와 판매자 ID를 확인하세요")
            elif "네트워크" in error_msg or "연결" in error_msg:
                print(f"   💡 해결방법: 네트워크 연결 상태를 확인하세요")
        
        print(f"\n💡 등록 현황 조회 활용 방안:")
        print(f"   📊 모니터링: 정기적인 등록 현황 체크")
        print(f"   📈 계획: 상품 등록 전략 수립")
        print(f"   🚨 알림: 한도 도달 시 조기 경고")
        print(f"   📋 리포팅: 월간/분기별 현황 보고")
                
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 상품 등록 현황 조회 오류: {e}")


def test_time_frame_query():
    """상품 목록 구간 조회 테스트"""
    print("\n" + "=" * 60 + " 상품 목록 구간 조회 테스트 " + "=" * 60)
    
    try:
        client = ProductClient()
        
        vendor_id = os.getenv('COUPANG_VENDOR_ID', 'A00012345')  # 실제 벤더 ID로 변경 필요
        
        print(f"\n📊 상품 목록 구간 조회 기능 테스트")
        print(f"   📝 기능: 생성일시 기준으로 특정 시간 구간의 상품 목록 조회")
        print(f"   🔗 API: GET /v2/providers/seller_api/apis/api/v1/marketplace/seller-products/time-frame")
        print(f"   ⏱️ 제한: 최대 10분 범위")
        
        # 현재 시간에서 10분 전부터 현재까지 조회
        from datetime import datetime, timedelta
        now = datetime.now()
        start_time = now - timedelta(minutes=10)
        
        created_at_from = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        created_at_to = now.strftime("%Y-%m-%dT%H:%M:%S")
        
        print(f"\n📅 조회 시간 설정:")
        print(f"   📅 시작시간: {created_at_from}")
        print(f"   📅 종료시간: {created_at_to}")
        print(f"   ⏱️ 조회 범위: 10분")
        
        # 시간 구간 조회 실행
        print(f"\n📤 시간 구간 조회 요청 중...")
        result = client.get_products_by_time_frame(vendor_id, created_at_from, created_at_to)
        
        if result.get("success"):
            print(f"\n✅ 시간 구간 조회 성공!")
            
            # 기본 정보 표시
            data = result.get("data", [])
            time_range_minutes = result.get("time_range_minutes", 0)
            
            print(f"\n📋 조회 결과 정보:")
            print(f"   🏢 판매자 ID: {vendor_id}")
            print(f"   📦 조회된 상품수: {len(data)}개")
            print(f"   ⏱️ 실제 조회 범위: {time_range_minutes:.1f}분")
            print(f"   📅 조회 기간: {created_at_from} ~ {created_at_to}")
            
            # 상품 목록 표시
            if data:
                print(f"\n📋 해당 시간대 등록된 상품 (상위 5개):")
                for i, product in enumerate(data[:5], 1):
                    seller_product_id = product.get('sellerProductId')
                    seller_product_name = product.get('sellerProductName', 'N/A')
                    status_name = product.get('statusName', 'N/A')
                    brand = product.get('brand', 'N/A')
                    created_at = product.get('createdAt', 'N/A')
                    
                    print(f"\n   {i}. 상품 정보:")
                    print(f"      🆔 등록상품ID: {seller_product_id}")
                    print(f"      📝 상품명: {seller_product_name[:50]}{'...' if len(seller_product_name) > 50 else ''}")
                    print(f"      🏷️ 브랜드: {brand}")
                    print(f"      📊 상태: {status_name}")
                    print(f"      📅 등록시각: {created_at}")
                
                if len(data) > 5:
                    print(f"\n   ... 외 {len(data) - 5}개 상품")
                
                # 시간대별 분석
                print(f"\n📈 시간대 등록 분석:")
                
                # 상태별 분포
                status_count = {}
                for product in data:
                    status = product.get('statusName', 'Unknown')
                    status_count[status] = status_count.get(status, 0) + 1
                
                print(f"\n📊 상품 상태 분포:")
                for status, count in status_count.items():
                    percentage = (count / len(data)) * 100
                    print(f"   📊 {status}: {count}개 ({percentage:.1f}%)")
                
                # 등록 빈도 분석
                print(f"\n⏰ 등록 빈도 분석:")
                print(f"   📊 총 등록수: {len(data)}개")
                print(f"   📊 평균 등록률: {len(data) / time_range_minutes:.1f}개/분")
                
                activity_level = "높음" if len(data) / time_range_minutes > 1 else "보통" if len(data) / time_range_minutes > 0.5 else "낮음"
                print(f"   💡 활동성: {activity_level}")
                
            else:
                print(f"\n📭 해당 시간대에 등록된 상품이 없습니다")
                print(f"💡 다른 시간대를 조회해보세요")
            
            # 응답 데이터 표시
            data_sample = result.get("originalResponse", {})
            if data_sample and len(data) > 0:
                print(f"\n📊 응답 데이터 샘플:")
                pprint(data[0], width=100, indent=8)
                
        else:
            print(f"\n❌ 시간 구간 조회 실패:")
            print(f"   🚨 오류: {result.get('error')}")
            print(f"   📊 코드: {result.get('code')}")
            
            # 일반적인 오류 상황들
            error_msg = result.get('error', '')
            if "10분" in error_msg:
                print(f"   💡 해결방법: 조회 범위를 10분 이내로 줄이세요")
            elif "권한" in error_msg or "인증" in error_msg:
                print(f"   💡 해결방법: API 키와 판매자 ID를 확인하세요")
            elif "형식" in error_msg:
                print(f"   💡 해결방법: 날짜 형식을 'yyyy-MM-ddTHH:mm:ss'로 확인하세요")
        
        print(f"\n💡 시간 구간 조회 활용 방안:")
        print(f"   🔍 실시간 모니터링: 최근 등록 상품 추적")
        print(f"   📊 패턴 분석: 시간대별 등록 활동 파악")
        print(f"   🚨 알림 시스템: 특정 시간대 등록 알림")
        print(f"   📈 트렌드 추적: 등록 활동의 시간적 변화")
        print(f"   🔄 배치 처리: 특정 시간대 상품 일괄 처리")
                
    except ValueError as e:
        print(f"❌ 검증 오류: {e}")
    except Exception as e:
        print(f"❌ 시간 구간 조회 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 쿠팡 상품 등록 API 예제 시작")
    print("=" * 120)
    
    try:
        # 기본 상품 등록 테스트
        test_basic_product_creation()
        
        # 카테고리 추천 테스트
        test_category_recommendation()
        
        # 복잡한 상품 등록 테스트
        test_complex_product_creation()
        
        # 검증 시나리오 테스트
        test_validation_scenarios()
        
        # 상품 조회 테스트
        test_product_get()
        
        # 상품 조회 (승인불필요) 테스트
        test_product_partial_get()
        
        # 상품 수정 테스트
        test_product_update()
        
        # 상품 부분 수정 (승인불필요) 테스트
        test_product_partial_update()
        
        # 상품 승인 요청 테스트
        test_product_approval()
        
        # 지원 옵션 조회 테스트
        test_supported_options()
        
        # 상품 등록 현황 조회 테스트
        test_inflow_status()
        
        # 상품 목록 구간 조회 테스트
        test_time_frame_query()
        
        print(f"\n" + "=" * 50 + " 상품 등록 예제 완료 " + "=" * 50)
        print("✅ 모든 상품 등록 예제가 완료되었습니다!")
        
        print(f"\n🎉 확인된 기능들:")
        print("   1. ✅ 기본 상품 등록")
        print("   2. ✅ 카테고리 추천")
        print("   3. ✅ 다중 옵션 상품 등록")
        print("   4. ✅ 이미지 다중 등록")
        print("   5. ✅ 인증정보 등록")
        print("   6. ✅ 상품 속성 설정")
        print("   7. ✅ 고시정보 등록")
        print("   8. ✅ 상세 컨텐츠 등록")
        print("   9. ✅ 검색 태그 설정")
        print("  10. ✅ 조건부 무료배송 설정")
        print("  11. ✅ 상품 조회")
        print("  12. ✅ 상품 조회 (승인불필요)")
        print("  13. ✅ 상품 수정 (승인필요)")
        print("  14. ✅ 상품 부분 수정 (승인불필요)")
        print("  15. ✅ 상품 승인 요청")
        print("  16. ✅ 상품 등록 현황 조회")
        print("  17. ✅ 상품 목록 구간 조회 (시간 기준)")
        print("  18. ✅ 데이터 검증")
        
        print(f"\n💡 주요 확인사항:")
        print("   - 상품 등록은 카테고리/물류센터 API 연동 필요")
        print("   - 대표이미지(REPRESENTATION)는 필수")
        print("   - 아이템은 최소 1개 이상 필요")
        print("   - 카테고리별 필수 속성 확인 필요")
        print("   - 고시정보는 카테고리에 따라 달라짐")
        print("   - 배송비 종류에 따른 설정값 주의")
        print("   - 이미지는 3MB 이하 정사각형(500x500~5000x5000)")
        
    except Exception as e:
        print(f"\n❌ 상품 등록 예제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()