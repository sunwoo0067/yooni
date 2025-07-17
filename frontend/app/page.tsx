'use client';

import { useState, useEffect } from 'react';
import { Package, AlertTriangle, XCircle, TrendingUp } from 'lucide-react';
import axios from 'axios';

export default function HomePage() {
  const [stockSummary, setStockSummary] = useState({
    total: 0,
    in_stock: 0,
    low_stock: 0,
    out_of_stock: 0
  });

  useEffect(() => {
    fetchStockSummary();
  }, []);

  const fetchStockSummary = async () => {
    try {
      const { data } = await axios.get('/api/stock/summary');
      setStockSummary(data);
    } catch (error) {
      console.error('Failed to fetch stock summary:', error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">대시보드</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">전체 상품</h3>
          <p className="text-2xl font-bold">135,281</p>
          <p className="text-sm text-green-600 mt-2">+371 오늘</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">활성 상품</h3>
          <p className="text-2xl font-bold">125,359</p>
          <p className="text-sm text-gray-600 mt-2">92.67%</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">오늘 주문</h3>
          <p className="text-2xl font-bold">84</p>
          <p className="text-sm text-blue-600 mt-2">+12% 전일 대비</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">오늘 매출</h3>
          <p className="text-2xl font-bold">₩4,382,500</p>
          <p className="text-sm text-green-600 mt-2">+8.3% 전일 대비</p>
        </div>
      </div>

      {/* 재고 상태 요약 추가 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">총 재고 상품</h3>
            <Package className="text-gray-400" size={20} />
          </div>
          <p className="text-2xl font-bold">{stockSummary.total.toLocaleString()}</p>
          <p className="text-sm text-gray-600 mt-2">실시간 재고 현황</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">재고 있음</h3>
            <TrendingUp className="text-green-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-green-600">{stockSummary.in_stock.toLocaleString()}</p>
          <p className="text-sm text-gray-600 mt-2">
            {stockSummary.total > 0 ? `${((stockSummary.in_stock / stockSummary.total) * 100).toFixed(1)}%` : '0%'}
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">저재고</h3>
            <AlertTriangle className="text-yellow-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-yellow-600">{stockSummary.low_stock.toLocaleString()}</p>
          <p className="text-sm text-gray-600 mt-2">10개 미만</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-500">품절</h3>
            <XCircle className="text-red-500" size={20} />
          </div>
          <p className="text-2xl font-bold text-red-600">{stockSummary.out_of_stock.toLocaleString()}</p>
          <p className="text-sm text-red-600 mt-2">즉시 확인 필요</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">공급업체별 상품 분포</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium">도매매</span>
                <span className="text-sm text-gray-600">89,335개 (66.04%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: '66.04%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium">오너클랜</span>
                <span className="text-sm text-gray-600">42,410개 (31.35%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full" style={{ width: '31.35%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium">젠트레이드</span>
                <span className="text-sm text-gray-600">3,536개 (2.61%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-yellow-600 h-2 rounded-full" style={{ width: '2.61%' }}></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-4">상품 상태</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm">활성 (Active)</span>
              <span className="text-sm font-medium">125,359</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm">판매가능 (Available)</span>
              <span className="text-sm font-medium">6,325</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm">비활성 (Inactive)</span>
              <span className="text-sm font-medium">3,531</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm">품절 (Soldout)</span>
              <span className="text-sm font-medium">66</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}