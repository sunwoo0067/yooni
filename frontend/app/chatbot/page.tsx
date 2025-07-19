'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  MessageCircle,
  Users,
  BarChart3,
  RefreshCcw,
  Search,
  Trash2,
  Eye,
  Globe
} from 'lucide-react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface Session {
  session_id: string;
  user_id?: string;
  message_count: number;
  last_activity: string;
  language: string;
}

interface Analytics {
  total_sessions: number;
  total_messages: number;
  active_websocket_connections: number;
  average_conversation_length: number;
  intent_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
}

interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: string;
}

const INTENT_COLORS: Record<string, string> = {
  greeting: '#10b981',
  product_inquiry: '#3b82f6',
  order_status: '#8b5cf6',
  return_exchange: '#f97316',
  price_inquiry: '#eab308',
  complaint: '#ef4444',
  unknown: '#6b7280'
};

export default function ChatbotDashboard() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_CHATBOT_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // 30초마다 업데이트
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // 세션 목록
      const sessionsRes = await fetch(`${apiUrl}/api/sessions`);
      const sessionsData = await sessionsRes.json();
      setSessions(sessionsData.sessions);

      // 분석 데이터
      const analyticsRes = await fetch(`${apiUrl}/api/analytics/chat`);
      const analyticsData = await analyticsRes.json();
      setAnalytics(analyticsData);

      // FAQ 목록
      const faqsRes = await fetch(`${apiUrl}/api/faq`);
      const faqsData = await faqsRes.json();
      setFaqs(faqsData.faqs);
    } catch (error) {
      console.error('데이터 로드 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await fetch(`${apiUrl}/api/session/${sessionId}`, {
        method: 'DELETE'
      });
      fetchData();
    } catch (error) {
      console.error('세션 삭제 오류:', error);
    }
  };

  const filteredSessions = sessions.filter(session =>
    session.session_id.includes(searchTerm) ||
    (session.user_id && session.user_id.includes(searchTerm))
  );

  const intentChartData = analytics ? Object.entries(analytics.intent_distribution).map(([intent, count]) => ({
    name: intent,
    value: count,
    fill: INTENT_COLORS[intent] || '#6b7280'
  })) : [];

  const languageChartData = analytics ? Object.entries(analytics.language_distribution).map(([lang, count]) => ({
    name: lang === 'ko' ? '한국어' : '영어',
    value: count
  })) : [];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">챗봇 관리 대시보드</h1>
        <p className="text-muted-foreground mt-2">
          실시간 챗봇 상태 및 분석 데이터
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              전체 세션
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.total_sessions || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              활성 대화 세션
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              전체 메시지
            </CardTitle>
            <MessageCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.total_messages || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              주고받은 메시지
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              평균 대화 길이
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.average_conversation_length.toFixed(1) || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              메시지/세션
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              WebSocket 연결
            </CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.active_websocket_connections || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              실시간 연결
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="sessions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sessions">활성 세션</TabsTrigger>
          <TabsTrigger value="analytics">분석</TabsTrigger>
          <TabsTrigger value="faq">FAQ 관리</TabsTrigger>
        </TabsList>

        {/* 활성 세션 탭 */}
        <TabsContent value="sessions" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>활성 세션 목록</CardTitle>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="세션 검색..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 w-64"
                    />
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchData}
                    disabled={loading}
                  >
                    <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>세션 ID</TableHead>
                    <TableHead>사용자 ID</TableHead>
                    <TableHead>메시지 수</TableHead>
                    <TableHead>언어</TableHead>
                    <TableHead>마지막 활동</TableHead>
                    <TableHead>작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSessions.map((session) => (
                    <TableRow key={session.session_id}>
                      <TableCell className="font-mono text-sm">
                        {session.session_id}
                      </TableCell>
                      <TableCell>{session.user_id || '-'}</TableCell>
                      <TableCell>{session.message_count}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {session.language === 'ko' ? '한국어' : '영어'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {format(new Date(session.last_activity), 'PPP HH:mm', { locale: ko })}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setSelectedSession(session.session_id)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteSession(session.session_id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 분석 탭 */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>의도 분포</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={intentChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {intentChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>언어 분포</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={languageChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>의도별 상세 통계</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analytics && Object.entries(analytics.intent_distribution).map(([intent, count]) => (
                  <div key={intent} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: INTENT_COLORS[intent] || '#6b7280' }}
                      />
                      <span className="text-sm">{intent}</span>
                    </div>
                    <Badge>{count}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* FAQ 관리 탭 */}
        <TabsContent value="faq" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>FAQ 목록</CardTitle>
                <Button>FAQ 추가</Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-4">
                  {faqs.map((faq) => (
                    <Card key={faq.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold">{faq.question}</h4>
                          <Badge variant="outline">{faq.category}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground">
                          {faq.answer}
                        </p>
                        <div className="mt-2 flex gap-2">
                          <Button variant="outline" size="sm">수정</Button>
                          <Button variant="outline" size="sm">삭제</Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}