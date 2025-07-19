#!/usr/bin/env python3
"""
WebSocket 서버 - 실시간 모니터링을 위한 WebSocket 서버
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Any
import websockets
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import sys

sys.path.append('/home/sunwoo/yooni/backend')
from core import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5434,
            'database': 'yoonni',
            'user': 'postgres',
            'password': '1234'
        }
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """실시간 메트릭 수집"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'sales': self._get_sales_metrics(cursor),
                'orders': self._get_order_metrics(cursor),
                'inventory': self._get_inventory_metrics(cursor),
                'system': self._get_system_metrics(cursor),
                'api_status': self._get_api_status()
            }
            
            cursor.close()
            conn.close()
            
            return metrics
            
        except Exception as e:
            logger.error(f"메트릭 수집 오류: {e}")
            return {}
    
    def _get_sales_metrics(self, cursor) -> Dict[str, Any]:
        """매출 메트릭"""
        cursor.execute("""
            SELECT 
                COUNT(*) as today_orders,
                COALESCE(SUM(total_price), 0) as today_revenue,
                COUNT(DISTINCT buyer_email) as unique_customers
            FROM market_orders
            WHERE DATE(order_date) = CURRENT_DATE
        """)
        today = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                DATE(order_date) as date,
                COUNT(*) as orders,
                COALESCE(SUM(total_price), 0) as revenue
            FROM market_orders
            WHERE order_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(order_date)
            ORDER BY date
        """)
        weekly = cursor.fetchall()
        
        # 시간별 매출
        cursor.execute("""
            SELECT 
                EXTRACT(HOUR FROM order_date) as hour,
                COUNT(*) as orders,
                COALESCE(SUM(total_price), 0) as revenue
            FROM market_orders
            WHERE DATE(order_date) = CURRENT_DATE
            GROUP BY EXTRACT(HOUR FROM order_date)
            ORDER BY hour
        """)
        hourly = cursor.fetchall()
        
        return {
            'today': today,
            'weekly_trend': weekly,
            'hourly_trend': hourly
        }
    
    def _get_order_metrics(self, cursor) -> Dict[str, Any]:
        """주문 메트릭"""
        cursor.execute("""
            SELECT 
                order_status,
                COUNT(*) as count
            FROM market_orders
            WHERE DATE(order_date) >= CURRENT_DATE - INTERVAL '1 day'
            GROUP BY order_status
        """)
        status_counts = {row['order_status']: row['count'] for row in cursor.fetchall()}
        
        # 마켓별 주문
        cursor.execute("""
            SELECT 
                market_code,
                COUNT(*) as orders,
                COALESCE(SUM(total_price), 0) as revenue
            FROM market_orders
            WHERE DATE(order_date) = CURRENT_DATE
            GROUP BY market_code
        """)
        by_market = cursor.fetchall()
        
        return {
            'status_counts': status_counts,
            'by_market': by_market,
            'pending': status_counts.get('pending', 0),
            'processing': status_counts.get('processing', 0),
            'completed': status_counts.get('completed', 0)
        }
    
    def _get_inventory_metrics(self, cursor) -> Dict[str, Any]:
        """재고 메트릭"""
        cursor.execute("""
            SELECT 
                COUNT(*) as total_products,
                COUNT(*) FILTER (WHERE stock_quantity <= 10) as low_stock,
                COUNT(*) FILTER (WHERE stock_quantity = 0) as out_of_stock,
                COALESCE(SUM(stock_quantity * sale_price), 0) as inventory_value
            FROM unified_products
            WHERE status = 'active'
        """)
        inventory = cursor.fetchone()
        
        return inventory
    
    def _get_system_metrics(self, cursor) -> Dict[str, Any]:
        """시스템 메트릭"""
        # 최근 에러 수
        cursor.execute("""
            SELECT 
                level,
                COUNT(*) as count
            FROM system_logs
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
            GROUP BY level
        """)
        log_counts = {row['level']: row['count'] for row in cursor.fetchall()}
        
        # API 응답 시간
        cursor.execute("""
            SELECT 
                AVG(execution_time) as avg_response_time,
                MAX(execution_time) as max_response_time,
                COUNT(*) as total_requests
            FROM system_logs
            WHERE execution_time IS NOT NULL
            AND timestamp >= NOW() - INTERVAL '5 minutes'
        """)
        api_metrics = cursor.fetchone()
        
        # 스케줄러 상태
        cursor.execute("""
            SELECT 
                job_type,
                status,
                last_run_at,
                next_run_at
            FROM schedule_jobs
            WHERE status = 'active'
            ORDER BY next_run_at
            LIMIT 10
        """)
        scheduled_jobs = cursor.fetchall()
        
        return {
            'error_rate': log_counts.get('ERROR', 0) + log_counts.get('CRITICAL', 0),
            'warning_count': log_counts.get('WARNING', 0),
            'api_metrics': api_metrics,
            'scheduled_jobs': scheduled_jobs
        }
    
    def _get_api_status(self) -> Dict[str, Any]:
        """외부 API 상태 체크"""
        # Redis에서 캐시된 상태 가져오기
        api_status = {}
        
        for market in ['coupang', 'naver', '11st']:
            status_key = f"api_status:{market}"
            status = self.redis_client.get(status_key)
            
            if status:
                api_status[market] = json.loads(status)
            else:
                api_status[market] = {
                    'status': 'unknown',
                    'last_check': None,
                    'response_time': None
                }
        
        return api_status


class MonitoringWebSocketServer:
    """WebSocket 서버"""
    
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.metrics_collector = MetricsCollector()
        self.update_interval = 5  # 5초마다 업데이트
        
    async def register(self, websocket):
        """클라이언트 등록"""
        self.clients.add(websocket)
        logger.info(f"클라이언트 연결: {websocket.remote_address}")
        
        # 초기 데이터 전송
        metrics = self.metrics_collector.get_realtime_metrics()
        await websocket.send(json.dumps({
            'type': 'initial',
            'data': metrics
        }))
        
    async def unregister(self, websocket):
        """클라이언트 등록 해제"""
        self.clients.remove(websocket)
        logger.info(f"클라이언트 연결 해제: {websocket.remote_address}")
        
    async def send_to_all(self, message: Dict[str, Any]):
        """모든 클라이언트에 메시지 전송"""
        if self.clients:
            message_str = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_str) for client in self.clients],
                return_exceptions=True
            )
    
    async def handle_client(self, websocket, path):
        """클라이언트 핸들러"""
        await self.register(websocket)
        try:
            async for message in websocket:
                # 클라이언트 메시지 처리
                data = json.loads(message)
                
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                elif data.get('type') == 'subscribe':
                    # 특정 메트릭 구독
                    topic = data.get('topic')
                    logger.info(f"클라이언트 구독: {topic}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def broadcast_metrics(self):
        """주기적으로 메트릭 브로드캐스트"""
        while True:
            try:
                if self.clients:
                    metrics = self.metrics_collector.get_realtime_metrics()
                    await self.send_to_all({
                        'type': 'update',
                        'data': metrics
                    })
                    
            except Exception as e:
                logger.error(f"메트릭 브로드캐스트 오류: {e}")
                
            await asyncio.sleep(self.update_interval)
    
    async def start(self):
        """서버 시작"""
        logger.info(f"WebSocket 서버 시작: {self.host}:{self.port}")
        
        # 브로드캐스트 태스크 시작
        asyncio.create_task(self.broadcast_metrics())
        
        # WebSocket 서버 시작
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # 무한 대기


def main():
    """메인 함수"""
    server = MonitoringWebSocketServer()
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("서버 종료")


if __name__ == "__main__":
    main()