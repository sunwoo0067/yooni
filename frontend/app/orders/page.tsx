'use client';

import { useState } from 'react';
import { useOrders } from '@/lib/hooks/useOrders';
import { SUPPLIERS } from '@/lib/types/product';
import { ORDER_STATUS } from '@/lib/types/order';
import { Search, Calendar, Download, ChevronLeft, ChevronRight, Package } from 'lucide-react';

export default function OrdersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [tempSearch, setTempSearch] = useState('');
  const [supplier, setSupplier] = useState('');
  const [status, setStatus] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  const { data, isLoading, error } = useOrders({
    page,
    limit: 20,
    search,
    supplier,
    status,
    startDate,
    endDate,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(tempSearch);
    setPage(1);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(price);
  };

  const getStatusBadge = (status: string) => {
    const statusInfo = ORDER_STATUS[status as keyof typeof ORDER_STATUS];
    if (!statusInfo) return null;
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusInfo.color}`}>
        {statusInfo.label}
      </span>
    );
  };

  // 오늘 날짜 가져오기
  const today = new Date().toISOString().split('T')[0];

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          주문 목록을 불러오는 중 오류가 발생했습니다.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">주문 관리</h1>
        <p className="text-gray-600 mt-2">주문 내역을 조회하고 처리 상태를 관리합니다.</p>
      </div>

      {/* 필터 영역 */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">검색</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                <input
                  type="text"
                  value={tempSearch}
                  onChange={(e) => setTempSearch(e.target.value)}
                  placeholder="주문번호, 고객명, 연락처 검색..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
            
            <div className="w-48">
              <label className="block text-sm font-medium text-gray-700 mb-1">공급업체</label>
              <select
                value={supplier}
                onChange={(e) => { setSupplier(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              >
                <option value="">전체</option>
                {Object.values(SUPPLIERS).map((sup) => (
                  <option key={sup.id} value={sup.id}>{sup.name}</option>
                ))}
              </select>
            </div>
            
            <div className="w-40">
              <label className="block text-sm font-medium text-gray-700 mb-1">주문 상태</label>
              <select
                value={status}
                onChange={(e) => { setStatus(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              >
                <option value="">전체</option>
                {Object.entries(ORDER_STATUS).map(([value, info]) => (
                  <option key={value} value={value}>{info.label}</option>
                ))}
              </select>
            </div>
            
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              검색
            </button>
          </div>
          
          <div className="flex gap-4 items-end">
            <div className="flex items-center gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">시작일</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
                  max={today}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">종료일</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
                  max={today}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setStartDate(today);
                    setEndDate(today);
                    setPage(1);
                  }}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  오늘
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const date = new Date();
                    date.setDate(date.getDate() - 7);
                    setStartDate(date.toISOString().split('T')[0]);
                    setEndDate(today);
                    setPage(1);
                  }}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  최근 7일
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const date = new Date();
                    date.setMonth(date.getMonth() - 1);
                    setStartDate(date.toISOString().split('T')[0]);
                    setEndDate(today);
                    setPage(1);
                  }}
                  className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  최근 1개월
                </button>
              </div>
            </div>
            
            <div className="ml-auto">
              <button
                type="button"
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 flex items-center gap-2"
              >
                <Download size={20} />
                내보내기
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* 주문 목록 테이블 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  주문번호
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  고객 정보
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  공급업체
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상품
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  금액
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  주문일시
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    로딩 중...
                  </td>
                </tr>
              ) : data?.orders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    검색 결과가 없습니다.
                  </td>
                </tr>
              ) : (
                data?.orders.map((order) => (
                  <tr 
                    key={order.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => window.location.href = `/orders/${order.id}`}
                  >
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {order.order_number}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {order.customer_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {order.customer_phone}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {SUPPLIERS[order.supplier_id]?.name || order.supplier_id}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Package size={16} className="text-gray-400" />
                        <span className="text-sm text-gray-900">
                          {order.item_count}개 상품
                        </span>
                        <span className="text-sm text-gray-500">
                          (총 {order.total_quantity}개)
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 font-medium">
                        {formatPrice(order.total_amount)}
                      </div>
                      {order.shipping_fee > 0 && (
                        <div className="text-xs text-gray-500">
                          배송비 {formatPrice(order.shipping_fee)}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(order.status)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {new Date(order.created_at).toLocaleDateString('ko-KR')}
                      <br />
                      <span className="text-xs text-gray-500">
                        {new Date(order.created_at).toLocaleTimeString('ko-KR', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* 페이지네이션 */}
        {data && data.pagination.totalPages > 1 && (
          <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                전체 <span className="font-medium">{data.pagination.total}</span>개 중{' '}
                <span className="font-medium">{(page - 1) * 20 + 1}</span> -{' '}
                <span className="font-medium">
                  {Math.min(page * 20, data.pagination.total)}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft size={20} />
                </button>
                <span className="px-4 py-1 border border-gray-300 rounded-md bg-gray-50">
                  {page} / {data.pagination.totalPages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page === data.pagination.totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight size={20} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}