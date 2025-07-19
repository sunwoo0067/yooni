# 데이터베이스 연결 통합 가이드

## 🎯 목표
76개 파일에서 개별적으로 생성하던 DB 연결을 중앙화된 connection pool로 통합

## ✅ 완료된 작업
1. **통합 Connection Pool 구축**: `frontend/lib/db/connection-pool.ts`
2. **유틸리티 함수 제공**: `frontend/lib/db/index.ts` 
3. **예시 변경**: `dashboard/stats/route.ts`, `monitoring/database/route.ts`

## 📋 변경 방법

### Before (기존 방식) ❌
```typescript
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DATABASE_HOST || 'localhost',
  port: parseInt(process.env.DATABASE_PORT || '5434'),
  database: process.env.DATABASE_NAME || 'yoonni',
  user: process.env.DATABASE_USER || 'postgres',
  password: process.env.DATABASE_PASSWORD || 'postgres',
});

export async function GET() {
  const client = await pool.connect();
  try {
    const result = await client.query('SELECT * FROM products');
    return NextResponse.json(result.rows);
  } finally {
    client.release();
  }
}
```

### After (권장 방식) ✅
```typescript
import { query, getOne, transaction } from '@/lib/db';

export async function GET() {
  try {
    // 단일 행 조회
    const product = await getOne<Product>('SELECT * FROM products WHERE id = $1', [1]);
    
    // 여러 행 조회
    const products = await query<Product>('SELECT * FROM products WHERE status = $1', ['active']);
    
    // 트랜잭션
    const result = await transaction(async (client) => {
      await client.query('INSERT INTO orders...', []);
      await client.query('UPDATE products...', []);
      return { success: true };
    });
    
    return NextResponse.json({ product, products, result });
  } catch (error) {
    return NextResponse.json({ error: 'Database error' }, { status: 500 });
  }
}
```

## 🔄 변경 대상 파일들 (20개)

### API Routes
- `app/api/dashboard/stats/route.ts` ✅ 완료
- `app/api/monitoring/database/route.ts` ✅ 완료  
- `app/api/monitoring/business/route.ts`
- `app/api/erp/stats/route.ts`
- `app/api/scheduler/jobs/[id]/run/route.ts`
- `app/api/scheduler/jobs/[id]/toggle/route.ts` 
- `app/api/workflow/[id]/rules/route.ts`
- `app/api/workflow/[id]/executions/route.ts`
- `app/api/workflow/route.ts`
- `app/api/settings/database/stats/route.ts`
- `app/api/settings/database/partitions/create/route.ts`
- `app/api/settings/database/partitions/route.ts`
- `app/api/scheduler/executions/route.ts`
- `app/api/scheduler/jobs/route.ts` 
- `app/api/config/history/route.ts`
- `app/api/config/route.ts`

### Test Files
- `app/api/erp/__tests__/inventory.test.ts`
- `app/api/erp/__tests__/stats.test.ts`
- `test-collection.ts`
- `test-collection.js`

## 🚀 제공되는 유틸리티 함수들

### 1. `query<T>(sql, params)` - 여러 행 조회
```typescript
const products = await query<Product>('SELECT * FROM products WHERE status = $1', ['active']);
```

### 2. `getOne<T>(sql, params)` - 단일 행 조회  
```typescript
const product = await getOne<Product>('SELECT * FROM products WHERE id = $1', [1]);
```

### 3. `transaction(callback)` - 트랜잭션 처리
```typescript
const result = await transaction(async (client) => {
  await client.query('INSERT INTO...', []);
  await client.query('UPDATE...', []);
  return data;
});
```

### 4. `getPoolStats()` - 연결 풀 상태 확인
```typescript
const stats = await getPoolStats();
// { totalCount: 5, idleCount: 3, waitingCount: 0 }
```

### 5. `healthCheck()` - DB 헬스 체크
```typescript
const isHealthy = await healthCheck(); // boolean
```

## 📊 예상 효과

### 성능 개선
- **메모리 사용량**: 50% 감소 (개별 Pool → 통합 Pool)
- **연결 관리**: 자동 최적화 (min: 2, max: 10)
- **쿼리 성능**: 느린 쿼리 자동 감지 (>1초)

### 유지보수성 향상
- **중앙화된 설정**: 1개 파일에서 모든 DB 설정 관리
- **에러 처리**: 통합된 에러 핸들링
- **로깅**: 개발 환경에서 자동 쿼리 로깅

### 안정성 증대
- **자동 정리**: 프로세스 종료 시 연결 자동 해제
- **타임아웃 처리**: 연결/유휴 타임아웃 자동 관리
- **헬스 체크**: 연결 상태 모니터링

## 🛠️ 마이그레이션 단계

### 1단계: 즉시 적용 가능 (30분)
- 새로운 API 개발 시 통합 함수 사용
- 기존 단순한 쿼리들부터 변경

### 2단계: 점진적 적용 (1-2시간)
- 복잡한 API routes 하나씩 변경
- 테스트 파일들 업데이트

### 3단계: 검증 및 모니터링 (30분)
- Pool 상태 모니터링 대시보드 확인
- 성능 지표 측정

## 💡 Best Practices

### 타입 안정성
```typescript
interface User {
  id: number;
  name: string;
  email: string;
}

const users = await query<User>('SELECT * FROM users');
// users는 User[] 타입으로 안전하게 추론됨
```

### 에러 처리
```typescript
try {
  const result = await query('SELECT * FROM products');
  return NextResponse.json(result);
} catch (error) {
  console.error('Database query failed:', error);
  return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
}
```

### 파라미터 바인딩 (SQL 인젝션 방지)
```typescript
// ✅ 안전한 방식
const products = await query('SELECT * FROM products WHERE status = $1', [status]);

// ❌ 위험한 방식  
const products = await query(`SELECT * FROM products WHERE status = '${status}'`);
```

## 🔗 관련 파일
- 구현: `frontend/lib/db/connection-pool.ts`
- 인터페이스: `frontend/lib/db/index.ts`
- 예시: `frontend/app/api/dashboard/stats/route.ts`