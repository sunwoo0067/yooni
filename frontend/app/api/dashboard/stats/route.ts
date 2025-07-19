import { NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';

export async function GET() {
  try {
    // Get total products count
    const totalProductsResult = await getOne<{ count: string }>('SELECT COUNT(*) as count FROM products');
    const totalProducts = parseInt(totalProductsResult?.count || '0');
    
    // Get active products count
    const activeProductsResult = await getOne<{ count: string }>(
      "SELECT COUNT(*) as count FROM products WHERE status = 'active'"
    );
    const activeProducts = parseInt(activeProductsResult?.count || '0');
      
    // Get today's orders (check if orders table exists)
    let todayOrders = 0;
    let todayRevenue = 0;
    try {
      const todayOrdersResult = await query(
        "SELECT COUNT(*) as count FROM orders WHERE DATE(created_at) = CURRENT_DATE"
      );
      todayOrders = parseInt(todayOrdersResult[0]?.count || '0');
      
      const todayRevenueResult = await query(
        "SELECT COALESCE(SUM(price), 0) as revenue FROM orders WHERE DATE(created_at) = CURRENT_DATE"
      );
      todayRevenue = parseFloat(todayRevenueResult[0]?.revenue || '0');
    } catch (orderError) {
      console.log('Orders table not available:', orderError);
    }
    
    // Get supplier distribution
    const supplierStatsResult = await query(`
      SELECT 
        COALESCE(s.name, 'Unknown') as supplier,
        COUNT(*) as count
      FROM products p
      LEFT JOIN suppliers s ON p.supplier_id = s.id
      GROUP BY s.name
      ORDER BY count DESC
    `);
    
    const supplierStats = supplierStatsResult.map(row => ({
      name: row.supplier,
      count: parseInt(row.count),
      percentage: ((parseInt(row.count) / totalProducts) * 100).toFixed(2)
    }));
    
    // Get product status distribution
    const statusStatsResult = await query(`
      SELECT 
        COALESCE(status, 'Unknown') as status,
        COUNT(*) as count
      FROM products 
      GROUP BY status
      ORDER BY count DESC
    `);
    
    const statusStats = statusStatsResult.map(row => ({
      status: row.status,
      count: parseInt(row.count)
    }));
    
    // Get inventory stats
    const inventoryStatsResult = await query(`
      SELECT 
        COUNT(*) FILTER (WHERE stock_quantity > 0) as in_stock,
        COUNT(*) FILTER (WHERE stock_quantity = 0) as out_of_stock,
        COUNT(*) FILTER (WHERE stock_quantity > 0 AND stock_quantity < 10) as low_stock
      FROM products
    `);
    
    const inventoryStats = {
      total: totalProducts,
      inStock: parseInt(inventoryStatsResult[0]?.in_stock || '0'),
      outOfStock: parseInt(inventoryStatsResult[0]?.out_of_stock || '0'),
      lowStock: parseInt(inventoryStatsResult[0]?.low_stock || '0')
    };
    
    return NextResponse.json({
      success: true,
      data: {
        products: {
          total: totalProducts,
          active: activeProducts,
          activePercentage: totalProducts > 0 ? ((activeProducts / totalProducts) * 100).toFixed(2) : '0'
        },
        orders: {
          today: todayOrders,
          todayRevenue: todayRevenue
        },
        suppliers: supplierStats,
        status: statusStats,
        inventory: inventoryStats
      }
    });
    
  } catch (error) {
    console.error('Dashboard stats error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch dashboard stats',
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}