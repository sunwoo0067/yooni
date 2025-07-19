#!/usr/bin/env python3
"""
쿠팡 파트너스 API - 상품 관련 검증 함수들
"""

import re
from datetime import datetime
from typing import List

from .models import ProductRequest, ProductSearchParams, ProductPartialUpdateRequest, ProductStatusHistoryParams
from .constants import (
    DELIVERY_METHODS, DELIVERY_CHARGE_TYPES, PRODUCT_STATUS,
    MAX_SELLER_PRODUCT_NAME_LENGTH, MAX_PAGE_SIZE, MIN_PAGE_SIZE,
    MAX_TIME_FRAME_MINUTES, DATE_PATTERN, DATETIME_PATTERN
)


def validate_product_request(request: ProductRequest):
    """상품 등록 요청 데이터 검증"""
    # 필수 필드 검증
    if not request.display_category_code:
        raise ValueError("노출카테고리코드는 필수입니다")
    if not request.seller_product_name.strip():
        raise ValueError("등록상품명은 필수입니다")
    if not request.vendor_id.strip():
        raise ValueError("업체코드는 필수입니다")
    if not request.vendor_user_id.strip():
        raise ValueError("쿠팡Wing ID는 필수입니다")
    
    # 배송방법 검증
    if request.delivery_method not in DELIVERY_METHODS:
        raise ValueError(f"지원하지 않는 배송방법입니다: {request.delivery_method}")
    
    # 배송비 종류 검증
    if request.delivery_charge_type not in DELIVERY_CHARGE_TYPES:
        raise ValueError(f"지원하지 않는 배송비 종류입니다: {request.delivery_charge_type}")
    
    # 아이템 검증
    if not request.items:
        raise ValueError("최소 1개 이상의 아이템이 필요합니다")
    
    # 대표 이미지 검증
    if not request.images:
        raise ValueError("최소 1개 이상의 이미지가 필요합니다")
    
    representation_image_exists = any(
        img.image_type == "REPRESENTATION" for img in request.images
    )
    if not representation_image_exists:
        raise ValueError("대표 이미지(REPRESENTATION)는 필수입니다")
    
    # 아이템별 상세 검증
    for item in request.items:
        validate_product_item(item)


def validate_product_item(item):
    """상품 아이템 검증"""
    if not item.item_name.strip():
        raise ValueError("아이템명은 필수입니다")
    if item.original_price <= 0:
        raise ValueError("정가는 0보다 커야 합니다")
    if item.sale_price <= 0:
        raise ValueError("판매가는 0보다 커야 합니다")
    if item.sale_price > item.original_price:
        raise ValueError("판매가는 정가보다 클 수 없습니다")
    if item.maximum_buy_count <= 0:
        raise ValueError("판매가능수량은 0보다 커야 합니다")
    if item.maximum_buy_for_person <= 0:
        raise ValueError("인당최대구매수량은 0보다 커야 합니다")


def validate_product_update_request(request: ProductRequest):
    """상품 수정 요청 데이터 검증"""
    # 필수 필드 검증 (수정 시)
    if request.seller_product_id is None:
        raise ValueError("상품 수정 시 등록상품ID(seller_product_id)는 필수입니다")
    if not request.display_category_code:
        raise ValueError("노출카테고리코드는 필수입니다")
    if not request.seller_product_name.strip():
        raise ValueError("등록상품명은 필수입니다")
    if not request.vendor_id.strip():
        raise ValueError("업체코드는 필수입니다")
    if not request.vendor_user_id.strip():
        raise ValueError("쿠팡Wing ID는 필수입니다")
    
    # 배송방법 검증
    if request.delivery_method not in DELIVERY_METHODS:
        raise ValueError(f"지원하지 않는 배송방법입니다: {request.delivery_method}")
    
    # 배송비 종류 검증
    if request.delivery_charge_type not in DELIVERY_CHARGE_TYPES:
        raise ValueError(f"지원하지 않는 배송비 종류입니다: {request.delivery_charge_type}")
    
    # 아이템 검증
    if not request.items:
        raise ValueError("최소 1개 이상의 아이템이 필요합니다")
    
    # 아이템별 상세 검증
    for item in request.items:
        validate_product_item(item)


