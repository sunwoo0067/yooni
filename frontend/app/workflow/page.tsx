'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PlayCircle, PauseCircle, Plus, Clock, Zap, Settings } from 'lucide-react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { WorkflowCreateModal } from '@/components/workflow/WorkflowCreateModal'
import { WorkflowDetailModal } from '@/components/workflow/WorkflowDetailModal'
import { WorkflowExecutionModal } from '@/components/workflow/WorkflowExecutionModal'

interface Workflow {
  id: number
  name: string
  description: string
  trigger_type: 'event' | 'schedule' | 'manual'
  config: any
  is_active: boolean
  execution_count: number
  last_executed_at: string | null
  avg_execution_time: number | null
  created_at: string
}

export default function WorkflowPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isExecutionModalOpen, setIsExecutionModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchWorkflows()
  }, [])

  const fetchWorkflows = async () => {
    try {
      const params = new URLSearchParams()
      if (activeTab !== 'all') {
        params.append('trigger_type', activeTab)
      }
      
      const response = await fetch(`/api/workflow?${params}`)
      if (!response.ok) throw new Error('Failed to fetch workflows')
      
      const data = await response.json()
      setWorkflows(data.workflows)
    } catch (error) {
      console.error('Error fetching workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleWorkflow = async (workflow: Workflow) => {
    try {
      const response = await fetch('/api/workflow', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: workflow.id,
          is_active: !workflow.is_active
        })
      })

      if (!response.ok) throw new Error('Failed to toggle workflow')
      
      // 목록 새로고침
      fetchWorkflows()
    } catch (error) {
      console.error('Error toggling workflow:', error)
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

  const getTriggerColor = (type: string) => {
    switch (type) {
      case 'event':
        return 'bg-blue-500'
      case 'schedule':
        return 'bg-green-500'
      case 'manual':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-500'
    }
  }

  const filteredWorkflows = workflows.filter(workflow =>
    workflow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    workflow.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">워크플로우 자동화</h1>
        <p className="text-gray-600">비즈니스 프로세스를 자동화하고 관리합니다</p>
      </div>

      <div className="flex justify-between items-center mb-6">
        <Input
          placeholder="워크플로우 검색..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-md"
        />
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          새 워크플로우
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={(value) => {
        setActiveTab(value)
        fetchWorkflows()
      }}>
        <TabsList className="mb-6">
          <TabsTrigger value="all">전체</TabsTrigger>
          <TabsTrigger value="event">이벤트 기반</TabsTrigger>
          <TabsTrigger value="schedule">스케줄</TabsTrigger>
          <TabsTrigger value="manual">수동 실행</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          {loading ? (
            <div className="text-center py-8">로딩 중...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredWorkflows.map((workflow) => (
                <Card 
                  key={workflow.id} 
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => {
                    setSelectedWorkflow(workflow)
                    setIsDetailModalOpen(true)
                  }}
                >
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{workflow.name}</CardTitle>
                        <CardDescription className="mt-1">
                          {workflow.description}
                        </CardDescription>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleWorkflow(workflow)
                        }}
                      >
                        {workflow.is_active ? (
                          <PauseCircle className="w-5 h-5 text-green-500" />
                        ) : (
                          <PlayCircle className="w-5 h-5 text-gray-400" />
                        )}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Badge className={`${getTriggerColor(workflow.trigger_type)} text-white`}>
                          <span className="flex items-center gap-1">
                            {getTriggerIcon(workflow.trigger_type)}
                            {workflow.trigger_type === 'event' && '이벤트'}
                            {workflow.trigger_type === 'schedule' && '스케줄'}
                            {workflow.trigger_type === 'manual' && '수동'}
                          </span>
                        </Badge>
                        {workflow.config?.cron && (
                          <span className="text-sm text-gray-500">
                            {workflow.config.cron}
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500">실행 횟수:</span>
                          <span className="ml-1 font-medium">{workflow.execution_count || 0}회</span>
                        </div>
                        <div>
                          <span className="text-gray-500">평균 시간:</span>
                          <span className="ml-1 font-medium">
                            {workflow.avg_execution_time 
                              ? `${Math.round(workflow.avg_execution_time)}ms`
                              : '-'}
                          </span>
                        </div>
                      </div>

                      {workflow.last_executed_at && (
                        <div className="text-sm text-gray-500">
                          마지막 실행: {format(new Date(workflow.last_executed_at), 'yyyy-MM-dd HH:mm', { locale: ko })}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* 워크플로우 생성 모달 */}
      <WorkflowCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={() => {
          setIsCreateModalOpen(false)
          fetchWorkflows()
        }}
      />

      {/* 워크플로우 상세 모달 */}
      {selectedWorkflow && (
        <WorkflowDetailModal
          workflow={selectedWorkflow}
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false)
            setSelectedWorkflow(null)
          }}
          onExecute={() => {
            setIsDetailModalOpen(false)
            setIsExecutionModalOpen(true)
          }}
        />
      )}

      {/* 워크플로우 실행 모달 */}
      {selectedWorkflow && (
        <WorkflowExecutionModal
          workflow={selectedWorkflow}
          isOpen={isExecutionModalOpen}
          onClose={() => {
            setIsExecutionModalOpen(false)
            setSelectedWorkflow(null)
            fetchWorkflows()
          }}
        />
      )}
    </div>
  )
}