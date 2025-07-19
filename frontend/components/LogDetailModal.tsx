import { useState } from 'react'
import { format } from 'date-fns'

interface LogEntry {
  id: number
  timestamp: string
  level: string
  logger: string
  message: string
  module: string
  function: string
  line: number
  user_id?: string
  market_code?: string
  request_id?: string
  execution_time?: number
  exception_type?: string
  exception_message?: string
  traceback?: string
  metadata?: Record<string, any>
}

interface LogDetailModalProps {
  log: LogEntry | null
  isOpen: boolean
  onClose: () => void
}

export default function LogDetailModal({ log, isOpen, onClose }: LogDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'metadata' | 'traceback'>('details')

  if (!isOpen || !log) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* 헤더 */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold">로그 상세 정보</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 탭 */}
        <div className="border-b">
          <nav className="flex">
            <button
              onClick={() => setActiveTab('details')}
              className={`px-6 py-3 text-sm font-medium ${
                activeTab === 'details'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              상세 정보
            </button>
            {log.metadata && Object.keys(log.metadata).length > 0 && (
              <button
                onClick={() => setActiveTab('metadata')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'metadata'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                메타데이터
              </button>
            )}
            {log.traceback && (
              <button
                onClick={() => setActiveTab('traceback')}
                className={`px-6 py-3 text-sm font-medium ${
                  activeTab === 'traceback'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                스택 트레이스
              </button>
            )}
          </nav>
        </div>

        {/* 컨텐츠 */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 180px)' }}>
          {activeTab === 'details' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-500">시간</label>
                  <p className="mt-1">{format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss.SSS')}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">레벨</label>
                  <p className="mt-1">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      log.level === 'ERROR' ? 'bg-red-100 text-red-800' :
                      log.level === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                      log.level === 'INFO' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {log.level}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">로거</label>
                  <p className="mt-1">{log.logger}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">모듈</label>
                  <p className="mt-1">{log.module}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">함수</label>
                  <p className="mt-1">{log.function} (line {log.line})</p>
                </div>
                {log.market_code && (
                  <div>
                    <label className="block text-sm font-medium text-gray-500">마켓</label>
                    <p className="mt-1">{log.market_code}</p>
                  </div>
                )}
                {log.user_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-500">사용자 ID</label>
                    <p className="mt-1">{log.user_id}</p>
                  </div>
                )}
                {log.request_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-500">요청 ID</label>
                    <p className="mt-1 font-mono text-sm">{log.request_id}</p>
                  </div>
                )}
                {log.execution_time && (
                  <div>
                    <label className="block text-sm font-medium text-gray-500">실행 시간</label>
                    <p className="mt-1">{log.execution_time.toFixed(3)}초</p>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-500 mb-2">메시지</label>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="whitespace-pre-wrap">{log.message}</p>
                </div>
              </div>

              {log.exception_type && (
                <div>
                  <label className="block text-sm font-medium text-gray-500 mb-2">예외 정보</label>
                  <div className="bg-red-50 p-4 rounded-md">
                    <p className="font-semibold text-red-800">{log.exception_type}</p>
                    <p className="mt-1 text-red-700">{log.exception_message}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'metadata' && log.metadata && (
            <div>
              <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto">
                <code className="text-sm">
                  {JSON.stringify(log.metadata, null, 2)}
                </code>
              </pre>
            </div>
          )}

          {activeTab === 'traceback' && log.traceback && (
            <div>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto">
                <code className="text-sm">
                  {log.traceback}
                </code>
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}