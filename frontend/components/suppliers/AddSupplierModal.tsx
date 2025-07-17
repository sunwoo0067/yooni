'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import axios from 'axios';

interface AddSupplierModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddSupplierModal({ isOpen, onClose, onSuccess }: AddSupplierModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    contact_info: '',
    business_number: '',
    address: '',
    api_type: 'REST API',
    api_endpoint: '',
    api_key: '',
    api_secret: '',
    collection_enabled: true,
    collection_schedule: 'daily',
    schedule_time: '02:00',
  });

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // 공급사 생성
      const supplierResponse = await axios.post('/api/suppliers', {
        name: formData.name,
        contact_info: formData.contact_info,
        business_number: formData.business_number,
        address: formData.address,
      });

      const supplierId = supplierResponse.data.id;

      // 공급사 설정 생성
      await axios.post(`/api/suppliers/${supplierId}/config`, {
        api_type: formData.api_type,
        api_endpoint: formData.api_endpoint,
        api_key: formData.api_key,
        api_secret: formData.api_secret,
        collection_enabled: formData.collection_enabled,
        collection_schedule: formData.collection_schedule,
        schedule_time: formData.schedule_time,
      });

      alert('공급사가 성공적으로 추가되었습니다.');
      onSuccess();
      onClose();
      resetForm();
    } catch (error) {
      console.error('Error adding supplier:', error);
      alert('공급사 추가 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      contact_info: '',
      business_number: '',
      address: '',
      api_type: 'REST API',
      api_endpoint: '',
      api_key: '',
      api_secret: '',
      collection_enabled: true,
      collection_schedule: 'daily',
      schedule_time: '02:00',
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">새 공급사 추가</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 기본 정보 */}
          <div>
            <h3 className="text-lg font-medium mb-4">기본 정보</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  공급사명 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  사업자등록번호
                </label>
                <input
                  type="text"
                  value={formData.business_number}
                  onChange={(e) => setFormData({ ...formData, business_number: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="123-45-67890"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  연락처
                </label>
                <input
                  type="text"
                  value={formData.contact_info}
                  onChange={(e) => setFormData({ ...formData, contact_info: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="02-1234-5678"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  주소
                </label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* API 설정 */}
          <div>
            <h3 className="text-lg font-medium mb-4">API 연동 설정</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  연동 방식 <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={formData.api_type}
                  onChange={(e) => setFormData({ ...formData, api_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="REST API">REST API</option>
                  <option value="GraphQL">GraphQL</option>
                  <option value="crawling">Web Crawling</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API 엔드포인트 <span className="text-red-500">*</span>
                </label>
                <input
                  type="url"
                  required
                  value={formData.api_endpoint}
                  onChange={(e) => setFormData({ ...formData, api_endpoint: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="https://api.example.com/v1"
                />
              </div>
              {/* API 인증 정보 - API 유형에 따라 다른 필드 표시 */}
              {formData.api_type === 'GraphQL' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Access Token
                    </label>
                    <input
                      type="text"
                      value={formData.api_key}
                      onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="Bearer 토큰"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Refresh Token (선택)
                    </label>
                    <input
                      type="text"
                      value={formData.api_secret}
                      onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              )}
              
              {formData.api_type === 'REST API' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Key
                    </label>
                    <input
                      type="text"
                      value={formData.api_key}
                      onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Secret
                    </label>
                    <input
                      type="password"
                      value={formData.api_secret}
                      onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              )}
              
              {formData.api_type === 'crawling' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      로그인 ID
                    </label>
                    <input
                      type="text"
                      value={formData.api_key}
                      onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      placeholder="웹사이트 로그인 아이디"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      로그인 비밀번호
                    </label>
                    <input
                      type="password"
                      value={formData.api_secret}
                      onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 수집 설정 */}
          <div>
            <h3 className="text-lg font-medium mb-4">수집 설정</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="collection_enabled"
                  checked={formData.collection_enabled}
                  onChange={(e) => setFormData({ ...formData, collection_enabled: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="collection_enabled" className="text-sm font-medium text-gray-700">
                  자동 수집 활성화
                </label>
              </div>
              {formData.collection_enabled && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      수집 주기
                    </label>
                    <select
                      value={formData.collection_schedule}
                      onChange={(e) => setFormData({ ...formData, collection_schedule: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="hourly">매시간</option>
                      <option value="daily">매일</option>
                      <option value="weekly">매주</option>
                      <option value="manual">수동</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      수집 시간
                    </label>
                    <input
                      type="time"
                      value={formData.schedule_time}
                      onChange={(e) => setFormData({ ...formData, schedule_time: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '추가 중...' : '공급사 추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}