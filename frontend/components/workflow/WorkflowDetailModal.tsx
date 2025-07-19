'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PlayCircle, Clock, Zap, Activity, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

interface WorkflowDetailModalProps {
  workflow: any
  isOpen: boolean
  onClose: () => void
  onExecute: () => void
}

interface Execution {
  id: number
  status: string
  started_at: string
  completed_at: string | null
  execution_time_ms: number | null
  trigger_source: string
  error_message: string | null
}

export function WorkflowDetailModal({ workflow, isOpen, onClose, onExecute }: WorkflowDetailModalProps) {
  const [executions, setExecutions] = useState<Execution[]>([])
  const [rules, setRules] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isOpen && workflow) {
      fetchWorkflowDetails()
    }
  }, [isOpen, workflow])

  const fetchWorkflowDetails = async () => {
    try {
      // 워크플로우 규칙 조회
      const rulesResponse = await fetch(`/api/workflow/${workflow.id}/rules`)
      if (rulesResponse.ok) {
        const rulesData = await rulesResponse.json()
        setRules(rulesData.rules || [])
      }

      // 실행 이력 조회
      const executionsResponse = await fetch(`/api/workflow/${workflow.id}/executions`)
      if (executionsResponse.ok) {
        const executionsData = await executionsResponse.json()
        setExecutions(executionsData.executions || [])
      }
    } catch (error) {
      console.error('Error fetching workflow details:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'running':
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '성공'
      case 'failed':
        return '실패'
      case 'running':
        return '실행 중'
      case 'cancelled':
        return '취소됨'
      default:
        return '대기 중'
    }
  }

  const getTriggerIcon = (type: string) => {
    switch (type) {
      case 'event':
        return <Zap className="w-4 h-4" />
      case 'schedule':
        return <Clock className="w-4 h-4" />
      case 'manual':
        return <PlayCircle className="w-4 h-4" />
      default:
        return null
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>{workflow?.name}</span>
            <div className="flex items-center gap-2">
              <Badge variant={workflow?.is_active ? 'default' : 'secondary'}>
                {workflow?.is_active ? '활성' : '비활성'}
              </Badge>
              {workflow?.trigger_type === 'manual' && (
                <Button size="sm" onClick={onExecute}>
                  <PlayCircle className="w-4 h-4 mr-1" />
                  실행
                </Button>
              )}
            </div>
          </DialogTitle>
          <DialogDescription>
            {workflow?.description}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="overview" className="mt-4">
          <TabsList>
            <TabsTrigger value="overview">개요</TabsTrigger>
            <TabsTrigger value="rules">규칙</TabsTrigger>
            <TabsTrigger value="executions">실행 이력</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardContent className="p-4">
                <h3 className="font-medium mb-3">트리거 설정</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">타입:</span>
                    <Badge variant="outline" className="gap-1">
                      {getTriggerIcon(workflow?.trigger_type)}
                      {workflow?.trigger_type === 'event' && '이벤트'}
                      {workflow?.trigger_type === 'schedule' && '스케줄'}
                      {workflow?.trigger_type === 'manual' && '수동'}
                    </Badge>
                  </div>

                  {workflow?.trigger_type === 'event' && workflow?.config && (
                    <>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">이벤트:</span>
                        <span className="font-mono text-sm">{workflow.config.event_type}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">소스:</span>
                        <span className="font-mono text-sm">{workflow.config.event_source}</span>
                      </div>
                    </>
                  )}

                  {workflow?.trigger_type === 'schedule' && workflow?.config?.cron && (
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">Cron:</span>
                      <span className="font-mono text-sm">{workflow.config.cron}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <h3 className="font-medium mb-3">통계</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-gray-500">총 실행 횟수:</span>
                    <p className="text-2xl font-bold">{workflow?.execution_count || 0}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">평균 실행 시간:</span>
                    <p className="text-2xl font-bold">
                      {workflow?.avg_execution_time 
                        ? `${Math.round(workflow.avg_execution_time)}ms`
                        : '-'}
                    </p>
                  </div>
                  {workflow?.last_executed_at && (
                    <div className="col-span-2">
                      <span className="text-gray-500">마지막 실행:</span>
                      <p className="text-sm">
                        {format(new Date(workflow.last_executed_at), 'yyyy-MM-dd HH:mm:ss', { locale: ko })}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rules" className="space-y-3">
            {loading ? (
              <div className="text-center py-8">로딩 중...</div>
            ) : rules.length === 0 ? (
              <div className="text-center py-8 text-gray-500">규칙이 없습니다</div>
            ) : (
              rules.map((rule, index) => (
                <Card key={rule.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <Badge variant="outline">규칙 {index + 1}</Badge>
                      {!rule.is_active && (
                        <Badge variant="secondary">비활성</Badge>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium text-sm mb-2">조건</h4>
                        <div className="space-y-1 text-sm">
                          <div className="flex items-center gap-2">
                            <span className="text-gray-500">타입:</span>
                            <span className="font-mono">{rule.condition_type}</span>
                          </div>
                          {rule.condition_config && (
                            <div className="bg-gray-50 rounded p-2 mt-1">
                              <pre className="text-xs overflow-x-auto">
                                {JSON.stringify(rule.condition_config, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-medium text-sm mb-2">액션</h4>
                        <div className="space-y-1 text-sm">
                          <div className="flex items-center gap-2">
                            <span className="text-gray-500">타입:</span>
                            <span className="font-mono">{rule.action_type}</span>
                          </div>
                          {rule.action_config && (
                            <div className="bg-gray-50 rounded p-2 mt-1">
                              <pre className="text-xs overflow-x-auto">
                                {JSON.stringify(rule.action_config, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          <TabsContent value="executions" className="space-y-3">
            {loading ? (
              <div className="text-center py-8">로딩 중...</div>
            ) : executions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">실행 이력이 없습니다</div>
            ) : (
              executions.map((execution) => (
                <Card key={execution.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(execution.status)}
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">
                              {getStatusText(execution.status)}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {execution.trigger_source}
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-500">
                            {format(new Date(execution.started_at), 'yyyy-MM-dd HH:mm:ss', { locale: ko })}
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        {execution.execution_time_ms && (
                          <div className="text-sm">
                            <span className="text-gray-500">실행 시간:</span>
                            <span className="ml-1 font-mono">{execution.execution_time_ms}ms</span>
                          </div>
                        )}
                        {execution.error_message && (
                          <div className="text-sm text-red-500 mt-1">
                            {execution.error_message}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}