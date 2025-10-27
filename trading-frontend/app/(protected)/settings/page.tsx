'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { AlertCircle, CheckCircle2, Loader2, TrendingUp, Shield, DollarSign, Bell, Settings as SettingsIcon, Trash2, Power, Edit } from 'lucide-react';
import { RISK_PRESETS, AVAILABLE_COINS, type CoinSymbol } from '@/types';
import { useTradingStore } from '@/lib/stores/tradingStore';
import { useSession } from 'next-auth/react';

// Form validation schema
const settingsFormSchema = z.object({
  risk_tolerance: z.enum(['low', 'medium', 'high']),
  selected_coins: z.array(z.string()).min(1, 'Select at least one coin'),
  leverage: z.number().min(1).max(5),
  position_size_pct: z.number().min(0.05).max(0.20),
  stop_loss_atr_multiplier: z.number().min(1.0).max(3.0),
  take_profit_atr_multiplier: z.number().min(2.0).max(5.0),
  auto_close_on_reversal: z.boolean(),
});

type SettingsFormData = z.infer<typeof settingsFormSchema>;

interface TradingConfig {
  id: string;
  api_key_id: string;
  exchange: string;
  strategy: string | null;
  investment_type: string;
  investment_value: number;
  leverage: number;
  stop_loss_percentage: number;
  take_profit_percentage: number;
  is_active: boolean;
  created_at: string;
}

interface ApiKeyAccount {
  id: string;
  exchange: string;
  testnet: boolean;
  is_active: boolean;
}

