# Korean E-commerce Platform Specifics

## Coupang (쿠팡)
- **Authentication**: HMAC-SHA256 with vendor-specific keys
- **Rate Limits**: 10-15 requests/second per vendor
- **Multi-Account**: Supported via accounts.json configuration
- **Required Centers**: Shipping (출고지) and Return (반품지) addresses
- **Date Range Limits**: Typically 31-93 days depending on endpoint

### Example API Call - Get Orders:
```python
from backend.market.coupang.order.order_client import OrderClient

# Initialize client
client = OrderClient(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    vendor_id="YOUR_VENDOR_ID"
)

# Get orders from last 7 days
from datetime import datetime, timedelta
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

orders = client.get_orders_by_date(
    search_start_date=start_date.strftime('%Y-%m-%d'),
    search_end_date=end_date.strftime('%Y-%m-%d'),
    status='INSTRUCT'  # 발주확인 상태
)

# Process results
for order in orders:
    print(f"Order ID: {order['orderId']}")
    print(f"Buyer: {order['orderer']['name']}")
```

## OwnerClan (오너클랜)
- **API Type**: GraphQL with JWT authentication
- **Rate Limit**: 1000 requests/second
- **Endpoints**: 
  - Production: `https://api.ownerclan.com/v1/graphql`
  - Sandbox: `https://api-sandbox.ownerclan.com/v1/graphql`
- **Auth Server**: `https://auth.ownerclan.com/auth`
- **Special Features**: Automatic order splitting by vendor and shipping type

### Example GraphQL Query - Get Product:
```python
import requests
import jwt

# Get JWT token
auth_response = requests.post(
    'https://auth.ownerclan.com/auth',
    json={
        'username': 'YOUR_USERNAME',
        'password': 'YOUR_PASSWORD'
    }
)
token = auth_response.json()['token']

# GraphQL query
query = """
query getProduct($key: String!) {
    item(key: $key) {
        name
        model
        price
        quantity
        options {
            price
            quantity
            optionAttributes {
                name
                value
            }
        }
    }
}
"""

# Make request
response = requests.post(
    'https://api.ownerclan.com/v1/graphql',
    json={
        'query': query,
        'variables': {'key': 'W000000'}
    },
    headers={'Authorization': f'Bearer {token}'}
)

product = response.json()['data']['item']
```

## ZenTrade (젠트레이드)
- **Authentication**: Session-based with login credentials
- **Data Format**: Excel/CSV exports
- **Collection**: Web scraping with session management
- **Special Handling**: Cookie-based session persistence

### Example Session Setup:
```python
import requests
from bs4 import BeautifulSoup

# Create session
session = requests.Session()

# Login
login_data = {
    'user_id': 'YOUR_ID',
    'password': 'YOUR_PASSWORD'
}
session.post('https://zentrade.co.kr/login', data=login_data)

# Get product list
response = session.get('https://zentrade.co.kr/products')
soup = BeautifulSoup(response.text, 'html.parser')

# Parse products
products = []
for row in soup.find_all('tr', class_='product-row'):
    product = {
        'name': row.find('td', class_='name').text,
        'price': row.find('td', class_='price').text,
        'stock': row.find('td', class_='stock').text
    }
    products.append(product)
```