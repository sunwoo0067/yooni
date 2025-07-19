import Link from 'next/link';

export default function SettingsPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">설정</h1>
        <p className="text-gray-600 mt-2">시스템 설정을 관리합니다.</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">기본 설정</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">시스템 이름</label>
                <input
                  type="text"
                  defaultValue="ERP System"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">기본 언어</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500">
                  <option value="ko">한국어</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">시간대</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500">
                  <option value="Asia/Seoul">서울 (GMT+9)</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">데이터베이스 설정</h2>
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">현재 데이터베이스 상태</p>
                <p className="text-lg font-medium mt-1">연결됨</p>
                <p className="text-xs text-gray-500 mt-2">PostgreSQL 5434 포트</p>
              </div>
              <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                연결 테스트
              </button>
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">시스템 정보</h2>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">버전</span>
                <span className="font-medium">1.0.0</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">총 상품 수</span>
                <span className="font-medium">135,281개</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">데이터베이스 크기</span>
                <span className="font-medium">169 MB</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">마지막 업데이트</span>
                <span className="font-medium">오늘</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">빠른 작업</h2>
            <div className="space-y-3">
              <Link href="/settings/config" className="block">
                <button className="w-full px-4 py-2 text-left border border-blue-500 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">
                  환경변수 관리
                </button>
              </Link>
              <button className="w-full px-4 py-2 text-left border border-gray-300 rounded-lg hover:bg-gray-50">
                데이터 백업
              </button>
              <button className="w-full px-4 py-2 text-left border border-gray-300 rounded-lg hover:bg-gray-50">
                캐시 초기화
              </button>
              <button className="w-full px-4 py-2 text-left border border-gray-300 rounded-lg hover:bg-gray-50">
                시스템 로그 확인
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}