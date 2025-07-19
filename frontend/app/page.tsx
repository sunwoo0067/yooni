'use client';

import { useState, useEffect } from 'react';
import { Package, AlertTriangle, XCircle, TrendingUp } from 'lucide-react';
import axios from 'axios';

interface DashboardStats {
  products: {
    total: number;
    active: number;
    activePercentage: string;
  };
  orders: {
    today: number;
    todayRevenue: number;
  };
  suppliers: Array<{
    name: string;
    count: number;
    percentage: string;
  }>;
  status: Array<{
    status: string;
    count: number;
  }>;
  inventory: {
    total: number;
    inStock: number;
    outOfStock: number;
    lowStock: number;
  };
}

export default function HomePage() {
  const [dashboardData, setDashboardData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const { data } = await axios.get('/api/dashboard/stats');
      if (data.success) {
        setDashboardData(data.data);
      } else {
        setError(data.error || 'Failed to fetch dashboard data');
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setError('Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">대시보드</h1>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">데이터를 불러오는 중...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">대시보드</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">데이터를 불러오는 중 오류가 발생했습니다: {error}</p>
          <button 
            onClick={fetchDashboardData}
            className="mt-2 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">대시보드</h1>
        <p className="text-gray-600">데이터가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">대시보드</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">전체 상품</h3>
          <p className="text-2xl font-bold">{dashboardData.products.total.toLocaleString()}</p>
          <p className="text-sm text-gray-600 mt-2">실시간 데이터</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">활성 상품</h3>
          <p className="text-2xl font-bold">{dashboardData.products.active.toLocaleString()}</p>
          <p className="text-sm text-gray-600 mt-2">{dashboardData.products.activePercentage}%</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">오늘 주문</h3>
          <p className="text-2xl font-bold">{dashboardData.orders.today.toLocaleString()}</p>
          <p className="text-sm text-blue-600 mt-2">실시간 주문</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">오늘 매출</h3>
          <p className="text-2xl font-bold">₩{dashboardData.orders.todayRevenue.toLocaleString()}</p>
          <p className="text-sm text-green-600 mt-2">실시간 매출</p>
        </div>
      </div>

      {/* 재고 상태 요약 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">총 재고 상품</h3>
            <Package className="text-gray-400" size={20} />
          </div>
          <p className="text-2xl font-bold">{dashboardData.inventory.total.toLocaleString()}</p>
          <p className="text-sm text-gray-600 mt-2">실시간 재고 현황</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">재고 있음</h3>
            <TrendingUp className="text-green-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-green-600">{dashboardData.inventory.inStock.toLocaleString()}</p>
          <p className="text-sm text-gray-600 mt-2">
            {dashboardData.inventory.total > 0 ? `${((dashboardData.inventory.inStock / dashboardData.inventory.total) * 100).toFixed(1)}%` : '0%'}
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">저재고</h3>
            <AlertTriangle className="text-yellow-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-yellow-600">{dashboardData.inventory.lowStock.toLocaleString()}</p>
          <p className="text-sm text-gray-600 mt-2">10개 미만</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">품절</h3>
            <XCircle className="text-red-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-red-600">{dashboardData.inventory.outOfStock.toLocaleString()}</p>
          <p className="text-sm text-red-600 mt-2">즉시 확인 필요</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">공급업체별 상품 분포</h2>
          <div className="space-y-4">
            {dashboardData.suppliers.map((supplier, index) => {
              const colors = ['bg-blue-600', 'bg-green-600', 'bg-yellow-600', 'bg-purple-600', 'bg-red-600'];
              const color = colors[index % colors.length];
              return (
                <div key={supplier.name}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">{supplier.name}</span>
                    <span className="text-sm text-gray-600">
                      {supplier.count.toLocaleString()}개 ({supplier.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`${color} h-2 rounded-full`} 
                      style={{ width: `${supplier.percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">상품 상태</h2>
          <div className="space-y-3">
            {dashboardData.status.map((statusItem) => (
              <div key={statusItem.status} className="flex justify-between">
                <span className="text-sm capitalize">{statusItem.status}</span>
                <span className="text-sm font-medium">{statusItem.count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}