'use client';

import { useState } from 'react';
import axios from 'axios';

export default function SupplierTestPage() {
  const [supplierId, setSupplierId] = useState('1');
  const [testResult, setTestResult] = useState<any>(null);
  const [collectResult, setCollectResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [collectLoading, setCollectLoading] = useState(false);

  const runTest = async () => {
    setLoading(true);
    setTestResult(null);
    try {
      const { data } = await axios.get(`/api/suppliers/${supplierId}/collect/test`);
      setTestResult(data);
    } catch (error: any) {
      setTestResult({ 
        error: error.response?.data?.error || error.message,
        status: error.response?.status
      });
    } finally {
      setLoading(false);
    }
  };

  const runCollection = async () => {
    setCollectLoading(true);
    setCollectResult(null);
    try {
      const { data } = await axios.post(`/api/suppliers/${supplierId}/collect`, {
        periodType: 'days',
        periodValue: 1
      });
      setCollectResult(data);
      
      // 로그 ID로 상태 체크
      if (data.logId) {
        checkCollectionStatus(data.logId);
      }
    } catch (error: any) {
      setCollectResult({ 
        error: error.response?.data?.error || error.message,
        status: error.response?.status,
        details: error.response?.data
      });
    } finally {
      setCollectLoading(false);
    }
  };

  const checkCollectionStatus = async (logId: number) => {
    // 5초마다 상태 체크 (최대 10번)
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const { data } = await axios.get(`/api/suppliers/${supplierId}/logs?limit=1`);
        const log = data.find((l: any) => l.id === logId);
        
        if (log) {
          setCollectResult(prev => ({
            ...prev,
            currentStatus: log.status,
            log: log
          }));
          
          if (log.status !== 'running' || attempts >= 10) {
            clearInterval(interval);
          }
        }
      } catch (error) {
        console.error('Status check error:', error);
      }
    }, 5000);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">공급사 수집 테스트</h1>
      
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">공급사 ID</label>
        <input
          type="number"
          value={supplierId}
          onChange={(e) => setSupplierId(e.target.value)}
          className="w-full px-3 py-2 border rounded-lg"
          placeholder="공급사 ID 입력"
        />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <button
          onClick={runTest}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '테스트 중...' : '환경 테스트'}
        </button>
        
        <button
          onClick={runCollection}
          disabled={collectLoading || !testResult?.tablesReady}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {collectLoading ? '수집 중...' : '수집 시작'}
        </button>
      </div>

      {/* 테스트 결과 */}
      {testResult && (
        <div className="mb-8 p-4 bg-gray-50 rounded-lg">
          <h2 className="text-lg font-semibold mb-4">환경 테스트 결과</h2>
          
          {testResult.error ? (
            <div className="text-red-600">
              <p className="font-medium">에러 발생:</p>
              <pre className="mt-2 text-sm">{JSON.stringify(testResult, null, 2)}</pre>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium">공급사 정보</h3>
                <pre className="mt-1 text-sm bg-white p-2 rounded">
                  {JSON.stringify(testResult.supplier, null, 2)}
                </pre>
              </div>
              
              <div>
                <h3 className="font-medium">설정 정보</h3>
                <pre className="mt-1 text-sm bg-white p-2 rounded">
                  {JSON.stringify(testResult.config, null, 2)}
                </pre>
              </div>
              
              <div>
                <h3 className="font-medium">현재 상품 수: {testResult.currentProductCount}</h3>
              </div>
              
              <div>
                <h3 className="font-medium">최근 수집 로그</h3>
                <pre className="mt-1 text-sm bg-white p-2 rounded max-h-40 overflow-auto">
                  {JSON.stringify(testResult.recentLogs, null, 2)}
                </pre>
              </div>
              
              <div className="text-green-600">
                ✓ 테이블 준비 완료: {testResult.tablesReady ? 'Yes' : 'No'}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 수집 결과 */}
      {collectResult && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h2 className="text-lg font-semibold mb-4">수집 결과</h2>
          
          {collectResult.error ? (
            <div className="text-red-600">
              <p className="font-medium">에러 발생:</p>
              <pre className="mt-2 text-sm">{JSON.stringify(collectResult, null, 2)}</pre>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-green-600">
                <p className="font-medium">{collectResult.message}</p>
                <p className="text-sm">로그 ID: {collectResult.logId}</p>
              </div>
              
              {collectResult.currentStatus && (
                <div>
                  <p className="font-medium">현재 상태: {collectResult.currentStatus}</p>
                </div>
              )}
              
              {collectResult.log && (
                <div>
                  <h3 className="font-medium">수집 로그 상세</h3>
                  <pre className="mt-1 text-sm bg-white p-2 rounded">
                    {JSON.stringify(collectResult.log, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}