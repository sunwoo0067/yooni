"""
이벤트 매니저 - 이벤트 기반 워크플로우 트리거 관리
"""
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

sys.path.append('/home/sunwoo/yooni/backend')
from core import get_logger
from workflow.engine import WorkflowEngine

logger = get_logger(__name__)


class EventManager:
    """이벤트 매니저"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.workflow_engine = WorkflowEngine(db_config)
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._pubsub = None
        self._running = False
        
    def start(self):
        """이벤트 리스너 시작"""
        if not self._running:
            self._running = True
            asyncio.create_task(self._listen_events())
            logger.info("이벤트 매니저 시작됨")
    
    def stop(self):
        """이벤트 리스너 중지"""
        self._running = False
        if self._pubsub:
            self._pubsub.unsubscribe()
            self._pubsub.close()
        logger.info("이벤트 매니저 중지됨")
    
    async def emit_event(self, event_type: str, event_source: str, data: Dict[str, Any]):
        """이벤트 발행"""
        event = {
            'type': event_type,
            'source': event_source,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Redis에 이벤트 발행
        channel = f"events:{event_source}:{event_type}"
        self.redis_client.publish(channel, json.dumps(event))
        
        # 이벤트 로그 저장
        self._log_event(event)
        
        logger.info(f"이벤트 발행: {channel}")
    
    async def _listen_events(self):
        """Redis 이벤트 리스닝"""
        self._pubsub = self.redis_client.pubsub()
        
        # 모든 이벤트 채널 구독
        self._pubsub.psubscribe('events:*')
        
        logger.info("이벤트 리스닝 시작")
        
        while self._running:
            try:
                message = self._pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'pmessage':
                    await self._handle_event(message)
            except Exception as e:
                logger.error(f"이벤트 리스닝 오류: {e}")
                await asyncio.sleep(5)
    
    async def _handle_event(self, message: Dict[str, Any]):
        """이벤트 처리"""
        try:
            # 채널에서 이벤트 타입과 소스 추출
            channel = message['channel'].decode() if isinstance(message['channel'], bytes) else message['channel']
            parts = channel.split(':')
            if len(parts) >= 3:
                event_source = parts[1]
                event_type = ':'.join(parts[2:])
            else:
                return
            
            # 이벤트 데이터 파싱
            event_data = json.loads(message['data'])
            
            logger.debug(f"이벤트 수신: {event_type} from {event_source}")
            
            # 이벤트 트리거 확인 및 워크플로우 실행
            triggers = self._get_event_triggers(event_type, event_source)
            
            for trigger in triggers:
                # 필터 조건 확인
                if self._match_filter(trigger['filter_config'], event_data):
                    # 워크플로우 실행
                    asyncio.create_task(
                        self.workflow_engine.execute_workflow(
                            trigger['workflow_id'],
                            event_data
                        )
                    )
                    
                    logger.info(f"워크플로우 트리거됨: {trigger['workflow_id']} by {event_type}")
            
        except Exception as e:
            logger.error(f"이벤트 처리 오류: {e}")
    
    def _get_event_triggers(self, event_type: str, event_source: str) -> List[Dict[str, Any]]:
        """이벤트 트리거 조회"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT et.*, wd.name as workflow_name
            FROM event_triggers et
            JOIN workflow_definitions wd ON et.workflow_id = wd.id
            WHERE et.event_type = %s 
            AND et.event_source = %s
            AND et.is_active = true
            AND wd.is_active = true
        """, (event_type, event_source))
        
        triggers = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(trigger) for trigger in triggers]
    
    def _match_filter(self, filter_config: Optional[Dict[str, Any]], event_data: Dict[str, Any]) -> bool:
        """필터 조건 매칭"""
        if not filter_config:
            return True
        
        # 필터 조건 평가
        for field, condition in filter_config.items():
            value = event_data.get('data', {}).get(field)
            
            if isinstance(condition, dict):
                # 복잡한 조건
                operator = condition.get('operator', '=')
                expected = condition.get('value')
                
                if operator == '=' and value != expected:
                    return False
                elif operator == '!=' and value == expected:
                    return False
                elif operator == '>' and not (value and value > expected):
                    return False
                elif operator == '<' and not (value and value < expected):
                    return False
                elif operator == 'in' and value not in expected:
                    return False
                elif operator == 'contains' and expected not in str(value):
                    return False
            else:
                # 단순 동등 비교
                if value != condition:
                    return False
        
        return True
    
    def _log_event(self, event: Dict[str, Any]):
        """이벤트 로그 저장"""
        # 최근 100개 이벤트만 유지
        key = f"event_log:{event['source']}:{event['type']}"
        self.redis_client.lpush(key, json.dumps(event))
        self.redis_client.ltrim(key, 0, 99)
        self.redis_client.expire(key, 86400)  # 24시간 TTL
    
    async def register_event_trigger(self, event_type: str, event_source: str, 
                                   workflow_id: int, filter_config: Optional[Dict[str, Any]] = None):
        """이벤트 트리거 등록"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO event_triggers (event_type, event_source, workflow_id, filter_config)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (event_type, event_source, workflow_id) 
                DO UPDATE SET filter_config = EXCLUDED.filter_config, is_active = true
            """, (event_type, event_source, workflow_id, json.dumps(filter_config) if filter_config else None))
            
            conn.commit()
            logger.info(f"이벤트 트리거 등록: {event_type} -> 워크플로우 {workflow_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"이벤트 트리거 등록 실패: {e}")
            raise
        finally:
            cursor.close()
            conn.close()


class EventEmitter:
    """이벤트 발행 헬퍼 클래스"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def emit(self, event_type: str, event_source: str, data: Dict[str, Any]):
        """동기적 이벤트 발행"""
        event = {
            'type': event_type,
            'source': event_source,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        channel = f"events:{event_source}:{event_type}"
        self.redis_client.publish(channel, json.dumps(event))
        
        logger.debug(f"이벤트 발행: {channel}")


# 전역 이벤트 발행자
event_emitter = EventEmitter()


# 일반적인 이벤트 타입
class EventTypes:
    # 재고 이벤트
    INVENTORY_LOW_STOCK = "inventory.low_stock"
    INVENTORY_OUT_OF_STOCK = "inventory.out_of_stock"
    INVENTORY_RESTOCKED = "inventory.restocked"
    
    # 주문 이벤트
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"
    ORDER_CANCELLED = "order.cancelled"
    
    # 가격 이벤트
    PRICE_CHANGED = "price.changed"
    COMPETITOR_PRICE_CHANGE = "competitor.price_change"
    
    # 상품 이벤트
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    
    # 시스템 이벤트
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    API_LIMIT_REACHED = "system.api_limit_reached"