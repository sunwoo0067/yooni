"""
워크플로우 실행 엔진
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import yaml
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import sys

sys.path.append('/home/sunwoo/yooni/backend')
from core import get_logger, log_execution_time, handle_error
from core.exceptions import BusinessLogicException

logger = get_logger(__name__)


class TriggerType(Enum):
    EVENT = "event"
    SCHEDULE = "schedule"
    MANUAL = "manual"


class ConditionType(Enum):
    THRESHOLD = "threshold"
    COMPARISON = "comparison"
    TIME_BASED = "time_based"
    FIELD_CHECK = "field_check"
    CUSTOM = "custom"
    ALWAYS = "always"


class ActionType(Enum):
    NOTIFICATION = "notification"
    API_CALL = "api_call"
    DATABASE_UPDATE = "database_update"
    WORKFLOW_TRIGGER = "workflow_trigger"
    CUSTOM = "custom"


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowEngine:
    """워크플로우 실행 엔진"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.condition_handlers = self._register_condition_handlers()
        self.action_handlers = self._register_action_handlers()
        self._running_workflows = {}
        
    def _register_condition_handlers(self) -> Dict[str, Callable]:
        """조건 핸들러 등록"""
        return {
            ConditionType.THRESHOLD.value: self._evaluate_threshold,
            ConditionType.COMPARISON.value: self._evaluate_comparison,
            ConditionType.TIME_BASED.value: self._evaluate_time_based,
            ConditionType.FIELD_CHECK.value: self._evaluate_field_check,
            ConditionType.ALWAYS.value: lambda *args: True,
        }
    
    def _register_action_handlers(self) -> Dict[str, Callable]:
        """액션 핸들러 등록"""
        return {
            ActionType.NOTIFICATION.value: self._execute_notification,
            ActionType.API_CALL.value: self._execute_api_call,
            ActionType.DATABASE_UPDATE.value: self._execute_database_update,
            ActionType.WORKFLOW_TRIGGER.value: self._execute_workflow_trigger,
        }
    
    @log_execution_time()
    async def execute_workflow(self, workflow_id: int, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 실행"""
        execution_id = None
        
        try:
            # 워크플로우 정의 로드
            workflow = self._load_workflow_definition(workflow_id)
            if not workflow or not workflow['is_active']:
                raise BusinessLogicException(f"워크플로우를 찾을 수 없거나 비활성 상태입니다: {workflow_id}")
            
            # 실행 기록 생성
            execution_id = self._create_execution_record(workflow_id, trigger_data)
            self._running_workflows[execution_id] = True
            
            logger.info(f"워크플로우 실행 시작: {workflow['name']} (ID: {workflow_id}, Execution: {execution_id})")
            
            # 규칙 실행
            rules = self._load_workflow_rules(workflow_id)
            results = []
            
            for rule in rules:
                if not rule['is_active']:
                    continue
                
                # 조건 평가
                condition_met = await self._evaluate_condition(
                    rule['condition_type'],
                    rule['condition_config'],
                    trigger_data
                )
                
                if condition_met:
                    # 액션 실행
                    step_result = await self._execute_action(
                        execution_id,
                        rule,
                        trigger_data
                    )
                    results.append(step_result)
                    
                    # 액션 결과를 다음 규칙의 입력으로 사용
                    if step_result.get('output_data'):
                        trigger_data.update(step_result['output_data'])
            
            # 실행 완료 처리
            self._complete_execution(execution_id, WorkflowStatus.COMPLETED, results)
            
            logger.info(f"워크플로우 실행 완료: {workflow['name']} (Execution: {execution_id})")
            
            return {
                'success': True,
                'execution_id': execution_id,
                'workflow_name': workflow['name'],
                'results': results
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"워크플로우 실행 실패: {error_msg}", exc_info=True)
            
            if execution_id:
                self._complete_execution(execution_id, WorkflowStatus.FAILED, error_message=error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'execution_id': execution_id
            }
        finally:
            if execution_id and execution_id in self._running_workflows:
                del self._running_workflows[execution_id]
    
    def _load_workflow_definition(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """워크플로우 정의 로드"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM workflow_definitions WHERE id = %s
        """, (workflow_id,))
        
        workflow = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return dict(workflow) if workflow else None
    
    def _load_workflow_rules(self, workflow_id: int) -> List[Dict[str, Any]]:
        """워크플로우 규칙 로드"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM workflow_rules 
            WHERE workflow_id = %s 
            ORDER BY rule_order
        """, (workflow_id,))
        
        rules = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [dict(rule) for rule in rules]
    
    def _create_execution_record(self, workflow_id: int, trigger_data: Dict[str, Any]) -> int:
        """실행 기록 생성"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workflow_executions 
            (workflow_id, trigger_source, trigger_data, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            workflow_id,
            trigger_data.get('source', 'manual'),
            Json(trigger_data),
            WorkflowStatus.RUNNING.value
        ))
        
        execution_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return execution_id
    
    def _complete_execution(self, execution_id: int, status: WorkflowStatus, 
                          results: Optional[List] = None, error_message: Optional[str] = None):
        """실행 완료 처리"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workflow_executions
            SET status = %s,
                completed_at = NOW(),
                execution_time_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000,
                result = %s,
                error_message = %s
            WHERE id = %s
        """, (
            status.value,
            Json(results) if results else None,
            error_message,
            execution_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    async def _evaluate_condition(self, condition_type: str, config: Dict[str, Any], 
                                 data: Dict[str, Any]) -> bool:
        """조건 평가"""
        handler = self.condition_handlers.get(condition_type)
        if not handler:
            logger.warning(f"알 수 없는 조건 타입: {condition_type}")
            return False
        
        try:
            return await handler(config, data)
        except Exception as e:
            logger.error(f"조건 평가 실패: {e}")
            return False
    
    async def _evaluate_threshold(self, config: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """임계치 조건 평가"""
        field = config.get('field')
        operator = config.get('operator')
        threshold = config.get('value')
        
        if not all([field, operator, threshold is not None]):
            return False
        
        # 중첩된 필드 접근 지원 (예: "inventory.stock_quantity")
        value = data
        for part in field.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return False
        
        if value is None:
            return False
        
        # 연산자별 비교
        operators = {
            '=': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y,
        }
        
        op_func = operators.get(operator)
        if op_func:
            return op_func(value, threshold)
        
        return False
    
    async def _evaluate_comparison(self, config: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """비교 조건 평가"""
        field1 = config.get('field')
        field2 = config.get('compare_field')
        operator = config.get('operator')
        margin = config.get('margin', 1.0)
        
        # 필드 값 추출
        value1 = self._get_field_value(data, field1)
        value2 = self._get_field_value(data, field2)
        
        if value1 is None or value2 is None:
            return False
        
        # 마진 적용
        value2 = value2 * margin
        
        # 비교
        operators = {
            '=': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y,
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y,
        }
        
        op_func = operators.get(operator)
        return op_func(value1, value2) if op_func else False
    
    async def _evaluate_time_based(self, config: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """시간 기반 조건 평가"""
        # TODO: 구현 필요
        return True
    
    async def _evaluate_field_check(self, config: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """필드 체크 조건 평가"""
        field = config.get('field')
        expected_value = config.get('value')
        
        actual_value = self._get_field_value(data, field)
        return actual_value == expected_value
    
    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """중첩된 필드 값 추출"""
        value = data
        for part in field_path.split('.'):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
    
    async def _execute_action(self, execution_id: int, rule: Dict[str, Any], 
                            data: Dict[str, Any]) -> Dict[str, Any]:
        """액션 실행"""
        step_id = self._create_step_record(execution_id, rule['id'], data)
        
        try:
            handler = self.action_handlers.get(rule['action_type'])
            if not handler:
                raise ValueError(f"알 수 없는 액션 타입: {rule['action_type']}")
            
            # 액션 실행
            result = await handler(rule['action_config'], data)
            
            # 스텝 완료 기록
            self._complete_step(step_id, 'completed', result)
            
            return {
                'rule_id': rule['id'],
                'action_type': rule['action_type'],
                'success': True,
                'output_data': result
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"액션 실행 실패: {error_msg}")
            
            self._complete_step(step_id, 'failed', error_message=error_msg)
            
            return {
                'rule_id': rule['id'],
                'action_type': rule['action_type'],
                'success': False,
                'error': error_msg
            }
    
    def _create_step_record(self, execution_id: int, rule_id: int, data: Dict[str, Any]) -> int:
        """스텝 실행 기록 생성"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workflow_step_executions
            (execution_id, rule_id, step_order, status, input_data)
            VALUES (%s, %s, 
                (SELECT COALESCE(MAX(step_order), 0) + 1 
                 FROM workflow_step_executions WHERE execution_id = %s),
                'running', %s)
            RETURNING id
        """, (execution_id, rule_id, execution_id, Json(data)))
        
        step_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return step_id
    
    def _complete_step(self, step_id: int, status: str, output_data: Optional[Dict] = None,
                      error_message: Optional[str] = None):
        """스텝 완료 처리"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE workflow_step_executions
            SET status = %s,
                completed_at = NOW(),
                output_data = %s,
                error_message = %s
            WHERE id = %s
        """, (status, Json(output_data) if output_data else None, error_message, step_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    async def _execute_notification(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """알림 액션 실행"""
        channel = config.get('channel', 'email')
        template = config.get('template')
        recipients = config.get('recipients', [])
        
        logger.info(f"알림 전송: {channel} - {template}")
        
        # TODO: 실제 알림 전송 구현
        # 이메일, SMS, 슬랙 등
        
        return {
            'notification_sent': True,
            'channel': channel,
            'template': template,
            'recipients': recipients
        }
    
    async def _execute_api_call(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """API 호출 액션 실행"""
        import aiohttp
        
        endpoint = config.get('endpoint')
        method = config.get('method', 'POST')
        params = config.get('params', {})
        
        # 파라미터에 데이터 병합
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                # 템플릿 변수 치환
                field_path = value[2:-2].strip()
                params[key] = self._get_field_value(data, field_path)
        
        logger.info(f"API 호출: {method} {endpoint}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, endpoint, json=params) as response:
                    result = await response.json()
                    
                    return {
                        'api_response': result,
                        'status_code': response.status
                    }
        except Exception as e:
            logger.error(f"API 호출 실패: {e}")
            raise
    
    async def _execute_database_update(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터베이스 업데이트 액션 실행"""
        table = config.get('table')
        set_values = config.get('set', {})
        where_clause = config.get('where', {})
        
        if not table or not set_values:
            raise ValueError("테이블명과 업데이트 값은 필수입니다")
        
        # SET 절 구성
        set_parts = []
        set_params = []
        for key, value in set_values.items():
            set_parts.append(f"{key} = %s")
            
            # 템플릿 변수 치환
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                field_path = value[2:-2].strip()
                value = self._get_field_value(data, field_path)
            
            set_params.append(value)
        
        # WHERE 절 구성
        where_parts = []
        where_params = []
        for key, value in where_clause.items():
            where_parts.append(f"{key} = %s")
            
            # 템플릿 변수 치환
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                field_path = value[2:-2].strip()
                value = self._get_field_value(data, field_path)
            
            where_params.append(value)
        
        # 쿼리 실행
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        query = f"""
            UPDATE {table}
            SET {', '.join(set_parts)}
            {f"WHERE {' AND '.join(where_parts)}" if where_parts else ''}
            RETURNING *
        """
        
        cursor.execute(query, set_params + where_params)
        updated_rows = cursor.fetchall()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"데이터베이스 업데이트: {table} - {len(updated_rows)}행")
        
        return {
            'updated_rows': len(updated_rows),
            'table': table
        }
    
    async def _execute_workflow_trigger(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """다른 워크플로우 트리거 액션 실행"""
        target_workflow_id = config.get('workflow_id')
        pass_data = config.get('pass_data', True)
        
        if not target_workflow_id:
            raise ValueError("대상 워크플로우 ID가 필요합니다")
        
        # 데이터 전달
        trigger_data = data if pass_data else {}
        trigger_data['triggered_by'] = 'workflow'
        
        # 비동기로 다른 워크플로우 실행
        result = await self.execute_workflow(target_workflow_id, trigger_data)
        
        return {
            'triggered_workflow_id': target_workflow_id,
            'execution_result': result
        }