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
import { AlertCircle, CheckCircle2, Loader2, TrendingUp, Shield, DollarSign } from 'lucide-react';
import { RISK_PRESETS, AVAILABLE_COINS, type CoinSymbol } from '@/types';
import { useTradingStore } from '@/lib/stores/tradingStore';

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

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const { settings, setSettings } = useTradingStore();

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
        setMessage({ type: 'success', text: '설정이 성공적으로 저장되었습니다!' });
        if (result.data) {
          setSettings(result.data);
        }
      } else {
        setMessage({ type: 'error', text: result.error || '설정 저장에 실패했습니다.' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '네트워크 오류가 발생했습니다.' });
    } finally {
      setIsSaving(false);
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
        <h1 className="text-3xl font-bold text-gray-900">거래 설정</h1>
        <p className="text-gray-600 mt-2">
          AI 자동 거래 봇의 위험 관리 및 거래 전략을 설정하세요
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
          {message.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Risk Tolerance Presets */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              위험 성향
            </CardTitle>
            <CardDescription>
              투자 성향에 맞는 프리셋을 선택하세요 (레버리지와 포지션 크기가 자동 설정됩니다)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <button
                type="button"
                onClick={() => applyRiskPreset('low')}
                className={`p-4 border-2 rounded-lg transition-all ${
                  riskTolerance === 'low'
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-sm font-semibold text-gray-900">안정형 (Low)</div>
                <div className="mt-2 space-y-1 text-xs text-gray-600">
                  <div>레버리지: 3배</div>
                  <div>포지션 크기: 5%</div>
                  <div>진입 기준: 엄격</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => applyRiskPreset('medium')}
                className={`p-4 border-2 rounded-lg transition-all ${
                  riskTolerance === 'medium'
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-sm font-semibold text-gray-900">균형형 (Medium)</div>
                <div className="mt-2 space-y-1 text-xs text-gray-600">
                  <div>레버리지: 5배</div>
                  <div>포지션 크기: 10%</div>
                  <div>진입 기준: 보통</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => applyRiskPreset('high')}
                className={`p-4 border-2 rounded-lg transition-all ${
                  riskTolerance === 'high'
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-sm font-semibold text-gray-900">공격형 (High)</div>
                <div className="mt-2 space-y-1 text-xs text-gray-600">
                  <div>레버리지: 5배</div>
                  <div>포지션 크기: 15%</div>
                  <div>진입 기준: 유연</div>
                </div>
              </button>
            </div>
            {errors.risk_tolerance && (
              <p className="text-red-600 text-sm mt-2">{errors.risk_tolerance.message}</p>
            )}
          </CardContent>
        </Card>

        {/* Coin Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              거래 코인 선택
            </CardTitle>
            <CardDescription>
              자동 거래를 수행할 암호화폐를 선택하세요 (다중 선택 가능)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {AVAILABLE_COINS.map((coin) => (
                <button
                  key={coin}
                  type="button"
                  onClick={() => toggleCoin(coin)}
                  className={`p-4 border-2 rounded-lg transition-all font-semibold ${
                    selectedCoins.includes(coin)
                      ? 'border-blue-600 bg-blue-50 text-blue-900'
                      : 'border-gray-200 text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {coin}
                </button>
              ))}
            </div>
            {selectedCoins.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {selectedCoins.map((coin) => (
                  <Badge key={coin} variant="default">
                    {coin}
                  </Badge>
                ))}
              </div>
            )}
            {errors.selected_coins && (
              <p className="text-red-600 text-sm mt-2">{errors.selected_coins.message}</p>
            )}
          </CardContent>
        </Card>

        {/* Leverage & Position Size */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              레버리지 및 포지션 크기
            </CardTitle>
            <CardDescription>
              거래당 사용할 레버리지와 계좌 자산 대비 포지션 크기를 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Leverage Slider */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="leverage">레버리지 배수</Label>
                <span className="text-2xl font-bold text-blue-600">{leverage}x</span>
              </div>
              <Slider
                id="leverage"
                min={1}
                max={5}
                step={1}
                value={[leverage]}
                onValueChange={(value) => setValue('leverage', value[0])}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>1x (안전)</span>
                <span>3x (보통)</span>
                <span>5x (공격적)</span>
              </div>
            </div>

            {/* Position Size Slider */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="position-size">포지션 크기 (계좌 대비 %)</Label>
                <span className="text-2xl font-bold text-blue-600">
                  {(positionSizePct * 100).toFixed(0)}%
                </span>
              </div>
              <Slider
                id="position-size"
                min={0.05}
                max={0.20}
                step={0.01}
                value={[positionSizePct]}
                onValueChange={(value) => setValue('position_size_pct', value[0])}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>5% (안전)</span>
                <span>10% (보통)</span>
                <span>20% (공격적)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ATR Multipliers */}
        <Card>
          <CardHeader>
            <CardTitle>손절/익절 설정 (ATR 기준)</CardTitle>
            <CardDescription>
              ATR (Average True Range) 배수로 손절가와 익절가를 설정합니다
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Stop Loss Multiplier */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="stop-loss">손절 ATR 배수</Label>
                <span className="text-xl font-bold text-red-600">
                  {stopLossMultiplier.toFixed(1)}x
                </span>
              </div>
              <Slider
                id="stop-loss"
                min={1.0}
                max={3.0}
                step={0.1}
                value={[stopLossMultiplier]}
                onValueChange={(value) => setValue('stop_loss_atr_multiplier', value[0])}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>1.0x (타이트)</span>
                <span>2.0x (보통)</span>
                <span>3.0x (여유)</span>
              </div>
            </div>

            {/* Take Profit Multiplier */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="take-profit">익절 ATR 배수</Label>
                <span className="text-xl font-bold text-green-600">
                  {takeProfitMultiplier.toFixed(1)}x
                </span>
              </div>
              <Slider
                id="take-profit"
                min={2.0}
                max={5.0}
                step={0.1}
                value={[takeProfitMultiplier]}
                onValueChange={(value) => setValue('take_profit_atr_multiplier', value[0])}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>2.0x (빠른 청산)</span>
                <span>3.5x (보통)</span>
                <span>5.0x (큰 수익)</span>
              </div>
            </div>

            {/* Risk-Reward Ratio */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-sm font-semibold text-blue-900">
                위험/보상 비율 (Risk-Reward Ratio)
              </div>
              <div className="text-2xl font-bold text-blue-600 mt-2">
                1 : {(takeProfitMultiplier / stopLossMultiplier).toFixed(2)}
              </div>
              <p className="text-xs text-blue-700 mt-1">
                손실 1원당 예상 수익 {(takeProfitMultiplier / stopLossMultiplier).toFixed(2)}원
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Auto Close on Reversal */}
        <Card>
          <CardHeader>
            <CardTitle>추가 옵션</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="auto-close">AI 예측 반전 시 자동 청산</Label>
                <p className="text-sm text-gray-500 mt-1">
                  AI가 포지션 반대 방향으로 예측을 변경하면 즉시 포지션을 청산합니다
                </p>
              </div>
              <Switch
                id="auto-close"
                checked={watch('auto_close_on_reversal')}
                onCheckedChange={(checked) => setValue('auto_close_on_reversal', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex justify-end">
          <Button
            type="submit"
            size="lg"
            disabled={isSaving}
            className="min-w-[200px]"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                저장 중...
              </>
            ) : (
              '설정 저장'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
