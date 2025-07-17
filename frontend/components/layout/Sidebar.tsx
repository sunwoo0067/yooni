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
  Truck
} from 'lucide-react';

const menuItems = [
  {
    title: '대시보드',
    href: '/',
    icon: Home,
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
    title: '거래처 관리',
    href: '/suppliers',
    icon: Users,
  },
  {
    title: '통계 분석',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    title: '설정',
    href: '/settings',
    icon: Settings,
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 bg-gray-900 text-white h-screen fixed left-0 top-0">
      <div className="p-6">
        <h1 className="text-2xl font-bold">ERP System</h1>
        <p className="text-sm text-gray-400 mt-1">통합 관리 시스템</p>
      </div>
      
      <nav className="mt-6">
        {menuItems.map((item) => {
          const isActive = pathname === item.href || 
                          (item.href !== '/' && pathname.startsWith(item.href));
          const Icon = item.icon;
          
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