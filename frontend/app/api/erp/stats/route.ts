import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    // 데이터베이스 통계
    const dbStatsQuery = `
      SELECT 
        pg_database_size(current_database()) as db_size,
        (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count,
        (SELECT count(*) FROM unified_products) as product_count,
        (SELECT count(*) FROM market_orders) as order_count,
        (SELECT count(DISTINCT buyer_email) FROM market_orders WHERE buyer_email IS NOT NULL) as customer_count,
        (SELECT count(DISTINCT account_name) FROM market_accounts WHERE is_active = true) as supplier_count
    `;
    
    const dbStats = await query(dbStatsQuery);
    const dbRow = dbStats[0];
    
    // 재고 통계
    const inventoryQuery = `
      SELECT 
        COUNT(*) as total_products,
        SUM(COALESCE(sale_price * stock_quantity, 0)) as total_value,
        COUNT(CASE WHEN stock_quantity > 0 AND stock_quantity <= 10 THEN 1 END) as low_stock,
        COUNT(CASE WHEN stock_quantity = 0 OR status = 'soldout' THEN 1 END) as out_of_stock,
        market_code,
        COUNT(*) as market_count
      FROM market_products mp
      JOIN market_accounts ma ON mp.market_account_id = ma.id
      JOIN markets m ON ma.market_id = m.id
      WHERE mp.is_active = true
      GROUP BY market_code
    `;
    
    const inventoryStats = await query(inventoryQuery);
    
    // 마켓별 상품 수 집계
    const byMarket: Record<string, number> = {};
    let totalValue = 0;
    let lowStock = 0;
    let outOfStock = 0;
    
    inventoryStats.forEach(row => {
      byMarket[row.market_code] = parseInt(row.market_count);
      totalValue += parseFloat(row.total_value || '0');
      lowStock += parseInt(row.low_stock || '0');
      outOfStock += parseInt(row.out_of_stock || '0');
    });
    
    // 매출 통계
    const salesQuery = `
      WITH sales_data AS (
        SELECT 
          DATE(order_date) as order_day,
          SUM(total_price) as daily_sales,
          market_code
        FROM market_orders mo
        JOIN market_accounts ma ON mo.market_account_id = ma.id
        JOIN markets m ON ma.market_id = m.id
        WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(order_date), market_code
      )
      SELECT 
        SUM(CASE WHEN order_day = CURRENT_DATE THEN daily_sales ELSE 0 END) as today_sales,
        SUM(CASE WHEN order_day >= CURRENT_DATE - INTERVAL '7 days' THEN daily_sales ELSE 0 END) as week_sales,
        SUM(daily_sales) as month_sales,
        market_code,
        SUM(daily_sales) as market_total
      FROM sales_data
      GROUP BY ROLLUP(market_code)
    `;
    
    const salesStats = await query(salesQuery);
    
    let todaySales = 0;
    let weekSales = 0;
    let monthSales = 0;
    const salesByMarket: Record<string, number> = {};
    
    salesStats.forEach(row => {
      if (!row.market_code) {
        // ROLLUP으로 인한 전체 합계
        todaySales = parseFloat(row.today_sales || '0');
        weekSales = parseFloat(row.week_sales || '0');
        monthSales = parseFloat(row.month_sales || '0');
      } else {
        salesByMarket[row.market_code] = parseFloat(row.market_total || '0');
      }
    });
    
    // 운영 통계
    const operationsQuery = `
      SELECT 
        COUNT(CASE WHEN order_status = 'pending' THEN 1 END) as pending_orders,
        COUNT(CASE WHEN order_status IN ('confirmed', 'processing') THEN 1 END) as processing_orders,
        COUNT(CASE WHEN order_status = 'confirmed' AND 
          NOT EXISTS (SELECT 1 FROM market_shipments ms WHERE ms.market_order_id = mo.market_order_id)
          THEN 1 END) as pending_shipments,
        COUNT(CASE WHEN order_status = 'return_requested' THEN 1 END) as returns_to_process
      FROM market_orders mo
      WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
    `;
    
    const operationsStats = await query(operationsQuery);
    const opsRow = operationsStats[0];
    
    // 성장률 계산 (이번주 vs 지난주)
    const growthQuery = `
      WITH weekly_sales AS (
        SELECT 
          CASE 
            WHEN order_date >= CURRENT_DATE - INTERVAL '7 days' THEN 'this_week'
            ELSE 'last_week'
          END as week_period,
          SUM(total_price) as total
        FROM market_orders
        WHERE order_date >= CURRENT_DATE - INTERVAL '14 days'
        GROUP BY week_period
      )
      SELECT 
        MAX(CASE WHEN week_period = 'this_week' THEN total ELSE 0 END) as this_week,
        MAX(CASE WHEN week_period = 'last_week' THEN total ELSE 0 END) as last_week
      FROM weekly_sales
    `;
    
    const growthStats = await query(growthQuery);
    const growthRow = growthStats[0];
    const growthRate = growthRow.last_week > 0 
      ? ((growthRow.this_week - growthRow.last_week) / growthRow.last_week * 100).toFixed(1)
      : 0;
    
    // 백업 정보 (예시)
    const lastBackup = new Date();
    lastBackup.setHours(3, 0, 0, 0);
    
    const stats = {
      database: {
        total_size: formatBytes(parseInt(dbRow.db_size)),
        table_count: parseInt(dbRow.table_count),
        record_counts: {
          products: parseInt(dbRow.product_count),
          orders: parseInt(dbRow.order_count),
          customers: parseInt(dbRow.customer_count),
          suppliers: parseInt(dbRow.supplier_count)
        },
        last_backup: lastBackup.toISOString()
      },
      inventory: {
        total_products: parseInt(dbRow.product_count),
        total_value: Math.round(totalValue),
        low_stock: lowStock,
        out_of_stock: outOfStock,
        by_market: byMarket
      },
      sales: {
        today: Math.round(todaySales),
        this_week: Math.round(weekSales),
        this_month: Math.round(monthSales),
        growth_rate: parseFloat(String(growthRate)),
        by_market: salesByMarket
      },
      operations: {
        pending_orders: parseInt(opsRow.pending_orders),
        processing_orders: parseInt(opsRow.processing_orders),
        pending_shipments: parseInt(opsRow.pending_shipments),
        returns_to_process: parseInt(opsRow.returns_to_process)
      }
    };
    
    return NextResponse.json({
      success: true,
      data: stats
    });
    
  } catch (error) {
    console.error('ERP stats error:', error);
    return NextResponse.json(
      { success: false, error: 'ERP 통계 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}