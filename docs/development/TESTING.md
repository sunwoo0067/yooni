# Testing

## Frontend Testing
```bash
npm test              # Jest watch mode
npm run test:ci       # CI mode
npm run test:coverage # Coverage report
```

### Jest Configuration (jest.config.js):
- Module path aliases configured for `@/` imports
- Coverage thresholds: 60% for all metrics (branches, functions, lines, statements)
- Test patterns: `**/__tests__/**/*.[jt]s?(x)`, `**/?(*.)+(spec|test).[jt]s?(x)`
- Setup file: `jest.setup.js` for test environment configuration

## Backend Testing
```bash
cd backend

# Run all tests
python -m pytest

# Run specific test categories
python -m pytest -m "not db"      # Skip database tests
python -m pytest -m "not slow"    # Skip slow tests
python -m pytest -m integration   # Integration tests only
python -m pytest -m unit          # Unit tests only
python -m pytest -m api           # API tests only
python -m pytest -m scheduler     # Scheduler tests only
python -m pytest -m asyncio       # Async tests only

# With coverage
python -m pytest --cov=. --cov-report=html
python -m pytest --cov=. --cov-report=term-missing  # Show missing lines in terminal

# Parallel execution (faster)
python -m pytest -n auto          # Auto-detect CPU count
python -m pytest -n 4            # Use 4 processes
```

### Test Structure:
- `backend/tests/` - Test directory
- `conftest.py` - Global fixtures and configuration
- Test markers (from pytest.ini):
  - `unit` - Unit tests
  - `integration` - Integration tests  
  - `slow` - Slow-running tests
  - `api` - API endpoint tests
  - `db` - Database tests
  - `scheduler` - Scheduler tests
  - `asyncio` - Async tests
- Async mode: `asyncio_mode = auto`

### Key Test Fixtures:
- `test_db` - Test database setup/teardown
- `db_connection/db_cursor` - Database connections
- `mock_coupang_api` - Mocked marketplace APIs
- `sample_product_data/sample_order_data` - Test data

### Coverage Reports:
- HTML report: `htmlcov/index.html`
- Terminal report with missing lines
- Codecov integration in CI/CD pipeline