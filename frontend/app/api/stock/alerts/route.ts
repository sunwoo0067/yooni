import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const unreadOnly = searchParams.get('unread') === 'true';
    
    let alertsQuery = `
      SELECT 
        a.*,
        p.name as product_name,
        p.product_key,
        s.name as supplier_name
      FROM stock_alerts a
      JOIN products p ON a.product_id = p.id
      JOIN suppliers s ON p.supplier_id = s.id
    `;
    
    if (unreadOnly) {
      alertsQuery += ' WHERE a.is_read = false';
    }
    
    alertsQuery += ' ORDER BY a.created_at DESC LIMIT 50';
    
    const alerts = await query(alertsQuery);
    
    // 읽지 않은 알림 개수
    const unreadCount = await query(
      'SELECT COUNT(*) as count FROM stock_alerts WHERE is_read = false'
    );
    
    return NextResponse.json({
      alerts,
      unreadCount: parseInt(unreadCount[0]?.count || '0')
    });
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch alerts' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const { alertIds } = await request.json();
    
    if (alertIds && alertIds.length > 0) {
      await query(
        'UPDATE stock_alerts SET is_read = true WHERE id = ANY($1)',
        [alertIds]
      );
    }
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error updating alerts:', error);
    return NextResponse.json(
      { error: 'Failed to update alerts' },
      { status: 500 }
    );
  }
}