'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Package, 
  ShoppingCart, 
  BarChart3, 
  Settings,
  Home,
  Users,
  Truck,
  Database,
  FileSpreadsheet,
  LayoutDashboard,
  Store,
  Clock,
  TrendingUp,
  DollarSign,
  Eye
} from 'lucide-react';

const menuItems = [
  {
    title: '대시보드',
    href: '/',
    icon: Home,
  },
  {
    title: 'ERP 통합관리',
    href: '/erp',
    icon: Database,
    subItems: [
      {
        title: 'ERP 대시보드',
        href: '/erp/dashboard',
        icon: LayoutDashboard,
      },
      {
        title: '통합 재고관리',
        href: '/erp/inventory',
        icon: Package,
      },
      {
        title: '통합 주문관리',
        href: '/erp/orders',
        icon: FileSpreadsheet,
      },
    ]
  },
  {
    title: '마켓별 관리',
    href: '/markets',
    icon: Store,
    subItems: [
      {
        title: '쿠팡',
        href: '/coupang/dashboard',
        icon: Store,
      },
      {
        title: '네이버',
        href: '/naver/dashboard',
        icon: Store,
      },
      {
        title: '11번가',
        href: '/eleven/dashboard',
        icon: Store,
      },
    ]
  },
  {
    title: '상품 관리',
    href: '/products',
    icon: Package,
  },
  {
    title: '주문 관리',
    href: '/orders',
    icon: ShoppingCart,
  },
  {
    title: '배송 관리',
    href: '/shipments',
    icon: Truck,
  },
  {
    title: '공급사 관리',
    href: '/suppliers',
    icon: Users,
    subItems: [
      {
        title: '공급사 목록',
        href: '/suppliers',
        icon: Users,
      },
      {
        title: '통합 관리',
        href: '/suppliers/management',
        icon: Database,
      },
    ]
  },
  {
    title: '통계 분석',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    title: '비즈니스 인텔리전스',
    href: '/bi',
    icon: TrendingUp,
    subItems: [
      {
        title: 'BI 대시보드',
        href: '/bi/dashboard',
        icon: LayoutDashboard,
      },
      {
        title: '수익성 분석',
        href: '/bi/profitability',
        icon: DollarSign,
      },
      {
        title: '경쟁사 모니터링',
        href: '/bi/competitors',
        icon: Eye,
      },
      {
        title: '시장 트렌드',
        href: '/bi/trends',
        icon: TrendingUp,
      },
    ]
  },
  {
    title: '작업 스케줄러',
    href: '/scheduler',
    icon: Clock,
  },
  {
    title: '설정',
    href: '/settings',
    icon: Settings,
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isItemActive = (item: any) => {
    if (item.subItems) {
      return item.subItems.some((sub: any) => pathname === sub.href || pathname.startsWith(sub.href));
    }
    return pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
  };

  return (
    <div className="w-64 bg-gray-900 text-white h-screen fixed left-0 top-0 overflow-y-auto">
      <div className="p-6">
        <h1 className="text-2xl font-bold">ERP System</h1>
        <p className="text-sm text-gray-400 mt-1">통합 관리 시스템</p>
      </div>
      
      <nav className="mt-6">
        {menuItems.map((item) => {
          const isActive = isItemActive(item);
          const Icon = item.icon;
          
          if (item.subItems) {
            return (
              <div key={item.href}>
                <div className={`flex items-center gap-3 px-6 py-3 text-gray-300 ${
                  isActive ? 'bg-gray-800' : ''
                }`}>
                  <Icon size={20} />
                  <span className="font-medium">{item.title}</span>
                </div>
                <div className="bg-gray-800/50">
                  {item.subItems.map((subItem) => {
                    const SubIcon = subItem.icon;
                    const isSubActive = pathname === subItem.href || pathname.startsWith(subItem.href);
                    
                    return (
                      <Link
                        key={subItem.href}
                        href={subItem.href}
                        className={`flex items-center gap-3 pl-12 pr-6 py-2 hover:bg-gray-700 transition-colors ${
                          isSubActive ? 'bg-gray-700 border-l-4 border-blue-500' : ''
                        }`}
                      >
                        <SubIcon size={16} />
                        <span className="text-sm">{subItem.title}</span>
                      </Link>
                    );
                  })}
                </div>
              </div>
            );
          }
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition-colors ${
                isActive ? 'bg-gray-800 border-l-4 border-blue-500' : ''
              }`}
            >
              <Icon size={20} />
              <span>{item.title}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}