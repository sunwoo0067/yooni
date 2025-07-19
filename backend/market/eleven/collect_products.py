#!/usr/bin/env python3
"""
11번가 상품 수집 스크립트
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List

# 상위 디렉토리 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from market.eleven.eleven_client import ElevenClient
from market_manager import MarketSync
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ElevenProductCollector:
    """11번가 상품 수집기"""
    
    def __init__(self, account_name: str = '11번가'):
        self.client = ElevenClient()
        self.sync_manager = MarketSync()
        self.account_name = account_name
    
    def collect_all_products(self) -> Dict:
        """모든 상품 수집"""
        logger.info("11번가 상품 수집 시작")
        
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
            empty_page_count = 0
            
            while True:
                logger.info(f"페이지 {page} 수집 중...")
                
                try:
                    # 상품 조회
                    response = self.client.products.get_products(page=page)
                    
                    # 상품 추출
                    products = []
                    if 'Products' in response and 'Product' in response['Products']:
                        products = response['Products']['Product']
                        if not isinstance(products, list):
                            products = [products]
                    
                    if not products:
                        empty_page_count += 1
                        if empty_page_count >= 3:  # 연속 3페이지 비어있으면 종료
                            logger.info("더 이상 상품이 없습니다.")
                            break
                        page += 1
                        continue
                    
                    empty_page_count = 0
                    
                    # 상품 변환 및 저장
                    converted_products = self._convert_products(products)
                    sync_result = self.sync_manager.sync_eleven_products(
                        self.account_name, 
                        converted_products
                    )
                    
                    # 결과 집계
                    result['total_products'] += sync_result['total']
                    result['updated_products'] += sync_result['updated']
                    result['failed_products'] += sync_result['failed']
                    result['errors'].extend(sync_result['errors'])
                    
                    # 다음 페이지
                    page += 1
                    
                    # 페이지 제한 (안전장치)
                    if page > 1000:
                        logger.warning("페이지 제한 도달 (1000페이지)")
                        break
                        
                except Exception as e:
                    logger.error(f"페이지 {page} 수집 중 오류: {e}")
                    result['errors'].append(f"Page {page}: {str(e)}")
                    page += 1
                    
                    if page > 5:  # 초반 5페이지에서 계속 실패하면 중단
                        break
                
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
        """11번가 상품 데이터를 공통 형식으로 변환"""
        converted = []
        
        for product in products:
            try:
                # 가격 정보 추출
                price = self._extract_number(product.get('selPrc', '0'))
                
                # 재고 정보 (별도 API 호출 필요)
                stock_quantity = 0
                try:
                    product_no = product.get('prdNo', '')
                    if product_no:
                        stock_result = self.client.products.get_product_stock(product_no)
                        if 'ProductStock' in stock_result:
                            stock_quantity = int(stock_result['ProductStock'].get('stckQty', 0))
                except:
                    pass
                
                converted_product = {
                    'id': str(product.get('prdNo', '')),
                    'name': product.get('prdNm', ''),
                    'brand': product.get('brand'),
                    'manufacturer': product.get('manufact'),
                    'modelName': product.get('modelNm'),
                    'originalPrice': price,
                    'price': price,
                    'status': self._convert_status(product.get('prdSelStat')),
                    'stockQuantity': stock_quantity,
                    'category': {
                        'id': product.get('dispCtgrNo'),
                        'name': product.get('dispCtgrNm')
                    },
                    'images': self._extract_images(product),
                    'sellerCode': product.get('sellerPrdCd'),
                    'original_data': product
                }
                
                converted.append(converted_product)
                
            except Exception as e:
                logger.error(f"상품 변환 오류: {e}")
                logger.error(f"원본 데이터: {json.dumps(product, ensure_ascii=False)[:200]}")
        
        return converted
    
    def _extract_number(self, value: str) -> float:
        """문자열에서 숫자 추출"""
        if not value:
            return 0
        try:
            # 숫자가 아닌 문자 제거
            import re
            numbers = re.findall(r'\d+', str(value))
            if numbers:
                return float(''.join(numbers))
        except:
            pass
        return 0
    
    def _convert_status(self, status: Optional[str]) -> str:
        """11번가 상품 상태를 표준 상태로 변환"""
        if not status:
            return 'INACTIVE'
        
        # 103: 판매중, 104: 품절, 105: 판매중지
        status_map = {
            '103': 'ACTIVE',
            '104': 'INACTIVE',
            '105': 'INACTIVE'
        }
        
        return status_map.get(str(status), 'INACTIVE')
    
    def _extract_images(self, product: Dict) -> List[str]:
        """상품 이미지 URL 추출"""
        images = []
        
        # 기본 이미지
        if product.get('prdImage'):
            images.append(product['prdImage'])
        
        # 상세 이미지
        if product.get('prdImage01'):
            images.append(product['prdImage01'])
        if product.get('prdImage02'):
            images.append(product['prdImage02'])
        if product.get('prdImage03'):
            images.append(product['prdImage03'])
        
        return images[:10]  # 최대 10개

def main():
    """메인 실행 함수"""
    try:
        # 계정 이름 설정
        account_name = os.getenv('ELEVEN_ACCOUNT_NAME', '11번가')
        
        # 수집기 생성 및 실행
        collector = ElevenProductCollector(account_name)
        
        # 연결 테스트
        if not collector.client.test_connection():
            logger.error("11번가 API 연결 실패")
            return
        
        # 상품 수집
        result = collector.collect_all_products()
        
        # JSON 형식으로 결과 출력
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