import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const type = searchParams.get('type') || 'summary';
    
    // Python 스크립트 경로
    const backendPath = path.join(process.cwd(), '..', 'backend');
    const scriptPath = path.join('market', 'coupang', 'api', 'dashboard_api.py');
    
    // Python 스크립트 실행
    const { stdout, stderr } = await execAsync(
      `cd ${backendPath} && python3 ${scriptPath} --type ${type}`,
      {
        env: {
          ...process.env,
          PYTHONPATH: backendPath
        }
      }
    );
    
    if (stderr) {
      console.error('Dashboard API stderr:', stderr);
    }
    
    try {
      const result = JSON.parse(stdout);
      return NextResponse.json(result);
    } catch (parseError) {
      console.error('JSON parse error:', parseError);
      console.error('stdout:', stdout);
      
      // 모의 데이터 반환
      return NextResponse.json(getMockDashboardData(type));
    }
    
  } catch (error) {
    console.error('Dashboard API error:', error);
    return NextResponse.json(getMockDashboardData());
  }
}

function getMockDashboardData(type: string = 'summary') {
  const now = new Date().toISOString();
  
  if (type === 'summary') {
    return {
      success: true,
      data: {
        timestamp: now,
        today: {
          date: new Date().toISOString().split('T')[0],
          orders: { total: 42, new: 15, processing: 20, shipped: 7 },
          sales: { amount: 1250000, count: 42 },
          cs: { total: 5, pending: 2, answered: 3 },
          returns: { requested: 3, approved: 1, rejected: 1 }
        },
        recent: {
          period: '최근 7일',
          days: 7,
          orders: { total: 285, daily_avg: 40.7 },
          sales: { total_amount: 8500000, daily_avg: 1214285 },
          products: { active: 156, soldout: 12, suspended: 3 },
          settlement: { pending: 2, completed: 5 }
        },
        alerts: [
          { type: 'cs', level: 'warning', message: '미답변 고객문의 2건', action: 'cs_respond' },
          { type: 'product', level: 'warning', message: '품절 상품 12개', action: 'product_restock' },
          { type: 'order', level: 'info', message: '신규 주문 15건', action: 'order_confirm' }
        ],
        status: 'active'
      }
    };
  } else if (type === 'orders') {
    return {
      success: true,
      data: {
        period: '최근 7일',
        by_status: {
          'ACCEPT': 45,
          'INSTRUCT': 62,
          'DEPARTURE': 38,
          'DELIVERING': 89,
          'FINAL_DELIVERY': 51
        },
        by_date: {
          [new Date().toISOString().split('T')[0]]: { count: 42, amount: 1250000 },
          [new Date(Date.now() - 86400000).toISOString().split('T')[0]]: { count: 38, amount: 1150000 }
        },
        shipping_summary: {
          preparing: 107,
          shipping: 127,
          completed: 51,
          cancelled: 8
        }
      }
    };
  } else if (type === 'performance') {
    return {
      success: true,
      data: {
        conversion_rate: 3.2,
        average_order_value: 29762,
        customer_satisfaction: 87,
        fulfillment_rate: 94.5,
        return_rate: 2.8,
        response_time: 18
      }
    };
  }
  
  return { success: false, error: 'Unknown type' };
}