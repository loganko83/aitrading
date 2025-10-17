'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Save, RotateCcw, TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { toast } from 'sonner'
import BacktestChart from '@/components/trading/BacktestChart'
import PerformanceAnalytics from '@/components/trading/PerformanceAnalytics'

interface StrategyConfig {
  id: string
  userId: string
  strategyId: string
  name: string
  isActive: boolean
  customParams: {
    mlWeight?: number
    gpt4Weight?: number
    claudeWeight?: number
    taWeight?: number
    minProbability?: number
    minConfidence?: number
    minAgreement?: number
    defaultLeverage?: number
    positionSizePct?: number
    slAtrMultiplier?: number
    tpAtrMultiplier?: number
    maxOpenPositions?: number
  } | null
  totalTrades: number
  winRate: number | null
  totalPnl: number
  autoTradeEnabled: boolean
  selectedSymbols: string[]
  strategy: {
    id: string
    name: string
    description: string
    category: string
    mlWeight: number
    gpt4Weight: number
    claudeWeight: number
    taWeight: number
    minProbability: number
    minConfidence: number
    minAgreement: number
    defaultLeverage: number
    positionSizePct: number
    slAtrMultiplier: number
    tpAtrMultiplier: number
    maxOpenPositions: number
  }
}

interface StrategyParams {
  mlWeight: number
  gpt4Weight: number
  claudeWeight: number
  taWeight: number
  minProbability: number
  minConfidence: number
  minAgreement: number
  defaultLeverage: number
  positionSizePct: number
  slAtrMultiplier: number
  tpAtrMultiplier: number
  maxOpenPositions: number
}

