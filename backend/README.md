# Backend - E-commerce Integration System

Korean e-commerce platform integration backend for Coupang, OwnerClan, ZenTrade, etc.

## Setup

### 1. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file with your credentials:
```env
# Database
DB_HOST=localhost
DB_PORT=5434
DB_NAME=yoonni
DB_USER=postgres
DB_PASSWORD=1234

# Coupang (optional - can use accounts.json)
COUPANG_ACCESS_KEY=your_key
COUPANG_SECRET_KEY=your_secret
COUPANG_VENDOR_ID=your_vendor_id

# OwnerClan
OWNERCLAN_USER=your_username
OWNERCLAN_PASS=your_password

# ZenTrade
ZENTRADE_USER=your_username
ZENTRADE_PASS=your_password
```

## Usage

### Product Collection
```bash
# Coupang products
python market/coupang/collect_products_unified.py

# OwnerClan products
python supplier/ownerclan/collect_all.py

# ZenTrade products
python supplier/zentrade/collect_products.py
```

### Order Collection
```bash
# Coupang orders
python market/coupang/collect_orders_jsonb.py
```

### Multi-Account Operations
```bash
# Using accounts.json configuration
python market/coupang/multi_account_product_collector.py
```

## Project Structure
```
backend/
├── market/           # Marketplace integrations
│   └── coupang/     # Coupang Partners API
├── supplier/        # Supplier platform integrations
│   ├── ownerclan/   # OwnerClan GraphQL API
│   └── zentrade/    # ZenTrade API
└── product/         # Product data processing
```

## API Documentation
- Coupang: See `market/coupang/API_SPECIFICATION.md`
- OwnerClan: See `supplier/ownerclan/docs/`