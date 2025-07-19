'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, Activity, AlertCircle, BarChart3,
  Clock, Zap, Database, TrendingUp
} from 'lucide-react'

export default function MonitoringLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  const navigation = [
    { name: '실시간 대시보드', href: '/monitoring/dashboard', icon: LayoutDashboard },
    { name: '시스템 성능', href: '/monitoring/performance', icon: Activity },
    { name: '에러 추적', href: '/monitoring/errors', icon: AlertCircle },
    { name: '비즈니스 분석', href: '/monitoring/analytics', icon: BarChart3 },
    { name: 'API 상태', href: '/monitoring/api-status', icon: Zap },
    { name: '스케줄러 모니터링', href: '/monitoring/scheduler', icon: Clock },
    { name: '데이터베이스 상태', href: '/monitoring/database', icon: Database },
  ]

  return (
    <div className="flex h-screen bg-gray-100">
      {/* 사이드바 */}
      <div className="w-64 bg-gray-900 text-white">
        <div className="p-4">
          <h1 className="text-2xl font-bold">모니터링 센터</h1>
          <p className="text-sm text-gray-400 mt-1">실시간 시스템 모니터링</p>
        </div>
        
        <nav className="mt-6">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-4 py-3 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <item.icon className={`h-5 w-5 mr-3`} />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* 실시간 상태 표시 */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm">시스템 상태</span>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-green-400">정상</span>
              </div>
            </div>
            <div className="space-y-1 text-xs text-gray-400">
              <div className="flex justify-between">
                <span>CPU</span>
                <span>32%</span>
              </div>
              <div className="flex justify-between">
                <span>메모리</span>
                <span>4.2GB / 16GB</span>
              </div>
              <div className="flex justify-between">
                <span>디스크</span>
                <span>125GB / 500GB</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  )
}