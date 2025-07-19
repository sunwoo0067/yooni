# 11번가 Open API 클라이언트

11번가 Open API를 사용한 마켓플레이스 연동 모듈

## API 문서
- [11번가 Open API](https://openapi.11st.co.kr/openapi/OpenApiGuide.tmall)
- [API 가이드](https://openapi.11st.co.kr/openapi/guide)

## 주요 기능
- API Key 인증
- 상품 관리 (조회/등록/수정)
- 주문 관리 (조회/처리)
- 배송 관리
- 카테고리 조회

## 설정
```python
# .env 파일
ELEVEN_API_KEY=your_api_key
```

## 사용 예시
```python
from market.eleven import ElevenClient

client = ElevenClient(api_key='your_api_key')

# 상품 조회
products = client.get_products()

# 주문 조회
orders = client.get_orders(start_date='2024-01-01')
```

## API 제한사항
- 일일 호출 제한: 10,000건
- 분당 호출 제한: 100건
- XML 형식으로 응답