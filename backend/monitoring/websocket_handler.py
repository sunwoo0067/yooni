"""
웹소켓을 통한 실시간 메트릭 스트리밍
"""
import asyncio
import json
from typing import Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from .metrics_collector import get_metrics_collector
from ..core.structured_logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """웹소켓 연결 관리자"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriber_topics: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        """새 웹소켓 연결"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriber_topics[websocket] = set()
        logger.info(f"웹소켓 연결 수락: {len(self.active_connections)}개 활성 연결")
    
    def disconnect(self, websocket: WebSocket):
        """웹소켓 연결 해제"""
        self.active_connections.discard(websocket)
        self.subscriber_topics.pop(websocket, None)
        logger.info(f"웹소켓 연결 해제: {len(self.active_connections)}개 활성 연결")
    
    async def subscribe(self, websocket: WebSocket, topics: Set[str]):
        """토픽 구독"""
        self.subscriber_topics[websocket] = topics
        logger.info(f"웹소켓 토픽 구독: {topics}")
    
    async def unsubscribe(self, websocket: WebSocket, topics: Set[str]):
        """토픽 구독 해제"""
        if websocket in self.subscriber_topics:
            self.subscriber_topics[websocket] -= topics
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """개별 메시지 전송"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict, topic: str = None):
        """브로드캐스트 메시지"""
        disconnected = set()
        
        for websocket in self.active_connections:
            # 토픽 필터링
            if topic and topic not in self.subscriber_topics.get(websocket, set()):
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"브로드캐스트 실패: {e}")
                disconnected.add(websocket)
        
        # 실패한 연결 정리
        for websocket in disconnected:
            self.disconnect(websocket)


# 전역 연결 관리자
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """웹소켓 엔드포인트 핸들러"""
    await manager.connect(websocket)
    
    try:
        # 초기 메시지 전송
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # 메시지 수신 루프
        while True:
            data = await websocket.receive_json()
            
            # 명령 처리
            command = data.get("command")
            
            if command == "subscribe":
                topics = set(data.get("topics", []))
                await manager.subscribe(websocket, topics)
                
                await manager.send_personal_message({
                    "type": "subscription",
                    "status": "subscribed",
                    "topics": list(topics),
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            elif command == "unsubscribe":
                topics = set(data.get("topics", []))
                await manager.unsubscribe(websocket, topics)
                
                await manager.send_personal_message({
                    "type": "subscription",
                    "status": "unsubscribed",
                    "topics": list(topics),
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            elif command == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            elif command == "get_metrics":
                # 현재 메트릭 전송
                collector = get_metrics_collector()
                metrics = collector.get_metrics_summary(time_range_minutes=5)
                
                await manager.send_personal_message({
                    "type": "metrics",
                    "data": metrics,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"웹소켓 에러: {e}")
        manager.disconnect(websocket)


async def broadcast_metrics_updates():
    """주기적으로 메트릭 업데이트 브로드캐스트"""
    collector = get_metrics_collector()
    
    while True:
        try:
            # 시스템 메트릭 브로드캐스트
            system_metrics = {
                "type": "metrics_update",
                "topic": "system",
                "data": {
                    "cpu": collector.gauges.get("system.cpu.usage", 0),
                    "memory": collector.gauges.get("system.memory.usage", 0),
                    "disk": collector.gauges.get("system.disk.usage", 0)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.broadcast(system_metrics, "system")
            
            # API 메트릭 브로드캐스트
            api_metrics_summary = {}
            error_count = 0
            total_count = 0
            
            for key, value in collector.counters.items():
                if key.startswith("api.requests"):
                    total_count += value
                elif key.startswith("api.errors"):
                    error_count += value
            
            api_metrics = {
                "type": "metrics_update",
                "topic": "api",
                "data": {
                    "requestCount": total_count,
                    "errorCount": error_count,
                    "errorRate": (error_count / total_count * 100) if total_count > 0 else 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.broadcast(api_metrics, "api")
            
            # 데이터베이스 메트릭 브로드캐스트
            db_metrics = {
                "type": "metrics_update",
                "topic": "database",
                "data": {
                    "activeConnections": collector.gauges.get("database.pool.active", 0),
                    "availableConnections": collector.gauges.get("database.pool.available", 0)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.broadcast(db_metrics, "database")
            
            # 5초 대기
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"메트릭 브로드캐스트 에러: {e}")
            await asyncio.sleep(5)


# 브로드캐스트 태스크를 시작하는 함수
async def start_metrics_broadcast():
    """메트릭 브로드캐스트 시작"""
    asyncio.create_task(broadcast_metrics_updates())