def validate_product_partial_update_request(request: ProductPartialUpdateRequest):
    """상품 부분 수정 요청 데이터 검증"""
    # 필수 필드 검증
    if not request.seller_product_id:
        raise ValueError("등록상품ID는 필수입니다")
    
    # 배송방법 검증 (값이 있는 경우만)
    if request.delivery_method is not None and request.delivery_method not in DELIVERY_METHODS:
        raise ValueError(f"지원하지 않는 배송방법입니다: {request.delivery_method}")
    
    # 배송비 종류 검증 (값이 있는 경우만)
    if request.delivery_charge_type is not None and request.delivery_charge_type not in DELIVERY_CHARGE_TYPES:
        raise ValueError(f"지원하지 않는 배송비 종류입니다: {request.delivery_charge_type}")
    
    # 배송비 검증 (값이 있는 경우만)
    if request.delivery_charge is not None and request.delivery_charge < 0:
        raise ValueError("기본배송비는 0 이상이어야 합니다")
    if request.delivery_charge_on_return is not None and request.delivery_charge_on_return < 0:
        raise ValueError("초도반품배송비는 0 이상이어야 합니다")
    if request.free_ship_over_amount is not None and request.free_ship_over_amount < 0:
        raise ValueError("무료배송 조건 금액은 0 이상이어야 합니다")
    if request.return_charge is not None and request.return_charge < 0:
        raise ValueError("반품배송비는 0 이상이어야 합니다")
    if request.outbound_shipping_time_day is not None and request.outbound_shipping_time_day < 0:
        raise ValueError("기준출고일은 0 이상이어야 합니다")


def validate_product_search_params(params: ProductSearchParams):
    """상품 목록 검색 파라미터 검증"""
    # 필수 필드 검증
    if not params.vendor_id.strip():
        raise ValueError("판매자 ID(vendor_id)는 필수입니다")
    
    # 페이지당 건수 검증
    if params.max_per_page is not None:
        if params.max_per_page < MIN_PAGE_SIZE or params.max_per_page > MAX_PAGE_SIZE:
            raise ValueError(f"페이지당 건수는 {MIN_PAGE_SIZE}-{MAX_PAGE_SIZE} 사이여야 합니다")
    
    # 등록상품명 길이 검증
    if params.seller_product_name is not None and len(params.seller_product_name) > MAX_SELLER_PRODUCT_NAME_LENGTH:
        raise ValueError(f"등록상품명은 {MAX_SELLER_PRODUCT_NAME_LENGTH}자 이하여야 합니다")
    
    # 상품 상태 검증
    if params.status is not None and params.status not in PRODUCT_STATUS:
        raise ValueError(f"지원하지 않는 상품상태입니다: {params.status}")
    
    # 날짜 형식 검증
    if params.created_at is not None:
        if not re.match(DATE_PATTERN, params.created_at):
            raise ValueError("상품등록일시는 'yyyy-MM-dd' 형식이어야 합니다")