export default function SettingsPage() {
  const { data: session } = useSession();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const { settings, setSettings } = useTradingStore();

  // Telegram states
  const [telegramBotToken, setTelegramBotToken] = useState('');
  const [telegramChatId, setTelegramChatId] = useState('');
  const [notifyEntry, setNotifyEntry] = useState(true);
  const [notifyExit, setNotifyExit] = useState(true);
  const [notifyStopLoss, setNotifyStopLoss] = useState(true);
  const [notifyTakeProfit, setNotifyTakeProfit] = useState(true);
  const [isSavingTelegram, setIsSavingTelegram] = useState(false);
  const [isTestingTelegram, setIsTestingTelegram] = useState(false);
  const [telegramMessage, setTelegramMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Trading Config states
  const [tradingConfigs, setTradingConfigs] = useState<TradingConfig[]>([]);
  const [apiKeyAccounts, setApiKeyAccounts] = useState<ApiKeyAccount[]>([]);
  const [isLoadingConfigs, setIsLoadingConfigs] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [configMessage, setConfigMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Config form states
  const [selectedApiKey, setSelectedApiKey] = useState('');
  const [strategyName, setStrategyName] = useState('');
  const [investmentType, setInvestmentType] = useState<'percentage' | 'fixed'>('percentage');
  const [investmentValue, setInvestmentValue] = useState('10');
  const [configLeverage, setConfigLeverage] = useState(10);
  const [stopLossPercentage, setStopLossPercentage] = useState(2.0);
  const [takeProfitPercentage, setTakeProfitPercentage] = useState(5.0);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SettingsFormData>({
    resolver: zodResolver(settingsFormSchema),
    defaultValues: {
      risk_tolerance: 'medium',
      selected_coins: ['BTC/USDT', 'ETH/USDT'],
      leverage: 5,
      position_size_pct: 0.10,
      stop_loss_atr_multiplier: 1.2,
      take_profit_atr_multiplier: 2.5,
      auto_close_on_reversal: true,
    },
  });

  const selectedCoins = watch('selected_coins') || [];
  const leverage = watch('leverage');
  const positionSizePct = watch('position_size_pct');
  const stopLossMultiplier = watch('stop_loss_atr_multiplier');
  const takeProfitMultiplier = watch('take_profit_atr_multiplier');
  const riskTolerance = watch('risk_tolerance');

  // Load settings on mount
  useEffect(() => {
    loadSettings();
    loadTelegramConfig();
    loadTradingConfigs();
    loadApiKeyAccounts();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/settings');
      const result = await res.json();

      if (result.success && result.data) {
        const data = result.data;
        setValue('risk_tolerance', data.risk_tolerance);
        setValue('selected_coins', data.selected_coins);
        setValue('leverage', data.leverage);
        setValue('position_size_pct', data.position_size_pct);
        setValue('stop_loss_atr_multiplier', data.stop_loss_atr_multiplier);
        setValue('take_profit_atr_multiplier', data.take_profit_atr_multiplier);
        setValue('auto_close_on_reversal', data.auto_close_on_reversal);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadTelegramConfig = async () => {
    try {
      const res = await fetch('/api/telegram/config');
      const result = await res.json();

      if (result.success && result.config) {
        setNotifyEntry(result.config.notify_entry);
        setNotifyExit(result.config.notify_exit);
        setNotifyStopLoss(result.config.notify_stop_loss);
        setNotifyTakeProfit(result.config.notify_take_profit);
      }
    } catch (error) {
      console.error('Failed to load Telegram config:', error);
    }
  };

  const loadTradingConfigs = async () => {
    setIsLoadingConfigs(true);
    try {
      const res = await fetch('/api/trading-config');
      const configs = await res.json();
      setTradingConfigs(configs);
    } catch (error) {
      console.error('Failed to load trading configs:', error);
    } finally {
      setIsLoadingConfigs(false);
    }
  };

  const loadApiKeyAccounts = async () => {
    try {
      const res = await fetch('/api/accounts-secure/list');
      const result = await res.json();
      if (result.accounts) {
        setApiKeyAccounts(result.accounts);
      }
    } catch (error) {
      console.error('Failed to load API key accounts:', error);
    }
  };

  const onSubmit = async (data: SettingsFormData) => {
    setIsSaving(true);
    setMessage(null);

    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await res.json();

      if (result.success) {
        setMessage({ type: 'success', text: 'Settings saved successfully!' });
        if (result.data) {
          setSettings(result.data);
        }
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to save settings.' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error occurred.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveTelegram = async () => {
    setIsSavingTelegram(true);
    setTelegramMessage(null);

    try {
      const res = await fetch('/api/telegram/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_token: telegramBotToken,
          chat_id: telegramChatId,
          notify_entry: notifyEntry,
          notify_exit: notifyExit,
          notify_stop_loss: notifyStopLoss,
          notify_take_profit: notifyTakeProfit,
        }),
      });

      const result = await res.json();

      if (result.success) {
        setTelegramMessage({ type: 'success', text: 'Telegram settings saved! (AES-256 encrypted)' });
        setTelegramBotToken('');
        setTelegramChatId('');
      } else {
        setTelegramMessage({ type: 'error', text: result.error || 'Failed to save.' });
      }
    } catch (error) {
      setTelegramMessage({ type: 'error', text: 'Network error.' });
    } finally {
      setIsSavingTelegram(false);
    }
  };

  const handleTestTelegram = async () => {
    setIsTestingTelegram(true);
    setTelegramMessage(null);

    try {
      const res = await fetch('/api/telegram/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bot_token: telegramBotToken,
          chat_id: telegramChatId,
        }),
      });

      const result = await res.json();

      if (result.success) {
        setTelegramMessage({ type: 'success', text: 'Test sent! Check Telegram.' });
      } else {
        setTelegramMessage({ type: 'error', text: result.error || 'Test failed.' });
      }
    } catch (error) {
      setTelegramMessage({ type: 'error', text: 'Network error.' });
    } finally {
      setIsTestingTelegram(false);
    }
  };

  const handleSaveTradingConfig = async () => {
    if (!selectedApiKey) {
      setConfigMessage({ type: 'error', text: 'Please select an API key account' });
      return;
    }

    if (!investmentValue || parseFloat(investmentValue) <= 0) {
      setConfigMessage({ type: 'error', text: 'Please enter a valid investment value' });
      return;
    }

    setIsSavingConfig(true);
    setConfigMessage(null);

    try {
      const res = await fetch('/api/trading-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key_id: selectedApiKey,
          strategy: strategyName || null,
          investment_type: investmentType,
          investment_value: investmentType === 'percentage' ? parseFloat(investmentValue) / 100 : parseFloat(investmentValue),
          leverage: configLeverage,
          stop_loss_percentage: stopLossPercentage,
          take_profit_percentage: takeProfitPercentage,
          is_active: true,
        }),
      });

      const result = await res.json();

      if (res.ok) {
        setConfigMessage({ type: 'success', text: 'Trading config created successfully!' });
        // Reset form
        setSelectedApiKey('');
        setStrategyName('');
        setInvestmentValue('10');
        setConfigLeverage(10);
        setStopLossPercentage(2.0);
        setTakeProfitPercentage(5.0);
        // Reload configs
        loadTradingConfigs();
      } else {
        setConfigMessage({ type: 'error', text: result.detail || 'Failed to create config' });
      }
    } catch (error) {
      setConfigMessage({ type: 'error', text: 'Network error occurred' });
    } finally {
      setIsSavingConfig(false);
    }
  };

  const handleToggleConfig = async (configId: string) => {
    try {
      const res = await fetch(`/api/trading-config/${configId}/toggle`, {
        method: 'POST',
      });

      const result = await res.json();

      if (result.success) {
        loadTradingConfigs();
      }
    } catch (error) {
      console.error('Failed to toggle config:', error);
    }
  };

  const handleDeleteConfig = async (configId: string) => {
    if (!confirm('Are you sure you want to delete this trading config?')) {
      return;
    }

    try {
      const res = await fetch(`/api/trading-config/${configId}`, {
        method: 'DELETE',
      });

      const result = await res.json();

      if (result.success) {
        setConfigMessage({ type: 'success', text: 'Config deleted successfully' });
        loadTradingConfigs();
      }
    } catch (error) {
      setConfigMessage({ type: 'error', text: 'Failed to delete config' });
    }
  };

  const applyRiskPreset = (preset: 'low' | 'medium' | 'high') => {
    const presetData = RISK_PRESETS[preset];
    setValue('risk_tolerance', preset);
    setValue('leverage', presetData.leverage);
    setValue('position_size_pct', presetData.position_size_pct);
  };

  const toggleCoin = (coin: string) => {
    const newCoins = selectedCoins.includes(coin)
      ? selectedCoins.filter((c) => c !== coin)
      : [...selectedCoins, coin];
    setValue('selected_coins', newCoins);
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
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Trading Settings</h1>
        <p className="text-gray-600 mt-2">
          Configure risk management, strategies, and notifications
        </p>
      </div>

      {message && (
        <div
          className={`flex items-center gap-3 p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          <span>{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Risk Presets */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Risk Tolerance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              {(['low', 'medium', 'high'] as const).map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => applyRiskPreset(preset)}
                  className={`p-4 border-2 rounded-lg ${
                    riskTolerance === preset ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="font-semibold capitalize">{preset}</div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Coins */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Trading Coins
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-3">
              {AVAILABLE_COINS.map((coin) => (
                <button
                  key={coin}
                  type="button"
                  onClick={() => toggleCoin(coin)}
                  className={`p-4 border-2 rounded-lg ${
                    selectedCoins.includes(coin) ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  {coin}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Leverage */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              Leverage & Position
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Leverage</Label>
                <span className="font-bold text-blue-600">{leverage}x</span>
              </div>
              <Slider min={1} max={5} step={1} value={[leverage]} onValueChange={(v) => setValue('leverage', v[0])} />
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Position Size</Label>
                <span className="font-bold text-blue-600">{(positionSizePct * 100).toFixed(0)}%</span>
              </div>
              <Slider min={0.05} max={0.20} step={0.01} value={[positionSizePct]} onValueChange={(v) => setValue('position_size_pct', v[0])} />
            </div>
          </CardContent>
        </Card>

        <Button type="submit" size="lg" disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save Trading Settings'}
        </Button>
      </form>

      {/* Telegram Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Telegram Notifications
          </CardTitle>
          <CardDescription>Real-time alerts via Telegram bot</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm">
            <div className="font-semibold mb-2">Setup Guide:</div>
            <ol className="list-decimal list-inside space-y-1 text-xs">
              <li>Search @BotFather in Telegram</li>
              <li>Create bot with /newbot</li>
              <li>Copy bot token</li>
              <li>Message your bot</li>
              <li>Get chat ID from https://api.telegram.org/bot&lt;TOKEN&gt;/getUpdates</li>
            </ol>
          </div>

          <div className="space-y-2">
            <Label>Bot Token</Label>
            <Input
              type="password"
              placeholder="123456789:ABC..."
              value={telegramBotToken}
              onChange={(e) => setTelegramBotToken(e.target.value)}
            />
            <p className="text-xs text-gray-500">Encrypted with AES-256</p>
          </div>

          <div className="space-y-2">
            <Label>Chat ID</Label>
            <Input
              placeholder="123456789"
              value={telegramChatId}
              onChange={(e) => setTelegramChatId(e.target.value)}
            />
          </div>

          <div className="space-y-4">
            <div className="font-semibold">Notification Types</div>
            <div className="flex justify-between">
              <Label>Entry</Label>
              <Switch checked={notifyEntry} onCheckedChange={setNotifyEntry} />
            </div>
            <div className="flex justify-between">
              <Label>Exit</Label>
              <Switch checked={notifyExit} onCheckedChange={setNotifyExit} />
            </div>
            <div className="flex justify-between">
              <Label>Stop Loss</Label>
              <Switch checked={notifyStopLoss} onCheckedChange={setNotifyStopLoss} />
            </div>
            <div className="flex justify-between">
              <Label>Take Profit</Label>
              <Switch checked={notifyTakeProfit} onCheckedChange={setNotifyTakeProfit} />
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={handleTestTelegram}
              disabled={!telegramBotToken || !telegramChatId || isTestingTelegram}
              className="flex-1"
            >
              {isTestingTelegram ? 'Testing...' : 'Test'}
            </Button>
            <Button
              type="button"
              onClick={handleSaveTelegram}
              disabled={!telegramBotToken || !telegramChatId || isSavingTelegram}
              className="flex-1"
            >
              {isSavingTelegram ? 'Saving...' : 'Save'}
            </Button>
          </div>

          {telegramMessage && (
            <div
              className={`flex items-center gap-2 p-3 rounded-lg ${
                telegramMessage.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
              }`}
            >
              {telegramMessage.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              <span className="text-sm">{telegramMessage.text}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trading Bot Configuration Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            Trading Bot Configuration
          </CardTitle>
          <CardDescription>
            Configure automated trading settings for TradingView webhook integration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {configMessage && (
            <div
              className={`flex items-center gap-2 p-3 rounded-lg ${
                configMessage.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {configMessage.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              <span className="text-sm">{configMessage.text}</span>
            </div>
          )}

          {/* Existing Configs */}
          {tradingConfigs.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-sm">Active Configurations</h3>
              {tradingConfigs.map((config) => (
                <div key={config.id} className="border rounded-lg p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{config.exchange.toUpperCase()}</Badge>
                      {config.strategy && (
                        <Badge variant="secondary">{config.strategy}</Badge>
                      )}
                      <Badge variant={config.is_active ? 'default' : 'outline'}>
                        {config.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleConfig(config.id)}
                      >
                        <Power className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteConfig(config.id)}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Investment:</span>{' '}
                      <span className="font-medium">
                        {config.investment_type === 'percentage'
                          ? `${(config.investment_value * 100).toFixed(1)}%`
                          : `$${config.investment_value.toFixed(2)}`
                        }
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Leverage:</span>{' '}
                      <span className="font-medium">{config.leverage}x</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Stop Loss:</span>{' '}
                      <span className="font-medium">{config.stop_loss_percentage}%</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Take Profit:</span>{' '}
                      <span className="font-medium">{config.take_profit_percentage}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* New Config Form */}
          <div className="space-y-4 border-t pt-6">
            <h3 className="font-semibold text-sm">Create New Configuration</h3>

            {/* API Key Selection */}
            <div className="space-y-2">
              <Label>Exchange Account</Label>
              <Select value={selectedApiKey} onValueChange={setSelectedApiKey}>
                <SelectTrigger>
                  <SelectValue placeholder="Select API key account" />
                </SelectTrigger>
                <SelectContent>
                  {apiKeyAccounts.filter(acc => acc.is_active).map((acc) => (
                    <SelectItem key={acc.id} value={acc.id}>
                      {acc.exchange.toUpperCase()} ({acc.testnet ? 'Testnet' : 'Mainnet'})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Strategy Name */}
            <div className="space-y-2">
              <Label>Strategy Name (Optional)</Label>
              <Input
                placeholder="e.g., SuperTrend, RSI+EMA"
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
              />
            </div>

            {/* Investment Type */}
            <div className="space-y-2">
              <Label>Investment Type</Label>
              <RadioGroup value={investmentType} onValueChange={(v: any) => setInvestmentType(v)}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="percentage" id="percentage" />
                  <Label htmlFor="percentage">Percentage of Balance</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="fixed" id="fixed" />
                  <Label htmlFor="fixed">Fixed Amount (USDT)</Label>
                </div>
              </RadioGroup>
            </div>

            {/* Investment Value */}
            <div className="space-y-2">
              <Label>
                Investment Value {investmentType === 'percentage' ? '(%)' : '(USDT)'}
              </Label>
              <Input
                type="number"
                placeholder={investmentType === 'percentage' ? '10' : '100'}
                value={investmentValue}
                onChange={(e) => setInvestmentValue(e.target.value)}
                min="0"
                step={investmentType === 'percentage' ? '1' : '0.01'}
              />
              <p className="text-xs text-gray-500">
                {investmentType === 'percentage'
                  ? 'Percentage of available balance to use per trade (e.g., 10 = 10%)'
                  : 'Fixed USDT amount to use per trade (e.g., 100 = 100 USDT)'
                }
              </p>
            </div>

            {/* Leverage */}
            <div className="space-y-3">
              <div className="flex justify-between">
                <Label>Leverage</Label>
                <span className="font-bold text-blue-600">{configLeverage}x</span>
              </div>
              <Slider
                min={1}
                max={125}
                step={1}
                value={[configLeverage]}
                onValueChange={(v) => setConfigLeverage(v[0])}
              />
            </div>

            {/* Stop Loss */}
            <div className="space-y-2">
              <Label>Stop Loss (%)</Label>
              <Input
                type="number"
                placeholder="2.0"
                value={stopLossPercentage}
                onChange={(e) => setStopLossPercentage(parseFloat(e.target.value) || 0)}
                min="0.1"
                step="0.1"
              />
            </div>

            {/* Take Profit */}
            <div className="space-y-2">
              <Label>Take Profit (%)</Label>
              <Input
                type="number"
                placeholder="5.0"
                value={takeProfitPercentage}
                onChange={(e) => setTakeProfitPercentage(parseFloat(e.target.value) || 0)}
                min="0.1"
                step="0.1"
              />
            </div>

            <Button
              onClick={handleSaveTradingConfig}
              disabled={isSavingConfig || !selectedApiKey}
              className="w-full"
            >
              {isSavingConfig ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Trading Config'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}