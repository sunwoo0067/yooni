#!/usr/bin/env python3
"""
네이버 스마트스토어 상품 수집 스크립트
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List

# 상위 디렉토리 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from market.naver.naver_client import NaverClient
from market_manager import MarketSync
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NaverProductCollector:
    """네이버 상품 수집기"""
    
    def __init__(self, account_name: str = '기본계정'):
        self.client = NaverClient()
        self.sync_manager = MarketSync()
        self.account_name = account_name
    
    def collect_all_products(self) -> Dict:
        """모든 상품 수집"""
        logger.info("네이버 스마트스토어 상품 수집 시작")
        
        result = {
            'success': True,
            'total_products': 0,
            'new_products': 0,
            'updated_products': 0,
            'failed_products': 0,
            'errors': []
        }
        
        try:
            page = 1
            while True:
                logger.info(f"페이지 {page} 수집 중...")
                
                # 상품 조회
                response = self.client.products.get_products(page=page, size=100)
                
                # 응답 구조 확인 (contents 또는 products)
                products = response.get('contents', response.get('products', []))
                
                if not products:
                    logger.info("더 이상 상품이 없습니다.")
                    break
                
                # 상품 변환 및 저장
                converted_products = self._convert_products(products)
                sync_result = self.sync_manager.sync_naver_products(
                    self.account_name, 
                    converted_products
                )
                
                # 결과 집계
                result['total_products'] += sync_result['total']
                result['updated_products'] += sync_result['updated']
                result['failed_products'] += sync_result['failed']
                result['errors'].extend(sync_result['errors'])
                
                # 페이징 정보 확인
                page_info = response.get('pagination', response.get('pageInfo', {}))
                total_pages = page_info.get('totalPages', 1)
                
                if page >= total_pages:
                    break
                
                page += 1
                
        except Exception as e:
            logger.error(f"수집 중 오류 발생: {e}")
            result['success'] = False
            result['errors'].append(str(e))
        
        finally:
            self.sync_manager.close()
        
        # 최종 결과 출력
        logger.info(f"수집 완료: 총 {result['total_products']}개")
        logger.info(f"업데이트: {result['updated_products']}개, 실패: {result['failed_products']}개")
        
        if result['errors']:
            logger.error(f"오류 발생: {len(result['errors'])}건")
            for error in result['errors'][:5]:  # 처음 5개만 출력
                logger.error(f"  - {error}")
        
        return result
    
    def _convert_products(self, products: List[Dict]) -> List[Dict]:
        """네이버 상품 데이터를 공통 형식으로 변환"""
        converted = []
        
        for product in products:
            try:
                # 상품 상태 변환
                status = self._convert_status(product.get('statusType', product.get('status')))
                
                # 가격 정보 추출
                sale_price = product.get('salePrice', 0)
                discount_price = product.get('discountPrice')
                
                # 실제 판매가 결정
                actual_price = discount_price if discount_price else sale_price
                
                converted_product = {
                    'id': str(product.get('productNo', product.get('id', ''))),
                    'name': product.get('name', ''),
                    'brand': product.get('brand'),
                    'manufacturer': product.get('manufacturer'),
                    'modelName': product.get('modelName'),
                    'originalPrice': sale_price,
                    'price': actual_price,
                    'status': status,
                    'stockQuantity': product.get('stockQuantity', 0),
                    'category': {
                        'id': product.get('categoryId'),
                        'name': product.get('categoryName')
                    },
                    'images': self._extract_images(product),
                    'detailContent': product.get('detailContent', ''),
                    'original_data': product
                }
                
                converted.append(converted_product)
                
            except Exception as e:
                logger.error(f"상품 변환 오류: {e}")
                logger.error(f"원본 데이터: {json.dumps(product, ensure_ascii=False)[:200]}")
        
        return converted
    
    def _convert_status(self, status: Optional[str]) -> str:
        """네이버 상품 상태를 표준 상태로 변환"""
        if not status:
            return 'INACTIVE'
        
        status_map = {
            'SALE': 'ACTIVE',
            'OUTOFSTOCK': 'INACTIVE',
            'SUSPENSION': 'INACTIVE',
            'CLOSE': 'INACTIVE',
            'PROHIBITION': 'INACTIVE'
        }
        
        return status_map.get(status.upper(), 'INACTIVE')
    
    def _extract_images(self, product: Dict) -> List[str]:
        """상품 이미지 URL 추출"""
        images = []
        
        # 대표 이미지
        if product.get('representImage'):
            images.append(product['representImage'])
        
        # 추가 이미지
        if product.get('images'):
            if isinstance(product['images'], list):
                images.extend(product['images'])
            elif isinstance(product['images'], dict):
                # 이미지 객체에서 URL 추출
                for img in product['images'].values():
                    if isinstance(img, str):
                        images.append(img)
                    elif isinstance(img, dict) and img.get('url'):
                        images.append(img['url'])
        
        return images[:10]  # 최대 10개

def main():
    """메인 실행 함수"""
    try:
        # 계정 이름 설정 (환경변수 또는 기본값)
        account_name = os.getenv('NAVER_ACCOUNT_NAME', '스마트스토어1')
        
        # 수집기 생성 및 실행
        collector = NaverProductCollector(account_name)
        
        # 연결 테스트
        if not collector.client.test_connection():
            logger.error("네이버 API 연결 실패")
            return
        
        # 상품 수집
        result = collector.collect_all_products()
        
        # JSON 형식으로 결과 출력 (다른 프로세스에서 파싱 가능)
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"수집 실패: {e}")
        error_result = {
            'success': False,
            'total_products': 0,
            'new_products': 0,
            'updated_products': 0,
            'failed_products': 0,
            'errors': [str(e)]
        }
        print(json.dumps(error_result, ensure_ascii=False))

if __name__ == '__main__':
    main()