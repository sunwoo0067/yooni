# CLAUDE.md - Yooni E-commerce Automation Platform

## Project Overview

Yooni is a multi-marketplace e-commerce automation platform that integrates with various online marketplaces (primarily Coupang) and suppliers (Ownerclan) to automate order processing, fulfillment, and inventory management.

### Core Architecture

The project consists of several key components:

1. **Market Integrations** (`market/`)
   - Coupang marketplace integration with HMAC authentication
   - Order fetching, status updates, shipping management
   - Location/warehouse management

2. **Supplier Integrations** (`supplier/`)
   - Ownerclan supplier integration
   - Order placement, cancellation, and tracking

3. **Worker System** (`workers/`)
   - Base worker architecture for automation tasks
   - Coupang fetch worker for order synchronization
   - Ownerclan place worker for order fulfillment

4. **Database** (Supabase/PostgreSQL)
   - Multi-tenant architecture supporting multiple marketplace accounts
   - Comprehensive order and inventory tracking
   - Product SKU mapping between marketplaces and suppliers

5. **Supabase MCP Server** (`supabase-mcp/`)
   - Model Context Protocol integration for AI assistants
   - Allows Claude/Cursor to interact with Supabase directly

## Tech Stack

- **Backend**: Python 3.12
- **Database**: Supabase (PostgreSQL)
- **Authentication**: HMAC SHA256 for Coupang API
- **Environment**: Virtual environment (venv)
- **Dependencies**:
  - requests (HTTP client)
  - python-dotenv (environment management)
  - supabase (database client)

## Project Structure

```
yooni/
├── market/                     # Marketplace integrations
│   └── coupaing/              # Coupang marketplace
│       ├── HMAC Signature/    # Authentication utilities
│       ├── location/          # Warehouse management
│       ├── order/             # Order management
│       └── utils/             # Shared utilities
├── supplier/                   # Supplier integrations
│   └── ownerclan/             # Ownerclan supplier
├── workers/                    # Automation workers
│   ├── base_worker.py         # Abstract base class
│   ├── coupang_fetch_worker.py
│   └── ownerclan_place_worker.py
├── supabase/                   # Database migrations
│   └── migrations/            # SQL migration files
├── supabase-mcp/              # MCP server for AI assistants
├── docs/                       # API documentation
└── .env                        # Environment configuration
```

## Key Database Tables

1. **markets** - Marketplace definitions (Coupang, Naver, etc.)
2. **accounts** - Vendor accounts per marketplace
3. **orders** - Unified order tracking across all marketplaces
4. **order_items** - Individual items within orders
5. **product_mappings** - SKU mapping between marketplaces and suppliers
6. **ownerclan_orders** - Supplier order tracking
7. **automation_logs** - System event and error logging

## Environment Variables

Required environment variables in `.env`:

```
# Coupang API Credentials
COUPANG_ACCESS_KEY=
COUPANG_SECRET_KEY=
COUPANG_VENDOR_ID=

# Supabase Configuration
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_DB_URL=
SUPABASE_ACCESS_TOKEN=

# Ownerclan Credentials
OWNERCLAN_USERNAME=
OWNERCLAN_PASSWORD=
```

## Development Guidelines

### Code Style
- UTF-8 encoding with explicit declarations (`# -*- coding: utf-8 -*-`)
- Clear module imports with proper path management
- Comprehensive error handling and logging
- Korean comments for business logic documentation

### API Integration Patterns
1. **Authentication**: Each marketplace has its own auth module
2. **Error Handling**: Graceful degradation with detailed logging
3. **Pagination**: Support for paginated API responses
4. **Rate Limiting**: Built-in delays to prevent API throttling

### Database Operations
- Use Supabase client for all database operations
- Implement upsert patterns for idempotent operations
- Store raw API responses in JSONB columns for debugging
- Handle schema evolution gracefully

### Worker Architecture
- Inherit from `BaseWorker` for consistent behavior
- Each worker is tied to a specific marketplace account
- Comprehensive logging to `automation_logs` table
- Support for both scheduled and on-demand execution

## Common Tasks

### Fetch Coupang Orders
```python
python market/coupaing/order/list_ordersheets.py
```

### Run Database Migrations
```bash
supabase db push
```

### Test Supabase Connection
```python
python supabase_test.py
```

## Security Considerations

1. **API Credentials**: Never commit credentials to version control
2. **HMAC Authentication**: Time-based signatures for Coupang API
3. **Database Access**: Use service role keys only for backend operations
4. **MCP Server**: Configure with read-only access for safety

## Future Enhancements

1. Support for additional marketplaces (Naver Smart Store, 11st)
2. Real-time order synchronization using webhooks
3. Advanced inventory management and forecasting
4. Multi-supplier order routing optimization
5. Comprehensive reporting and analytics dashboard

## Debugging Tips

1. Check `automation_logs` table for detailed error messages
2. Enable debug logging in HMAC authentication for API issues
3. Use raw_data columns to inspect original API responses
4. Monitor Supabase logs for database-related issues

## Important Notes

- The project uses both global and project-specific virtual environments
- Database migrations should be applied sequentially
- Some migrations handle backward compatibility for missing columns
- The MCP server enables AI-assisted database operations