'use client';

import { useState, useEffect } from 'react';
import { X, Clock, Calendar, Save } from 'lucide-react';
import axios from 'axios';

interface ScheduleManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SupplierSchedule {
  id: number;
  name: string;
  collection_enabled: boolean;
  collection_schedule: string;
  schedule_time: string;
}

export default function ScheduleManagementModal({ isOpen, onClose }: ScheduleManagementModalProps) {
  const [schedules, setSchedules] = useState<SupplierSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [modifiedSchedules, setModifiedSchedules] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (isOpen) {
      fetchSchedules();
    }
  }, [isOpen]);

  const fetchSchedules = async () => {
    try {
      setLoading(true);
      const { data: suppliers } = await axios.get('/api/suppliers');
      
      // 각 공급사의 설정 가져오기
      const schedulesData = await Promise.all(
        suppliers.map(async (supplier: any) => {
          try {
            const { data: config } = await axios.get(`/api/suppliers/${supplier.id}/config`);
            return {
              id: supplier.id,
              name: supplier.name,
              collection_enabled: config.enabled || false,
              collection_schedule: config.schedule || 'manual',
              schedule_time: config.schedule_time || '02:00'
            };
          } catch (error) {
            // 설정이 없는 경우 기본값
            return {
              id: supplier.id,
              name: supplier.name,
              collection_enabled: false,
              collection_schedule: 'manual',
              schedule_time: '02:00'
            };
          }
        })
      );
      
      setSchedules(schedulesData);
    } catch (error) {
      console.error('Failed to fetch schedules:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleChange = (supplierId: number, field: string, value: any) => {
    setSchedules(schedules.map(s => 
      s.id === supplierId ? { ...s, [field]: value } : s
    ));
    setModifiedSchedules(new Set(modifiedSchedules).add(supplierId));
  };

  const handleSaveAll = async () => {
    setSaving(true);
    
    try {
      // 변경된 스케줄만 저장
      const savePromises = Array.from(modifiedSchedules).map(supplierId => {
        const schedule = schedules.find(s => s.id === supplierId);
        if (!schedule) return Promise.resolve();
        
        return axios.post(`/api/suppliers/${supplierId}/config`, {
          collection_enabled: schedule.collection_enabled,
          collection_schedule: schedule.collection_schedule,
          schedule_time: schedule.schedule_time + ':00' // 시간 형식 맞추기
        });
      });
      
      await Promise.all(savePromises);
      alert('스케줄이 저장되었습니다.');
      setModifiedSchedules(new Set());
    } catch (error) {
      console.error('Failed to save schedules:', error);
      alert('스케줄 저장 중 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const getScheduleLabel = (schedule: string) => {
    switch (schedule) {
      case 'hourly': return '매시간';
      case 'daily': return '매일';
      case 'weekly': return '매주';
      case 'manual': return '수동';
      default: return schedule;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Calendar size={24} className="text-blue-600" />
            <h2 className="text-xl font-semibold">수집 스케줄 관리</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-160px)]">
          {loading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">공급사</th>
                    <th className="text-center py-3 px-4">자동 수집</th>
                    <th className="text-center py-3 px-4">수집 주기</th>
                    <th className="text-center py-3 px-4">수집 시간</th>
                    <th className="text-center py-3 px-4">다음 수집</th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((schedule) => (
                    <tr key={schedule.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{schedule.name}</td>
                      <td className="py-3 px-4 text-center">
                        <label className="inline-flex items-center">
                          <input
                            type="checkbox"
                            checked={schedule.collection_enabled}
                            onChange={(e) => handleScheduleChange(schedule.id, 'collection_enabled', e.target.checked)}
                            className="rounded text-blue-600"
                          />
                        </label>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <select
                          value={schedule.collection_schedule}
                          onChange={(e) => handleScheduleChange(schedule.id, 'collection_schedule', e.target.value)}
                          disabled={!schedule.collection_enabled}
                          className="px-3 py-1 border border-gray-300 rounded text-sm disabled:bg-gray-100"
                        >
                          <option value="hourly">매시간</option>
                          <option value="daily">매일</option>
                          <option value="weekly">매주</option>
                          <option value="manual">수동</option>
                        </select>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {schedule.collection_schedule !== 'manual' && schedule.collection_enabled ? (
                          <input
                            type="time"
                            value={schedule.schedule_time}
                            onChange={(e) => handleScheduleChange(schedule.id, 'schedule_time', e.target.value)}
                            className="px-3 py-1 border border-gray-300 rounded text-sm"
                          />
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {schedule.collection_enabled && schedule.collection_schedule !== 'manual' ? (
                          <span className="text-sm text-gray-600">
                            {getNextScheduleTime(schedule.collection_schedule, schedule.schedule_time)}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-white border-t px-6 py-4 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {modifiedSchedules.size > 0 && (
              <span className="text-blue-600 font-medium">
                {modifiedSchedules.size}개 공급사의 스케줄이 변경되었습니다.
              </span>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              닫기
            </button>
            <button
              onClick={handleSaveAll}
              disabled={modifiedSchedules.size === 0 || saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Save size={16} />
              {saving ? '저장 중...' : '변경사항 저장'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function getNextScheduleTime(schedule: string, time: string): string {
  const now = new Date();
  const [hours, minutes] = time.split(':').map(Number);
  
  switch (schedule) {
    case 'hourly':
      const nextHour = new Date(now);
      nextHour.setHours(nextHour.getHours() + 1, minutes, 0, 0);
      if (nextHour <= now) {
        nextHour.setHours(nextHour.getHours() + 1);
      }
      return nextHour.toLocaleString('ko-KR', { 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      
    case 'daily':
      const nextDay = new Date(now);
      nextDay.setHours(hours, minutes, 0, 0);
      if (nextDay <= now) {
        nextDay.setDate(nextDay.getDate() + 1);
      }
      return nextDay.toLocaleString('ko-KR', { 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      
    case 'weekly':
      const nextWeek = new Date(now);
      nextWeek.setHours(hours, minutes, 0, 0);
      if (nextWeek <= now) {
        nextWeek.setDate(nextWeek.getDate() + 7);
      }
      return nextWeek.toLocaleString('ko-KR', { 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      
    default:
      return '-';
  }
}