export default function StrategyDetailPage() {
  const params = useParams()
  const router = useRouter()
  const configId = params.id as string

  const [config, setConfig] = useState<StrategyConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Editable parameters
  const [editedParams, setEditedParams] = useState<StrategyParams | null>(null)

  // Backtest data
  const [backtestData, setBacktestData] = useState<any>(null)
  const [loadingBacktest, setLoadingBacktest] = useState(false)

  useEffect(() => {
    loadConfig()
  }, [configId])

  const loadConfig = async () => {
    try {
      const res = await fetch(`/api/strategies/configs/${configId}`)
      if (!res.ok) throw new Error('Failed to load config')

      const data = await res.json()
      setConfig(data)

      // Initialize edited params with custom params or default strategy params
      const initialParams = {
        mlWeight: data.customParams?.mlWeight ?? data.strategy.mlWeight,
        gpt4Weight: data.customParams?.gpt4Weight ?? data.strategy.gpt4Weight,
        claudeWeight: data.customParams?.claudeWeight ?? data.strategy.claudeWeight,
        taWeight: data.customParams?.taWeight ?? data.strategy.taWeight,
        minProbability: data.customParams?.minProbability ?? data.strategy.minProbability,
        minConfidence: data.customParams?.minConfidence ?? data.strategy.minConfidence,
        minAgreement: data.customParams?.minAgreement ?? data.strategy.minAgreement,
        defaultLeverage: data.customParams?.defaultLeverage ?? data.strategy.defaultLeverage,
        positionSizePct: data.customParams?.positionSizePct ?? data.strategy.positionSizePct,
        slAtrMultiplier: data.customParams?.slAtrMultiplier ?? data.strategy.slAtrMultiplier,
        tpAtrMultiplier: data.customParams?.tpAtrMultiplier ?? data.strategy.tpAtrMultiplier,
        maxOpenPositions: data.customParams?.maxOpenPositions ?? data.strategy.maxOpenPositions,
      }
      setEditedParams(initialParams)
    } catch (error) {
      toast.error('설정을 불러오는데 실패했습니다')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const loadBacktestData = async () => {
    setLoadingBacktest(true)
    try {
      const res = await fetch(`/api/strategies/configs/${configId}/backtest`)
      if (!res.ok) throw new Error('Failed to load backtest data')
      const data = await res.json()
      setBacktestData(data)
    } catch (error) {
      toast.error('백테스팅 데이터를 불러오는데 실패했습니다')
      console.error(error)
    } finally {
      setLoadingBacktest(false)
    }
  }

  const handleSave = async () => {
    if (!editedParams) return

    setSaving(true)
    try {
      const res = await fetch(`/api/strategies/configs/${configId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customParams: editedParams
        })
      })

      if (!res.ok) throw new Error('Failed to save')

      toast.success('설정이 저장되었습니다')
      await loadConfig()
    } catch (error) {
      toast.error('설정 저장에 실패했습니다')
      console.error(error)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    if (!config) return

    setEditedParams({
      mlWeight: config.strategy.mlWeight,
      gpt4Weight: config.strategy.gpt4Weight,
      claudeWeight: config.strategy.claudeWeight,
      taWeight: config.strategy.taWeight,
      minProbability: config.strategy.minProbability,
      minConfidence: config.strategy.minConfidence,
      minAgreement: config.strategy.minAgreement,
      defaultLeverage: config.strategy.defaultLeverage,
      positionSizePct: config.strategy.positionSizePct,
      slAtrMultiplier: config.strategy.slAtrMultiplier,
      tpAtrMultiplier: config.strategy.tpAtrMultiplier,
      maxOpenPositions: config.strategy.maxOpenPositions,
    })
    toast.info('기본값으로 초기화되었습니다')
  }

  const updateParam = (key: keyof StrategyParams, value: number) => {
    if (!editedParams) return
    setEditedParams({ ...editedParams, [key]: value })
  }

  if (loading || !config || !editedParams) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">전략 설정을 불러오는 중...</p>
        </div>
      </div>
    )
  }

  const aiWeightTotal = editedParams.mlWeight + editedParams.gpt4Weight + editedParams.claudeWeight + editedParams.taWeight
  const isWeightValid = Math.abs(aiWeightTotal - 1.0) < 0.01

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{config.name}</h1>
            <p className="text-muted-foreground">{config.strategy.name}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-2" />
            기본값 복원
          </Button>
          <Button onClick={handleSave} disabled={saving || !isWeightValid}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? '저장 중...' : '설정 저장'}
          </Button>
        </div>
      </div>

      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>총 거래 횟수</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{config.totalTrades}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>승률</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {config.winRate !== null ? `${(config.winRate * 100).toFixed(1)}%` : 'N/A'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>총 손익</CardDescription>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold flex items-center ${config.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {config.totalPnl >= 0 ? <TrendingUp className="h-5 w-5 mr-1" /> : <TrendingDown className="h-5 w-5 mr-1" />}
              ${config.totalPnl.toFixed(2)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>상태</CardDescription>
          </CardHeader>
          <CardContent>
            <Badge variant={config.isActive ? 'default' : 'secondary'}>
              {config.isActive ? '활성화' : '비활성화'}
            </Badge>
            {config.autoTradeEnabled && (
              <Badge variant="outline" className="ml-2">자동매매</Badge>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Settings Tabs */}
      <Tabs defaultValue="ai-weights" className="space-y-4">
        <TabsList>
          <TabsTrigger value="ai-weights">AI 가중치</TabsTrigger>
          <TabsTrigger value="entry-conditions">진입 조건</TabsTrigger>
          <TabsTrigger value="risk-management">리스크 관리</TabsTrigger>
          <TabsTrigger value="backtest" onClick={() => !backtestData && loadBacktestData()}>
            백테스팅
          </TabsTrigger>
          <TabsTrigger value="performance">성과 분석</TabsTrigger>
        </TabsList>

        {/* AI Weights Tab */}
        <TabsContent value="ai-weights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI 모델 가중치 설정</CardTitle>
              <CardDescription>
                각 AI 모델의 영향력을 조절합니다. 합계는 1.0이어야 합니다.
                {!isWeightValid && (
                  <span className="text-red-500 block mt-2">
                    ⚠️ 가중치 합계: {aiWeightTotal.toFixed(2)} (1.00이어야 함)
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* ML Weight */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>ML 모델 (LSTM, Transformer, LightGBM)</Label>
                  <span className="text-sm font-medium">{(editedParams.mlWeight * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[editedParams.mlWeight * 100]}
                  onValueChange={([value]) => updateParam('mlWeight', value / 100)}
                  max={100}
                  step={5}
                />
              </div>

              {/* GPT-4 Weight */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>GPT-4 (시장 분석 & 패턴 인식)</Label>
                  <span className="text-sm font-medium">{(editedParams.gpt4Weight * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[editedParams.gpt4Weight * 100]}
                  onValueChange={([value]) => updateParam('gpt4Weight', value / 100)}
                  max={100}
                  step={5}
                />
              </div>

              {/* Claude Weight */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Claude (리스크 관리 & 전략 최적화)</Label>
                  <span className="text-sm font-medium">{(editedParams.claudeWeight * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[editedParams.claudeWeight * 100]}
                  onValueChange={([value]) => updateParam('claudeWeight', value / 100)}
                  max={100}
                  step={5}
                />
              </div>

              {/* TA Weight */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>기술적 분석 (ATR 기반)</Label>
                  <span className="text-sm font-medium">{(editedParams.taWeight * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[editedParams.taWeight * 100]}
                  onValueChange={([value]) => updateParam('taWeight', value / 100)}
                  max={100}
                  step={5}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Entry Conditions Tab */}
        <TabsContent value="entry-conditions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>진입 조건 설정</CardTitle>
              <CardDescription>
                거래 진입을 위한 최소 요구 조건을 설정합니다.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Min Probability */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>최소 승률 예측</Label>
                  <span className="text-sm font-medium">{(editedParams.minProbability * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[editedParams.minProbability * 100]}
                  onValueChange={([value]) => updateParam('minProbability', value / 100)}
                  min={50}
                  max={95}
                  step={5}
                />
              </div>

              {/* Min Confidence */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>최소 신뢰도</Label>
                  <span className="text-sm font-medium">{(editedParams.minConfidence * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[editedParams.minConfidence * 100]}
                  onValueChange={([value]) => updateParam('minConfidence', value / 100)}
                  min={50}
                  max={95}
                  step={5}
                />
              </div>

              {/* Min Agreement */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>최소 AI 합의도</Label>
                  <span className="text-sm font-medium">{(editedParams.minAgreement * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[editedParams.minAgreement * 100]}
                  onValueChange={([value]) => updateParam('minAgreement', value / 100)}
                  min={50}
                  max={95}
                  step={5}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Management Tab */}
        <TabsContent value="risk-management" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>리스크 관리 설정</CardTitle>
              <CardDescription>
                레버리지, 포지션 크기, 손절/익절 설정을 조절합니다.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Leverage */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>레버리지</Label>
                  <span className="text-sm font-medium">{editedParams.defaultLeverage}x</span>
                </div>
                <Slider
                  value={[editedParams.defaultLeverage]}
                  onValueChange={([value]) => updateParam('defaultLeverage', value)}
                  min={1}
                  max={20}
                  step={1}
                />
              </div>

              {/* Position Size */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>포지션 크기 (잔고 대비)</Label>
                  <span className="text-sm font-medium">{(editedParams.positionSizePct * 100).toFixed(0)}%</span>
                </div>
                <Slider
                  value={[editedParams.positionSizePct * 100]}
                  onValueChange={([value]) => updateParam('positionSizePct', value / 100)}
                  min={5}
                  max={50}
                  step={5}
                />
              </div>

              {/* Stop Loss */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>손절 (ATR 배수)</Label>
                  <span className="text-sm font-medium">{editedParams.slAtrMultiplier.toFixed(1)}x</span>
                </div>
                <Slider
                  value={[editedParams.slAtrMultiplier * 10]}
                  onValueChange={([value]) => updateParam('slAtrMultiplier', value / 10)}
                  min={10}
                  max={50}
                  step={5}
                />
              </div>

              {/* Take Profit */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>익절 (ATR 배수)</Label>
                  <span className="text-sm font-medium">{editedParams.tpAtrMultiplier.toFixed(1)}x</span>
                </div>
                <Slider
                  value={[editedParams.tpAtrMultiplier * 10]}
                  onValueChange={([value]) => updateParam('tpAtrMultiplier', value / 10)}
                  min={10}
                  max={100}
                  step={5}
                />
              </div>

              {/* Max Open Positions */}
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>최대 동시 포지션</Label>
                  <span className="text-sm font-medium">{editedParams.maxOpenPositions}</span>
                </div>
                <Slider
                  value={[editedParams.maxOpenPositions]}
                  onValueChange={([value]) => updateParam('maxOpenPositions', value)}
                  min={1}
                  max={10}
                  step={1}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Backtest Tab */}
        <TabsContent value="backtest" className="space-y-4">
          {loadingBacktest ? (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <Activity className="h-8 w-8 animate-spin" />
              </CardContent>
            </Card>
          ) : backtestData ? (
            <BacktestChart data={backtestData.data} metrics={backtestData.metrics} />
          ) : null}
        </TabsContent>

        {/* Performance Analytics Tab */}
        <TabsContent value="performance" className="space-y-4">
          <PerformanceAnalytics strategyConfigId={configId} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
