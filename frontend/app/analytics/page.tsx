'use client';

import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  ResponsiveContainer 
} from 'recharts';
import { TrendingUp, TrendingDown, Package, ShoppingCart, DollarSign, Users } from 'lucide-react';

export default function AnalyticsPage() {
  // 샘플 데이터
  const salesData = [
    { date: '12/11', 매출: 3200000, 주문수: 45 },
    { date: '12/12', 매출: 2800000, 주문수: 38 },
    { date: '12/13', 매출: 3500000, 주문수: 52 },
    { date: '12/14', 매출: 4100000, 주문수: 63 },
    { date: '12/15', 매출: 3800000, 주문수: 58 },
    { date: '12/16', 매출: 4500000, 주문수: 72 },
    { date: '12/17', 매출: 4382500, 주문수: 84 },
  ];

  const categoryData = [
    { name: '의류', value: 45000, percentage: 33.3 },
    { name: '전자제품', value: 35000, percentage: 25.9 },
    { name: '생활용품', value: 28000, percentage: 20.7 },
    { name: '식품', value: 15000, percentage: 11.1 },
    { name: '기타', value: 12281, percentage: 9.0 },
  ];

  const supplierPerformance = [
    { name: '도매매', 매출: 18500000, 주문수: 245, 평균단가: 75510 },
    { name: '오너클랜', 매출: 12300000, 주문수: 189, 평균단가: 65079 },
    { name: '젠트레이드', 매출: 2100000, 주문수: 42, 평균단가: 50000 },
  ];

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">통계 분석</h1>
        <p className="text-gray-600 mt-2">판매 현황과 실적을 분석합니다.</p>
      </div>

      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <DollarSign className="text-blue-600" size={24} />
            </div>
            <span className="flex items-center text-sm text-green-600">
              <TrendingUp size={16} className="mr-1" />
              12.5%
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-500">이번 달 매출</h3>
          <p className="text-2xl font-bold mt-1">₩87,635,400</p>
          <p className="text-xs text-gray-500 mt-2">전월 대비 +₩9,743,200</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <ShoppingCart className="text-green-600" size={24} />
            </div>
            <span className="flex items-center text-sm text-green-600">
              <TrendingUp size={16} className="mr-1" />
              8.3%
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-500">이번 달 주문</h3>
          <p className="text-2xl font-bold mt-1">1,847</p>
          <p className="text-xs text-gray-500 mt-2">전월 대비 +142건</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Package className="text-purple-600" size={24} />
            </div>
            <span className="flex items-center text-sm text-red-600">
              <TrendingDown size={16} className="mr-1" />
              3.2%
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-500">평균 주문 금액</h3>
          <p className="text-2xl font-bold mt-1">₩47,450</p>
          <p className="text-xs text-gray-500 mt-2">전월 대비 -₩1,570</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Users className="text-yellow-600" size={24} />
            </div>
            <span className="flex items-center text-sm text-green-600">
              <TrendingUp size={16} className="mr-1" />
              15.7%
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-500">활성 고객</h3>
          <p className="text-2xl font-bold mt-1">892</p>
          <p className="text-xs text-gray-500 mt-2">전월 대비 +121명</p>
        </div>
      </div>

      {/* 차트 영역 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* 일별 매출 추이 */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">일별 매출 추이</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={salesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis tickFormatter={(value) => `${value / 1000000}M`} />
              <Tooltip 
                formatter={(value: any) => formatPrice(value)}
                contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb' }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="매출" 
                stroke="#3B82F6" 
                strokeWidth={2}
                dot={{ fill: '#3B82F6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 카테고리별 판매 비중 */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">카테고리별 판매 비중</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ percentage }) => `${percentage.toFixed(1)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => formatPrice(value)} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {categoryData.map((item, index) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span>{item.name}</span>
                </div>
                <span className="font-medium">{formatPrice(item.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 공급업체별 실적 */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold mb-4">공급업체별 실적</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={supplierPerformance}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis yAxisId="left" tickFormatter={(value) => `${value / 1000000}M`} />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip 
              formatter={(value: any, name: string) => {
                if (name === '매출' || name === '평균단가') {
                  return formatPrice(value);
                }
                return value;
              }}
              contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb' }}
            />
            <Legend />
            <Bar yAxisId="left" dataKey="매출" fill="#3B82F6" />
            <Bar yAxisId="right" dataKey="주문수" fill="#10B981" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}