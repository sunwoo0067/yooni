'use client';

import { useState } from 'react';
import { Calendar } from 'lucide-react';

interface CollectionPeriodFilterProps {
  supplierId: number;
  onCollect: (period: CollectionPeriod) => void;
  isCollecting: boolean;
}

export interface CollectionPeriod {
  type: 'days' | 'months' | 'custom';
  value?: number;
  startDate?: string;
  endDate?: string;
}

export default function CollectionPeriodFilter({ supplierId, onCollect, isCollecting }: CollectionPeriodFilterProps) {
  const [showFilter, setShowFilter] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('7days');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');

  const handleCollect = () => {
    let period: CollectionPeriod;

    switch (selectedPeriod) {
      case '7days':
        period = { type: 'days', value: 7 };
        break;
      case '1month':
        period = { type: 'months', value: 1 };
        break;
      case '3months':
        period = { type: 'months', value: 3 };
        break;
      case 'custom':
        if (!customStartDate || !customEndDate) {
          alert('시작일과 종료일을 모두 선택해주세요.');
          return;
        }
        period = { type: 'custom', startDate: customStartDate, endDate: customEndDate };
        break;
      default:
        period = { type: 'days', value: 7 };
    }

    onCollect(period);
    setShowFilter(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowFilter(!showFilter)}
        disabled={isCollecting}
        className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
          isCollecting
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        <Calendar size={16} />
        기간별 수집
      </button>

      {showFilter && !isCollecting && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
          <div className="p-4">
            <h3 className="text-sm font-medium mb-3">수집 기간 선택</h3>
            
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="7days"
                  checked={selectedPeriod === '7days'}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="text-blue-600"
                />
                <span className="text-sm">최근 7일</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="1month"
                  checked={selectedPeriod === '1month'}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="text-blue-600"
                />
                <span className="text-sm">최근 1개월</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="3months"
                  checked={selectedPeriod === '3months'}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="text-blue-600"
                />
                <span className="text-sm">최근 3개월</span>
              </label>
              
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="custom"
                  checked={selectedPeriod === 'custom'}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="text-blue-600"
                />
                <span className="text-sm">기간 직접 선택</span>
              </label>
            </div>

            {selectedPeriod === 'custom' && (
              <div className="mt-3 space-y-2">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">시작일</label>
                  <input
                    type="date"
                    value={customStartDate}
                    onChange={(e) => setCustomStartDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">종료일</label>
                  <input
                    type="date"
                    value={customEndDate}
                    onChange={(e) => setCustomEndDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded"
                  />
                </div>
              </div>
            )}

            <div className="mt-4 flex gap-2">
              <button
                onClick={() => setShowFilter(false)}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleCollect}
                className="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                수집 시작
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}