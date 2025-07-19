#!/usr/bin/env python3
"""
API 연동 통합 테스트
실제 API 키 없이도 테스트 가능한 모의 모드
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_integration_manager import APIIntegrationManager, APICredentials, CollectionResult
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockAPIIntegrationManager(APIIntegrationManager):
    """API 연동 매니저 모의 버전"""
    
    async def _authenticate_ownerclan(self, credentials: APICredentials) -> str:
        """오너클랜 인증 모의"""
        logger.info("🔐 오너클랜 인증 모의 실행")
        await asyncio.sleep(0.1)  # API 호출 시뮬레이션
        return "mock_auth_token_ownerclan_" + str(int(asyncio.get_event_loop().time()))
    
    async def _fetch_ownerclan_products(self, credentials: APICredentials, 
                                      token: str, limit: int, offset: int):
        """오너클랜 상품 조회 모의"""
        logger.info(f"📦 오너클랜 상품 조회 모의: offset={offset}, limit={limit}")
        await asyncio.sleep(0.05)  # API 호출 시뮬레이션
        
        # 모의 상품 데이터
        if offset >= 250:  # 총 250개 상품 시뮬레이션
            return {'items': [], 'totalCount': 250}
            
        items = []
        for i in range(limit):
            product_id = offset + i + 1
            if product_id > 250:
                break
                
            items.append({
                'id': f'OC_REAL_{product_id:04d}',
                'name': f'오너클랜 실제연동 상품 {product_id}',
                'code': f'OC{product_id:04d}',
                'barcode': f'8801234{product_id:06d}',
                'brandName': ['삼성', 'LG', '애플', '나이키', '아디다스'][product_id % 5],
                'manufacturerName': f'제조사 {product_id % 10 + 1}',
                'originCountry': ['대한민국', '중국', '미국', '일본'][product_id % 4],
                'description': f'실제 API 연동으로 수집된 고품질 상품입니다. ID: {product_id}',
                'stock': 50 + (product_id * 10) % 500,
                'price': 15000 + (product_id * 2000) % 200000,
                'costPrice': 8000 + (product_id * 1000) % 100000,
                'weight': 0.2 + (product_id * 0.1) % 10.0,
                'status': 'ACTIVE' if product_id % 8 != 0 else 'INACTIVE',
                'createdAt': '2024-01-15T00:00:00Z',
                'updatedAt': '2024-07-19T10:00:00Z',
                'category': {
                    'id': f'CAT{(product_id % 8) + 1}',
                    'name': ['전자제품', '의류', '식품', '뷰티', '스포츠', '도서', '완구', '생활용품'][product_id % 8],
                    'fullPath': f'대분류 > 중분류 > {["전자제품", "의류", "식품", "뷰티", "스포츠", "도서", "완구", "생활용품"][product_id % 8]}'
                },
                'options': [
                    {
                        'id': f'OPT{product_id}_SIZE',
                        'name': '크기',
                        'values': ['S', 'M', 'L', 'XL']
                    },
                    {
                        'id': f'OPT{product_id}_COLOR',
                        'name': '색상',
                        'values': ['블랙', '화이트', '그레이', '네이비']
                    }
                ],
                'images': [
                    {
                        'url': f'https://cdn.ownerclan.com/real/products/{product_id}_main.jpg',
                        'isMain': True
                    },
                    {
                        'url': f'https://cdn.ownerclan.com/real/products/{product_id}_detail1.jpg',
                        'isMain': False
                    },
                    {
                        'url': f'https://cdn.ownerclan.com/real/products/{product_id}_detail2.jpg',
                        'isMain': False
                    }
                ]
            })
        
        return {
            'items': items,
            'totalCount': 250
        }
    
    async def _fetch_zentrade_products(self, credentials: APICredentials, 
                                     page: int, per_page: int):
        """젠트레이드 상품 조회 모의"""
        logger.info(f"📦 젠트레이드 상품 조회 모의: page={page}, per_page={per_page}")
        await asyncio.sleep(0.03)  # API 호출 시뮬레이션
        
        # 총 150개 상품 시뮬레이션
        total_products = 150
        start_id = (page - 1) * per_page
        
        if start_id >= total_products:
            return {'data': [], 'total': total_products}
        
        items = []
        for i in range(per_page):
            product_id = start_id + i + 1
            if product_id > total_products:
                break
                
            items.append({
                'id': f'ZT_REAL_{product_id:04d}',
                'name': f'젠트레이드 실제연동 상품 {product_id}',
                'code': f'ZT{product_id:04d}',
                'barcode': f'8809876{product_id:06d}',
                'brand': ['현대', '기아', 'SK', 'LG유플러스', 'KT'][product_id % 5],
                'manufacturer': f'젠트레이드 제조사 {product_id % 7 + 1}',
                'origin': ['대한민국', '베트남', '태국'][product_id % 3],
                'description': f'젠트레이드 API로 수집된 프리미엄 상품입니다. 상품번호: {product_id}',
                'stock_quantity': 30 + (product_id * 5) % 300,
                'price': 25000 + (product_id * 3000) % 300000,
                'cost_price': 12000 + (product_id * 1500) % 150000,
                'weight': 0.5 + (product_id * 0.2) % 15.0,
                'status': 'active' if product_id % 6 != 0 else 'inactive',
                'images': [
                    {
                        'url': f'https://cdn.zentrade.co.kr/real/products/{product_id}_main.jpg',
                        'isMain': True
                    }
                ],
                'category': {
                    'name': ['B2B 전자부품', 'B2B 기계부품', 'B2B 화학소재', 'B2B 의료기기'][product_id % 4],
                    'fullPath': f'B2B > {["전자부품", "기계부품", "화학소재", "의료기기"][product_id % 4]}'
                }
            })
        
        return {
            'data': items,
            'total': total_products,
            'page': page,
            'per_page': per_page
        }

async def test_api_integration():
    """API 연동 통합 테스트"""
    print("🚀 실제 API 연동 시스템 테스트 시작")
    print("=" * 60)
    
    # 모의 모드 매니저 생성
    manager = MockAPIIntegrationManager()
    
    try:
        # 1. 개별 공급사 테스트
        print("\n🔍 1단계: 개별 공급사 API 연동 테스트")
        
        # 오너클랜 테스트
        print("\n📡 오너클랜 API 연동 테스트...")
        ownerclan_creds = manager.get_supplier_credentials('오너클랜')
        if ownerclan_creds:
            ownerclan_result = await manager.collect_ownerclan_products(ownerclan_creds)
            print(f"   ✅ 오너클랜: {ownerclan_result.total_products}개 수집 "
                  f"({ownerclan_result.duration_seconds:.1f}초)")
        else:
            print("   ❌ 오너클랜: 인증 정보 없음")
        
        # 젠트레이드 테스트
        print("\n📡 젠트레이드 API 연동 테스트...")
        zentrade_creds = manager.get_supplier_credentials('젠트레이드')
        if zentrade_creds:
            zentrade_result = await manager.collect_zentrade_products(zentrade_creds)
            print(f"   ✅ 젠트레이드: {zentrade_result.total_products}개 수집 "
                  f"({zentrade_result.duration_seconds:.1f}초)")
        else:
            print("   ❌ 젠트레이드: 인증 정보 없음")
        
        # 2. 전체 통합 수집 테스트
        print("\n🔄 2단계: 전체 공급사 통합 수집 테스트")
        all_results = await manager.collect_all_suppliers()
        
        # 3. 결과 요약
        print("\n📊 3단계: 최종 결과 요약")
        total_products = 0
        total_new = 0
        total_updated = 0
        total_failed = 0
        
        for supplier_name, result in all_results.items():
            status = "✅" if result.success else "❌"
            print(f"\n{status} {supplier_name}:")
            print(f"   📦 총 상품: {result.total_products}개")
            print(f"   🆕 신규: {result.new_products}개")
            print(f"   🔄 업데이트: {result.updated_products}개")
            print(f"   ❌ 실패: {result.failed_products}개")
            print(f"   ⏱️ 소요시간: {result.duration_seconds:.1f}초")
            
            if result.errors:
                print(f"   🚨 오류: {', '.join(result.errors[:2])}")
            
            total_products += result.total_products
            total_new += result.new_products
            total_updated += result.updated_products
            total_failed += result.failed_products
        
        # 4. 데이터베이스 검증
        print("\n🔍 4단계: 데이터베이스 검증")
        with manager.conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.name as supplier_name,
                    COUNT(sp.id) as total_products,
                    COUNT(CASE WHEN sp.status = 'active' THEN 1 END) as active_products,
                    MAX(sp.collected_at) as last_collected
                FROM suppliers s
                LEFT JOIN supplier_products sp ON s.id = sp.supplier_id
                WHERE s.name IN ('오너클랜', '젠트레이드')
                GROUP BY s.id, s.name
                ORDER BY s.name
            """)
            
            db_results = cursor.fetchall()
            
            for row in db_results:
                print(f"   📊 {row[0]}: {row[1]}개 상품 ({row[2]}개 활성)")
                if row[3]:
                    print(f"      마지막 수집: {row[3]}")
        
        print("\n" + "=" * 60)
        print(f"🎯 전체 요약:")
        print(f"   총 수집: {total_products}개 상품")
        print(f"   신규: {total_new}개, 업데이트: {total_updated}개, 실패: {total_failed}개")
        print(f"   성공률: {((total_products - total_failed) / max(1, total_products)) * 100:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"테스트 실행 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        manager.close()

if __name__ == "__main__":
    success = asyncio.run(test_api_integration())
    print("\n" + "=" * 60)
    if success:
        print("🎉 API 연동 시스템 테스트 성공!")
    else:
        print("💥 API 연동 시스템 테스트 실패!")
    
    sys.exit(0 if success else 1)