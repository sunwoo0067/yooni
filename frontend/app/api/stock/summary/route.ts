import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    // 먼저 stock_status 컬럼이 있는지 확인
    try {
      const checkColumn = await query(`
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name = 'stock_status'
        LIMIT 1
      `);
      
      if (!checkColumn || checkColumn.length === 0) {
        // 컬럼이 없으면 기본값 반환
        return NextResponse.json({
          total: 0,
          in_stock: 0,
          low_stock: 0,
          out_of_stock: 0
        });
      }
    } catch (err) {
      console.error('Error checking column:', err);
    }
    
    const summary = await query(`
      SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE stock_status = 'in_stock') as in_stock,
        COUNT(*) FILTER (WHERE stock_status = 'low_stock') as low_stock,
        COUNT(*) FILTER (WHERE stock_status = 'out_of_stock') as out_of_stock
      FROM products
    `);
    
    return NextResponse.json({
      total: parseInt(summary[0]?.total || '0'),
      in_stock: parseInt(summary[0]?.in_stock || '0'),
      low_stock: parseInt(summary[0]?.low_stock || '0'),
      out_of_stock: parseInt(summary[0]?.out_of_stock || '0')
    });
  } catch (error) {
    console.error('Error fetching stock summary:', error);
    return NextResponse.json(
      { error: 'Failed to fetch stock summary' },
      { status: 500 }
    );
  }
}