'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { toast } from 'sonner'
import {
  FileText, Download, Calendar, Clock, Mail, 
  Plus, Play, Pause, Trash2, Edit, FileSpreadsheet,
  FileImage, BarChart, PieChart, TrendingUp, Package,
  Users, DollarSign
} from 'lucide-react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

interface Schedule {
  id: string
  name: string
  report_type: string
  schedule_time: string
  frequency: string
  recipients: string[]
  params: any
  enabled: boolean
  last_run?: string
  next_run?: string
}

interface Template {
  id: number
  name: string
  description?: string
  template_type: string
  config: any
  created_at: string
}

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState('generate')
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [templates, setTemplates] = useState<Template[]>([])
  const [defaultTemplates, setDefaultTemplates] = useState<any>({})
  const [loading, setLoading] = useState(false)
  const [showScheduleDialog, setShowScheduleDialog] = useState(false)
  const [showTemplateDialog, setShowTemplateDialog] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)

  // 리포트 생성 폼 상태
  const [reportType, setReportType] = useState('sales')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [reportFormat, setReportFormat] = useState('pdf')
  const [includeCharts, setIncludeCharts] = useState(true)

  // 스케줄 폼 상태
  const [scheduleName, setScheduleName] = useState('')
  const [scheduleTime, setScheduleTime] = useState('09:00')
  const [scheduleFrequency, setScheduleFrequency] = useState('daily')
  const [scheduleRecipients, setScheduleRecipients] = useState('')

  useEffect(() => {
    fetchSchedules()
    fetchTemplates()
  }, [])

  const fetchSchedules = async () => {
    try {
      const res = await fetch('http://localhost:8004/schedules')
      if (res.ok) {
        const data = await res.json()
        setSchedules(data.schedules || [])
      }
    } catch (error) {
      console.error('Error fetching schedules:', error)
    }
  }

  const fetchTemplates = async () => {
    try {
      const res = await fetch('http://localhost:8004/templates')
      if (res.ok) {
        const data = await res.json()
        setTemplates(data.templates || [])
        setDefaultTemplates(data.default_templates || {})
      }
    } catch (error) {
      console.error('Error fetching templates:', error)
    }
  }

  const generateReport = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8004/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_type: reportType,
          start_date: startDate,
          end_date: endDate,
          format: reportFormat,
          include_charts: includeCharts
        })
      })

      if (res.ok) {
        const data = await res.json()
        toast.success('리포트가 생성되었습니다')
        
        // 파일 다운로드
        const downloadRes = await fetch(`http://localhost:8004/reports/download/${data.filename}`)
        if (downloadRes.ok) {
          const blob = await downloadRes.blob()
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = data.filename
          a.click()
          window.URL.revokeObjectURL(url)
        }
      } else {
        const error = await res.json()
        toast.error(error.detail || '리포트 생성 실패')
      }
    } catch (error) {
      toast.error('리포트 생성 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const createSchedule = async () => {
    try {
      const res = await fetch('http://localhost:8004/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: scheduleName,
          report_type: reportType,
          schedule_time: scheduleTime,
          frequency: scheduleFrequency,
          recipients: scheduleRecipients.split(',').map(email => email.trim()),
          params: {
            format: reportFormat,
            include_charts: includeCharts
          }
        })
      })

      if (res.ok) {
        toast.success('스케줄이 생성되었습니다')
        setShowScheduleDialog(false)
        fetchSchedules()
        // 폼 초기화
        setScheduleName('')
        setScheduleRecipients('')
      } else {
        const error = await res.json()
        toast.error(error.detail || '스케줄 생성 실패')
      }
    } catch (error) {
      toast.error('스케줄 생성 중 오류가 발생했습니다')
    }
  }

  const deleteSchedule = async (scheduleId: string) => {
    if (!confirm('이 스케줄을 삭제하시겠습니까?')) return

    try {
      const res = await fetch(`http://localhost:8004/schedules/${scheduleId}`, {
        method: 'DELETE'
      })

      if (res.ok) {
        toast.success('스케줄이 삭제되었습니다')
        fetchSchedules()
      }
    } catch (error) {
      toast.error('스케줄 삭제 중 오류가 발생했습니다')
    }
  }

  const runScheduleNow = async (scheduleId: string) => {
    try {
      const res = await fetch(`http://localhost:8004/schedules/${scheduleId}/run`, {
        method: 'POST'
      })

      if (res.ok) {
        toast.success('스케줄 실행이 시작되었습니다')
      }
    } catch (error) {
      toast.error('스케줄 실행 중 오류가 발생했습니다')
    }
  }

  const getReportTypeIcon = (type: string) => {
    switch (type) {
      case 'sales':
        return <DollarSign className="w-4 h-4" />
      case 'inventory':
        return <Package className="w-4 h-4" />
      case 'customer':
        return <Users className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }

  const getReportTypeName = (type: string) => {
    switch (type) {
      case 'sales':
        return '매출 리포트'
      case 'inventory':
        return '재고 리포트'
      case 'customer':
        return '고객 리포트'
      default:
        return type
    }
  }

  const getFrequencyName = (frequency: string) => {
    switch (frequency) {
      case 'daily':
        return '매일'
      case 'weekly':
        return '매주'
      case 'monthly':
        return '매월'
      default:
        return frequency
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">고급 리포팅 시스템</h1>
        <p className="text-gray-600">
          다양한 형식의 리포트를 생성하고 스케줄을 관리하세요
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="generate">리포트 생성</TabsTrigger>
          <TabsTrigger value="schedules">스케줄 관리</TabsTrigger>
          <TabsTrigger value="templates">템플릿</TabsTrigger>
        </TabsList>

        <TabsContent value="generate">
          <Card>
            <CardHeader>
              <CardTitle>새 리포트 생성</CardTitle>
              <CardDescription>
                원하는 리포트 유형과 기간을 선택하여 리포트를 생성하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label>리포트 유형</Label>
                    <Select value={reportType} onValueChange={setReportType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sales">
                          <div className="flex items-center gap-2">
                            <DollarSign className="w-4 h-4" />
                            매출 리포트
                          </div>
                        </SelectItem>
                        <SelectItem value="inventory">
                          <div className="flex items-center gap-2">
                            <Package className="w-4 h-4" />
                            재고 리포트
                          </div>
                        </SelectItem>
                        <SelectItem value="customer">
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            고객 리포트
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {(reportType === 'sales' || reportType === 'customer') && (
                    <>
                      <div>
                        <Label>시작일</Label>
                        <Input
                          type="date"
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                        />
                      </div>
                      <div>
                        <Label>종료일</Label>
                        <Input
                          type="date"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                        />
                      </div>
                    </>
                  )}
                </div>

                <div className="space-y-4">
                  <div>
                    <Label>출력 형식</Label>
                    <Select value={reportFormat} onValueChange={setReportFormat}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pdf">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            PDF
                          </div>
                        </SelectItem>
                        <SelectItem value="excel">
                          <div className="flex items-center gap-2">
                            <FileSpreadsheet className="w-4 h-4" />
                            Excel
                          </div>
                        </SelectItem>
                        <SelectItem value="html">
                          <div className="flex items-center gap-2">
                            <FileImage className="w-4 h-4" />
                            HTML
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="include-charts"
                      checked={includeCharts}
                      onChange={(e) => setIncludeCharts(e.target.checked)}
                      className="rounded"
                    />
                    <Label htmlFor="include-charts">차트 포함</Label>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <Button onClick={generateReport} disabled={loading}>
                  {loading ? '생성 중...' : '리포트 생성'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 빠른 액세스 템플릿 */}
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-4">빠른 리포트</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card 
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => {
                  setReportType('sales')
                  setStartDate(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0])
                  setEndDate(new Date().toISOString().split('T')[0])
                  setReportFormat('pdf')
                }}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">주간 매출 리포트</CardTitle>
                    <TrendingUp className="w-4 h-4 text-green-500" />
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-gray-600">
                    지난 7일간의 매출 분석
                  </p>
                </CardContent>
              </Card>

              <Card 
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => {
                  setReportType('inventory')
                  setReportFormat('excel')
                }}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">재고 현황</CardTitle>
                    <Package className="w-4 h-4 text-blue-500" />
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-gray-600">
                    현재 재고 수준 및 회전율
                  </p>
                </CardContent>
              </Card>

              <Card 
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => {
                  setReportType('customer')
                  setStartDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0])
                  setEndDate(new Date().toISOString().split('T')[0])
                  setReportFormat('pdf')
                }}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">월간 고객 분석</CardTitle>
                    <Users className="w-4 h-4 text-purple-500" />
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-gray-600">
                    지난 30일간의 고객 동향
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="schedules">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">리포트 스케줄</h3>
              <Button onClick={() => setShowScheduleDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                새 스케줄
              </Button>
            </div>

            {schedules.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-600">등록된 스케줄이 없습니다</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {schedules.map((schedule) => (
                  <Card key={schedule.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getReportTypeIcon(schedule.report_type)}
                          <div>
                            <CardTitle className="text-lg">{schedule.name}</CardTitle>
                            <CardDescription>
                              {getReportTypeName(schedule.report_type)} · {getFrequencyName(schedule.frequency)} {schedule.schedule_time}
                            </CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={schedule.enabled ? 'default' : 'secondary'}>
                            {schedule.enabled ? '활성' : '비활성'}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => runScheduleNow(schedule.id)}
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteSchedule(schedule.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500">수신자</p>
                          <p className="font-medium">{schedule.recipients.join(', ')}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">다음 실행</p>
                          <p className="font-medium">
                            {schedule.next_run ? 
                              format(new Date(schedule.next_run), 'yyyy-MM-dd HH:mm', { locale: ko }) : 
                              '-'
                            }
                          </p>
                        </div>
                      </div>
                      {schedule.last_run && (
                        <div className="mt-4 pt-4 border-t">
                          <p className="text-sm text-gray-500">
                            마지막 실행: {format(new Date(schedule.last_run), 'yyyy-MM-dd HH:mm', { locale: ko })}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="templates">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">리포트 템플릿</h3>
              <Button onClick={() => setShowTemplateDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                새 템플릿
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 기본 템플릿 */}
              {Object.entries(defaultTemplates).map(([key, template]: [string, any]) => (
                <Card key={key} className="border-dashed">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm">{template.name}</CardTitle>
                      <Badge variant="outline">기본</Badge>
                    </div>
                    <CardDescription className="text-xs">
                      {template.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              ))}

              {/* 사용자 정의 템플릿 */}
              {templates.map((template) => (
                <Card key={template.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm">{template.name}</CardTitle>
                      <Badge>{template.template_type}</Badge>
                    </div>
                    <CardDescription className="text-xs">
                      {template.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* 스케줄 생성/수정 다이얼로그 */}
      <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>새 스케줄 만들기</DialogTitle>
            <DialogDescription>
              정기적으로 실행될 리포트 스케줄을 설정하세요
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>스케줄 이름</Label>
              <Input
                value={scheduleName}
                onChange={(e) => setScheduleName(e.target.value)}
                placeholder="예: 주간 매출 리포트"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>실행 시간</Label>
                <Input
                  type="time"
                  value={scheduleTime}
                  onChange={(e) => setScheduleTime(e.target.value)}
                />
              </div>
              <div>
                <Label>실행 주기</Label>
                <Select value={scheduleFrequency} onValueChange={setScheduleFrequency}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">매일</SelectItem>
                    <SelectItem value="weekly">매주</SelectItem>
                    <SelectItem value="monthly">매월</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>수신자 이메일 (쉼표로 구분)</Label>
              <Input
                value={scheduleRecipients}
                onChange={(e) => setScheduleRecipients(e.target.value)}
                placeholder="user1@example.com, user2@example.com"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowScheduleDialog(false)}>
              취소
            </Button>
            <Button onClick={createSchedule}>생성</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}