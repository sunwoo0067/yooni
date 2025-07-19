#!/usr/bin/env python3
"""
통합 공급사 상품 수집 스크립트
모든 공급사의 상품을 수집하여 통합 테이블에 저장
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging
import argparse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedSupplierCollector:
    def __init__(self):
        # 데이터베이스 연결
        self.conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="yoonni",
            user="postgres",
            password="1234"
        )
        
    def collect_supplier(self, supplier_id):
        """특정 공급사의 상품 수집"""
        try:
            # 공급사 정보 조회
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT s.*, sc.api_endpoint, sc.api_key, sc.api_secret, 
                           sc.api_type, sc.settings
                    FROM suppliers s
                    LEFT JOIN supplier_configs sc ON s.id = sc.supplier_id
                    WHERE s.id = %s
                """, (supplier_id,))
                supplier = cursor.fetchone()
                
            if not supplier:
                raise ValueError(f"Supplier {supplier_id} not found")
                
            logger.info(f"수집 시작: {supplier['name']} (ID: {supplier_id})")
            
            # 수집 타입 결정 (이름 기반)
            supplier_type_map = {
                '쿠팡': 'coupang',
                '오너클랜': 'ownerclan',
                '젠트레이드': 'zentrade',
                '네이버': 'naver',
                '도매매': 'domemae'
            }
            
            supplier_type = supplier_type_map.get(supplier['name'])
            
            if not supplier_type:
                raise ValueError(f"Unknown supplier name: {supplier['name']}")
            
            # 수집 타입에 따른 처리
            if supplier_type == 'coupang':
                return self._collect_coupang(supplier)
            elif supplier_type == 'ownerclan':
                return self._collect_ownerclan(supplier)
            elif supplier_type == 'zentrade':
                return self._collect_zentrade(supplier)
            elif supplier_type == 'naver':
                return self._collect_naver(supplier)
            elif supplier_type == 'domemae':
                return self._collect_domemae(supplier)
            else:
                raise ValueError(f"Unsupported supplier type: {supplier_type}")
                
        except Exception as e:
            logger.error(f"수집 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_products": 0,
                "new_products": 0,
                "updated_products": 0,
                "failed_products": 0
            }
            
    def _collect_coupang(self, supplier):
        """쿠팡 상품 수집"""
        try:
            # 쿠팡 수집 모듈 임포트
            import os
            backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(backend_path)
            from market.coupang.collect_products_unified import UnifiedCoupangProductCollector
            
            # 환경변수 설정
            os.environ['COUPANG_ACCESS_KEY'] = supplier.get('api_key', '')
            os.environ['COUPANG_SECRET_KEY'] = supplier.get('api_secret', '')
            os.environ['COUPANG_VENDOR_ID'] = supplier.get('vendor_id', '')
            
            collector = UnifiedCoupangProductCollector()
            
            # 단일 계정 수집
            account = {
                'access_key': supplier.get('api_key'),
                'secret_key': supplier.get('api_secret'),
                'vendor_id': supplier.get('vendor_id'),
                'tag': supplier['name']
            }
            
            results = collector.collect_products_for_account(account)
            
            # 결과 집계
            total = results.get('total_collected', 0)
            new = results.get('new_products', 0)
            updated = results.get('updated_products', 0)
            failed = results.get('failed_products', 0)
            
            return {
                "success": True,
                "total_products": total,
                "new_products": new,
                "updated_products": updated,
                "failed_products": failed,
                "errors": results.get('errors', [])
            }
            
        except Exception as e:
            logger.error(f"쿠팡 수집 오류: {str(e)}")
            raise
            
    def _collect_ownerclan(self, supplier):
        """오너클랜 상품 수집"""
        try:
            # 오너클랜 수집 모듈 임포트
            import os
            backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(backend_path)
            from supplier.ownerclan.collect_products import OwnerClanCollector
            
            # 환경변수 설정
            os.environ['OWNERCLAN_API_KEY'] = supplier.get('api_key', '')
            
            collector = OwnerClanCollector()
            result = collector.collect_products()
            
            return result
            
        except Exception as e:
            logger.error(f"오너클랜 수집 오류: {str(e)}")
            raise
        
    def _collect_zentrade(self, supplier):
        """젠트레이드 상품 수집"""
        try:
            # 젠트레이드 수집 모듈 임포트
            import os
            backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(backend_path)
            from supplier.zentrade.collect_products import ZentradeCollector
            
            # 환경변수 설정
            os.environ['ZENTRADE_API_KEY'] = supplier.get('api_key', '')
            
            collector = ZentradeCollector()
            result = collector.collect_products()
            
            return result
            
        except Exception as e:
            logger.error(f"젠트레이드 수집 오류: {str(e)}")
            raise
        
    def _collect_naver(self, supplier):
        """네이버 상품 수집"""
        try:
            # 네이버 수집 모듈 임포트
            sys.path.append('/home/sunwoo/yooni/backend')
            from market.naver.collect_products import NaverProductCollector
            
            # 환경변수 설정
            os.environ['NAVER_CLIENT_ID'] = supplier.get('api_key', '')
            os.environ['NAVER_CLIENT_SECRET'] = supplier.get('api_secret', '')
            
            collector = NaverProductCollector()
            results = collector.collect_all_products()
            
            return {
                "success": True,
                "total_products": results.get('total', 0),
                "new_products": results.get('new', 0),
                "updated_products": results.get('updated', 0),
                "failed_products": results.get('failed', 0),
                "errors": results.get('errors', [])
            }
            
        except Exception as e:
            logger.error(f"네이버 수집 오류: {str(e)}")
            raise
            
    def _collect_domemae(self, supplier):
        """도매매 상품 수집"""
        logger.info("도매매 수집은 아직 구현되지 않았습니다")
        return {
            "success": False,
            "error": "Not implemented yet",
            "total_products": 0,
            "new_products": 0,
            "updated_products": 0,
            "failed_products": 0
        }
        
    def collect_all(self):
        """모든 활성 공급사 수집"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT s.id, s.name 
                    FROM suppliers s
                    JOIN supplier_configs sc ON s.id = sc.supplier_id
                    WHERE sc.is_active = true
                    ORDER BY s.id
                """)
                suppliers = cursor.fetchall()
                
            results = []
            for supplier in suppliers:
                logger.info(f"수집 중: {supplier['name']}")
                result = self.collect_supplier(supplier['id'])
                result['supplier_name'] = supplier['name']
                result['supplier_id'] = supplier['id']
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"전체 수집 실패: {str(e)}")
            return []

def main():
    parser = argparse.ArgumentParser(description='통합 공급사 상품 수집')
    parser.add_argument('--supplier-id', type=int, help='특정 공급사 ID')
    parser.add_argument('--all', action='store_true', help='모든 공급사 수집')
    
    args = parser.parse_args()
    
    collector = UnifiedSupplierCollector()
    
    if args.supplier_id:
        # 특정 공급사 수집
        result = collector.collect_supplier(args.supplier_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.all:
        # 모든 공급사 수집
        results = collector.collect_all()
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        # 환경변수에서 supplier_id 확인
        supplier_id = os.environ.get('SUPPLIER_ID')
        if supplier_id:
            result = collector.collect_supplier(int(supplier_id))
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.error("공급사 ID를 지정하세요 (--supplier-id 또는 --all)")
            sys.exit(1)

if __name__ == "__main__":
    main()