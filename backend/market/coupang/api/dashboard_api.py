#!/usr/bin/env python3
"""
쿠팡 대시보드 API
프론트엔드를 위한 데이터 제공
"""
import os
import sys
import json
import argparse
from datetime import datetime

# 상위 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from market.coupang.dashboard import CoupangDashboardClient, CoupangStatsAnalyzer

def main():
    parser = argparse.ArgumentParser(description='쿠팡 대시보드 API')
    parser.add_argument('--type', default='summary', 
                       choices=['summary', 'orders', 'products', 'performance', 'insights'],
                       help='데이터 타입')
    parser.add_argument('--days', type=int, default=7, help='조회 기간 (일)')
    
    args = parser.parse_args()
    
    try:
        dashboard = CoupangDashboardClient()
        
        if args.type == 'summary':
            data = dashboard.get_dashboard_summary()
        elif args.type == 'orders':
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=args.days-1)
            data = dashboard.get_order_statistics(
                start_date.isoformat(), 
                end_date.isoformat()
            )
        elif args.type == 'performance':
            data = dashboard.get_performance_metrics()
        elif args.type == 'insights':
            analyzer = CoupangStatsAnalyzer()
            data = {
                'sales_trend': analyzer.analyze_sales_trend(days=args.days),
                'product_performance': analyzer.analyze_product_performance(days=args.days),
                'customer_behavior': analyzer.analyze_customer_behavior(days=args.days),
                'insights': analyzer.generate_insights()
            }
            analyzer.close()
        else:
            data = {}
        
        result = {
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        dashboard.close()
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    
    # JSON 출력
    print(json.dumps(result, ensure_ascii=False, default=str))

if __name__ == '__main__':
    from datetime import timedelta
    main()