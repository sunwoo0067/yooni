'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Plus, Minus, Zap, Clock, PlayCircle } from 'lucide-react'
import { WorkflowTemplates } from './WorkflowTemplates'

interface WorkflowCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface WorkflowRule {
  condition_type: string
  condition_config: any
  action_type: string
  action_config: any
}

export function WorkflowCreateModal({ isOpen, onClose, onSuccess }: WorkflowCreateModalProps) {
  const [showTemplates, setShowTemplates] = useState(true)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [triggerType, setTriggerType] = useState<'event' | 'schedule' | 'manual'>('event')
  const [config, setConfig] = useState<any>({})
  const [rules, setRules] = useState<WorkflowRule[]>([{
    condition_type: 'always',
    condition_config: {},
    action_type: 'notification',
    action_config: { channel: 'email' }
  }])
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!name) return

    setLoading(true)
    try {
      const response = await fetch('/api/workflow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description,
          trigger_type: triggerType,
          config,
          rules
        })
      })

      if (!response.ok) throw new Error('Failed to create workflow')
      
      onSuccess()
      resetForm()
    } catch (error) {
      console.error('Error creating workflow:', error)
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setName('')
    setDescription('')
    setTriggerType('event')
    setConfig({})
    setRules([{
      condition_type: 'always',
      condition_config: {},
      action_type: 'notification',
      action_config: { channel: 'email' }
    }])
    setShowTemplates(true)
  }

  const handleTemplateSelect = (template: any) => {
    setName(template.name)
    setDescription(template.description)
    setTriggerType(template.trigger_type)
    setConfig(template.config)
    setRules(template.rules)
    setShowTemplates(false)
  }

  const addRule = () => {
    setRules([...rules, {
      condition_type: 'always',
      condition_config: {},
      action_type: 'notification',
      action_config: { channel: 'email' }
    }])
  }

  const removeRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index))
  }

  const updateRule = (index: number, field: string, value: any) => {
    const newRules = [...rules]
    if (field.includes('.')) {
      const [parent, child] = field.split('.')
      newRules[index] = {
        ...newRules[index],
        [parent]: {
          ...newRules[index][parent as keyof WorkflowRule],
          [child]: value
        }
      }
    } else {
      newRules[index] = {
        ...newRules[index],
        [field]: value
      }
    }
    setRules(newRules)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>새 워크플로우 만들기</DialogTitle>
          <DialogDescription>
            비즈니스 프로세스를 자동화하는 워크플로우를 생성합니다
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* 템플릿 선택 */}
          {showTemplates ? (
            <div>
              <WorkflowTemplates onSelectTemplate={handleTemplateSelect} />
              <div className="mt-6 text-center">
                <Button
                  variant="outline"
                  onClick={() => setShowTemplates(false)}
                >
                  템플릿 없이 만들기
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* 기본 정보 */}
              <div className="space-y-4">
                <div>
                  <Label htmlFor="name">워크플로우 이름</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="예: 재고 부족 알림"
              />
            </div>

            <div>
              <Label htmlFor="description">설명</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="워크플로우의 목적과 동작을 설명하세요"
                rows={3}
              />
            </div>
          </div>

          {/* 트리거 설정 */}
          <div className="space-y-4">
            <Label>트리거 타입</Label>
            <div className="grid grid-cols-3 gap-3">
              <Card 
                className={`cursor-pointer transition-colors ${
                  triggerType === 'event' ? 'border-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => setTriggerType('event')}
              >
                <CardContent className="p-4 text-center">
                  <Zap className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                  <h4 className="font-medium">이벤트 기반</h4>
                  <p className="text-sm text-gray-600 mt-1">특정 이벤트 발생 시</p>
                </CardContent>
              </Card>

              <Card 
                className={`cursor-pointer transition-colors ${
                  triggerType === 'schedule' ? 'border-green-500 bg-green-50' : ''
                }`}
                onClick={() => setTriggerType('schedule')}
              >
                <CardContent className="p-4 text-center">
                  <Clock className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  <h4 className="font-medium">스케줄</h4>
                  <p className="text-sm text-gray-600 mt-1">주기적으로 실행</p>
                </CardContent>
              </Card>

              <Card 
                className={`cursor-pointer transition-colors ${
                  triggerType === 'manual' ? 'border-yellow-500 bg-yellow-50' : ''
                }`}
                onClick={() => setTriggerType('manual')}
              >
                <CardContent className="p-4 text-center">
                  <PlayCircle className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
                  <h4 className="font-medium">수동 실행</h4>
                  <p className="text-sm text-gray-600 mt-1">필요할 때 실행</p>
                </CardContent>
              </Card>
            </div>

            {/* 트리거 세부 설정 */}
            {triggerType === 'event' && (
              <div className="space-y-3">
                <div>
                  <Label>이벤트 타입</Label>
                  <Select
                    value={config.event_type || ''}
                    onValueChange={(value) => setConfig({ ...config, event_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="이벤트 타입 선택" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="inventory.low_stock">재고 부족</SelectItem>
                      <SelectItem value="order.created">주문 생성</SelectItem>
                      <SelectItem value="price.changed">가격 변경</SelectItem>
                      <SelectItem value="product.updated">상품 업데이트</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>이벤트 소스</Label>
                  <Input
                    value={config.event_source || ''}
                    onChange={(e) => setConfig({ ...config, event_source: e.target.value })}
                    placeholder="예: coupang, zentrade"
                  />
                </div>
              </div>
            )}

            {triggerType === 'schedule' && (
              <div>
                <Label>Cron 표현식</Label>
                <Input
                  value={config.cron || ''}
                  onChange={(e) => setConfig({ ...config, cron: e.target.value })}
                  placeholder="예: 0 9 * * * (매일 오전 9시)"
                />
                <p className="text-sm text-gray-500 mt-1">
                  분 시 일 월 요일 형식으로 입력하세요
                </p>
              </div>
            )}
          </div>

          {/* 규칙 설정 */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <Label>실행 규칙</Label>
              <Button size="sm" variant="outline" onClick={addRule}>
                <Plus className="w-4 h-4 mr-1" />
                규칙 추가
              </Button>
            </div>

            {rules.map((rule, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex justify-between items-start mb-3">
                    <Badge variant="outline">규칙 {index + 1}</Badge>
                    {rules.length > 1 && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removeRule(index)}
                      >
                        <Minus className="w-4 h-4" />
                      </Button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <h5 className="font-medium text-sm">조건</h5>
                      <Select
                        value={rule.condition_type}
                        onValueChange={(value) => updateRule(index, 'condition_type', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="always">항상</SelectItem>
                          <SelectItem value="threshold">임계값</SelectItem>
                          <SelectItem value="field_check">필드 확인</SelectItem>
                          <SelectItem value="comparison">비교</SelectItem>
                        </SelectContent>
                      </Select>

                      {rule.condition_type === 'threshold' && (
                        <div className="space-y-2">
                          <Input
                            placeholder="필드명 (예: stock_quantity)"
                            value={rule.condition_config.field || ''}
                            onChange={(e) => updateRule(index, 'condition_config.field', e.target.value)}
                          />
                          <Select
                            value={rule.condition_config.operator || ''}
                            onValueChange={(value) => updateRule(index, 'condition_config.operator', value)}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="연산자" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="<">미만</SelectItem>
                              <SelectItem value="<=">이하</SelectItem>
                              <SelectItem value=">">초과</SelectItem>
                              <SelectItem value=">=">이상</SelectItem>
                              <SelectItem value="=">같음</SelectItem>
                            </SelectContent>
                          </Select>
                          <Input
                            type="number"
                            placeholder="값"
                            value={rule.condition_config.value || ''}
                            onChange={(e) => updateRule(index, 'condition_config.value', Number(e.target.value))}
                          />
                        </div>
                      )}
                    </div>

                    <div className="space-y-3">
                      <h5 className="font-medium text-sm">액션</h5>
                      <Select
                        value={rule.action_type}
                        onValueChange={(value) => updateRule(index, 'action_type', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="notification">알림 전송</SelectItem>
                          <SelectItem value="api_call">API 호출</SelectItem>
                          <SelectItem value="database_update">데이터베이스 업데이트</SelectItem>
                          <SelectItem value="workflow_trigger">다른 워크플로우 실행</SelectItem>
                        </SelectContent>
                      </Select>

                      {rule.action_type === 'notification' && (
                        <Select
                          value={rule.action_config.channel || ''}
                          onValueChange={(value) => updateRule(index, 'action_config.channel', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="알림 채널" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="email">이메일</SelectItem>
                            <SelectItem value="sms">SMS</SelectItem>
                            <SelectItem value="slack">슬랙</SelectItem>
                          </SelectContent>
                        </Select>
                      )}

                      {rule.action_type === 'api_call' && (
                        <Input
                          placeholder="API 엔드포인트"
                          value={rule.action_config.endpoint || ''}
                          onChange={(e) => updateRule(index, 'action_config.endpoint', e.target.value)}
                        />
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={onClose}>
                  취소
                </Button>
                <Button onClick={handleSubmit} disabled={loading || !name}>
                  {loading ? '생성 중...' : '워크플로우 생성'}
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}