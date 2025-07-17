'use client';

import { useState } from 'react';
import { useProducts } from '@/lib/hooks/useProducts';
import { SUPPLIERS } from '@/lib/types/product';
import { Search, Filter, Download, ChevronLeft, ChevronRight, Package, AlertTriangle, XCircle } from 'lucide-react';

export default function ProductsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [tempSearch, setTempSearch] = useState('');
  const [supplier, setSupplier] = useState('');
  const [status, setStatus] = useState('');
  
  const { data, isLoading, error } = useProducts({
    page,
    limit: 20,
    search,
    supplier,
    status,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(tempSearch);
    setPage(1);
  };

  const formatPrice = (price: number | null) => {
    if (!price) return '-';
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(price);
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      soldout: 'bg-red-100 text-red-800',
      available: 'bg-blue-100 text-blue-800',
    };
    
    const labels = {
      active: '활성',
      inactive: '비활성',
      soldout: '품절',
      available: '판매가능',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800'}`}>
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  };

  const getStockBadge = (stockStatus?: string, quantity?: number) => {
    if (!stockStatus) {
      return <span className="text-sm text-gray-500">-</span>;
    }

    const config = {
      in_stock: {
        icon: Package,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        label: '재고있음'
      },
      low_stock: {
        icon: AlertTriangle,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50',
        label: '저재고'
      },
      out_of_stock: {
        icon: XCircle,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        label: '품절'
      }
    };

    const status = config[stockStatus as keyof typeof config] || config.out_of_stock;
    const Icon = status.icon;

    return (
      <div className={`flex items-center gap-2 px-2 py-1 rounded-lg ${status.bgColor}`}>
        <Icon size={16} className={status.color} />
        <span className={`text-sm font-medium ${status.color}`}>
          {status.label}
          {quantity !== undefined && quantity > 0 && ` (${quantity})`}
        </span>
      </div>
    );
  };

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          상품 목록을 불러오는 중 오류가 발생했습니다.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">상품 관리</h1>
        <p className="text-gray-600 mt-2">전체 상품 목록을 조회하고 관리합니다.</p>
      </div>

      {/* 필터 영역 */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
        <form onSubmit={handleSearch} className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">검색</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={tempSearch}
                onChange={(e) => setTempSearch(e.target.value)}
                placeholder="상품명, 브랜드, 상품코드 검색..."
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
            <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="">전체</option>
              <option value="active">활성</option>
              <option value="available">판매가능</option>
              <option value="inactive">비활성</option>
              <option value="soldout">품절</option>
            </select>
          </div>
          
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            검색
          </button>
          
          <button
            type="button"
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 flex items-center gap-2"
          >
            <Download size={20} />
            내보내기
          </button>
        </form>
      </div>

      {/* 상품 목록 테이블 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상품 정보
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  공급업체
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  가격
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  재고
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  등록일
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    로딩 중...
                  </td>
                </tr>
              ) : data?.products.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    검색 결과가 없습니다.
                  </td>
                </tr>
              ) : (
                data?.products.map((product) => (
                  <tr 
                    key={product.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => window.location.href = `/products/${product.id}`}
                  >
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {product.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {product.product_key}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {SUPPLIERS[product.supplier_id]?.name || product.supplier_id}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{formatPrice(product.price)}</div>
                    </td>
                    <td className="px-6 py-4">
                      {getStockBadge(product.stock_status, product.stock_quantity)}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(product.status)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {new Date(product.created_at).toLocaleDateString('ko-KR')}
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