# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an e-commerce integration module that connects Korean e-commerce platforms (OwnerClan and ZenTrade) with a centralized system. The codebase handles product data conversion, order management, and synchronization between different platforms.

## Repository Structure

```
module/
├── product/                    # Core product data processing module
│   ├── __init__.py            # Module initialization
│   ├── cli.py                 # Command-line interface
│   ├── converter.py           # Data conversion logic
│   ├── database.py            # Database operations
│   ├── models.py              # Data models
│   └── log/                   # Conversion logs
│
└── supplier/                   # E-commerce platform integrations
    ├── product_mapper.py      # Product mapping between platforms
    ├── ownerclan/             # OwnerClan platform integration
    └── zentrade/              # ZenTrade platform integration
```

## Technology Stack

- **Language**: Python
- **Database**: PostgreSQL (port 5434)
- **API Integration**: GraphQL (OwnerClan)
- **Type Checking**: MyPy
- **Environment Variables**: python-dotenv

## Database Configuration

The project uses PostgreSQL with connection details stored in `product/.env`:
- Database name: `yoonni`
- Default port: 5434 (non-standard)

## Key Components

### Product Module
- **converter.py**: Handles data transformation between platform-specific formats
- **database.py**: Manages PostgreSQL connections and queries
- **models.py**: Defines data structures for products, orders, etc.
- **cli.py**: Provides command-line interface for operations

### Supplier Integration
- **ownerclan/**: Integration with OwnerClan's GraphQL API v0.11.0
  - Full API documentation available in Korean at `supplier/ownerclan/docs/ownerclan-api-spec copy.md`
  - Production endpoint: `https://api.ownerclan.com/v1/graphql`
  - Sandbox endpoint: `https://api-sandbox.ownerclan.com/v1/graphql`
- **zentrade/**: Integration with ZenTrade platform

## Common Operations

Based on log files, common operations include:
- Product conversion between platforms (convert_ownerclan_*, convert_products_*)
- Full product collection from suppliers
- Soldout product synchronization
- Order management and tracking

## Important Notes

- All API documentation for OwnerClan is in Korean
- The system uses JWT-based authentication for API access
- Rate limiting: 1000 requests per second for individual item queries (OwnerClan)
- Automatic order splitting based on vendor and shipping type
- Special handling for international shipping with customs clearance

## Development Considerations

- No explicit dependency management files found - dependencies may be managed at parent directory level
- No test files found in current structure - testing approach unclear
- Active logging system tracks all conversion and synchronization operations
- Multiple `.claude` directories suggest AI-assisted development patterns