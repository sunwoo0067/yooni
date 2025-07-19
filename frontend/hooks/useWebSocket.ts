import { useState, useEffect, useCallback, useRef } from 'react';
import { getLogger } from '@/lib/logger/structured-logger';

const logger = getLogger('websocket');

interface WebSocketOptions {
  url: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  reconnectAttempts?: number;
}

interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
  topic?: string;
}

export function useWebSocket(options: WebSocketOptions) {
  const {
    url,
    reconnect = true,
    reconnectInterval = 5000,
    reconnectAttempts = 5
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<Error | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());

  // 메시지 핸들러 등록
  const subscribe = useCallback((topic: string, handler: (data: any) => void) => {
    if (!messageHandlersRef.current.has(topic)) {
      messageHandlersRef.current.set(topic, new Set());
    }
    messageHandlersRef.current.get(topic)!.add(handler);

    // 웹소켓이 연결되어 있으면 구독 메시지 전송
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        command: 'subscribe',
        topics: [topic]
      }));
    }

    // 구독 해제 함수 반환
    return () => {
      const handlers = messageHandlersRef.current.get(topic);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          messageHandlersRef.current.delete(topic);
          
          // 웹소켓이 연결되어 있으면 구독 해제 메시지 전송
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              command: 'unsubscribe',
              topics: [topic]
            }));
          }
        }
      }
    };
  }, []);

  // 메시지 전송
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      logger.debug('메시지 전송', { message });
    } else {
      logger.warn('웹소켓이 연결되지 않음', { readyState: wsRef.current?.readyState });
    }
  }, []);

  // 연결 설정
  const connect = useCallback(() => {
    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        logger.info('웹소켓 연결됨', { url });
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;

        // 모든 구독 재전송
        const topics = Array.from(messageHandlersRef.current.keys());
        if (topics.length > 0) {
          sendMessage({
            command: 'subscribe',
            topics
          });
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          logger.debug('메시지 수신', { message });

          // 토픽별 핸들러 실행
          if (message.topic) {
            const handlers = messageHandlersRef.current.get(message.topic);
            if (handlers) {
              handlers.forEach(handler => handler(message.data));
            }
          }

          // 타입별 핸들러 실행
          const typeHandlers = messageHandlersRef.current.get(message.type);
          if (typeHandlers) {
            typeHandlers.forEach(handler => handler(message));
          }
        } catch (err) {
          logger.error('메시지 파싱 오류', err as Error);
        }
      };

      wsRef.current.onerror = (event) => {
        logger.error('웹소켓 오류', { event });
        setError(new Error('WebSocket error'));
      };

      wsRef.current.onclose = (event) => {
        logger.info('웹소켓 연결 종료', { code: event.code, reason: event.reason });
        setIsConnected(false);

        // 재연결 시도
        if (reconnect && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++;
          logger.info(`재연결 시도 ${reconnectCountRef.current}/${reconnectAttempts}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (err) {
      logger.error('웹소켓 연결 실패', err as Error);
      setError(err as Error);
    }
  }, [url, reconnect, reconnectInterval, reconnectAttempts, sendMessage]);

  // 연결 해제
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  // 컴포넌트 마운트 시 연결
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // 주기적인 핑 전송
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      sendMessage({ command: 'ping' });
    }, 30000); // 30초마다 핑

    return () => clearInterval(pingInterval);
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    subscribe,
    disconnect,
    reconnect: connect
  };
}

// 메트릭 전용 웹소켓 훅
export function useMetricsWebSocket() {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/metrics';
  const { isConnected, subscribe, error } = useWebSocket({ url: wsUrl });

  const subscribeToSystemMetrics = useCallback((handler: (data: any) => void) => {
    return subscribe('system', handler);
  }, [subscribe]);

  const subscribeToApiMetrics = useCallback((handler: (data: any) => void) => {
    return subscribe('api', handler);
  }, [subscribe]);

  const subscribeToDatabaseMetrics = useCallback((handler: (data: any) => void) => {
    return subscribe('database', handler);
  }, [subscribe]);

  const subscribeToBusinessMetrics = useCallback((handler: (data: any) => void) => {
    return subscribe('business', handler);
  }, [subscribe]);

  return {
    isConnected,
    error,
    subscribeToSystemMetrics,
    subscribeToApiMetrics,
    subscribeToDatabaseMetrics,
    subscribeToBusinessMetrics
  };
}