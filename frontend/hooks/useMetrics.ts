import { useState, useEffect, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';

interface MetricsOptions {
  interval?: number;
  autoRefresh?: boolean;
  onError?: (error: Error) => void;
}

export function useSystemMetrics(options: MetricsOptions = {}) {
  const { interval = 10000, autoRefresh = true, onError } = options;
  
  return useQuery({
    queryKey: ['system-metrics'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/monitoring/system');
        if (!response.ok) throw new Error('Failed to fetch system metrics');
        return response.json();
      } catch (error) {
        if (onError) onError(error as Error);
        throw error;
      }
    },
    refetchInterval: autoRefresh ? interval : false,
  });
}

export function useApiMetrics(timeRange: string, options: MetricsOptions = {}) {
  const { interval = 30000, autoRefresh = true, onError } = options;
  
  return useQuery({
    queryKey: ['api-metrics', timeRange],
    queryFn: async () => {
      try {
        const response = await fetch(`/api/monitoring/api?range=${timeRange}`);
        if (!response.ok) throw new Error('Failed to fetch API metrics');
        return response.json();
      } catch (error) {
        if (onError) onError(error as Error);
        throw error;
      }
    },
    refetchInterval: autoRefresh ? interval : false,
  });
}

export function useDatabaseMetrics(options: MetricsOptions = {}) {
  const { interval = 15000, autoRefresh = true, onError } = options;
  
  return useQuery({
    queryKey: ['db-metrics'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/monitoring/database');
        if (!response.ok) throw new Error('Failed to fetch database metrics');
        return response.json();
      } catch (error) {
        if (onError) onError(error as Error);
        throw error;
      }
    },
    refetchInterval: autoRefresh ? interval : false,
  });
}

export function useBusinessMetrics(timeRange: string, options: MetricsOptions = {}) {
  const { interval = 60000, autoRefresh = true, onError } = options;
  
  return useQuery({
    queryKey: ['business-metrics', timeRange],
    queryFn: async () => {
      try {
        const response = await fetch(`/api/monitoring/business?range=${timeRange}`);
        if (!response.ok) throw new Error('Failed to fetch business metrics');
        return response.json();
      } catch (error) {
        if (onError) onError(error as Error);
        throw error;
      }
    },
    refetchInterval: autoRefresh ? interval : false,
  });
}

export function useTimeseriesData(timeRange: string, options: MetricsOptions = {}) {
  const { interval = 30000, autoRefresh = true, onError } = options;
  
  return useQuery({
    queryKey: ['timeseries', timeRange],
    queryFn: async () => {
      try {
        const response = await fetch(`/api/monitoring/timeseries?range=${timeRange}`);
        if (!response.ok) throw new Error('Failed to fetch timeseries data');
        return response.json();
      } catch (error) {
        if (onError) onError(error as Error);
        throw error;
      }
    },
    refetchInterval: autoRefresh ? interval : false,
  });
}

// 메트릭 기록 훅
export function useRecordMetric() {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const recordMetric = useCallback(async (
    name: string,
    value: number,
    type: 'counter' | 'gauge' | 'histogram' = 'gauge',
    tags?: Record<string, string>
  ) => {
    setIsRecording(true);
    setError(null);
    
    try {
      const response = await fetch('/api/monitoring/api', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          value,
          metric_type: type,
          tags
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to record metric');
      }
      
      return await response.json();
    } catch (err) {
      const error = err as Error;
      setError(error);
      throw error;
    } finally {
      setIsRecording(false);
    }
  }, []);
  
  return { recordMetric, isRecording, error };
}

// 알림 임계값 관리
export function useMetricAlerts() {
  const [alerts, setAlerts] = useState<Array<{
    id: string;
    metric: string;
    condition: string;
    threshold: number;
    severity: 'warning' | 'critical';
    active: boolean;
    lastTriggered?: Date;
  }>>([]);
  
  const queryClient = useQueryClient();
  
  // 알림 체크
  useEffect(() => {
    const checkAlerts = () => {
      const systemMetrics = queryClient.getQueryData(['system-metrics']) as { cpu: number; memory: number } | undefined;
      const dbMetrics = queryClient.getQueryData(['db-metrics']) as { availableConnections: number } | undefined;
      
      if (!systemMetrics && !dbMetrics) return;
      
      const newAlerts = [...alerts];
      let hasChanges = false;
      
      // CPU 알림 체크
      if (systemMetrics?.cpu && systemMetrics.cpu > 80) {
        const cpuAlert = newAlerts.find(a => a.metric === 'cpu');
        if (cpuAlert && !cpuAlert.active) {
          cpuAlert.active = true;
          cpuAlert.lastTriggered = new Date();
          hasChanges = true;
        }
      }
      
      // 메모리 알림 체크
      if (systemMetrics?.memory && systemMetrics.memory > 85) {
        const memAlert = newAlerts.find(a => a.metric === 'memory');
        if (memAlert && !memAlert.active) {
          memAlert.active = true;
          memAlert.lastTriggered = new Date();
          hasChanges = true;
        }
      }
      
      // DB 연결 알림 체크
      if (dbMetrics?.availableConnections && dbMetrics.availableConnections < 2) {
        const dbAlert = newAlerts.find(a => a.metric === 'db_connections');
        if (dbAlert && !dbAlert.active) {
          dbAlert.active = true;
          dbAlert.lastTriggered = new Date();
          hasChanges = true;
        }
      }
      
      if (hasChanges) {
        setAlerts(newAlerts);
      }
    };
    
    const interval = setInterval(checkAlerts, 5000);
    return () => clearInterval(interval);
  }, [alerts, queryClient]);
  
  const addAlert = useCallback((alert: Omit<typeof alerts[0], 'id' | 'active'>) => {
    setAlerts(prev => [...prev, {
      ...alert,
      id: Date.now().toString(),
      active: false
    }]);
  }, []);
  
  const removeAlert = useCallback((id: string) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  }, []);
  
  const clearAlert = useCallback((id: string) => {
    setAlerts(prev => prev.map(a => 
      a.id === id ? { ...a, active: false } : a
    ));
  }, []);
  
  return {
    alerts: alerts.filter(a => a.active),
    addAlert,
    removeAlert,
    clearAlert
  };
}