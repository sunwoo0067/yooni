'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, Package, ShoppingCart, FileText,
  Database, Settings, BarChart3, AlertCircle, Workflow
} from 'lucide-react'

export default function ERPLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  const navigation = [
    { name: '대시보드', href: '/erp/dashboard', icon: LayoutDashboard },
    { name: '재고 관리', href: '/erp/inventory', icon: Package },
    { name: '주문 관리', href: '/erp/orders', icon: ShoppingCart },
    { name: '워크플로우', href: '/workflow', icon: Workflow },
    { name: '시스템 로그', href: '/erp/logs', icon: FileText },
    { name: '데이터베이스', href: '/erp/database', icon: Database },
    { name: '통계 분석', href: '/erp/analytics', icon: BarChart3 },
    { name: '설정', href: '/erp/settings', icon: Settings },
  ]

  return (
    <div className="flex h-screen bg-gray-100">
      {/* 사이드바 */}
      <div className="w-64 bg-white shadow-md">
        <div className="p-4">
          <h1 className="text-2xl font-bold text-gray-800">ERP System</h1>
          <p className="text-sm text-gray-600 mt-1">통합 관리 시스템</p>
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
                    ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <item.icon className={`h-5 w-5 mr-3 ${isActive ? 'text-blue-700' : 'text-gray-400'}`} />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* 시스템 상태 */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="bg-green-50 rounded-lg p-3">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <AlertCircle className="h-5 w-5 text-green-400" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">시스템 정상</p>
                <p className="text-xs text-green-600">모든 서비스 작동중</p>
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