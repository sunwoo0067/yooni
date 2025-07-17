'use client';

import { useState, useEffect } from 'react';
import { 
  Package, 
  RefreshCw, 
  Settings, 
  Calendar, 
  AlertCircle,
  CheckCircle,
  Clock,
  Activity,
  Plus,
  Users
} from 'lucide-react';
import axios from 'axios';
import { Supplier } from '@/lib/types/supplier';
import AddSupplierModal from '@/components/suppliers/AddSupplierModal';
import CollectionPeriodFilter, { CollectionPeriod } from '@/components/suppliers/CollectionPeriodFilter';
import MultiAccountModal from '@/components/suppliers/MultiAccountModal';
import ScheduleManagementModal from '@/components/suppliers/ScheduleManagementModal';

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [collectingSuppliers, setCollectingSuppliers] = useState<Set<number>>(new Set());
  const [supplierLogs, setSupplierLogs] = useState<Record<number, any[]>>({});
  const [supplierConfigs, setSupplierConfigs] = useState<Record<number, any>>({});
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedSupplierForSettings, setSelectedSupplierForSettings] = useState<number | null>(null);
  const [showMultiAccountModal, setShowMultiAccountModal] = useState(false);
  const [selectedSupplierForMultiAccount, setSelectedSupplierForMultiAccount] = useState<{id: number, name: string} | null>(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const { data } = await axios.get('/api/suppliers');
      setSuppliers(data);
      
      // 각 공급사의 최근 로그와 설정 가져오기
      for (const supplier of data) {
        fetchSupplierLogs(supplier.id);
        fetchSupplierConfig(supplier.id);
      }
    } catch (error) {
      console.error('Failed to fetch suppliers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSupplierLogs = async (supplierId: number) => {
    try {
      const { data } = await axios.get(`/api/suppliers/${supplierId}/logs?limit=3`);
      setSupplierLogs(prev => ({ ...prev, [supplierId]: data }));
    } catch (error) {
      console.error('Failed to fetch logs for supplier:', supplierId, error);
    }
  };

  const fetchSupplierConfig = async (supplierId: number) => {
    try {
      const { data } = await axios.get(`/api/suppliers/${supplierId}/config`);
      setSupplierConfigs(prev => ({ ...prev, [supplierId]: data }));
    } catch (error) {
      console.error('Failed to fetch config for supplier:', supplierId, error);
    }
  };

  const startCollection = async (supplierId: number, period?: CollectionPeriod) => {
    try {
      setCollectingSuppliers(prev => new Set(prev).add(supplierId));
      
      const payload: any = {};
      if (period) {
        if (period.type === 'custom') {
          payload.startDate = period.startDate;
          payload.endDate = period.endDate;
        } else {
          payload.periodType = period.type;
          payload.periodValue = period.value;
        }
      }
      
      const { data } = await axios.post(`/api/suppliers/${supplierId}/collect`, payload);
      alert(data.message);
      
      // 3초 후 상태 업데이트
      setTimeout(() => {
        setCollectingSuppliers(prev => {
          const next = new Set(prev);
          next.delete(supplierId);
          return next;
        });
        fetchSuppliers();
        fetchSupplierLogs(supplierId);
      }, 3000);
    } catch (error) {
      console.error('Failed to start collection:', error);
      setCollectingSuppliers(prev => {
        const next = new Set(prev);
        next.delete(supplierId);
        return next;
      });
    }
  };

  const formatNumber = (num: string | number) => {
    return new Intl.NumberFormat('ko-KR').format(Number(num));
  };

  const formatDate = (date: string | Date | null) => {
    if (!date) return '-';
    return new Date(date).toLocaleString('ko-KR');
  };

  const getSupplierConfig = (supplierId: number) => {
    // 데이터베이스에서 가져온 실제 설정 사용
    return supplierConfigs[supplierId] || {};
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">로딩 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">공급사 관리</h1>
          <p className="text-gray-600 mt-2">공급업체 정보와 상품 수집을 관리합니다.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus size={20} />
          새 공급사 추가
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {suppliers.map((supplier) => {
          const config = getSupplierConfig(supplier.id);
          const isCollecting = collectingSuppliers.has(supplier.id);
          
          return (
            <div key={supplier.id} className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                      {supplier.name}
                      {config.enabled ? (
                        <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                          자동 수집 활성화
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                          수동 수집
                        </span>
                      )}
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                      공급사 ID: {supplier.id} | 등록일: {formatDate(supplier.created_at)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <CollectionPeriodFilter
                      supplierId={supplier.id}
                      onCollect={(period) => startCollection(supplier.id, period)}
                      isCollecting={isCollecting}
                    />
                    <button
                      onClick={() => startCollection(supplier.id)}
                      disabled={isCollecting}
                      className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                        isCollecting 
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                          : 'bg-green-600 text-white hover:bg-green-700'
                      }`}
                    >
                      {isCollecting ? (
                        <>
                          <RefreshCw size={16} className="animate-spin" />
                          수집 중...
                        </>
                      ) : (
                        <>
                          <RefreshCw size={16} />
                          전체 수집
                        </>
                      )}
                    </button>
                    <button 
                      onClick={() => setSelectedSupplierForSettings(supplier.id)}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                    >
                      <Settings size={16} />
                      설정
                    </button>
                    <button 
                      onClick={() => {
                        setSelectedSupplierForMultiAccount({id: supplier.id, name: supplier.name});
                        setShowMultiAccountModal(true);
                      }}
                      className="px-4 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 flex items-center gap-2"
                    >
                      <Users size={16} />
                      멀티계정
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  {/* 상품 통계 */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-700">상품 현황</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">전체 상품</span>
                        <span className="text-sm font-medium">{formatNumber(supplier.product_count)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">활성 상품</span>
                        <span className="text-sm font-medium text-green-600">
                          {formatNumber(supplier.active_products)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">비활성 상품</span>
                        <span className="text-sm font-medium text-gray-500">
                          {formatNumber(Number(supplier.product_count) - Number(supplier.active_products))}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* API 정보 */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-700">연동 정보</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">연동 방식</span>
                        <span className="text-sm font-medium">{config.api_type || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">엔드포인트</span>
                        <span className="text-sm font-medium text-blue-600 truncate max-w-xs" title={config.endpoint}>
                          {config.endpoint ? config.endpoint.split('//')[1] : '-'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 수집 일정 */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-700">수집 일정</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">수집 주기</span>
                        <span className="text-sm font-medium">
                          {config.schedule === 'daily' && '매일'}
                          {config.schedule === 'hourly' && '매시간'}
                          {config.schedule === 'manual' && '수동'}
                          {!config.schedule && '-'}
                        </span>
                      </div>
                      {config.schedule_time && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">수집 시간</span>
                          <span className="text-sm font-medium">{config.schedule_time}</span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">마지막 업데이트</span>
                        <span className="text-sm font-medium">
                          {supplier.last_product_update 
                            ? new Date(supplier.last_product_update).toLocaleDateString('ko-KR')
                            : '-'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 최근 수집 상태 */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-700">최근 수집 이력</h3>
                    <div className="space-y-2">
                      {supplierLogs[supplier.id]?.length > 0 ? (
                        supplierLogs[supplier.id].map((log: any) => (
                          <div key={log.id} className="flex items-center gap-2 text-sm">
                            {log.status === 'completed' && <CheckCircle size={16} className="text-green-500" />}
                            {log.status === 'failed' && <AlertCircle size={16} className="text-red-500" />}
                            {log.status === 'partial' && <AlertCircle size={16} className="text-yellow-500" />}
                            {log.status === 'running' && <Clock size={16} className="text-blue-500 animate-pulse" />}
                            <span>{new Date(log.started_at).toLocaleString('ko-KR', { 
                              month: '2-digit', 
                              day: '2-digit', 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}</span>
                            <span className="text-gray-500">
                              {log.status === 'completed' && `성공 (${log.total_products}개)`}
                              {log.status === 'failed' && '실패'}
                              {log.status === 'partial' && `부분 실패 (${log.failed_products}개)`}
                              {log.status === 'running' && '진행 중'}
                            </span>
                          </div>
                        ))
                      ) : (
                        <div className="text-sm text-gray-500">수집 이력 없음</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 수집 진행 상태 표시 */}
                {isCollecting && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Activity className="text-blue-600 animate-pulse" size={20} />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-blue-900">상품 수집 진행 중</p>
                        <p className="text-xs text-blue-700">수집이 완료되면 자동으로 업데이트됩니다.</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 일괄 작업 영역 */}
      <div className="mt-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">일괄 작업</h2>
        <div className="flex gap-4">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
            <RefreshCw size={16} />
            전체 수집 시작
          </button>
          <button 
            onClick={() => setShowScheduleModal(true)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Calendar size={16} />
            수집 일정 관리
          </button>
          <button 
            onClick={() => window.location.href = '/collection-logs'}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Activity size={16} />
            수집 로그 보기
          </button>
        </div>
      </div>

      {/* 모달 컴포넌트 */}
      <AddSupplierModal 
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          fetchSuppliers();
          setShowAddModal(false);
        }}
      />

      {selectedSupplierForMultiAccount && (
        <MultiAccountModal
          isOpen={showMultiAccountModal}
          onClose={() => {
            setShowMultiAccountModal(false);
            setSelectedSupplierForMultiAccount(null);
          }}
          supplierId={selectedSupplierForMultiAccount.id}
          supplierName={selectedSupplierForMultiAccount.name}
        />
      )}

      <ScheduleManagementModal
        isOpen={showScheduleModal}
        onClose={() => setShowScheduleModal(false)}
      />
    </div>
  );
}