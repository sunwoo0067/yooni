#!/usr/bin/env python3
"""
API 통합 테스트
"""
import pytest
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# API 엔드포인트
FRONTEND_API = "http://localhost:3000/api"
BACKEND_API = "http://localhost:8001"
MONITORING_API = "http://localhost:8000"
WS_URL = "ws://localhost:8002"


class TestAPIIntegration:
    """전체 API 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_health_check_all_services(self):
        """모든 서비스 헬스 체크"""
        async with aiohttp.ClientSession() as session:
            # Backend services
            services = [
                (BACKEND_API, "/health"),
                (MONITORING_API, "/health"),
                (FRONTEND_API, "/health")
            ]
            
            for base_url, endpoint in services:
                async with session.get(f"{base_url}{endpoint}") as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data.get("status") in ["healthy", "ok"]
    
    @pytest.mark.asyncio
    async def test_monitoring_metrics_flow(self):
        """모니터링 메트릭 흐름 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. Get current metrics
            async with session.get(f"{MONITORING_API}/metrics") as response:
                assert response.status == 200
                metrics = await response.json()
                assert "stats" in metrics
                assert "recent_alerts" in metrics
            
            # 2. Connect to WebSocket
            ws_session = aiohttp.ClientSession()
            ws = await ws_session.ws_connect(WS_URL)
            
            try:
                # Wait for metrics update
                msg = await asyncio.wait_for(ws.receive(), timeout=10)
                assert msg.type == aiohttp.WSMsgType.TEXT
                data = json.loads(msg.data)
                assert data["type"] == "update"
                assert "data" in data
            finally:
                await ws.close()
                await ws_session.close()
    
    @pytest.mark.asyncio
    async def test_product_workflow(self):
        """상품 관리 워크플로우 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. Create product
            product_data = {
                "name": "Test Product",
                "sku": f"TEST-{datetime.now().timestamp()}",
                "price": 10000,
                "stock": 100,
                "supplier": "test_supplier"
            }
            
            async with session.post(
                f"{FRONTEND_API}/products",
                json=product_data
            ) as response:
                assert response.status == 201
                product = await response.json()
                product_id = product["id"]
            
            # 2. Update stock
            async with session.put(
                f"{FRONTEND_API}/products/{product_id}/stock",
                json={"quantity": 50}
            ) as response:
                assert response.status == 200
            
            # 3. Get product details
            async with session.get(
                f"{FRONTEND_API}/products/{product_id}"
            ) as response:
                assert response.status == 200
                product = await response.json()
                assert product["stock"] == 50
    
    @pytest.mark.asyncio
    async def test_order_processing_flow(self):
        """주문 처리 흐름 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. Create order
            order_data = {
                "customer_id": "TEST-CUSTOMER-001",
                "items": [
                    {
                        "product_id": "TEST-PRODUCT-001",
                        "quantity": 2,
                        "price": 10000
                    }
                ],
                "total_amount": 20000,
                "status": "pending"
            }
            
            async with session.post(
                f"{FRONTEND_API}/orders",
                json=order_data
            ) as response:
                assert response.status == 201
                order = await response.json()
                order_id = order["id"]
            
            # 2. Process order
            async with session.post(
                f"{FRONTEND_API}/orders/{order_id}/process"
            ) as response:
                assert response.status == 200
            
            # 3. Check order status
            async with session.get(
                f"{FRONTEND_API}/orders/{order_id}"
            ) as response:
                assert response.status == 200
                order = await response.json()
                assert order["status"] in ["processing", "confirmed"]
    
    @pytest.mark.asyncio
    async def test_log_aggregation(self):
        """로그 집계 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. Generate some logs
            log_data = {
                "level": "INFO",
                "message": "Integration test log",
                "source": "test_suite",
                "metadata": {
                    "test_id": "integration-001",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            async with session.post(
                f"{FRONTEND_API}/logs",
                json=log_data
            ) as response:
                assert response.status == 201
            
            # 2. Query logs
            params = {
                "level": "INFO",
                "source": "test_suite",
                "limit": 10
            }
            
            async with session.get(
                f"{FRONTEND_API}/logs",
                params=params
            ) as response:
                assert response.status == 200
                logs = await response.json()
                assert len(logs["items"]) > 0
                assert any(
                    log["message"] == "Integration test log" 
                    for log in logs["items"]
                )
    
    @pytest.mark.asyncio
    async def test_cross_service_event_flow(self):
        """서비스 간 이벤트 흐름 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. 재고 부족 이벤트 발행
            event_data = {
                "event_type": "inventory.low_stock",
                "event_source": "inventory_service",
                "data": {
                    "product_id": "TEST-PRODUCT-002",
                    "current_stock": 5,
                    "threshold": 10
                }
            }
            
            async with session.post(
                f"{BACKEND_API}/emit-event",
                json=event_data
            ) as response:
                assert response.status == 200
            
            # 2. 알림 확인 (잠시 대기)
            await asyncio.sleep(2)
            
            # 3. 모니터링 알림 확인
            async with session.get(
                f"{MONITORING_API}/alerts/recent"
            ) as response:
                assert response.status == 200
                alerts = await response.json()
                # 재고 부족 알림이 생성되었는지 확인
                recent_alert = any(
                    alert.get("type") == "low_stock" 
                    for alert in alerts
                )
                assert recent_alert
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """성능 메트릭 테스트"""
        async with aiohttp.ClientSession() as session:
            # Multiple concurrent requests
            tasks = []
            
            for i in range(10):
                task = session.get(f"{FRONTEND_API}/products")
                tasks.append(task)
            
            start_time = datetime.now()
            responses = await asyncio.gather(*tasks)
            end_time = datetime.now()
            
            # Check all requests succeeded
            for response in responses:
                assert response.status == 200
                response.close()
            
            # Check response time
            total_time = (end_time - start_time).total_seconds()
            avg_time = total_time / 10
            
            # Average response time should be under 500ms
            assert avg_time < 0.5