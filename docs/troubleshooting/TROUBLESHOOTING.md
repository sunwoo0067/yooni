# Troubleshooting

## Common Issues

### 1. PostgreSQL Connection Error
```
Error: connection to server at "localhost", port 5432 failed
```
Solution: Use port 5434, not default 5432
```bash
postgresql://postgres:1234@localhost:5434/yoonni
```

### 2. Redis Connection Failed
```
Error: NOAUTH Authentication required
```
Solution: Set Redis password in docker-compose
```yaml
command: redis-server --requirepass redis123
```

### 3. Module Import Errors
```
ModuleNotFoundError: No module named 'konlpy'
```
Solution: Install system dependencies first
```bash
# Ubuntu/Debian
sudo apt-get install g++ openjdk-8-jdk python3-dev
pip install konlpy
```

### 4. MLflow Tracking Error
```
Error: Could not connect to tracking server
```
Solution: Ensure MLflow is running
```bash
docker-compose -f docker-compose.dev.yml up mlflow
```

### 5. Coupang API Authentication Failed
```
Error: Invalid signature
```
Solution: Check timezone and request timestamp
```python
# Ensure UTC timezone
datetime.utcnow().strftime('%y%m%dT%H%M%SZ')
```

### 6. OwnerClan GraphQL Error
```
Error: Cannot query field "X" on type "Y"
```
Solution: Check API version and schema
```python
# Use introspection query
introspection_query = """
{
  __schema {
    types {
      name
      fields {
        name
      }
    }
  }
}
"""
```

### 7. Memory Issues with Large Data
```
MemoryError: Unable to allocate array
```
Solution: Use batch processing
```python
# Process in chunks
chunk_size = 1000
for i in range(0, len(data), chunk_size):
    chunk = data[i:i+chunk_size]
    process_chunk(chunk)
```