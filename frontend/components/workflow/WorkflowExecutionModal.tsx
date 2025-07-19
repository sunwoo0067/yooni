'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle, Activity, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

interface WorkflowExecutionModalProps {
  workflow: any
  isOpen: boolean
  onClose: () => void
}

interface ExecutionResult {
  success: boolean
  execution_id?: number
  workflow_name?: string
  results?: any[]
  error?: string
}

interface StepResult {
  rule_id: number
  action_type: string
  success: boolean
  output_data?: any
  error?: string
}

export function WorkflowExecutionModal({ workflow, isOpen, onClose }: WorkflowExecutionModalProps) {
  const [triggerData, setTriggerData] = useState('{}')
  const [executing, setExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [executionSteps, setExecutionSteps] = useState<StepResult[]>([])

  const handleExecute = async () => {
    setExecuting(true)
    setExecutionResult(null)
    setExecutionSteps([])

    try {
      // 트리거 데이터 파싱
      let parsedData = {}
      try {
        parsedData = JSON.parse(triggerData)
      } catch (e) {
        console.warn('Invalid JSON, using empty object')
      }

      // 워크플로우 실행
      const response = await fetch(`/api/workflow/${workflow.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trigger_data: parsedData })
      })

      if (!response.ok) throw new Error('Failed to execute workflow')
      
      const result = await response.json()
      setExecutionResult(result)
      
      if (result.results) {
        setExecutionSteps(result.results)
      }
    } catch (error) {
      console.error('Error executing workflow:', error)
      setExecutionResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    } finally {
      setExecuting(false)
    }
  }

  const getStatusIcon = (success: boolean) => {
    if (success) {
      return <CheckCircle className="w-5 h-5 text-green-500" />
    } else {
      return <XCircle className="w-5 h-5 text-red-500" />
    }
  }

  const getActionTypeLabel = (type: string) => {
    switch (type) {
      case 'notification':
        return '알림 전송'
      case 'api_call':
        return 'API 호출'
      case 'database_update':
        return '데이터베이스 업데이트'
      case 'workflow_trigger':
        return '워크플로우 트리거'
      default:
        return type
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>워크플로우 실행</DialogTitle>
          <DialogDescription>
            {workflow?.name} 워크플로우를 수동으로 실행합니다
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* 트리거 데이터 입력 */}
          {!executionResult && (
            <div>
              <Label htmlFor="trigger-data">트리거 데이터 (JSON)</Label>
              <Textarea
                id="trigger-data"
                value={triggerData}
                onChange={(e) => setTriggerData(e.target.value)}
                placeholder='{\n  "key": "value"\n}'
                rows={6}
                className="font-mono text-sm"
              />
              <p className="text-sm text-gray-500 mt-1">
                워크플로우에 전달할 데이터를 JSON 형식으로 입력하세요
              </p>
            </div>
          )}

          {/* 실행 결과 */}
          {executionResult && (
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-4">
                  {getStatusIcon(executionResult.success)}
                  <div>
                    <h3 className="font-medium">
                      {executionResult.success ? '실행 성공' : '실행 실패'}
                    </h3>
                    {executionResult.execution_id && (
                      <p className="text-sm text-gray-500">
                        실행 ID: {executionResult.execution_id}
                      </p>
                    )}
                  </div>
                </div>

                {executionResult.error && (
                  <div className="bg-red-50 text-red-700 p-3 rounded text-sm mb-4">
                    {executionResult.error}
                  </div>
                )}

                {/* 스텝별 결과 */}
                {executionSteps.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">실행 단계</h4>
                    {executionSteps.map((step, index) => (
                      <div key={index} className="border rounded p-3">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(step.success)}
                            <Badge variant="outline">
                              {getActionTypeLabel(step.action_type)}
                            </Badge>
                          </div>
                          <Badge variant="secondary" className="text-xs">
                            규칙 #{step.rule_id}
                          </Badge>
                        </div>

                        {step.error && (
                          <div className="text-sm text-red-600 mt-2">
                            {step.error}
                          </div>
                        )}

                        {step.output_data && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-500 mb-1">결과 데이터:</p>
                            <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                              {JSON.stringify(step.output_data, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 실행 중 상태 */}
          {executing && (
            <div className="flex items-center justify-center py-8">
              <Activity className="w-6 h-6 text-blue-500 animate-pulse mr-2" />
              <span>워크플로우 실행 중...</span>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
          {!executionResult ? (
            <>
              <Button variant="outline" onClick={onClose}>
                취소
              </Button>
              <Button onClick={handleExecute} disabled={executing}>
                {executing ? '실행 중...' : '워크플로우 실행'}
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={() => {
                  setExecutionResult(null)
                  setExecutionSteps([])
                  setTriggerData('{}')
                }}
              >
                다시 실행
              </Button>
              <Button onClick={onClose}>
                닫기
              </Button>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}