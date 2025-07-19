#!/usr/bin/env python3
"""
API 헬스 체커 - 외부 API 상태를 주기적으로 체크
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
import redis
import sys
from typing import Dict, Any

sys.path.append('/home/sunwoo/yooni/backend')
sys.path.append('/home/sunwoo/yooni/module/market/coupang')

from core import get_logger, log_execution_time
from auth.coupang_auth import CoupangAuth

logger = get_logger(__name__)


class APIHealthChecker:
    """API 상태 체커"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.check_interval = 60  # 60초마다 체크
        
        # API 엔드포인트
        self.endpoints = {
            'coupang': {
                'url': 'https://api-gateway.coupang.com/v2/providers/seller_api/apis/api/v1/marketplace/seller-products',
                'method': 'GET',
                'auth_required': True
            },
            'naver': {
                'url': 'https://api.commerce.naver.com/external/v1/product-api/products',
                'method': 'GET',
                'auth_required': True
            },
            '11st': {
                'url': 'https://api.11st.co.kr/rest/prodservices/product',
                'method': 'GET',
                'auth_required': True
            }
        }
        
    async def check_api_health(self, market: str, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """API 상태 체크"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                
                # 쿠팡 인증
                if market == 'coupang' and endpoint['auth_required']:
                    try:
                        # 임시 인증 정보 (실제로는 설정에서 가져와야 함)
                        auth = CoupangAuth(
                            access_key='dummy',
                            secret_key='dummy',
                            vendor_id='dummy'
                        )
                        headers = auth.generate_auth_header(endpoint['url'], endpoint['method'])
                    except:
                        pass
                
                # API 호출
                async with session.request(
                    method=endpoint['method'],
                    url=endpoint['url'],
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=False
                ) as response:
                    response_time = (time.time() - start_time) * 1000  # ms
                    
                    status = 'healthy' if response.status < 500 else 'degraded'
                    
                    return {
                        'status': status,
                        'status_code': response.status,
                        'response_time': round(response_time, 2),
                        'last_check': datetime.now().isoformat(),
                        'error': None
                    }
                    
        except asyncio.TimeoutError:
            return {
                'status': 'timeout',
                'status_code': None,
                'response_time': 10000,  # 10초 타임아웃
                'last_check': datetime.now().isoformat(),
                'error': 'Request timeout'
            }
        except Exception as e:
            logger.error(f"{market} API 체크 실패: {e}")
            return {
                'status': 'error',
                'status_code': None,
                'response_time': None,
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def check_all_apis(self):
        """모든 API 상태 체크"""
        tasks = []
        
        for market, endpoint in self.endpoints.items():
            task = self.check_api_health(market, endpoint)
            tasks.append((market, task))
        
        results = {}
        for market, task in tasks:
            result = await task
            results[market] = result
            
            # Redis에 저장
            key = f"api_status:{market}"
            self.redis_client.setex(
                key,
                300,  # 5분 TTL
                json.dumps(result)
            )
            
            logger.info(
                f"{market} API 상태: {result['status']} "
                f"(응답시간: {result.get('response_time', 'N/A')}ms)"
            )
        
        return results
    
    async def run(self):
        """주기적으로 API 상태 체크"""
        logger.info("API 헬스 체커 시작")
        
        while True:
            try:
                await self.check_all_apis()
            except Exception as e:
                logger.error(f"API 헬스 체크 오류: {e}")
            
            await asyncio.sleep(self.check_interval)


def main():
    """메인 함수"""
    checker = APIHealthChecker()
    
    try:
        asyncio.run(checker.run())
    except KeyboardInterrupt:
        logger.info("API 헬스 체커 종료")


if __name__ == "__main__":
    main()