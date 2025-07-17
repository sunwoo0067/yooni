'use client';

import { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Clock,
  RefreshCw,
  Filter,
  Download
} from 'lucide-react';
import axios from 'axios';

interface CollectionLog {
  id: number;
  supplier_id: number;
  supplier_name: string;
  started_at: string;
  completed_at?: string;
  status: 'running' | 'completed' | 'failed' | 'partial';
  total_products?: number;
  processed_products?: number;
  failed_products?: number;
  error_message?: string;
  metadata?: any;
}

export default function CollectionLogsPage() {
  const [logs, setLogs] = useState<CollectionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [selectedSupplier, setSelectedSupplier] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchSuppliers();
    fetchLogs();
    
    // 5초마다 자동 새로고침
    const interval = setInterval(() => {
      fetchLogs();
    }, 5000);
    
    setRefreshInterval(interval);
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [selectedSupplier, selectedStatus]);

  const fetchSuppliers = async () => {
    try {
      const { data } = await axios.get('/api/suppliers');
      setSuppliers(data);
    } catch (error) {
      console.error('Failed to fetch suppliers:', error);
    }
  };

  const fetchLogs = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedSupplier) params.append('supplier', selectedSupplier);
      if (selectedStatus) params.append('status', selectedStatus);
      
      const { data } = await axios.get(`/api/collection-logs?${params}`);
      setLogs(data);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'failed':
        return <XCircle className="text-red-500" size={20} />;
      case 'partial':
        return <AlertCircle className="text-yellow-500" size={20} />;
      case 'running':
        return <Clock className="text-blue-500 animate-pulse" size={20} />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '완료';
      case 'failed': return '실패';
      case 'partial': return '부분 실패';
      case 'running': return '진행 중';
      default: return status;
    }
  };

  const formatDuration = (start: string, end?: string) => {
    const startTime = new Date(start).getTime();
    const endTime = end ? new Date(end).getTime() : Date.now();
    const duration = endTime - startTime;
    
    const minutes = Math.floor(duration / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    
    if (minutes > 0) {
      return `${minutes}분 ${seconds}초`;
    }
    return `${seconds}초`;
  };

  const exportLogs = () => {
    const csvContent = [
      ['공급사', '시작 시간', '종료 시간', '상태', '전체 상품', '처리 상품', '실패 상품', '소요 시간', '오류 메시지'],
      ...logs.map(log => [
        log.supplier_name,
        new Date(log.started_at).toLocaleString('ko-KR'),
        log.completed_at ? new Date(log.completed_at).toLocaleString('ko-KR') : '-',
        getStatusText(log.status),
        log.total_products || '-',
        log.processed_products || '-',
        log.failed_products || '-',
        formatDuration(log.started_at, log.completed_at),
        log.error_message || '-'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `collection_logs_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">수집 로그</h1>
        <p className="text-gray-600 mt-2">상품 수집 작업의 이력을 확인하고 모니터링합니다.</p>
      </div>

      {/* 필터 영역 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-500" />
            <span className="font-medium">필터</span>
          </div>
          
          <select
            value={selectedSupplier}
            onChange={(e) => setSelectedSupplier(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          >
            <option value="">전체 공급사</option>
            {suppliers.map((supplier) => (
              <option key={supplier.id} value={supplier.id}>
                {supplier.name}
              </option>
            ))}
          </select>
          
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg"
          >
            <option value="">전체 상태</option>
            <option value="running">진행 중</option>
            <option value="completed">완료</option>
            <option value="failed">실패</option>
            <option value="partial">부분 실패</option>
          </select>
          
          <div className="flex-1" />
          
          <button
            onClick={exportLogs}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Download size={16} />
            CSV 내보내기
          </button>
          
          <button
            onClick={() => fetchLogs()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw size={16} />
            새로고침
          </button>
        </div>
      </div>

      {/* 로그 테이블 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">로딩 중...</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">수집 로그가 없습니다.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-700">상태</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-700">공급사</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-700">시작 시간</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-700">소요 시간</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-700">전체</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-700">처리</th>
                  <th className="text-center px-4 py-3 font-medium text-gray-700">실패</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-700">수집 기간</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-700">비고</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(log.status)}
                        <span className="text-sm">{getStatusText(log.status)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-medium">{log.supplier_name}</td>
                    <td className="px-4 py-3 text-sm">
                      {new Date(log.started_at).toLocaleString('ko-KR', {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                      })}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {log.status === 'running' ? (
                        <span className="text-blue-600">
                          {formatDuration(log.started_at)}
                        </span>
                      ) : (
                        formatDuration(log.started_at, log.completed_at)
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {log.total_products || '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {log.processed_products || '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {log.failed_products ? (
                        <span className="text-red-600">{log.failed_products}</span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {log.metadata?.period_start && log.metadata?.period_end ? (
                        <span className="text-gray-600">
                          {new Date(log.metadata.period_start).toLocaleDateString('ko-KR')} ~ 
                          {new Date(log.metadata.period_end).toLocaleDateString('ko-KR')}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {log.error_message && (
                        <span className="text-xs text-red-600" title={log.error_message}>
                          {log.error_message.length > 30 
                            ? log.error_message.substring(0, 30) + '...' 
                            : log.error_message}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}