'use client';

import { useState, useEffect } from 'react';
import { X, Plus, Trash2, Edit2, Check, XCircle } from 'lucide-react';
import axios from 'axios';

interface MultiAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  supplierId: number;
  supplierName: string;
}

interface Account {
  id?: number;
  account_name: string;
  api_key: string;
  api_secret: string;
  is_active: boolean;
  isEditing?: boolean;
}

interface SupplierConfig {
  api_type: string;
}

export default function MultiAccountModal({ 
  isOpen, 
  onClose, 
  supplierId,
  supplierName 
}: MultiAccountModalProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [supplierConfig, setSupplierConfig] = useState<SupplierConfig | null>(null);
  const [newAccount, setNewAccount] = useState<Account>({
    account_name: '',
    api_key: '',
    api_secret: '',
    is_active: true
  });

  useEffect(() => {
    if (isOpen && supplierId) {
      fetchAccounts();
      fetchSupplierConfig();
    }
  }, [isOpen, supplierId]);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const { data } = await axios.get(`/api/suppliers/${supplierId}/accounts`);
      setAccounts(data);
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSupplierConfig = async () => {
    try {
      const { data } = await axios.get(`/api/suppliers/${supplierId}/config`);
      setSupplierConfig({ api_type: data.api_type });
    } catch (error) {
      console.error('Failed to fetch supplier config:', error);
    }
  };

  const handleAddAccount = async () => {
    try {
      const { data } = await axios.post(`/api/suppliers/${supplierId}/accounts`, newAccount);
      setAccounts([...accounts, data]);
      setNewAccount({
        account_name: '',
        api_key: '',
        api_secret: '',
        is_active: true
      });
      setShowAddForm(false);
    } catch (error) {
      console.error('Failed to add account:', error);
      alert('계정 추가 중 오류가 발생했습니다.');
    }
  };

  const handleUpdateAccount = async (account: Account) => {
    try {
      await axios.put(`/api/suppliers/${supplierId}/accounts/${account.id}`, {
        account_name: account.account_name,
        api_key: account.api_key,
        api_secret: account.api_secret,
        is_active: account.is_active
      });
      
      setAccounts(accounts.map(a => 
        a.id === account.id ? { ...account, isEditing: false } : a
      ));
    } catch (error) {
      console.error('Failed to update account:', error);
      alert('계정 수정 중 오류가 발생했습니다.');
    }
  };

  const handleDeleteAccount = async (accountId: number) => {
    if (!confirm('정말로 이 계정을 삭제하시겠습니까?')) return;
    
    try {
      await axios.delete(`/api/suppliers/${supplierId}/accounts/${accountId}`);
      setAccounts(accounts.filter(a => a.id !== accountId));
    } catch (error) {
      console.error('Failed to delete account:', error);
      alert('계정 삭제 중 오류가 발생했습니다.');
    }
  };

  const toggleEdit = (accountId: number) => {
    setAccounts(accounts.map(a => 
      a.id === accountId ? { ...a, isEditing: !a.isEditing } : a
    ));
  };

  const updateEditingAccount = (accountId: number, field: string, value: any) => {
    setAccounts(accounts.map(a => 
      a.id === accountId ? { ...a, [field]: value } : a
    ));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">멀티계정 관리</h2>
            <p className="text-sm text-gray-600 mt-1">{supplierName}</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {loading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : (
            <>
              {/* 계정 목록 */}
              <div className="space-y-4">
                {accounts.map((account) => (
                  <div key={account.id} className="border rounded-lg p-4">
                    {account.isEditing ? (
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              계정명
                            </label>
                            <input
                              type="text"
                              value={account.account_name}
                              onChange={(e) => updateEditingAccount(account.id!, 'account_name', e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                            />
                          </div>
                          <div className="flex items-end gap-2">
                            <label className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={account.is_active}
                                onChange={(e) => updateEditingAccount(account.id!, 'is_active', e.target.checked)}
                                className="rounded"
                              />
                              <span className="text-sm">활성화</span>
                            </label>
                          </div>
                        </div>
                        {supplierConfig?.api_type === 'GraphQL' && (
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                Access Token
                              </label>
                              <input
                                type="text"
                                value={account.api_key}
                                onChange={(e) => updateEditingAccount(account.id!, 'api_key', e.target.value)}
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
                                value={account.api_secret}
                                onChange={(e) => updateEditingAccount(account.id!, 'api_secret', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                              />
                            </div>
                          </div>
                        )}
                        
                        {supplierConfig?.api_type === 'REST API' && (
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                API Key
                              </label>
                              <input
                                type="text"
                                value={account.api_key}
                                onChange={(e) => updateEditingAccount(account.id!, 'api_key', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                API Secret
                              </label>
                              <input
                                type="password"
                                value={account.api_secret}
                                onChange={(e) => updateEditingAccount(account.id!, 'api_secret', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                              />
                            </div>
                          </div>
                        )}
                        
                        {supplierConfig?.api_type === 'crawling' && (
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                로그인 ID
                              </label>
                              <input
                                type="text"
                                value={account.api_key}
                                onChange={(e) => updateEditingAccount(account.id!, 'api_key', e.target.value)}
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
                                value={account.api_secret}
                                onChange={(e) => updateEditingAccount(account.id!, 'api_secret', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                              />
                            </div>
                          </div>
                        )}
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => toggleEdit(account.id!)}
                            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                          >
                            취소
                          </button>
                          <button
                            onClick={() => handleUpdateAccount(account)}
                            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                          >
                            저장
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium flex items-center gap-2">
                            {account.account_name}
                            {account.is_active ? (
                              <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                                활성
                              </span>
                            ) : (
                              <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                                비활성
                              </span>
                            )}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            API Key: {account.api_key?.slice(0, 10)}...
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => toggleEdit(account.id!)}
                            className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                          >
                            <Edit2 size={16} />
                          </button>
                          <button
                            onClick={() => handleDeleteAccount(account.id!)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* 새 계정 추가 */}
              {showAddForm ? (
                <div className="mt-4 border-2 border-dashed border-blue-300 rounded-lg p-4 bg-blue-50">
                  <h3 className="font-medium mb-3">새 계정 추가</h3>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          계정명 <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={newAccount.account_name}
                          onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          placeholder="예: 메인 계정"
                        />
                      </div>
                      <div className="flex items-end">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={newAccount.is_active}
                            onChange={(e) => setNewAccount({ ...newAccount, is_active: e.target.checked })}
                            className="rounded"
                          />
                          <span className="text-sm">활성화</span>
                        </label>
                      </div>
                    </div>
                    {supplierConfig?.api_type === 'GraphQL' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Access Token <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={newAccount.api_key}
                            onChange={(e) => setNewAccount({ ...newAccount, api_key: e.target.value })}
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
                            value={newAccount.api_secret}
                            onChange={(e) => setNewAccount({ ...newAccount, api_secret: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                      </div>
                    )}
                    
                    {supplierConfig?.api_type === 'REST API' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            API Key <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={newAccount.api_key}
                            onChange={(e) => setNewAccount({ ...newAccount, api_key: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            API Secret <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="password"
                            value={newAccount.api_secret}
                            onChange={(e) => setNewAccount({ ...newAccount, api_secret: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                      </div>
                    )}
                    
                    {supplierConfig?.api_type === 'crawling' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            로그인 ID <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={newAccount.api_key}
                            onChange={(e) => setNewAccount({ ...newAccount, api_key: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                            placeholder="웹사이트 로그인 아이디"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            로그인 비밀번호 <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="password"
                            value={newAccount.api_secret}
                            onChange={(e) => setNewAccount({ ...newAccount, api_secret: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                      </div>
                    )}
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => {
                          setShowAddForm(false);
                          setNewAccount({
                            account_name: '',
                            api_key: '',
                            api_secret: '',
                            is_active: true
                          });
                        }}
                        className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                      >
                        취소
                      </button>
                      <button
                        onClick={handleAddAccount}
                        disabled={!newAccount.account_name || !newAccount.api_key || !newAccount.api_secret}
                        className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        추가
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowAddForm(true)}
                  className="mt-4 w-full py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 flex items-center justify-center gap-2 text-gray-600"
                >
                  <Plus size={20} />
                  새 계정 추가
                </button>
              )}

              {/* 안내 메시지 */}
              {accounts.length === 0 && !showAddForm && (
                <div className="text-center py-8 text-gray-500">
                  <p>등록된 계정이 없습니다.</p>
                  <p className="text-sm mt-2">멀티계정을 사용하면 여러 API 키로 상품을 수집할 수 있습니다.</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}