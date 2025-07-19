#!/usr/bin/env python3
"""
End-to-End 시나리오 테스트
"""
import pytest
import asyncio
import aiohttp
import psycopg2
from datetime import datetime, timedelta
import json

# 설정
FRONTEND_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8001"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni_test',
    'user': 'postgres',
    'password': '1234'
}


class TestE2EScenarios:
    """End-to-End 시나리오 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 설정"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        yield
        self.cursor.close()
        self.conn.close()
    
    @pytest.mark.asyncio
    async def test_complete_order_fulfillment_flow(self):
        """주문 처리 전체 프로세스 E2E 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. 상품 등록
            product_data = {
                "name": "E2E Test Product",
                "sku": f"E2E-{int(datetime.now().timestamp())}",
                "price": 15000,
                "stock": 50,
                "supplier": "ownerclan",
                "category": "test"
            }
            
            async with session.post(
                f"{FRONTEND_URL}/api/products",
                json=product_data
            ) as response:
                assert response.status == 201
                product = await response.json()
                product_id = product["id"]
            
            # 2. 주문 생성
            order_data = {
                "customer_id": "E2E-CUSTOMER-001",
                "customer_name": "E2E Test Customer",
                "items": [
                    {
                        "product_id": product_id,
                        "quantity": 3,
                        "price": 15000
                    }
                ],
                "shipping_address": "서울시 강남구 테스트로 123",
                "total_amount": 45000
            }
            
            async with session.post(
                f"{FRONTEND_URL}/api/orders",
                json=order_data
            ) as response:
                assert response.status == 201
                order = await response.json()
                order_id = order["id"]
            
            # 3. 주문 처리 워크플로우 트리거
            event_data = {
                "event_type": "order.created",
                "event_source": "e2e_test",
                "data": {
                    "order_id": order_id,
                    "total_amount": 45000
                }
            }
            
            async with session.post(
                f"{API_BASE_URL}/emit-event",
                json=event_data
            ) as response:
                assert response.status == 200
            
            # 4. 재고 확인
            await asyncio.sleep(2)  # 워크플로우 처리 대기
            
            async with session.get(
                f"{FRONTEND_URL}/api/products/{product_id}"
            ) as response:
                assert response.status == 200
                updated_product = await response.json()
                # 재고가 감소했는지 확인
                assert updated_product["stock"] == 47  # 50 - 3
            
            # 5. 모니터링 메트릭 확인
            async with session.get(
                "http://localhost:8000/metrics"
            ) as response:
                assert response.status == 200
                metrics = await response.json()
                # 주문 처리 메트릭이 업데이트되었는지 확인
                assert metrics["stats"]["total_orders"] > 0
    
    @pytest.mark.asyncio
    async def test_inventory_alert_workflow(self):
        """재고 부족 알림 워크플로우 E2E 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. 재고 부족 알림 워크플로우 생성
            workflow_data = {
                "name": "E2E Low Stock Alert",
                "description": "E2E 테스트용 재고 부족 알림",
                "trigger_type": "event",
                "config": {
                    "event_type": "inventory.low_stock",
                    "event_source": "inventory_monitor"
                },
                "rules": [
                    {
                        "condition_type": "threshold",
                        "condition_config": {
                            "field": "stock_quantity",
                            "operator": "<=",
                            "value": 10
                        },
                        "action_type": "database_update",
                        "action_config": {
                            "table": "inventory_alerts",
                            "set": {
                                "product_id": "{{product_id}}",
                                "alert_type": "low_stock",
                                "created_at": "NOW()"
                            }
                        }
                    }
                ]
            }
            
            async with session.post(
                f"{FRONTEND_URL}/api/workflow",
                json=workflow_data
            ) as response:
                assert response.status == 200
                result = await response.json()
                workflow_id = result["workflow_id"]
            
            # 2. 낮은 재고 상품 생성
            product_data = {
                "name": "Low Stock Product",
                "sku": f"LOW-{int(datetime.now().timestamp())}",
                "price": 20000,
                "stock": 8,  # 임계치 이하
                "supplier": "zentrade"
            }
            
            async with session.post(
                f"{FRONTEND_URL}/api/products",
                json=product_data
            ) as response:
                assert response.status == 201
                product = await response.json()
                product_id = product["id"]
            
            # 3. 재고 부족 이벤트 발행
            event_data = {
                "event_type": "inventory.low_stock",
                "event_source": "inventory_monitor",
                "data": {
                    "product_id": product_id,
                    "stock_quantity": 8,
                    "threshold": 10
                }
            }
            
            async with session.post(
                f"{API_BASE_URL}/emit-event",
                json=event_data
            ) as response:
                assert response.status == 200
            
            # 4. 알림 생성 확인
            await asyncio.sleep(2)
            
            # 데이터베이스에서 알림 확인
            self.cursor.execute("""
                SELECT COUNT(*) FROM inventory_alerts
                WHERE product_id = %s AND alert_type = 'low_stock'
            """, (product_id,))
            
            alert_count = self.cursor.fetchone()[0]
            assert alert_count > 0
    
    @pytest.mark.asyncio
    async def test_daily_report_generation(self):
        """일일 리포트 생성 E2E 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. 일일 리포트 워크플로우 생성 (수동 트리거)
            workflow_data = {
                "name": "E2E Daily Report",
                "description": "E2E 테스트용 일일 리포트",
                "trigger_type": "manual",
                "config": {},
                "rules": [
                    {
                        "condition_type": "always",
                        "condition_config": {},
                        "action_type": "api_call",
                        "action_config": {
                            "endpoint": f"{FRONTEND_URL}/api/reports/daily",
                            "method": "POST",
                            "params": {
                                "date": "{{trigger_date}}",
                                "type": "sales"
                            }
                        }
                    }
                ]
            }
            
            async with session.post(
                f"{FRONTEND_URL}/api/workflow",
                json=workflow_data
            ) as response:
                assert response.status == 200
                result = await response.json()
                workflow_id = result["workflow_id"]
            
            # 2. 테스트 데이터 생성 (주문 데이터)
            for i in range(5):
                order_data = {
                    "customer_id": f"REPORT-CUSTOMER-{i}",
                    "items": [{"product_id": "TEST-001", "quantity": 1, "price": 10000}],
                    "total_amount": 10000,
                    "created_at": datetime.now().isoformat()
                }
                
                async with session.post(
                    f"{FRONTEND_URL}/api/orders",
                    json=order_data
                ) as response:
                    assert response.status == 201
            
            # 3. 리포트 워크플로우 실행
            async with session.post(
                f"{API_BASE_URL}/execute-workflow",
                json={
                    "workflow_id": workflow_id,
                    "trigger_data": {
                        "trigger_date": datetime.now().strftime("%Y-%m-%d")
                    }
                }
            ) as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True
            
            # 4. 리포트 생성 확인
            await asyncio.sleep(3)
            
            async with session.get(
                f"{FRONTEND_URL}/api/reports/latest",
                params={"type": "daily_sales"}
            ) as response:
                assert response.status == 200
                report = await response.json()
                assert report is not None
                assert "total_sales" in report
                assert report["order_count"] >= 5
    
    @pytest.mark.asyncio
    async def test_multi_marketplace_sync(self):
        """멀티 마켓플레이스 동기화 E2E 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. 멀티 마켓 상품 등록
            marketplaces = ["coupang", "ownerclan", "zentrade"]
            product_ids = {}
            
            for marketplace in marketplaces:
                product_data = {
                    "name": f"Multi Market Product - {marketplace}",
                    "sku": f"MULTI-{marketplace}-{int(datetime.now().timestamp())}",
                    "price": 25000,
                    "stock": 100,
                    "supplier": marketplace,
                    "marketplace": marketplace
                }
                
                async with session.post(
                    f"{FRONTEND_URL}/api/products",
                    json=product_data
                ) as response:
                    assert response.status == 201
                    product = await response.json()
                    product_ids[marketplace] = product["id"]
            
            # 2. 가격 동기화 워크플로우 실행
            sync_data = {
                "action": "sync_prices",
                "base_marketplace": "coupang",
                "target_marketplaces": ["ownerclan", "zentrade"],
                "product_mapping": product_ids
            }
            
            async with session.post(
                f"{FRONTEND_URL}/api/sync/prices",
                json=sync_data
            ) as response:
                assert response.status == 200
            
            # 3. 가격 동기화 확인
            await asyncio.sleep(2)
            
            base_price = None
            for marketplace, product_id in product_ids.items():
                async with session.get(
                    f"{FRONTEND_URL}/api/products/{product_id}"
                ) as response:
                    assert response.status == 200
                    product = await response.json()
                    
                    if marketplace == "coupang":
                        base_price = product["price"]
                    else:
                        # 다른 마켓플레이스의 가격이 동기화되었는지 확인
                        assert product["price"] == base_price