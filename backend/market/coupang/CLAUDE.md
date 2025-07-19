# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive Python client library for the Coupang Partners API (쿠팡 파트너스 API), providing modular integration with all major Coupang e-commerce operations. The library is designed for Korean e-commerce vendors to manage their Coupang marketplace operations programmatically.

## Key Architecture Patterns

### Base Client Pattern
All API clients inherit from `BaseCoupangClient` in `common/base_client.py`:
- Handles HMAC-SHA256 authentication (CEA algorithm)
- Manages SSL context and network requests
- Provides automatic error handling and retry logic
- Centralizes vendor credentials management

### Module Structure
Each functional area is self-contained with consistent patterns:
```
module_name/
├── client.py or module_name_client.py  # Main API client
├── models.py                           # Data models and type definitions
├── validators.py                       # Input validation logic
├── constants.py                        # Module-specific constants
├── utils.py                           # Helper functions
└── test_*.py                          # Unit tests
```

### Authentication Flow
1. Credentials loaded from environment variables or passed directly
2. `CoupangAuth` class generates HMAC signatures for each request
3. Required headers: Authorization, X-EXTENDED-Timestamp, X-Coupang-Target-Market
4. Vendor ID included in most API endpoints

## Common Development Commands

### Running Tests
```bash
# Run all tests for a specific module
python -m unittest discover -s order -p "test_*.py"
python -m unittest discover -s product -p "test_*.py"
python -m unittest discover -s returns -p "test_*.py"

# Run specific test file
python -m unittest order.test_order
python -m unittest product.test_refactored

# Run integration tests (requires valid credentials)
python -m unittest order.test_integration
python -m unittest product.test_api_integration
```

### Type Checking
```bash
# Type check with mypy (cache present at .mypy_cache)
mypy .

# Type check specific module
mypy order/
mypy product/
```

### Environment Setup
```bash
# Create .env file with credentials
cat > .env << EOF
COUPANG_ACCESS_KEY=your_access_key
COUPANG_SECRET_KEY=your_secret_key
COUPANG_VENDOR_ID=your_vendor_id
EOF
```

## High-Level Architecture

### 1. Module Hierarchy
- **common/** - Base classes, configuration, error handling, and test utilities
- **auth/** - HMAC-SHA256 authentication implementation
- **cs/** - Customer service inquiries (online and call center)
- **sales/** - Revenue tracking and analysis
- **settlement/** - Payment settlement tracking
- **order/** - Order management and processing
- **product/** - Product catalog management
- **returns/** - Return request handling
- **exchange/** - Exchange request processing
- **category/** - Category management and validation
- **ShippingCenters/** - Shipping center configuration
- **ReturnCenters/** - Return center configuration
- **multi_account/** - Multi-vendor account management

### 2. Client Factory Pattern
`MultiClientFactory` in `multi_account/factory.py` enables:
- Creating clients for multiple vendor accounts
- Caching client instances for performance
- Tag-based account grouping
- Batch operations across accounts

### 3. API Integration Patterns
- RESTful JSON APIs with consistent response structure
- Pagination via `nextToken` for list operations
- Date range limitations (varies by module, typically 31-93 days)
- Rate limiting: 10-15 requests/second per vendor
- Automatic retry on network failures

### 4. Error Handling Architecture
Custom exception hierarchy in `common/errors.py`:
- `CoupangAPIError` - Base exception
- `CoupangAuthError` - Authentication failures
- `CoupangNetworkError` - Network issues
- `CoupangValidationError` - Input validation
- `CoupangRateLimitError` - Rate limit exceeded

### 5. Testing Strategy
- Unit tests with `unittest` framework
- Mock-based testing using `common/test_utils.py`
- Integration test examples for live API testing
- No pytest configuration (uses standard unittest)

## Module-Specific Considerations

### Product Module
- Complex nested data structures for product creation
- Vendor item management separate from product management
- Auto-generated options support
- Partial update capabilities for efficiency

### Order Module
- Time-based queries with specific status filtering
- Shipment invoice management
- Order cancellation and status updates
- Split shipment handling

### Returns/Exchange Modules
- Approval/rejection workflows
- Reason code management
- Status transition validations
- Vendor-specific return center configuration

### Category Module
- Excel-based category data parsing
- Option validation against Coupang requirements
- Display category management
- Category recommendation engine

## Important Notes

1. **No Package Management**: Dependencies are not defined in this directory. Assumed to be managed at parent level.

2. **SSL Context**: The code disables SSL certificate verification (`ssl.CERT_NONE`). This should be reviewed for production use.

3. **Language**: All API documentation and many comments are in Korean, as this targets Korean e-commerce vendors.

4. **Date Formats**: API uses various date formats:
   - ISO 8601 for most endpoints
   - YYYY-MM-DD for some legacy endpoints
   - Timezone: Korea Standard Time (KST)

5. **Multi-Account Usage**: For managing multiple vendor accounts, use the multi-account module with `accounts.json` configuration.

6. **Large File Handling**: Some operations (like bulk product updates) may require streaming or chunking for large datasets.