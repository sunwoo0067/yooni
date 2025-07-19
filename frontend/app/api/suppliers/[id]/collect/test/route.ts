import { NextRequest, NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';

// 테스트용 API - 실제 수집 없이 테이블 구조 확인 및 목업 데이터 생성
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const { id } = params;
    const supplierId = parseInt(id);
    
    // 공급업체 확인
    const supplier = await getOne(
      'SELECT * FROM suppliers WHERE id = $1',
      [supplierId]
    );
    
    if (!supplier) {
      return NextResponse.json(
        { error: '공급업체를 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    // collection_logs 테이블 확인 및 생성
    try {
      await query(`
        CREATE TABLE IF NOT EXISTS collection_logs (
          id SERIAL PRIMARY KEY,
          supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
          started_at TIMESTAMP NOT NULL DEFAULT NOW(),
          completed_at TIMESTAMP,
          status VARCHAR(50) NOT NULL DEFAULT 'running',
          total_products INTEGER DEFAULT 0,
          new_products INTEGER DEFAULT 0,
          updated_products INTEGER DEFAULT 0,
          failed_products INTEGER DEFAULT 0,
          error_message TEXT,
          details JSONB,
          created_at TIMESTAMP DEFAULT NOW()
        )
      `);
    } catch (error) {
      console.log('collection_logs table already exists or error:', error);
    }
    
    // supplier_configs 테이블 확인 및 생성
    try {
      await query(`
        CREATE TABLE IF NOT EXISTS supplier_configs (
          id SERIAL PRIMARY KEY,
          supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
          api_endpoint VARCHAR(500),
          api_key VARCHAR(255),
          api_secret VARCHAR(255),
          api_type VARCHAR(50),
          vendor_id VARCHAR(255),
          account_name VARCHAR(255),
          auth_type VARCHAR(50),
          enabled BOOLEAN DEFAULT true,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        )
      `);
    } catch (error) {
      console.log('supplier_configs table already exists or error:', error);
    }
    
    // products 테이블에 필요한 컬럼 추가
    try {
      await query(`
        ALTER TABLE products 
        ADD COLUMN IF NOT EXISTS stock_quantity INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS stock_status VARCHAR(50) DEFAULT 'in_stock',
        ADD COLUMN IF NOT EXISTS last_stock_check TIMESTAMP,
        ADD COLUMN IF NOT EXISTS metadata JSONB
      `);
    } catch (error) {
      console.log('Column already exists or error:', error);
    }
    
    // 공급사 설정 확인 또는 생성
    let config = await getOne(
      'SELECT * FROM supplier_configs WHERE supplier_id = $1',
      [supplierId]
    );
    
    if (!config) {
      // 기본 설정 생성
      const defaultConfigs = {
        1: { // 오너클랜
          api_endpoint: 'https://api-sandbox.ownerclan.com/v1/graphql',
          api_key: 'test_seller_id',
          api_secret: 'test_secret',
          api_type: 'graphql',
          auth_type: 'jwt'
        },
        2: { // 젠트레이드
          api_endpoint: 'https://zentrade.co.kr/api',
          api_key: 'test_key',
          api_secret: 'test_secret',
          api_type: 'rest',
          auth_type: 'session'
        }
      };
      
      const configData = defaultConfigs[supplierId] || {
        api_endpoint: 'https://api.example.com',
        api_key: 'test_key',
        api_secret: 'test_secret',
        api_type: 'rest',
        auth_type: 'basic'
      };
      
      config = await getOne(
        `INSERT INTO supplier_configs (supplier_id, api_endpoint, api_key, api_secret, api_type, auth_type)
         VALUES ($1, $2, $3, $4, $5, $6)
         RETURNING *`,
        [supplierId, configData.api_endpoint, configData.api_key, configData.api_secret, configData.api_type, configData.auth_type]
      );
    }
    
    // 최근 수집 로그 조회
    const recentLogs = await query(
      `SELECT * FROM collection_logs 
       WHERE supplier_id = $1 
       ORDER BY started_at DESC 
       LIMIT 5`,
      [supplierId]
    );
    
    // 현재 상품 수 조회
    const productCount = await getOne(
      'SELECT COUNT(*) as count FROM products WHERE supplier_id = $1',
      [supplierId]
    );
    
    return NextResponse.json({
      supplier,
      config: {
        ...config,
        api_key: config.api_key ? '***' + config.api_key.slice(-4) : null,
        api_secret: config.api_secret ? '***' : null
      },
      recentLogs,
      currentProductCount: parseInt(productCount?.count || '0'),
      tablesReady: true
    });
    
  } catch (error) {
    console.error('Test API error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '테스트 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}