def validate_time_frame_params(vendor_id: str, created_at_from: str, created_at_to: str):
    """시간 구간 조회 파라미터 검증"""
    # 필수 필드 검증
    if not vendor_id.strip():
        raise ValueError("판매자 ID(vendor_id)는 필수입니다")
    if not created_at_from.strip():
        raise ValueError("생성 시작일시(created_at_from)는 필수입니다")
    if not created_at_to.strip():
        raise ValueError("생성 종료일시(created_at_to)는 필수입니다")
    
    # 날짜 형식 검증
    if not re.match(DATETIME_PATTERN, created_at_from):
        raise ValueError("생성 시작일시는 'yyyy-MM-ddTHH:mm:ss' 형식이어야 합니다")
    if not re.match(DATETIME_PATTERN, created_at_to):
        raise ValueError("생성 종료일시는 'yyyy-MM-ddTHH:mm:ss' 형식이어야 합니다")
    
    # 시간 범위 검증 (최대 10분)
    time_range_minutes = calculate_time_range_minutes(created_at_from, created_at_to)
    if time_range_minutes > MAX_TIME_FRAME_MINUTES:
        raise ValueError(f"검색 허용 범위를 초과했습니다. 최대 허용 범위는 {MAX_TIME_FRAME_MINUTES}분입니다. (현재: {time_range_minutes}분)")
    if time_range_minutes < 0:
        raise ValueError("생성 종료일시는 시작일시보다 늦어야 합니다")


def calculate_time_range_minutes(created_at_from: str, created_at_to: str) -> float:
    """시간 범위를 분 단위로 계산"""
    try:
        start_time = datetime.fromisoformat(created_at_from)
        end_time = datetime.fromisoformat(created_at_to)
        time_diff = end_time - start_time
        return time_diff.total_seconds() / 60
    except ValueError as e:
        raise ValueError(f"날짜 형식 파싱 오류: {e}")


def validate_product_status_history_params(params: ProductStatusHistoryParams):
    """상품 상태변경이력 조회 파라미터 검증"""
    # 필수 필드 검증
    if not params.seller_product_id:
        raise ValueError("등록상품ID(seller_product_id)는 필수입니다")
    if params.seller_product_id <= 0:
        raise ValueError("등록상품ID는 0보다 큰 숫자여야 합니다")
    
    # 페이지당 건수 검증
    if params.max_per_page is not None:
        if params.max_per_page < MIN_PAGE_SIZE or params.max_per_page > MAX_PAGE_SIZE:
            raise ValueError(f"페이지당 건수는 {MIN_PAGE_SIZE}-{MAX_PAGE_SIZE} 사이여야 합니다")


def validate_external_vendor_sku_code(external_vendor_sku_code: str):
    """판매자 상품코드(externalVendorSkuCode) 검증"""
    # 필수 필드 검증
    if not external_vendor_sku_code:
        raise ValueError("판매자 상품코드(external_vendor_sku_code)는 필수입니다")
    if not external_vendor_sku_code.strip():
        raise ValueError("판매자 상품코드는 공백일 수 없습니다")
    
    # 길이 검증 (일반적으로 1-100자 사이)
    if len(external_vendor_sku_code.strip()) > 100:
        raise ValueError("판매자 상품코드는 100자 이하여야 합니다")
    
    # 특수문자 검증 (기본적인 영숫자, 하이픈, 언더스코어만 허용)
    import re
    if not re.match(r'^[a-zA-Z0-9\-_]+$', external_vendor_sku_code.strip()):
        raise ValueError("판매자 상품코드는 영문, 숫자, 하이픈(-), 언더스코어(_)만 사용 가능합니다")


def validate_vendor_item_id(vendor_item_id: int):
    """벤더아이템ID(vendorItemId) 검증"""
    # 필수 필드 검증
    if vendor_item_id is None:
        raise ValueError("벤더아이템ID(vendor_item_id)는 필수입니다")
    
    # 타입 검증
    if not isinstance(vendor_item_id, int):
        try:
            vendor_item_id = int(vendor_item_id)
        except (ValueError, TypeError):
            raise ValueError("벤더아이템ID는 숫자여야 합니다")
    
    # 범위 검증
    if vendor_item_id <= 0:
        raise ValueError("벤더아이템ID는 0보다 큰 숫자여야 합니다")
    
    # 실제 쿠팡 벤더아이템ID는 보통 10자리 정도의 큰 숫자
    if vendor_item_id > 9999999999999:  # 13자리 이상은 비현실적
        raise ValueError("벤더아이템ID가 유효 범위를 벗어났습니다")


