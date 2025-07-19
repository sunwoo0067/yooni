#!/usr/bin/env python3
"""
마켓 매니저 사용 예제
"""
from market_manager import MarketBase, MarketProduct, MarketOrder, MarketSync
from datetime import datetime, timedelta

def setup_market_accounts():
    """마켓 계정 설정"""
    base = MarketBase()
    
    # 쿠팡 계정 설정
    coupang_account = {
        'account_name': '메인계정',
        'api_key': 'your_access_key',
        'api_secret': 'your_secret_key',
        'vendor_id': 'A00123456',
        'extra_config': {
            'use_sandbox': False,
            'api_version': 'v2'
        }
    }
    account_id = base.create_market_account('coupang', coupang_account)
    print(f"쿠팡 계정 생성: ID={account_id}")
    
    # 네이버 계정 설정
    naver_account = {
        'account_name': '스마트스토어1',
        'api_key': 'your_client_id',
        'api_secret': 'your_client_secret',
        'extra_config': {
            'channel_id': 'your_channel_id'
        }
    }
    account_id = base.create_market_account('naver', naver_account)
    print(f"네이버 계정 생성: ID={account_id}")
    
    base.close()

def test_product_management():
    """상품 관리 테스트"""
    product_mgr = MarketProduct()
    
    # 쿠팡 상품 저장
    coupang_product = {
        'market_product_id': 'CP123456',
        'product_name': '테스트 상품 - 쿠팡',
        'brand': '테스트 브랜드',
        'manufacturer': '테스트 제조사',
        'original_price': 50000,
        'sale_price': 35000,
        'status': 'active',
        'stock_quantity': 100,
        'category_code': '12345',
        'category_name': '의류/잡화',
        'shipping_type': 'free',
        'market_data': {
            'sellerProductId': 'CP123456',
            'vendorItemId': 'VI123456',
            'displayCategoryCode': '12345'
        }
    }
    
    product_id = product_mgr.save_product('coupang', '메인계정', coupang_product)
    print(f"쿠팡 상품 저장: ID={product_id}")
    
    # 재고 업데이트
    product_mgr.update_stock('coupang', '메인계정', 'CP123456', 80)
    print("재고 업데이트 완료: 80개")
    
    # 가격 업데이트
    product_mgr.update_price('coupang', '메인계정', 'CP123456', 32000, 50000)
    print("가격 업데이트 완료: 32,000원")
    
    # 상품 조회
    products = product_mgr.get_products('coupang', '메인계정', status='active')
    print(f"\n활성 상품 목록 ({len(products)}개):")
    for product in products[:5]:
        print(f"- {product['product_name']} (재고: {product['stock_quantity']})")
    
    # 재고 부족 상품 조회
    low_stock = product_mgr.get_low_stock_products(threshold=10)
    print(f"\n재고 부족 상품 ({len(low_stock)}개):")
    for product in low_stock:
        print(f"- [{product['market_name']}] {product['product_name']} (재고: {product['stock_quantity']})")
    
    product_mgr.close()

def test_order_management():
    """주문 관리 테스트"""
    order_mgr = MarketOrder()
    
    # 쿠팡 주문 저장
    coupang_order = {
        'market_order_id': 'ORD123456789',
        'order_date': datetime.now(),
        'payment_date': datetime.now(),
        'buyer_name': '홍길동',
        'buyer_email': 'test@example.com',
        'buyer_phone': '010-1234-5678',
        'receiver_name': '홍길동',
        'receiver_phone': '010-1234-5678',
        'receiver_address': '서울시 강남구 테헤란로 123',
        'receiver_zipcode': '12345',
        'delivery_message': '부재시 경비실에 맡겨주세요',
        'order_status': 'confirmed',
        'payment_method': 'CARD',
        'total_price': 35000,
        'product_price': 32000,
        'shipping_fee': 3000,
        'items': [
            {
                'market_product_id': 'CP123456',
                'product_name': '테스트 상품',
                'option_name': '블랙/L',
                'quantity': 1,
                'unit_price': 32000,
                'total_price': 32000,
                'item_status': 'pending'
            }
        ],
        'market_data': {
            'orderId': 'ORD123456789',
            'orderedAt': '2024-01-01T10:00:00Z'
        }
    }
    
    order_id = order_mgr.save_order('coupang', '메인계정', coupang_order)
    print(f"쿠팡 주문 저장: ID={order_id}")
    
    # 송장 번호 업데이트
    order_mgr.update_tracking('coupang', '메인계정', 'ORD123456789', 0, 
                             'CJ대한통운', '1234567890')
    print("송장 번호 업데이트 완료")
    
    # 주문 조회
    orders = order_mgr.get_orders('coupang', '메인계정', 
                                 date_from=datetime.now() - timedelta(days=7))
    print(f"\n최근 7일 주문 ({len(orders)}개):")
    for order in orders[:5]:
        print(f"- {order['market_order_id']} ({order['order_status']}) - {order['total_price']:,}원")
    
    # 배송 대기 주문 조회
    pending_shipments = order_mgr.get_pending_shipments('coupang')
    print(f"\n배송 대기 주문 ({len(pending_shipments)}개):")
    for shipment in pending_shipments[:5]:
        print(f"- {shipment['market_order_id']} / {shipment['product_name']} ({shipment['quantity']}개)")
    
    # 주문 통계
    stats = order_mgr.get_order_statistics('coupang', '메인계정',
                                         date_from=datetime.now() - timedelta(days=30))
    print(f"\n최근 30일 주문 통계:")
    print(f"- 총 주문: {stats['total_orders']}건")
    print(f"- 총 매출: {stats['total_revenue']:,}원")
    print(f"- 배송완료: {stats['delivered_orders']}건")
    print(f"- 취소/반품: {stats['cancelled_orders']}건")
    
    order_mgr.close()

def test_sync_management():
    """동기화 관리 테스트"""
    sync_mgr = MarketSync()
    
    # 동기화 상태 조회
    sync_status = sync_mgr.get_sync_status()
    print("마켓별 동기화 상태:")
    for status in sync_status:
        print(f"- [{status['market_name']}] {status['account_name']}")
        print(f"  상품: {status['product_count']}개 (최종동기화: {status['last_product_sync']})")
        print(f"  주문: {status['order_count']}개 (최종동기화: {status['last_order_sync']})")
    
    sync_mgr.close()

if __name__ == '__main__':
    print("=== 마켓 매니저 테스트 ===\n")
    
    # 1. 계정 설정 (최초 1회만)
    # setup_market_accounts()
    
    # 2. 상품 관리 테스트
    print("\n[상품 관리 테스트]")
    test_product_management()
    
    # 3. 주문 관리 테스트
    print("\n[주문 관리 테스트]")
    test_order_management()
    
    # 4. 동기화 상태 확인
    print("\n[동기화 상태 확인]")
    test_sync_management()