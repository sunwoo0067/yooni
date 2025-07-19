'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Save, History, Plus, Trash2, Eye, EyeOff } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Config {
  id: number;
  category: string;
  key: string;
  value: string;
  description: string;
  data_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  encrypted?: boolean;
  masked?: boolean;
}

interface ConfigHistory {
  id: number;
  config_id: number;
  category: string;
  key: string;
  old_value: string;
  new_value: string;
  changed_at: string;
  changed_by: string;
  change_reason?: string;
  description?: string;
  data_type?: string;
  masked?: boolean;
}

const CONFIG_CATEGORIES = {
  database: '데이터베이스',
  api_keys: 'API 인증',
  marketplace: '마켓플레이스',
  collection: '수집 설정',
  notification: '알림 설정',
  system: '시스템 설정',
};

export default function ConfigPage() {
  const [configs, setConfigs] = useState<Record<string, Config[]>>({});
  const [history, setHistory] = useState<ConfigHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showHistory, setShowHistory] = useState(false);
  const [showValues, setShowValues] = useState<Record<string, boolean>>({});
  const [editingConfig, setEditingConfig] = useState<Config | null>(null);
  const [newConfig, setNewConfig] = useState({
    category: '',
    key: '',
    value: '',
    description: '',
    data_type: 'string',
  });
  const { toast } = useToast();

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/config');
      const data = await response.json();
      
      if (data.success) {
        setConfigs(data.data);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '설정을 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/config/history');
      const data = await response.json();
      
      if (data.success) {
        setHistory(data.data);
        setShowHistory(true);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '변경 이력을 불러오는데 실패했습니다.',
        variant: 'destructive',
      });
    }
  };

  const saveConfig = async (config: Partial<Config>) => {
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: '성공',
          description: '설정이 저장되었습니다.',
        });
        fetchConfigs();
        setEditingConfig(null);
        setNewConfig({
          category: '',
          key: '',
          value: '',
          description: '',
          data_type: 'string',
        });
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '설정 저장에 실패했습니다.',
        variant: 'destructive',
      });
    }
  };

  const deleteConfig = async (category: string, key: string) => {
    if (!confirm('정말 이 설정을 삭제하시겠습니까?')) return;
    
    try {
      const response = await fetch(`/api/config?category=${category}&key=${key}`, {
        method: 'DELETE',
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: '성공',
          description: '설정이 삭제되었습니다.',
        });
        fetchConfigs();
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '설정 삭제에 실패했습니다.',
        variant: 'destructive',
      });
    }
  };

  const toggleShowValue = (key: string) => {
    setShowValues(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const renderConfigValue = (config: Config) => {
    const isSecret = config.masked || config.key.includes('SECRET') || config.key.includes('PASSWORD');
    const show = showValues[`${config.category}-${config.key}`];
    
    if (config.data_type === 'boolean') {
      return (
        <Switch
          checked={config.value === 'true'}
          onCheckedChange={(checked) => {
            saveConfig({ ...config, value: checked ? 'true' : 'false' });
          }}
        />
      );
    }
    
    if (editingConfig?.id === config.id) {
      return (
        <div className="flex gap-2">
          <Input
            type={isSecret && !show ? 'password' : 'text'}
            value={editingConfig.value}
            onChange={(e) => setEditingConfig({ ...editingConfig, value: e.target.value })}
            className="flex-1"
          />
          <Button size="sm" onClick={() => saveConfig(editingConfig)}>
            <Save className="h-4 w-4" />
          </Button>
          <Button size="sm" variant="outline" onClick={() => setEditingConfig(null)}>
            취소
          </Button>
        </div>
      );
    }
    
    return (
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm">
          {isSecret && !show ? '••••••••' : config.value || '-'}
        </span>
        {isSecret && (
          <Button
            size="icon"
            variant="ghost"
            onClick={() => toggleShowValue(`${config.category}-${config.key}`)}
          >
            {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
        )}
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setEditingConfig(config)}
        >
          편집
        </Button>
      </div>
    );
  };

  const filteredConfigs = selectedCategory === 'all' 
    ? configs 
    : { [selectedCategory]: configs[selectedCategory] || [] };

  return (
    <div className="container mx-auto py-10">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">시스템 설정</h1>
          <p className="text-muted-foreground">데이터베이스에서 관리되는 시스템 설정</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchHistory} variant="outline">
            <History className="mr-2 h-4 w-4" />
            변경 이력
          </Button>
          <Button onClick={fetchConfigs}>
            <RefreshCw className="mr-2 h-4 w-4" />
            새로고침
          </Button>
        </div>
      </div>

      {showHistory ? (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>변경 이력</CardTitle>
              <Button variant="ghost" onClick={() => setShowHistory(false)}>
                닫기
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.map((item) => (
                <div key={item.id} className="border rounded p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium">
                        {item.category}.{item.key}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {item.description}
                      </div>
                      <div className="text-sm mt-1">
                        <span className="text-red-500">- {item.old_value || '(없음)'}</span>
                        {' → '}
                        <span className="text-green-500">+ {item.new_value || '(없음)'}</span>
                      </div>
                    </div>
                    <div className="text-right text-sm text-muted-foreground">
                      <div>{new Date(item.changed_at).toLocaleString()}</div>
                      <div>{item.changed_by}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
            <TabsList>
              <TabsTrigger value="all">전체</TabsTrigger>
              {Object.entries(CONFIG_CATEGORIES).map(([key, label]) => (
                <TabsTrigger key={key} value={key}>{label}</TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          <div className="mt-6 space-y-6">
            {/* 새 설정 추가 폼 */}
            <Card>
              <CardHeader>
                <CardTitle>새 설정 추가</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>카테고리</Label>
                    <Select
                      value={newConfig.category}
                      onValueChange={(value) => setNewConfig({ ...newConfig, category: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="카테고리 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(CONFIG_CATEGORIES).map(([key, label]) => (
                          <SelectItem key={key} value={key}>{label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>키</Label>
                    <Input
                      value={newConfig.key}
                      onChange={(e) => setNewConfig({ ...newConfig, key: e.target.value })}
                      placeholder="CONFIG_KEY"
                    />
                  </div>
                  <div>
                    <Label>값</Label>
                    <Input
                      value={newConfig.value}
                      onChange={(e) => setNewConfig({ ...newConfig, value: e.target.value })}
                      placeholder="설정 값"
                    />
                  </div>
                  <div>
                    <Label>데이터 타입</Label>
                    <Select
                      value={newConfig.data_type}
                      onValueChange={(value) => setNewConfig({ ...newConfig, data_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="string">문자열</SelectItem>
                        <SelectItem value="integer">정수</SelectItem>
                        <SelectItem value="boolean">불린</SelectItem>
                        <SelectItem value="json">JSON</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2">
                    <Label>설명</Label>
                    <Textarea
                      value={newConfig.description}
                      onChange={(e) => setNewConfig({ ...newConfig, description: e.target.value })}
                      placeholder="설정에 대한 설명"
                    />
                  </div>
                  <div className="col-span-2">
                    <Button onClick={() => saveConfig(newConfig)} disabled={!newConfig.category || !newConfig.key}>
                      <Plus className="mr-2 h-4 w-4" />
                      추가
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 설정 목록 */}
            {Object.entries(filteredConfigs).map(([category, items]) => (
              <Card key={category}>
                <CardHeader>
                  <CardTitle>{CONFIG_CATEGORIES[category as keyof typeof CONFIG_CATEGORIES] || category}</CardTitle>
                  <CardDescription>{items.length}개 설정</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {items.map((config) => (
                      <div key={config.id} className="border rounded p-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium">{config.key}</h4>
                              <Badge variant="outline">{config.data_type}</Badge>
                              {config.encrypted && <Badge variant="secondary">암호화</Badge>}
                            </div>
                            <p className="text-sm text-muted-foreground mt-1">
                              {config.description}
                            </p>
                            <div className="mt-2">
                              {renderConfigValue(config)}
                            </div>
                          </div>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => deleteConfig(config.category, config.key)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          마지막 수정: {new Date(config.updated_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}