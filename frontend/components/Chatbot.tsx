'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, X, MessageCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface Message {
  id: string;
  type: 'user' | 'bot' | 'system';
  content: string;
  timestamp: Date;
  intent?: string;
  confidence?: number;
  suggestions?: string[];
}

interface ChatbotProps {
  sessionId?: string;
  userId?: string;
  apiUrl?: string;
  position?: 'bottom-right' | 'bottom-left';
}

export default function Chatbot({ 
  sessionId = `session_${Date.now()}`,
  userId,
  apiUrl = 'http://localhost:8000',
  position = 'bottom-right'
}: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // WebSocket 연결
  useEffect(() => {
    if (isOpen && !socket) {
      connectWebSocket();
    }
    
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [isOpen]);

  // 메시지 자동 스크롤
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    const ws = new WebSocket(`${apiUrl.replace('http', 'ws')}/ws/chat/${sessionId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('챗봇 연결됨');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleBotMessage(data);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket 오류:', error);
      setIsConnected(false);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      setSocket(null);
    };
    
    setSocket(ws);
  };

  const handleBotMessage = (data: any) => {
    const message: Message = {
      id: `msg_${Date.now()}`,
      type: data.type || 'bot',
      content: data.response || data.message,
      timestamp: new Date(data.timestamp),
      intent: data.intent,
      confidence: data.confidence,
      suggestions: data.suggestions
    };
    
    setMessages(prev => [...prev, message]);
    setIsLoading(false);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    
    if (socket && socket.readyState === WebSocket.OPEN) {
      // WebSocket으로 전송
      socket.send(JSON.stringify({
        message: inputMessage,
        user_id: userId
      }));
    } else {
      // HTTP API 사용
      try {
        const response = await fetch(`${apiUrl}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            message: inputMessage,
            user_id: userId
          })
        });
        
        const data = await response.json();
        handleBotMessage(data);
      } catch (error) {
        console.error('메시지 전송 오류:', error);
        setIsLoading(false);
      }
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
    inputRef.current?.focus();
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const getIntentBadgeColor = (intent?: string) => {
    const colors: Record<string, string> = {
      greeting: 'bg-green-500',
      product_inquiry: 'bg-blue-500',
      order_status: 'bg-purple-500',
      return_exchange: 'bg-orange-500',
      price_inquiry: 'bg-yellow-500',
      complaint: 'bg-red-500',
      unknown: 'bg-gray-500'
    };
    
    return colors[intent || 'unknown'] || 'bg-gray-500';
  };

  const positionClasses = position === 'bottom-right' 
    ? 'bottom-4 right-4' 
    : 'bottom-4 left-4';

  return (
    <>
      {/* 챗봇 버튼 */}
      {!isOpen && (
        <Button
          className={`fixed ${positionClasses} rounded-full w-14 h-14 shadow-lg`}
          onClick={() => setIsOpen(true)}
        >
          <MessageCircle className="w-6 h-6" />
        </Button>
      )}

      {/* 챗봇 창 */}
      {isOpen && (
        <Card className={`fixed ${positionClasses} w-96 h-[600px] shadow-xl z-50`}>
          <CardHeader className="flex flex-row items-center justify-between p-4 border-b">
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg">고객 지원 챗봇</CardTitle>
              {isConnected ? (
                <Badge variant="outline" className="bg-green-100">
                  연결됨
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-red-100">
                  연결 끊김
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </CardHeader>

          <CardContent className="p-0 flex flex-col h-[calc(100%-4rem)]">
            {/* 메시지 영역 */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.type === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2 ${
                        message.type === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : message.type === 'system'
                          ? 'bg-muted text-muted-foreground'
                          : 'bg-secondary'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      
                      {/* 의도 표시 */}
                      {message.intent && (
                        <div className="mt-2">
                          <Badge
                            className={`text-xs ${getIntentBadgeColor(message.intent)}`}
                          >
                            {message.intent}
                          </Badge>
                          {message.confidence && (
                            <span className="ml-2 text-xs opacity-70">
                              {(message.confidence * 100).toFixed(0)}% 확신
                            </span>
                          )}
                        </div>
                      )}
                      
                      {/* 추천 응답 */}
                      {message.suggestions && message.suggestions.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {message.suggestions.map((suggestion, idx) => (
                            <Button
                              key={idx}
                              variant="outline"
                              size="sm"
                              className="w-full text-xs justify-start"
                              onClick={() => handleSuggestionClick(suggestion)}
                            >
                              {suggestion}
                            </Button>
                          ))}
                        </div>
                      )}
                      
                      <span className="text-xs opacity-50 mt-1 block">
                        {format(message.timestamp, 'HH:mm', { locale: ko })}
                      </span>
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-secondary rounded-lg px-4 py-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* 입력 영역 */}
            <div className="p-4 border-t">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
                className="flex gap-2"
              >
                <Input
                  ref={inputRef}
                  type="text"
                  placeholder="메시지를 입력하세요..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  disabled={isLoading || !isConnected}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={isLoading || !inputMessage.trim() || !isConnected}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
              
              {/* 빠른 액션 */}
              <div className="mt-2 flex flex-wrap gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => handleSuggestionClick('상품 찾기')}
                >
                  상품 찾기
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => handleSuggestionClick('주문 조회')}
                >
                  주문 조회
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => handleSuggestionClick('반품/교환')}
                >
                  반품/교환
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}