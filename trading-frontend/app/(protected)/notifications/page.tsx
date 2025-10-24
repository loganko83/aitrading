'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  RefreshCw,
  Send,
  Bell,
  BellOff,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Info,
} from 'lucide-react';
import {
  registerTelegram,
  getTelegramSettings,
  deleteTelegramSettings,
  sendTestNotification,
  type TelegramSettings,
} from '@/lib/api/telegram';

export default function NotificationsPage() {
  const { data: session } = useSession();
  const [settings, setSettings] = useState<TelegramSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form state
  const [chatId, setChatId] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    loadSettings();
  }, [session]);

  const loadSettings = async () => {
    if (!session?.user?.accessToken) {
      setIsLoading(false);
      return;
    }

    try {
      const data = await getTelegramSettings(session.user.accessToken);
      setSettings(data);
      setChatId(data.telegram_chat_id);
      setError('');
    } catch (err: any) {
      // 404 means not configured yet - not an error
      if (err.message?.includes('404') || err.message?.includes('not configured')) {
        setSettings(null);
      } else {
        console.error('Failed to load Telegram settings:', err);
        setError(err.message || 'Failed to load Telegram settings');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!chatId.trim()) {
      setError('Please enter your Telegram chat ID');
      return;
    }

    setIsRegistering(true);
    setError('');
    setSuccess('');

    try {
      const data = await registerTelegram(
        { telegram_chat_id: chatId.trim() },
        session!.user!.accessToken
      );
      setSettings(data);
      setSuccess('Telegram notifications registered successfully! A verification message was sent.');
    } catch (err: any) {
      console.error('Failed to register Telegram:', err);
      setError(err.message || 'Failed to register Telegram. Make sure you started a conversation with the bot.');
    } finally {
      setIsRegistering(false);
    }
  };

  const handleTestNotification = async () => {
    setIsTesting(true);
    setError('');
    setSuccess('');

    try {
      await sendTestNotification(session!.user!.accessToken);
      setSuccess('Test notification sent! Check your Telegram.');
    } catch (err: any) {
      console.error('Failed to send test notification:', err);
      setError(err.message || 'Failed to send test notification');
    } finally {
      setIsTesting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to disable Telegram notifications?')) {
      return;
    }

    setIsDeleting(true);
    setError('');
    setSuccess('');

    try {
      await deleteTelegramSettings(session!.user!.accessToken);
      setSettings(null);
      setChatId('');
      setSuccess('Telegram notifications disabled successfully');
    } catch (err: any) {
      console.error('Failed to delete Telegram settings:', err);
      setError(err.message || 'Failed to delete Telegram settings');
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Telegram Notifications</h2>
        <p className="text-muted-foreground">
          Receive real-time trading alerts on Telegram
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Success Alert */}
      {success && (
        <Alert className="border-green-500 bg-green-50 text-green-900">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {/* Current Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {settings ? (
                <Bell className="h-5 w-5 text-green-600" />
              ) : (
                <BellOff className="h-5 w-5 text-muted-foreground" />
              )}
              <CardTitle>Notification Status</CardTitle>
            </div>
            {settings && (
              <Badge variant={settings.is_active ? 'default' : 'secondary'}>
                {settings.is_active ? 'Active' : 'Inactive'}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {settings ? (
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Chat ID:</p>
                <code className="bg-muted px-3 py-2 rounded-md text-sm">{settings.telegram_chat_id}</code>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={handleTestNotification}
                  disabled={isTesting}
                  variant="outline"
                >
                  {isTesting ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4 mr-2" />
                  )}
                  Send Test Notification
                </Button>

                <Button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  variant="destructive"
                >
                  {isDeleting && <RefreshCw className="h-4 w-4 mr-2 animate-spin" />}
                  Disable Notifications
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center py-6">
              <BellOff className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                Telegram notifications are not configured yet. Follow the steps below to enable them.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Setup Instructions */}
      {!settings && (
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Info className="h-5 w-5 text-blue-600" />
              <CardTitle>How to Enable Telegram Notifications</CardTitle>
            </div>
            <CardDescription>Follow these steps to start receiving trading alerts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <MessageSquare className="h-4 w-4" />
              <AlertDescription>
                <strong>Step 1: Find Your Telegram Bot</strong>
                <ol className="list-decimal list-inside mt-2 space-y-1 text-sm">
                  <li>Open Telegram and search for your trading bot</li>
                  <li>Start a conversation with the bot by clicking "Start" or sending "/start"</li>
                  <li><strong>This step is required!</strong> The bot cannot send messages unless you initiate contact first.</li>
                </ol>
              </AlertDescription>
            </Alert>

            <Alert>
              <MessageSquare className="h-4 w-4" />
              <AlertDescription>
                <strong>Step 2: Get Your Chat ID</strong>
                <p className="mt-2 text-sm">Choose one of these methods:</p>
                <div className="mt-2 space-y-2 text-sm">
                  <div>
                    <strong>Method A: Using @userinfobot</strong>
                    <ol className="list-decimal list-inside ml-4 space-y-1">
                      <li>Open Telegram and search for "@userinfobot"</li>
                      <li>Start a conversation with @userinfobot</li>
                      <li>The bot will send you your user information</li>
                      <li>Copy your Chat ID (it's a number like "123456789")</li>
                    </ol>
                  </div>

                  <div>
                    <strong>Method B: Using getUpdates API</strong>
                    <ol className="list-decimal list-inside ml-4 space-y-1">
                      <li>Send any message to your trading bot</li>
                      <li>Open this URL in your browser (replace BOT_TOKEN with your bot token):</li>
                      <li><code className="bg-muted px-2 py-1 rounded text-xs">https://api.telegram.org/botBOT_TOKEN/getUpdates</code></li>
                      <li>Find "chat" → "id" in the response</li>
                    </ol>
                  </div>
                </div>
              </AlertDescription>
            </Alert>

            <Alert>
              <MessageSquare className="h-4 w-4" />
              <AlertDescription>
                <strong>Step 3: Register Your Chat ID</strong>
                <p className="mt-2 text-sm">Enter your Chat ID below and click "Register"</p>
              </AlertDescription>
            </Alert>

            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Telegram Chat ID</label>
                <input
                  type="text"
                  placeholder="Enter your Telegram chat ID (e.g., 123456789)"
                  value={chatId}
                  onChange={(e) => setChatId(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  required
                />
              </div>

              <Button type="submit" disabled={isRegistering} className="w-full">
                {isRegistering && <RefreshCw className="h-4 w-4 mr-2 animate-spin" />}
                Register Telegram Notifications
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Notification Types */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Types</CardTitle>
          <CardDescription>You will receive alerts for the following events</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium">Order Execution</p>
                <p className="text-sm text-muted-foreground">
                  Instant alerts when orders are executed (entry, exit, stop-loss, take-profit)
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium">Position Updates</p>
                <p className="text-sm text-muted-foreground">
                  Real-time updates on position PnL and status changes
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium">Liquidation Warnings</p>
                <p className="text-sm text-muted-foreground">
                  Alerts when positions are approaching liquidation levels
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium">Error Notifications</p>
                <p className="text-sm text-muted-foreground">
                  Immediate alerts for API errors, connection issues, or failed orders
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium">Daily Summary</p>
                <p className="text-sm text-muted-foreground">
                  Daily performance summary with total PnL and trading statistics
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
