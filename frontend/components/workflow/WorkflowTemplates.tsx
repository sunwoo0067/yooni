'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Package, ShoppingCart, FileText, TrendingUp } from 'lucide-react'

interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
  icon: React.ReactNode
  trigger_type: 'event' | 'schedule' | 'manual'
  config: any
  rules: any[]
}

const templates: WorkflowTemplate[] = [
  {
    id: 'low-stock-alert',
    name: '재고 부족 알림',
    description: '재고가 설정된 임계치 이하로 떨어지면 알림을 보냅니다',
    category: 'inventory',
    icon: <Package className="w-6 h-6" />,
    trigger_type: 'event',
    config: {
      event_type: 'inventory.low_stock',
      event_source: 'system'
    },
    rules: [
      {
        condition_type: 'threshold',
        condition_config: {
          field: 'stock_quantity',
          operator: '<=',
          value: 10
        },
        action_type: 'notification',
        action_config: {
          channel: 'email',
          template: 'low_stock_alert'
        }
      }
    ]
  },
  {
    id: 'new-order-process',
    name: '신규 주문 처리',
    description: '신규 주문이 들어오면 자동으로 검증하고 처리합니다',
    category: 'order',
    icon: <ShoppingCart className="w-6 h-6" />,
    trigger_type: 'event',
    config: {
      event_type: 'order.created',
      event_source: 'coupang'
    },
    rules: [
      {
        condition_type: 'always',
        condition_config: {},
        action_type: 'api_call',
        action_config: {
          endpoint: '/api/orders/validate',
          method: 'POST'
        }
      },
      {
        condition_type: 'field_check',
        condition_config: {
          field: 'validation_status',
          value: 'passed'
        },
        action_type: 'database_update',
        action_config: {
          table: 'orders',
          set: { status: 'processing' }
        }
      }
    ]
  },
  {
    id: 'daily-sales-report',
    name: '일일 매출 리포트',
    description: '매일 자정에 일일 매출 리포트를 생성하고 이메일로 발송합니다',
    category: 'reporting',
    icon: <FileText className="w-6 h-6" />,
    trigger_type: 'schedule',
    config: {
      cron: '0 0 * * *'
    },
    rules: [
      {
        condition_type: 'always',
        condition_config: {},
        action_type: 'api_call',
        action_config: {
          endpoint: '/api/reports/daily-sales',
          method: 'GET'
        }
      },
      {
        condition_type: 'always',
        condition_config: {},
        action_type: 'notification',
        action_config: {
          channel: 'email',
          template: 'daily_sales_report'
        }
      }
    ]
  },
  {
    id: 'price-auto-adjust',
    name: '가격 자동 조정',
    description: '경쟁사 가격 변동 시 자동으로 가격을 조정합니다',
    category: 'pricing',
    icon: <TrendingUp className="w-6 h-6" />,
    trigger_type: 'event',
    config: {
      event_type: 'competitor.price_change',
      event_source: 'price_monitor'
    },
    rules: [
      {
        condition_type: 'comparison',
        condition_config: {
          field: 'competitor_price',
          operator: '<',
          compare_field: 'our_price',
          margin: 0.95
        },
        action_type: 'api_call',
        action_config: {
          endpoint: '/api/products/adjust-price',
          method: 'POST',
          params: {
            strategy: 'match_competitor',
            margin: 0.98
          }
        }
      }
    ]
  }
]

interface WorkflowTemplatesProps {
  onSelectTemplate: (template: WorkflowTemplate) => void
}

export function WorkflowTemplates({ onSelectTemplate }: WorkflowTemplatesProps) {
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'inventory':
        return 'bg-blue-100 text-blue-800'
      case 'order':
        return 'bg-green-100 text-green-800'
      case 'reporting':
        return 'bg-purple-100 text-purple-800'
      case 'pricing':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium mb-2">워크플로우 템플릿</h3>
        <p className="text-sm text-gray-600">
          미리 정의된 템플릿을 사용하여 빠르게 워크플로우를 생성하세요
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map((template) => (
          <Card
            key={template.id}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => onSelectTemplate(template)}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    {template.icon}
                  </div>
                  <div>
                    <CardTitle className="text-base">{template.name}</CardTitle>
                    <CardDescription className="text-sm mt-1">
                      {template.description}
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Badge className={getCategoryColor(template.category)}>
                  {template.category === 'inventory' && '재고'}
                  {template.category === 'order' && '주문'}
                  {template.category === 'reporting' && '리포트'}
                  {template.category === 'pricing' && '가격'}
                </Badge>
                <Badge variant="outline">
                  {template.trigger_type === 'event' && '이벤트'}
                  {template.trigger_type === 'schedule' && '스케줄'}
                  {template.trigger_type === 'manual' && '수동'}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}