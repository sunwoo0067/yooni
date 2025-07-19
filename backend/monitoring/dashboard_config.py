"""
모니터링 대시보드 설정 관리
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from ..db.connection_pool import get_database_pool
from ..core.structured_logger import get_logger

logger = get_logger(__name__)


@dataclass
class DashboardWidget:
    """대시보드 위젯 설정"""
    id: str
    type: str  # metric_card, chart, table, etc.
    title: str
    metric: str
    position: Dict[str, int]  # {x, y, w, h}
    settings: Dict[str, Any]
    
    def to_dict(self):
        return asdict(self)


@dataclass
class DashboardLayout:
    """대시보드 레이아웃 설정"""
    id: str
    name: str
    description: str
    widgets: List[DashboardWidget]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self):
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['widgets'] = [w.to_dict() for w in self.widgets]
        return data


class DashboardConfigManager:
    """대시보드 설정 관리자"""
    
    def __init__(self):
        self._db_pool = None
        self._ensure_tables()
    
    def _ensure_tables(self):
        """테이블 생성 확인"""
        try:
            pool = get_database_pool()
            pool.execute_query("""
                CREATE TABLE IF NOT EXISTS dashboard_layouts (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    widgets JSONB NOT NULL DEFAULT '[]',
                    settings JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            pool.execute_query("""
                CREATE TABLE IF NOT EXISTS dashboard_alerts (
                    id SERIAL PRIMARY KEY,
                    metric VARCHAR(100) NOT NULL,
                    condition VARCHAR(20) NOT NULL,
                    threshold FLOAT NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    enabled BOOLEAN DEFAULT true,
                    notification_channels JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("대시보드 테이블 생성/확인 완료")
        except Exception as e:
            logger.error(f"테이블 생성 실패: {e}")
    
    async def save_layout(self, layout: DashboardLayout) -> bool:
        """대시보드 레이아웃 저장"""
        try:
            pool = get_database_pool()
            
            # UPSERT 쿼리
            pool.execute_query("""
                INSERT INTO dashboard_layouts (id, name, description, widgets, settings, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    widgets = EXCLUDED.widgets,
                    settings = EXCLUDED.settings,
                    updated_at = NOW()
            """, (
                layout.id,
                layout.name,
                layout.description,
                json.dumps([w.to_dict() for w in layout.widgets]),
                json.dumps(layout.settings)
            ))
            
            logger.info(f"대시보드 레이아웃 저장: {layout.id}")
            return True
            
        except Exception as e:
            logger.error(f"레이아웃 저장 실패: {e}")
            return False
    
    async def get_layout(self, layout_id: str) -> Optional[DashboardLayout]:
        """대시보드 레이아웃 조회"""
        try:
            pool = get_database_pool()
            
            result = pool.execute_query("""
                SELECT * FROM dashboard_layouts WHERE id = %s
            """, (layout_id,), fetch_one=True)
            
            if not result:
                return None
            
            widgets = [
                DashboardWidget(**widget_data)
                for widget_data in result['widgets']
            ]
            
            return DashboardLayout(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                widgets=widgets,
                settings=result['settings'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
            
        except Exception as e:
            logger.error(f"레이아웃 조회 실패: {e}")
            return None
    
    async def list_layouts(self) -> List[Dict[str, Any]]:
        """모든 레이아웃 목록 조회"""
        try:
            pool = get_database_pool()
            
            results = pool.execute_query("""
                SELECT id, name, description, created_at, updated_at
                FROM dashboard_layouts
                ORDER BY updated_at DESC
            """, fetch_all=True)
            
            return [
                {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'created_at': row['created_at'].isoformat(),
                    'updated_at': row['updated_at'].isoformat()
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"레이아웃 목록 조회 실패: {e}")
            return []
    
    async def delete_layout(self, layout_id: str) -> bool:
        """대시보드 레이아웃 삭제"""
        try:
            pool = get_database_pool()
            
            rowcount = pool.execute_query("""
                DELETE FROM dashboard_layouts WHERE id = %s
            """, (layout_id,))
            
            if rowcount > 0:
                logger.info(f"대시보드 레이아웃 삭제: {layout_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"레이아웃 삭제 실패: {e}")
            return False
    
    async def save_alert_rule(self, alert_rule: Dict[str, Any]) -> int:
        """알림 규칙 저장"""
        try:
            pool = get_database_pool()
            
            result = pool.execute_query("""
                INSERT INTO dashboard_alerts 
                (metric, condition, threshold, severity, enabled, notification_channels)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                alert_rule['metric'],
                alert_rule['condition'],
                alert_rule['threshold'],
                alert_rule['severity'],
                alert_rule.get('enabled', True),
                json.dumps(alert_rule.get('notification_channels', []))
            ), fetch_one=True)
            
            alert_id = result['id']
            logger.info(f"알림 규칙 저장: {alert_id}")
            return alert_id
            
        except Exception as e:
            logger.error(f"알림 규칙 저장 실패: {e}")
            return -1
    
    async def get_alert_rules(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """알림 규칙 목록 조회"""
        try:
            pool = get_database_pool()
            
            query = """
                SELECT * FROM dashboard_alerts
                {}
                ORDER BY created_at DESC
            """.format("WHERE enabled = true" if enabled_only else "")
            
            results = pool.execute_query(query, fetch_all=True)
            
            return [
                {
                    'id': row['id'],
                    'metric': row['metric'],
                    'condition': row['condition'],
                    'threshold': row['threshold'],
                    'severity': row['severity'],
                    'enabled': row['enabled'],
                    'notification_channels': row['notification_channels'],
                    'created_at': row['created_at'].isoformat()
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"알림 규칙 조회 실패: {e}")
            return []
    
    async def update_alert_rule(self, alert_id: int, updates: Dict[str, Any]) -> bool:
        """알림 규칙 업데이트"""
        try:
            pool = get_database_pool()
            
            # 업데이트 가능한 필드만 추출
            allowed_fields = ['metric', 'condition', 'threshold', 'severity', 'enabled', 'notification_channels']
            update_fields = []
            values = []
            
            for field in allowed_fields:
                if field in updates:
                    update_fields.append(f"{field} = %s")
                    if field == 'notification_channels':
                        values.append(json.dumps(updates[field]))
                    else:
                        values.append(updates[field])
            
            if not update_fields:
                return False
            
            values.append(alert_id)
            
            rowcount = pool.execute_query(f"""
                UPDATE dashboard_alerts
                SET {', '.join(update_fields)}
                WHERE id = %s
            """, values)
            
            return rowcount > 0
            
        except Exception as e:
            logger.error(f"알림 규칙 업데이트 실패: {e}")
            return False
    
    async def delete_alert_rule(self, alert_id: int) -> bool:
        """알림 규칙 삭제"""
        try:
            pool = get_database_pool()
            
            rowcount = pool.execute_query("""
                DELETE FROM dashboard_alerts WHERE id = %s
            """, (alert_id,))
            
            return rowcount > 0
            
        except Exception as e:
            logger.error(f"알림 규칙 삭제 실패: {e}")
            return False


# 기본 대시보드 레이아웃
DEFAULT_LAYOUTS = {
    'system': DashboardLayout(
        id='default-system',
        name='시스템 모니터링',
        description='시스템 리소스 모니터링 대시보드',
        widgets=[
            DashboardWidget(
                id='cpu-usage',
                type='metric_card',
                title='CPU 사용률',
                metric='system.cpu.usage',
                position={'x': 0, 'y': 0, 'w': 3, 'h': 2},
                settings={'suffix': '%', 'threshold': 80}
            ),
            DashboardWidget(
                id='memory-usage',
                type='metric_card',
                title='메모리 사용률',
                metric='system.memory.usage',
                position={'x': 3, 'y': 0, 'w': 3, 'h': 2},
                settings={'suffix': '%', 'threshold': 85}
            ),
            DashboardWidget(
                id='system-chart',
                type='line_chart',
                title='시스템 리소스 추이',
                metric='system.*',
                position={'x': 0, 'y': 2, 'w': 12, 'h': 4},
                settings={'timeRange': '1h', 'refreshInterval': 30}
            )
        ],
        settings={'refreshInterval': 10, 'theme': 'light'},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
}