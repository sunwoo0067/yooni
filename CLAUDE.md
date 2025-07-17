# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an e-commerce integration system that connects Korean e-commerce platforms (OwnerClan, ZenTrade, 도매매) with a centralized PostgreSQL database. The system handles product data synchronization, order management, and API integrations.

## Project Structure

```
/home/sunwoo/yooni/
├── module/
│   ├── product/             # Core product data processing
│   │   ├── __init__.py
│   │   ├── cli.py          # Command-line interface
│   │   ├── converter.py    # Data conversion logic
│   │   ├── database.py     # Database operations
│   │   ├── models.py       # Data models
│   │   └── log/            # Conversion logs
│   │
│   └── supplier/            # E-commerce platform integrations
│       ├── product_mapper.py
│       ├── ownerclan/       # OwnerClan GraphQL API integration
│       │   └── docs/        # API documentation (Korean)
│       └── zentrade/        # ZenTrade integration
│           └── log/         # Order and product logs
└── frontend/                # Empty directory (future frontend)
```

## Database Configuration

PostgreSQL database with custom port:
- **Host**: localhost
- **Port**: 5434 (non-standard)
- **Database**: yoonni
- **Connection**: `postgresql://postgres:1234@localhost:5434/yoonni`

Database contains ~135K products with partitioning planned at 1M records.

## Key API Integrations

### OwnerClan GraphQL API (v0.11.0)
- **Production**: `https://api.ownerclan.com/v1/graphql`
- **Sandbox**: `https://api-sandbox.ownerclan.com/v1/graphql`
- **Authentication**: JWT-based via auth endpoints
- **Rate Limit**: 1000 requests/second for item queries
- **Documentation**: `module/supplier/ownerclan/docs/ownerclan-api-spec copy.md` (Korean)

### Core Features
- Product synchronization across multiple suppliers
- Order lifecycle management
- Automatic order splitting by vendor/shipping type
- International shipping with customs handling
- Return/exchange request processing

## Common Commands

Since this is primarily a data integration system without standard build tools:

```bash
# Database operations (assumed based on structure)
python -m module.product.cli [command]

# Common operations observed from logs:
# - convert_ownerclan_*
# - convert_products_*
# - collect_full_products
# - collect_soldout_products
```

## Development Notes

- **Language**: Python with MyPy type checking
- **No explicit dependency management**: Dependencies likely managed at parent level
- **No test framework**: Testing approach unclear from current structure
- **Logging**: Active logging system tracks all operations
- **Documentation**: All OwnerClan API docs are in Korean

## Supplier Distribution

Current data distribution:
- 도매매: 66% (89,335 products)
- 오너클랜: 31% (42,410 products)  
- 젠트레이드: 3% (3,536 products)

## Important Considerations

- All content and API documentation is in Korean
- Focus on e-commerce platform connectivity and data synchronization
- No frontend implementation yet (empty frontend directory)
- Active development with AI assistance (multiple `.claude` directories)