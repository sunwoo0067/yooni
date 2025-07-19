'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import {
  Database, Activity, TrendingUp, AlertTriangle, 
  RefreshCw, Trash2, Search, Zap, HardDrive,
  BarChart3, Key, Hash, Clock
} from 'lucide-react'
import { Line, Doughnut } from 'react-chartjs-2'

interface CacheStats {
  stats: Record<string, any>
  summary: {
    total_hits: number
    total_misses: number
    total_sets: number
    hit_rate: number
    key_count: number
  }
}

interface CacheInfo {
  server: {
    version: string
    uptime_seconds: number
    connected_clients: number
  }
  memory: {
    used_memory: number
    used_memory_human: string
    used_memory_peak: number
    used_memory_peak_human: string
  }
  stats: {
    total_connections_received: number
    total_commands_processed: number
    instantaneous_ops_per_sec: number
    keyspace_hits: number
    keyspace_misses: number
  }
}

interface MemoryUsage {
  pattern: string
  key_count: number
  estimated_memory: number
  average_key_size: number
}

export default function CacheMonitorPage() {
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null)
  const [cacheInfo, setCacheInfo] = useState<CacheInfo | null>(null)
  const [memoryUsage, setMemoryUsage] = useState<MemoryUsage | null>(null)
  const [keys, setKeys] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [searchPattern, setSearchPattern] = useState('*')
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchCacheInfo()
    fetchCacheStats()
    const interval = setInterval(() => {
      fetchCacheInfo()
      fetchCacheStats()
    }, 5000) // 5초마다 업데이트

    return () => clearInterval(interval)
  }, [])

  const fetchCacheInfo = async () => {
    try {
      const res = await fetch('http://localhost:8005/cache/info')
      if (res.ok) {
        const data = await res.json()
        setCacheInfo(data)
      }
    } catch (error) {
      console.error('Error fetching cache info:', error)
    }
  }

  const fetchCacheStats = async () => {
    try {
      const res = await fetch('http://localhost:8005/cache/stats')
      if (res.ok) {
        const data = await res.json()
        setCacheStats(data)
      }
    } catch (error) {
      console.error('Error fetching cache stats:', error)
    }
  }

  const fetchMemoryUsage = async (pattern: string = '*') => {
    setLoading(true)
    try {
      const res = await fetch(`http://localhost:8005/cache/memory?pattern=${encodeURIComponent(pattern)}`)
      if (res.ok) {
        const data = await res.json()
        setMemoryUsage(data)
      }
    } catch (error) {
      console.error('Error fetching memory usage:', error)
    } finally {
      setLoading(false)
    }
  }

  const searchKeys = async () => {
    setLoading(true)
    try {
      const res = await fetch(`http://localhost:8005/cache/keys?pattern=${encodeURIComponent(searchPattern)}`)
      if (res.ok) {
        const data = await res.json()
        setKeys(data.keys || [])
      }
    } catch (error) {
      console.error('Error searching keys:', error)
    } finally {
      setLoading(false)
    }
  }

  const invalidateCache = async (pattern: string) => {
    if (!confirm(`패턴 "${pattern}"과 일치하는 모든 캐시를 삭제하시겠습니까?`)) return

    try {
      const res = await fetch('http://localhost:8005/cache/invalidate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pattern })
      })

      if (res.ok) {
        const data = await res.json()
        toast.success(`${data.deleted_count}개의 캐시가 삭제되었습니다`)
        fetchCacheStats()
        if (keys.length > 0) searchKeys()
      }
    } catch (error) {
      toast.error('캐시 삭제 중 오류가 발생했습니다')
    }
  }

  const resetStats = async () => {
    try {
      const res = await fetch('http://localhost:8005/cache/stats/reset', {
        method: 'POST'
      })

      if (res.ok) {
        toast.success('통계가 초기화되었습니다')
        fetchCacheStats()
      }
    } catch (error) {
      toast.error('통계 초기화 중 오류가 발생했습니다')
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${days}일 ${hours}시간 ${minutes}분`
  }

  // 차트 데이터
  const hitRateChartData = {
    labels: ['Hit', 'Miss'],
    datasets: [{
      data: [
        cacheStats?.summary.total_hits || 0,
        cacheStats?.summary.total_misses || 0
      ],
      backgroundColor: ['#10b981', '#ef4444'],
      borderWidth: 0
    }]
  }

  const performanceChartData = {
    labels: ['Hits', 'Misses', 'Sets'],
    datasets: [{
      label: '작업 수',
      data: [
        cacheStats?.summary.total_hits || 0,
        cacheStats?.summary.total_misses || 0,
        cacheStats?.summary.total_sets || 0
      ],
      backgroundColor: ['#3b82f6', '#ef4444', '#10b981']
    }]
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">캐시 모니터링</h1>
        <p className="text-gray-600">
          Redis 캐시 상태 및 성능 모니터링
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="stats">통계</TabsTrigger>
          <TabsTrigger value="keys">키 관리</TabsTrigger>
          <TabsTrigger value="memory">메모리</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          {/* 서버 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Redis 버전</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{cacheInfo?.server.version || '-'}</div>
                <p className="text-xs text-gray-500 mt-1">
                  가동 시간: {cacheInfo ? formatUptime(cacheInfo.server.uptime_seconds) : '-'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">메모리 사용량</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{cacheInfo?.memory.used_memory_human || '-'}</div>
                <p className="text-xs text-gray-500 mt-1">
                  최대: {cacheInfo?.memory.used_memory_peak_human || '-'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">연결된 클라이언트</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{cacheInfo?.server.connected_clients || 0}</div>
                <p className="text-xs text-gray-500 mt-1">
                  OPS: {cacheInfo?.stats.instantaneous_ops_per_sec || 0}/sec
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 성능 지표 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>캐시 히트율</CardTitle>
                <CardDescription>
                  전체 히트율: {cacheStats ? (cacheStats.summary.hit_rate * 100).toFixed(1) : 0}%
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <Doughnut
                    data={hitRateChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom'
                        }
                      }
                    }}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4 mt-4 text-sm">
                  <div className="text-center">
                    <p className="text-gray-500">Hits</p>
                    <p className="font-semibold">{cacheStats?.summary.total_hits.toLocaleString() || 0}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-500">Misses</p>
                    <p className="font-semibold">{cacheStats?.summary.total_misses.toLocaleString() || 0}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-500">Sets</p>
                    <p className="font-semibold">{cacheStats?.summary.total_sets.toLocaleString() || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>시스템 통계</CardTitle>
                <CardDescription>
                  Redis 서버 통계
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">총 연결 수</span>
                      <span className="text-sm font-medium">
                        {cacheInfo?.stats.total_connections_received.toLocaleString() || 0}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">총 명령 처리</span>
                      <span className="text-sm font-medium">
                        {cacheInfo?.stats.total_commands_processed.toLocaleString() || 0}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">Keyspace Hits</span>
                      <span className="text-sm font-medium">
                        {cacheInfo?.stats.keyspace_hits?.toLocaleString() || 0}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">Keyspace Misses</span>
                      <span className="text-sm font-medium">
                        {cacheInfo?.stats.keyspace_misses?.toLocaleString() || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="stats">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>캐시 통계</CardTitle>
                  <CardDescription>
                    키별 캐시 성능 통계
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={resetStats}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  통계 초기화
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {cacheStats && Object.keys(cacheStats.stats).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(cacheStats.stats).map(([key, stats]) => {
                    const total = stats.hits + stats.misses
                    const hitRate = total > 0 ? (stats.hits / total) * 100 : 0

                    return (
                      <div key={key} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Key className="w-4 h-4 text-gray-500" />
                            <span className="font-mono text-sm">{key}</span>
                          </div>
                          <Badge variant={hitRate >= 80 ? 'default' : hitRate >= 50 ? 'secondary' : 'destructive'}>
                            {hitRate.toFixed(1)}% 히트율
                          </Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Hits:</span> {stats.hits}
                          </div>
                          <div>
                            <span className="text-gray-500">Misses:</span> {stats.misses}
                          </div>
                          <div>
                            <span className="text-gray-500">Sets:</span> {stats.sets}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    아직 수집된 통계가 없습니다.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="keys">
          <Card>
            <CardHeader>
              <CardTitle>키 관리</CardTitle>
              <CardDescription>
                캐시 키 검색 및 관리
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <Input
                  placeholder="검색 패턴 (예: products:*)"
                  value={searchPattern}
                  onChange={(e) => setSearchPattern(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchKeys()}
                />
                <Button onClick={searchKeys} disabled={loading}>
                  <Search className="w-4 h-4 mr-2" />
                  검색
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => invalidateCache(searchPattern)}
                  disabled={loading || searchPattern === '*'}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  삭제
                </Button>
              </div>

              {keys.length > 0 ? (
                <div className="space-y-1">
                  <p className="text-sm text-gray-500 mb-2">{keys.length}개의 키를 찾았습니다</p>
                  <div className="max-h-96 overflow-y-auto border rounded p-2">
                    {keys.map((key) => (
                      <div key={key} className="flex items-center justify-between py-1 px-2 hover:bg-gray-50">
                        <span className="font-mono text-sm">{key}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => invalidateCache(key)}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : searchPattern !== '*' ? (
                <Alert>
                  <AlertDescription>
                    일치하는 키가 없습니다.
                  </AlertDescription>
                </Alert>
              ) : null}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="memory">
          <Card>
            <CardHeader>
              <CardTitle>메모리 사용량 분석</CardTitle>
              <CardDescription>
                패턴별 메모리 사용량 추정
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-4">
                <Input
                  placeholder="분석할 패턴 (예: products:*)"
                  value={searchPattern}
                  onChange={(e) => setSearchPattern(e.target.value)}
                />
                <Button onClick={() => fetchMemoryUsage(searchPattern)} disabled={loading}>
                  <HardDrive className="w-4 h-4 mr-2" />
                  분석
                </Button>
              </div>

              {memoryUsage && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-gray-500">패턴</p>
                      <p className="font-mono font-semibold">{memoryUsage.pattern}</p>
                    </div>
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-gray-500">키 개수</p>
                      <p className="text-xl font-semibold">{memoryUsage.key_count.toLocaleString()}</p>
                    </div>
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-gray-500">예상 메모리</p>
                      <p className="text-xl font-semibold">{formatBytes(memoryUsage.estimated_memory)}</p>
                    </div>
                    <div className="border rounded-lg p-4">
                      <p className="text-sm text-gray-500">평균 키 크기</p>
                      <p className="text-xl font-semibold">{formatBytes(memoryUsage.average_key_size)}</p>
                    </div>
                  </div>

                  <Alert>
                    <AlertDescription>
                      메모리 사용량은 샘플링을 통해 추정된 값입니다.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}