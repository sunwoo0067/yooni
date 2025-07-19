#!/usr/bin/env python3
"""
워크플로우 통합 테스트
"""
import pytest
import asyncio
import aiohttp
import psycopg2
import redis
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

# 테스트 설정
API_BASE_URL = "http://localhost:8001"
FRONTEND_BASE_URL = "http://localhost:3000"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'yoonni_test',
    'user': 'postgres',
    'password': '1234'
}


class TestWorkflowIntegration:
    """워크플로우 통합 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 설정"""
        # 데이터베이스 초기화
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        
        # Redis 클라이언트
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        yield
        
        # 테스트 데이터 정리
        self.cursor.execute("DELETE FROM workflow_executions")
        self.cursor.execute("DELETE FROM workflow_rules")
        self.cursor.execute("DELETE FROM workflow_definitions WHERE name LIKE 'Test%'")
        self.conn.commit()
        
        self.cursor.close()
        self.conn.close()
    
    @pytest.mark.asyncio
    async def test_create_and_execute_event_workflow(self):
        """이벤트 기반 워크플로우 생성 및 실행 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. 워크플로우 생성 (Frontend API)
            workflow_data = {
                "name": "Test Event Workflow",
                "description": "통합 테스트용 이벤트 워크플로우",
                "trigger_type": "event",
                "config": {
                    "event_type": "test.event",
                    "event_source": "integration_test"
                },
                "rules": [
                    {
                        "condition_type": "threshold",
                        "condition_config": {
                            "field": "value",
                            "operator": ">",
                            "value": 10
                        },
                        "action_type": "database_update",
                        "action_config": {
                            "table": "test_results",
                            "set": {"status": "triggered"},
                            "where": {"id": "{{data.id}}"}
                        }
                    }
                ]
            }
            
            async with session.post(
                f"{FRONTEND_BASE_URL}/api/workflow",
                json=workflow_data
            ) as response:
                assert response.status == 200
                result = await response.json()
                workflow_id = result['workflow_id']
            
            # 2. 이벤트 발행 (Backend API)
            event_data = {
                "event_type": "test.event",
                "event_source": "integration_test",
                "data": {
                    "id": "test-123",
                    "value": 15
                }
            }
            
            async with session.post(
                f"{API_BASE_URL}/emit-event",
                json=event_data
            ) as response:
                assert response.status == 200
            
            # 3. 실행 결과 확인 (잠시 대기)
            await asyncio.sleep(2)
            
            # 4. 실행 이력 조회
            self.cursor.execute("""
                SELECT status, trigger_source 
                FROM workflow_executions 
                WHERE workflow_id = %s
            """, (workflow_id,))
            
            execution = self.cursor.fetchone()
            assert execution is not None
            assert execution[0] == 'completed'
            assert execution[1] == 'integration_test'
    
    @pytest.mark.asyncio
    async def test_manual_workflow_execution(self):
        """수동 워크플로우 실행 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. 수동 워크플로우 생성
            workflow_data = {
                "name": "Test Manual Workflow",
                "description": "통합 테스트용 수동 워크플로우",
                "trigger_type": "manual",
                "config": {},
                "rules": [
                    {
                        "condition_type": "always",
                        "condition_config": {},
                        "action_type": "api_call",
                        "action_config": {
                            "endpoint": f"{API_BASE_URL}/health",
                            "method": "GET"
                        }
                    }
                ]
            }
            
            async with session.post(
                f"{FRONTEND_BASE_URL}/api/workflow",
                json=workflow_data
            ) as response:
                assert response.status == 200
                result = await response.json()
                workflow_id = result['workflow_id']
            
            # 2. 워크플로우 실행
            async with session.post(
                f"{API_BASE_URL}/execute-workflow",
                json={
                    "workflow_id": workflow_id,
                    "trigger_data": {"test": True}
                }
            ) as response:
                assert response.status == 200
                result = await response.json()
                assert result['success'] is True
                assert result['execution_id'] is not None
    
    @pytest.mark.asyncio
    async def test_workflow_crud_operations(self):
        """워크플로우 CRUD 작업 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. Create
            workflow_data = {
                "name": "Test CRUD Workflow",
                "description": "CRUD 테스트용 워크플로우",
                "trigger_type": "manual",
                "config": {},
                "rules": [
                    {
                        "condition_type": "always",
                        "condition_config": {},
                        "action_type": "notification",
                        "action_config": {"channel": "email"}
                    }
                ]
            }
            
            async with session.post(
                f"{FRONTEND_BASE_URL}/api/workflow",
                json=workflow_data
            ) as response:
                assert response.status == 200
                result = await response.json()
                workflow_id = result['workflow_id']
            
            # 2. Read
            async with session.get(
                f"{FRONTEND_BASE_URL}/api/workflow"
            ) as response:
                assert response.status == 200
                result = await response.json()
                workflows = result['workflows']
                assert any(w['id'] == workflow_id for w in workflows)
            
            # 3. Update (활성/비활성 토글)
            async with session.put(
                f"{FRONTEND_BASE_URL}/api/workflow",
                json={"id": workflow_id, "is_active": False}
            ) as response:
                assert response.status == 200
            
            # 4. Verify update
            self.cursor.execute(
                "SELECT is_active FROM workflow_definitions WHERE id = %s",
                (workflow_id,)
            )
            is_active = self.cursor.fetchone()[0]
            assert is_active is False
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """워크플로우 오류 처리 테스트"""
        async with aiohttp.ClientSession() as session:
            # 1. 잘못된 액션을 가진 워크플로우 생성
            workflow_data = {
                "name": "Test Error Workflow",
                "description": "오류 처리 테스트용 워크플로우",
                "trigger_type": "manual",
                "config": {},
                "rules": [
                    {
                        "condition_type": "always",
                        "condition_config": {},
                        "action_type": "api_call",
                        "action_config": {
                            "endpoint": "http://invalid-endpoint.test",
                            "method": "POST"
                        }
                    }
                ]
            }
            
            async with session.post(
                f"{FRONTEND_BASE_URL}/api/workflow",
                json=workflow_data
            ) as response:
                assert response.status == 200
                result = await response.json()
                workflow_id = result['workflow_id']
            
            # 2. 워크플로우 실행
            async with session.post(
                f"{API_BASE_URL}/execute-workflow",
                json={"workflow_id": workflow_id, "trigger_data": {}}
            ) as response:
                assert response.status == 200
                result = await response.json()
                assert result['success'] is False
            
            # 3. 실행 상태 확인
            await asyncio.sleep(1)
            self.cursor.execute("""
                SELECT status, error_message 
                FROM workflow_executions 
                WHERE workflow_id = %s
            """, (workflow_id,))
            
            execution = self.cursor.fetchone()
            assert execution[0] == 'failed'
            assert execution[1] is not None