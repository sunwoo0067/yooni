#!/usr/bin/env python3
"""
리포트 템플릿 관리
"""
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


class ReportTemplate:
    """
    커스텀 리포트 템플릿 관리 클래스
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.templates_dir = "reports/templates"
        os.makedirs(self.templates_dir, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                template_type VARCHAR(50) NOT NULL,
                config JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                is_active BOOLEAN DEFAULT true
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def create_template(self, name: str, template_type: str, config: Dict[str, Any], 
                       description: str = None, created_by: str = None) -> int:
        """템플릿 생성"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO report_templates (name, description, template_type, config, created_by)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (name, description, template_type, json.dumps(config), created_by))
        
        template_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return template_id
    
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """템플릿 조회"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM report_templates WHERE id = %s AND is_active = true
        """, (template_id,))
        
        template = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return template
    
    def list_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """템플릿 목록 조회"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if template_type:
            cursor.execute("""
                SELECT * FROM report_templates 
                WHERE template_type = %s AND is_active = true
                ORDER BY name
            """, (template_type,))
        else:
            cursor.execute("""
                SELECT * FROM report_templates 
                WHERE is_active = true
                ORDER BY name
            """)
        
        templates = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return templates
    
    def update_template(self, template_id: int, updates: Dict[str, Any]) -> bool:
        """템플릿 업데이트"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # 업데이트 가능한 필드
        allowed_fields = ['name', 'description', 'config']
        update_parts = []
        values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_parts.append(f"{field} = %s")
                if field == 'config':
                    values.append(json.dumps(value))
                else:
                    values.append(value)
        
        if not update_parts:
            return False
        
        update_parts.append("updated_at = CURRENT_TIMESTAMP")
        values.append(template_id)
        
        query = f"""
            UPDATE report_templates 
            SET {', '.join(update_parts)}
            WHERE id = %s
        """
        
        cursor.execute(query, values)
        conn.commit()
        
        success = cursor.rowcount > 0
        cursor.close()
        conn.close()
        
        return success
    
    def delete_template(self, template_id: int) -> bool:
        """템플릿 삭제 (soft delete)"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE report_templates 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (template_id,))
        
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        conn.close()
        
        return success
    
    def get_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """기본 템플릿 반환"""
        return {
            'sales_summary': {
                'name': '매출 요약 리포트',
                'description': '일일/주간/월간 매출 요약',
                'template_type': 'sales',
                'config': {
                    'sections': [
                        {
                            'type': 'summary',
                            'title': '매출 요약',
                            'metrics': ['total_revenue', 'order_count', 'avg_order_value']
                        },
                        {
                            'type': 'chart',
                            'title': '매출 추이',
                            'chart_type': 'line',
                            'data_source': 'daily_sales'
                        },
                        {
                            'type': 'table',
                            'title': '베스트셀러',
                            'data_source': 'best_sellers',
                            'columns': ['rank', 'product_name', 'sales', 'revenue'],
                            'limit': 10
                        }
                    ],
                    'filters': {
                        'date_range': 'last_7_days'
                    },
                    'format': {
                        'output': 'pdf',
                        'include_charts': True,
                        'language': 'ko'
                    }
                }
            },
            'inventory_status': {
                'name': '재고 현황 리포트',
                'description': '재고 수준 및 회전율 분석',
                'template_type': 'inventory',
                'config': {
                    'sections': [
                        {
                            'type': 'summary',
                            'title': '재고 요약',
                            'metrics': ['total_products', 'total_stock_value', 'low_stock_count']
                        },
                        {
                            'type': 'alert',
                            'title': '재고 부족 경고',
                            'data_source': 'low_stock_items',
                            'threshold': 10
                        },
                        {
                            'type': 'chart',
                            'title': '카테고리별 재고',
                            'chart_type': 'pie',
                            'data_source': 'category_inventory'
                        }
                    ],
                    'format': {
                        'output': 'excel',
                        'include_charts': True
                    }
                }
            },
            'customer_analytics': {
                'name': '고객 분석 리포트',
                'description': 'RFM 분석 및 고객 세그먼트',
                'template_type': 'customer',
                'config': {
                    'sections': [
                        {
                            'type': 'summary',
                            'title': '고객 현황',
                            'metrics': ['total_customers', 'new_customers', 'repeat_rate']
                        },
                        {
                            'type': 'segmentation',
                            'title': 'RFM 세그먼트',
                            'analysis_type': 'rfm'
                        },
                        {
                            'type': 'table',
                            'title': 'VIP 고객',
                            'data_source': 'top_customers',
                            'columns': ['customer_name', 'total_spent', 'order_count'],
                            'limit': 20
                        }
                    ],
                    'filters': {
                        'date_range': 'last_30_days'
                    },
                    'format': {
                        'output': 'pdf',
                        'include_charts': True
                    }
                }
            },
            'performance_dashboard': {
                'name': '성과 대시보드',
                'description': '종합 성과 지표 대시보드',
                'template_type': 'dashboard',
                'config': {
                    'sections': [
                        {
                            'type': 'kpi_grid',
                            'title': '핵심 성과 지표',
                            'kpis': [
                                {
                                    'name': '매출',
                                    'metric': 'total_revenue',
                                    'comparison': 'previous_period',
                                    'format': 'currency'
                                },
                                {
                                    'name': '주문 수',
                                    'metric': 'order_count',
                                    'comparison': 'previous_period',
                                    'format': 'number'
                                },
                                {
                                    'name': '고객 수',
                                    'metric': 'customer_count',
                                    'comparison': 'previous_period',
                                    'format': 'number'
                                },
                                {
                                    'name': '평균 주문액',
                                    'metric': 'avg_order_value',
                                    'comparison': 'previous_period',
                                    'format': 'currency'
                                }
                            ]
                        },
                        {
                            'type': 'multi_chart',
                            'title': '성과 추이',
                            'charts': [
                                {
                                    'title': '매출 추이',
                                    'type': 'line',
                                    'data_source': 'daily_revenue'
                                },
                                {
                                    'title': '카테고리별 판매',
                                    'type': 'bar',
                                    'data_source': 'category_sales'
                                }
                            ]
                        }
                    ],
                    'format': {
                        'output': 'html',
                        'interactive': True
                    }
                }
            }
        }
    
    def create_custom_query_template(self, name: str, description: str, 
                                   query: str, columns: List[Dict[str, str]]) -> int:
        """커스텀 SQL 쿼리 템플릿 생성"""
        config = {
            'sections': [
                {
                    'type': 'custom_query',
                    'title': name,
                    'query': query,
                    'columns': columns
                }
            ],
            'format': {
                'output': 'excel'
            }
        }
        
        return self.create_template(
            name=name,
            template_type='custom',
            config=config,
            description=description
        )
    
    def validate_template(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """템플릿 유효성 검증"""
        errors = []
        warnings = []
        
        # 필수 필드 확인
        if 'sections' not in config:
            errors.append("'sections' 필드가 필요합니다")
        elif not isinstance(config['sections'], list):
            errors.append("'sections'는 리스트여야 합니다")
        else:
            # 각 섹션 검증
            for i, section in enumerate(config['sections']):
                if 'type' not in section:
                    errors.append(f"섹션 {i}: 'type' 필드가 필요합니다")
                if 'title' not in section:
                    warnings.append(f"섹션 {i}: 'title' 필드가 없습니다")
        
        # 형식 검증
        if 'format' in config:
            if 'output' in config['format']:
                valid_formats = ['pdf', 'excel', 'html', 'csv']
                if config['format']['output'] not in valid_formats:
                    errors.append(f"지원되지 않는 출력 형식: {config['format']['output']}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }