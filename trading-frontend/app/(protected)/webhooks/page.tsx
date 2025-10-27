'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Webhook,
  Plus,
  Trash2,
  Copy,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Send,
  ExternalLink,
} from 'lucide-react';
import { TRADINGVIEW_ALERT_TEMPLATE, CUSTOM_ALERT_TEMPLATE } from '@/lib/webhook';

const webhookSchema = z.object({
  name: z.string().min(1, '이름을 입력하세요').max(100),
  description: z.string().max(500).optional(),
  is_active: z.boolean(),
});

type WebhookFormData = z.infer<typeof webhookSchema>;

interface WebhookItem {
  id: string;
  name: string;
  description?: string;
  webhook_url: string;
  secret_token: string;
  is_active: boolean;
  total_triggers: number;
  last_triggered?: string;
  created_at: string;
}

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<WebhookItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isTesting, setIsTesting] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showSecret, setShowSecret] = useState<Record<string, boolean>>({});
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<WebhookFormData>({
    resolver: zodResolver(webhookSchema),
    defaultValues: {
      name: '',
      description: '',
      is_active: true,
    },
  });

  useEffect(() => {
    loadWebhooks();
  }, []);

  const loadWebhooks = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/webhooks/');
      const result = await res.json();

      if (result.success && result.data) {
        setWebhooks(result.data);
      }
    } catch (error) {
      console.error('Failed to load webhooks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = async (data: WebhookFormData) => {
    setIsCreating(true);
    setMessage(null);

    try {
      const res = await fetch('/api/webhooks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await res.json();

      if (result.success) {
        setMessage({ type: 'success', text: 'Webhook created successfully!' });
        setIsDialogOpen(false);
        reset();
        await loadWebhooks();
      } else {
        setMessage({ type: 'error', text: result.error || 'Create Webhook에 실패했습니다.' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '네트워크 오류가 발생했습니다.' });
    } finally {
      setIsCreating(false);
    }
  };

  const deleteWebhook = async (webhookId: string) => {
    if (!confirm('Are you sure you want to delete this webhook?')) return;

    try {
      const res = await fetch(`/api/webhooks/?id=${webhookId}`, {
        method: 'DELETE',
      });

      const result = await res.json();

      if (result.success) {
        setMessage({ type: 'success', text: 'Webhook deleted successfully.' });
        await loadWebhooks();
      } else {
        setMessage({ type: 'error', text: result.error || '삭제에 실패했습니다.' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '네트워크 오류가 발생했습니다.' });
    }
  };

  const testWebhook = async (webhook: WebhookItem) => {
    setIsTesting(webhook.id);

    try {
      const res = await fetch('/api/webhooks/test/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          webhook_url: webhook.webhook_url,
          secret_token: webhook.secret_token,
        }),
      });

      const result = await res.json();

      if (result.success) {
        setMessage({ type: 'success', text: 'Test signal sent successfully!' });
      } else {
        setMessage({ type: 'error', text: 'Test failed: ' + (result.error || 'Unknown error') });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '네트워크 오류가 발생했습니다.' });
    } finally {
      setIsTesting(null);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setMessage({ type: 'success', text: `${label}가 copied to clipboard.` });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Webhook Management</h1>
          <p className="text-gray-600 mt-2">
            Connect with TradingView alerts and external systems
          </p>
        </div>

        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button size="lg">
              <Plus className="w-5 h-5 mr-2" />
              Create New Webhook
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Webhook</DialogTitle>
              <DialogDescription>
                TradingView 또는 외부 시스템에서 사용할 웹훅을 생성합니다
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label htmlFor="name">Webhook Name *</Label>
                <Input
                  id="name"
                  placeholder="예: TradingView BTC Strategy"
                  {...register('name')}
                />
                {errors.name && (
                  <p className="text-red-600 text-sm mt-1">{errors.name.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  placeholder="웹훅 용도를 설명하세요"
                  {...register('description')}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="is-active">Activate Immediately</Label>
                <Switch id="is-active" defaultChecked {...register('is_active')} />
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isCreating}>
                  {isCreating ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    '생성'
                  )}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {message && (
        <div
          className={`flex items-center gap-3 p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* TradingView Setup Instructions */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ExternalLink className="w-5 h-5 text-blue-600" />
            TradingView Integration Guide
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">1. Create Webhook</h3>
            <p className="text-sm text-gray-700">
              상단의 "Create New Webhook" 버튼을 클릭하여 웹훅을 만드세요.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">2. TradingView 알림 설정</h3>
            <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1">
              <li>TradingView 차트에서 알림 생성</li>
              <li>"Webhook URL" 필드에 생성된 웹훅 URL 붙여넣기</li>
              <li>아래 JSON 템플릿을 메시지 필드에 복사</li>
            </ol>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-900">3. 알림 메시지 템플릿</h3>
              <Button
                size="sm"
                variant="outline"
                onClick={() => copyToClipboard(TRADINGVIEW_ALERT_TEMPLATE, '템플릿')}
              >
                <Copy className="w-4 h-4 mr-2" />
                복사
              </Button>
            </div>
            <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto">
              {TRADINGVIEW_ALERT_TEMPLATE}
            </pre>
          </div>
        </CardContent>
      </Card>

      {/* Webhooks List */}
      <div className="space-y-4">
        {webhooks.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Webhook className="w-16 h-16 text-gray-400 mb-4" />
              <p className="text-gray-600 text-center">
                No webhooks created yet.
                <br />
                Create a new webhook to get started.
              </p>
            </CardContent>
          </Card>
        ) : (
          webhooks.map((webhook) => (
            <Card key={webhook.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <CardTitle>{webhook.name}</CardTitle>
                      <Badge variant={webhook.is_active ? 'default' : 'secondary'}>
                        {webhook.is_active ? '활성' : '비활성'}
                      </Badge>
                    </div>
                    {webhook.description && (
                      <CardDescription className="mt-2">{webhook.description}</CardDescription>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => testWebhook(webhook)}
                      disabled={isTesting === webhook.id || !webhook.is_active}
                    >
                      {isTesting === webhook.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => deleteWebhook(webhook.id)}
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Webhook URL */}
                <div>
                  <Label className="text-sm text-gray-600">웹훅 URL</Label>
                  <div className="flex gap-2 mt-1">
                    <Input
                      value={webhook.webhook_url}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(webhook.webhook_url, 'URL')}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Secret Token */}
                <div>
                  <Label className="text-sm text-gray-600">시크릿 토큰</Label>
                  <div className="flex gap-2 mt-1">
                    <Input
                      type={showSecret[webhook.id] ? 'text' : 'password'}
                      value={webhook.secret_token}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setShowSecret((prev) => ({ ...prev, [webhook.id]: !prev[webhook.id] }))
                      }
                    >
                      {showSecret[webhook.id] ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(webhook.secret_token, '토큰')}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div>
                    <div className="text-sm text-gray-600">총 트리거 횟수</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {webhook.total_triggers}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">마지막 실행</div>
                    <div className="text-sm font-semibold text-gray-900">
                      {webhook.last_triggered
                        ? new Date(webhook.last_triggered).toLocaleString('ko-KR')
                        : '실행 기록 없음'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