def validate_quantity(quantity: int):
    """재고수량 검증"""
    # 필수 필드 검증
    if quantity is None:
        raise ValueError("재고수량(quantity)은 필수입니다")
    
    # 타입 검증
    if not isinstance(quantity, int):
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            raise ValueError("재고수량은 숫자여야 합니다")
    
    # 범위 검증
    if quantity < 0:
        raise ValueError("재고수량은 0 이상이어야 합니다")
    
    # 최대값 검증 (일반적으로 999999개 이하)
    if quantity > 999999:
        raise ValueError("재고수량은 999,999개 이하여야 합니다")


def validate_price(price: int):
    """가격 검증"""
    # 필수 필드 검증
    if price is None:
        raise ValueError("가격(price)은 필수입니다")
    
    # 타입 검증
    if not isinstance(price, int):
        try:
            price = int(price)
        except (ValueError, TypeError):
            raise ValueError("가격은 숫자여야 합니다")
    
    # 범위 검증
    if price < 0:
        raise ValueError("가격은 0원 이상이어야 합니다")
    
    # 10원 단위 검증
    if price % 10 != 0:
        raise ValueError("가격은 최소 10원 단위로 입력가능합니다 (1원 단위 입력 불가)")
    
    # 최대값 검증 (1억원 이하로 제한)
    if price > 100000000:
        raise ValueError("가격은 1억원 이하여야 합니다")


def validate_original_price(original_price: int):
    """할인율 기준가격 검증"""
    # 필수 필드 검증
    if original_price is None:
        raise ValueError("할인율 기준가격(original_price)은 필수입니다")
    
    # 타입 검증
    if not isinstance(original_price, int):
        try:
            original_price = int(original_price)
        except (ValueError, TypeError):
            raise ValueError("할인율 기준가격은 숫자여야 합니다")
    
    # 범위 검증 (0원부터 가능)
    if original_price < 0:
        raise ValueError("할인율 기준가격은 0원 이상이어야 합니다")
    
    # 10원 단위 검증
    if original_price % 10 != 0:
        raise ValueError("할인율 기준가격은 최소 10원 단위로 입력가능합니다 (1원 단위 입력 불가)")
    
    # 최대값 검증 (1억원 이하로 제한)
    if original_price > 100000000:
        raise ValueError("할인율 기준가격은 1억원 이하여야 합니다")


def validate_vendor_id(vendor_id: str) -> bool:
    """판매자 ID 형식 검증"""
    if not vendor_id:
        return False
    # 쿠팡 판매자 ID는 보통 A + 8자리 숫자 형태
    return len(vendor_id) >= 5 and vendor_id.startswith('A')


def validate_image_requirements(images: List) -> List[str]:
    """이미지 요구사항 검증 및 오류 목록 반환"""
    errors = []
    
    if not images:
        errors.append("최소 1개 이상의 이미지가 필요합니다")
        return errors
    
    # 대표 이미지 확인
    representation_count = sum(1 for img in images if img.image_type == "REPRESENTATION")
    if representation_count == 0:
        errors.append("대표 이미지(REPRESENTATION)는 필수입니다")
    elif representation_count > 1:
        errors.append("대표 이미지(REPRESENTATION)는 1개만 등록 가능합니다")
    
    # 이미지 순서 검증
    image_orders = [img.image_order for img in images]
    if len(set(image_orders)) != len(image_orders):
        errors.append("이미지 순서(image_order)는 중복될 수 없습니다")
    
    return errors


def validate_search_tags(search_tags: List[str]) -> List[str]:
    """검색 태그 검증 및 오류 목록 반환"""
    errors = []
    
    if len(search_tags) > 10:
        errors.append("검색 태그는 최대 10개까지 등록 가능합니다")
    
    for tag in search_tags:
        if not tag.strip():
            errors.append("빈 검색 태그는 등록할 수 없습니다")
        elif len(tag) > 50:
            errors.append(f"검색 태그는 50자 이하여야 합니다: '{tag[:20]}...'")
    
    return errors