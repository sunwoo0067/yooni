// 수집 기능 직접 테스트
import dotenv from 'dotenv';
import path from 'path';
import { Pool } from 'pg';

// .env.local 파일 로드
dotenv.config({ path: path.join(process.cwd(), '.env.local') });

// DB 연결 직접 생성
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

async function query<T = any>(text: string, params?: any[]): Promise<T[]> {
  const client = await pool.connect();
  try {
    const result = await client.query(text, params);
    return result.rows;
  } finally {
    client.release();
  }
}

async function getOne<T = any>(text: string, params?: any[]): Promise<T | null> {
  const rows = await query<T>(text, params);
  return rows[0] || null;
}

async function testCollection() {
  console.log('🚀 Starting collection test...');
  console.log('📍 Database URL:', process.env.DATABASE_URL);
  
  try {
    // 1. 테스트할 공급사 확인
    const supplier = await getOne('SELECT * FROM suppliers WHERE id = $1', [1]);
    console.log('✅ Supplier found:', supplier);
    
    // 2. 공급사 설정 확인
    const config = await getOne('SELECT * FROM supplier_configs WHERE supplier_id = $1', [1]);
    console.log('✅ Config found:', config);
    
    // 3. 새 로그 생성
    const log = await getOne(
      `INSERT INTO collection_logs (supplier_id, started_at, status) 
       VALUES ($1, NOW(), 'running') 
       RETURNING id`,
      [1]
    );
    console.log('✅ Log created:', log);
    
    // 4. EnhancedCollectionManager 동적 import
    console.log('🔄 Loading EnhancedCollectionManager...');
    const { default: EnhancedCollectionManager } = await import('./lib/collection/enhanced-collection-manager');
    
    console.log('🔄 Starting collection...');
    const result = await EnhancedCollectionManager.runCollection(1, {
      startDate: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1일 전부터
      endDate: new Date()
    });
    
    console.log('✅ Collection result:', result);
    
    // 5. 로그 업데이트
    await query(
      `UPDATE collection_logs 
       SET completed_at = NOW(), 
           status = $1,
           total_products = $2,
           new_products = $3,
           updated_products = $4,
           failed_products = $5,
           error_message = $6,
           details = $7
       WHERE id = $8`,
      [
        result.success ? 'completed' : 'failed',
        result.statistics?.total || 0,
        result.statistics?.created || 0,
        result.statistics?.updated || 0,
        result.statistics?.failed || 0,
        result.errors ? result.errors.map((e: any) => e.message || e).join('\n') : '',
        JSON.stringify(result),
        log?.id
      ]
    );
    
    console.log('✅ Log updated');
    
    // 6. 상품 수 확인
    const productCount = await getOne(
      'SELECT COUNT(*) as count FROM products WHERE supplier_id = $1',
      [1]
    );
    console.log('✅ Total products for supplier 1:', productCount?.count);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await pool.end();
  }
  
  process.exit(0);
}

testCollection();