'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Plus,
  TrendingUp,
  Shield,
  Zap,
  Settings,
  CheckCircle,
  Circle,
  Play,
  Pause,
  Trash2
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"

interface Strategy {
  id: string
  name: string
  description: string
  category: string
  mlWeight: number
  gpt4Weight: number
  claudeWeight: number
  taWeight: number
  defaultLeverage: number
  positionSizePct: number
  maxOpenPositions: number
  minProbability: number
  minConfidence: number
  usageCount: number
  avgWinRate: number | null
}

interface StrategyConfig {
  id: string
  strategyId: string
  name: string
  isActive: boolean
  autoTradeEnabled: boolean
  selectedSymbols: string[]
  totalTrades: number
  winRate: number | null
  totalPnl: number
  strategy: Strategy
}

interface AutoTradeStatus {
  isRunning: boolean
  strategyName?: string
  symbols?: string[]
  message: string
}

export default function StrategiesPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [myConfigs, setMyConfigs] = useState<StrategyConfig[]>([])
  const [autoTradeStatus, setAutoTradeStatus] = useState<AutoTradeStatus>({
    isRunning: false,
    message: 'Not running'
  })
  const [loading, setLoading] = useState(true)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [newConfigName, setNewConfigName] = useState('')
  const [selectedSymbols, setSelectedSymbols] = useState('BTCUSDT')

  // Load strategies and configs
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)

      // Load all strategies
      const strategiesRes = await fetch('/api/strategies')
      const strategiesData = await strategiesRes.json()
      setStrategies(strategiesData)

      // Load user's configs
      const configsRes = await fetch('/api/strategies/configs/my')
      const configsData = await configsRes.json()
      setMyConfigs(configsData)

      // Load auto-trade status
      const statusRes = await fetch('/api/strategies/auto-trade/status')
      const statusData = await statusRes.json()
      setAutoTradeStatus(statusData)

    } catch (error) {
      console.error('Error loading data:', error)
      toast({
        title: "오류",
        description: "데이터를 불러오는 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Create new config
  const handleCreateConfig = async () => {
    if (!selectedStrategy) return

    try {
      const response = await fetch('/api/strategies/configs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategyId: selectedStrategy.id,
          name: newConfigName || selectedStrategy.name,
          selectedSymbols: selectedSymbols.split(',').map(s => s.trim())
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to create config')
      }

      toast({
        title: "성공",
        description: "전략이 추가되었습니다.",
      })

      setShowCreateDialog(false)
      setNewConfigName('')
      setSelectedSymbols('BTCUSDT')
      setSelectedStrategy(null)
      loadData()

    } catch (error: any) {
      toast({
        title: "오류",
        description: error.message || "전략 추가 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    }
  }

  // Activate/deactivate config
  const handleToggleActive = async (configId: string, currentStatus: boolean) => {
    try {
      const response = await fetch(`/api/strategies/configs/${configId}/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isActive: !currentStatus })
      })

      if (!response.ok) throw new Error('Failed to toggle active status')

      toast({
        title: "성공",
        description: currentStatus ? "전략이 비활성화되었습니다." : "전략이 활성화되었습니다.",
      })

      loadData()

    } catch (error) {
      toast({
        title: "오류",
        description: "전략 상태 변경 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    }
  }

  // Toggle auto-trading
  const handleToggleAutoTrade = async (configId: string, enabled: boolean) => {
    try {
      const response = await fetch(`/api/strategies/configs/${configId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ autoTradeEnabled: !enabled })
      })

      if (!response.ok) throw new Error('Failed to toggle auto-trade')

      toast({
        title: "성공",
        description: enabled ? "자동 거래가 비활성화되었습니다." : "자동 거래가 활성화되었습니다.",
      })

      loadData()

    } catch (error) {
      toast({
        title: "오류",
        description: "자동 거래 설정 변경 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    }
  }

  // Start auto-trading
  const handleStartAutoTrading = async () => {
    try {
      const response = await fetch('/api/strategies/auto-trade/start', {
        method: 'POST'
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to start auto-trading')
      }

      toast({
        title: "성공",
        description: "자동 거래가 시작되었습니다.",
      })

      loadData()

    } catch (error: any) {
      toast({
        title: "오류",
        description: error.message || "자동 거래 시작 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    }
  }

  // Stop auto-trading
  const handleStopAutoTrading = async () => {
    try {
      const response = await fetch('/api/strategies/auto-trade/stop', {
        method: 'POST'
      })

      if (!response.ok) throw new Error('Failed to stop auto-trading')

      toast({
        title: "성공",
        description: "자동 거래가 중지되었습니다.",
      })

      loadData()

    } catch (error) {
      toast({
        title: "오류",
        description: "자동 거래 중지 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    }
  }

  // Delete config
  const handleDeleteConfig = async (configId: string) => {
    if (!confirm('정말 이 전략을 삭제하시겠습니까?')) return

    try {
      const response = await fetch(`/api/strategies/configs/${configId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to delete config')
      }

      toast({
        title: "성공",
        description: "전략이 삭제되었습니다.",
      })

      loadData()

    } catch (error: any) {
      toast({
        title: "오류",
        description: error.message || "전략 삭제 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'AI_ENSEMBLE':
        return <Zap className="h-4 w-4" />
      case 'TECHNICAL':
        return <TrendingUp className="h-4 w-4" />
      case 'HYBRID':
        return <Settings className="h-4 w-4" />
      default:
        return <Shield className="h-4 w-4" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'AI_ENSEMBLE':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/20'
      case 'TECHNICAL':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
      case 'HYBRID':
        return 'bg-green-500/10 text-green-500 border-green-500/20'
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    }
  }

  if (loading) {
    return (
      <div className="container py-8">
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">거래 전략</h1>
          <p className="text-muted-foreground mt-2">
            AI 앙상블 전략을 선택하고 자동 거래를 시작하세요
          </p>
        </div>
      </div>

      {/* Auto-Trading Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {autoTradeStatus.isRunning ? (
              <><Play className="h-5 w-5 text-green-500" /> 자동 거래 실행 중</>
            ) : (
              <><Pause className="h-5 w-5 text-gray-500" /> 자동 거래 중지</>
            )}
          </CardTitle>
          <CardDescription>
            {autoTradeStatus.isRunning && autoTradeStatus.strategyName
              ? `전략: ${autoTradeStatus.strategyName} | 심볼: ${autoTradeStatus.symbols?.join(', ')}`
              : '자동 거래를 시작하려면 전략을 활성화하고 자동 거래를 활성화하세요.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {autoTradeStatus.isRunning ? (
            <Button variant="destructive" onClick={handleStopAutoTrading}>
              <Pause className="mr-2 h-4 w-4" />
              자동 거래 중지
            </Button>
          ) : (
            <Button onClick={handleStartAutoTrading}>
              <Play className="mr-2 h-4 w-4" />
              자동 거래 시작
            </Button>
          )}
        </CardContent>
      </Card>

      {/* My Strategies */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">내 전략</h2>
        {myConfigs.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center text-muted-foreground">
                <p>아직 선택한 전략이 없습니다.</p>
                <p className="text-sm mt-2">아래에서 전략을 선택하세요.</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {myConfigs.map((config) => (
              <Card key={config.id} className={config.isActive ? 'border-primary' : ''}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {config.isActive && <CheckCircle className="h-5 w-5 text-primary" />}
                        {config.name}
                      </CardTitle>
                      <CardDescription className="mt-2">
                        {config.strategy.description.split('\n')[0]}
                      </CardDescription>
                    </div>
                    <Badge className={getCategoryColor(config.strategy.category)}>
                      {getCategoryIcon(config.strategy.category)}
                      <span className="ml-1">{config.strategy.category}</span>
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">총 거래</p>
                      <p className="font-semibold">{config.totalTrades}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">승률</p>
                      <p className="font-semibold">
                        {config.winRate ? `${(config.winRate * 100).toFixed(1)}%` : '-'}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">총 수익</p>
                      <p className={`font-semibold ${config.totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        ${config.totalPnl.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">심볼</p>
                      <p className="font-semibold text-xs">{config.selectedSymbols.join(', ')}</p>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant={config.isActive ? 'default' : 'outline'}
                      size="sm"
                      className="flex-1"
                      onClick={() => handleToggleActive(config.id, config.isActive)}
                    >
                      {config.isActive ? <CheckCircle className="mr-2 h-4 w-4" /> : <Circle className="mr-2 h-4 w-4" />}
                      {config.isActive ? '활성' : '비활성'}
                    </Button>
                    <Button
                      variant={config.autoTradeEnabled ? 'default' : 'outline'}
                      size="sm"
                      className="flex-1"
                      onClick={() => handleToggleAutoTrade(config.id, config.autoTradeEnabled)}
                    >
                      {config.autoTradeEnabled ? <Play className="mr-2 h-4 w-4" /> : <Pause className="mr-2 h-4 w-4" />}
                      자동 거래
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/strategies/${config.id}`)}
                    >
                      <Settings className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteConfig(config.id)}
                      disabled={config.autoTradeEnabled}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Available Strategies */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">사용 가능한 전략</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {strategies.map((strategy) => (
            <Card key={strategy.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg">{strategy.name}</CardTitle>
                  <Badge className={getCategoryColor(strategy.category)}>
                    {getCategoryIcon(strategy.category)}
                    <span className="ml-1">{strategy.category}</span>
                  </Badge>
                </div>
                <CardDescription className="mt-2 line-clamp-3">
                  {strategy.description.split('\n')[2] || strategy.description.split('\n')[0]}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-muted-foreground">ML</p>
                    <p className="font-semibold">{(strategy.mlWeight * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">GPT-4</p>
                    <p className="font-semibold">{(strategy.gpt4Weight * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Claude</p>
                    <p className="font-semibold">{(strategy.claudeWeight * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">TA</p>
                    <p className="font-semibold">{(strategy.taWeight * 100).toFixed(0)}%</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm pt-2 border-t">
                  <div>
                    <p className="text-muted-foreground">레버리지</p>
                    <p className="font-semibold">{strategy.defaultLeverage}x</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">포지션 크기</p>
                    <p className="font-semibold">{(strategy.positionSizePct * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">최소 확률</p>
                    <p className="font-semibold">{(strategy.minProbability * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">사용자</p>
                    <p className="font-semibold">{strategy.usageCount}</p>
                  </div>
                </div>

                <Button
                  className="w-full"
                  onClick={() => {
                    setSelectedStrategy(strategy)
                    setShowCreateDialog(true)
                  }}
                  disabled={myConfigs.some(c => c.strategyId === strategy.id)}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  {myConfigs.some(c => c.strategyId === strategy.id) ? '이미 추가됨' : '전략 추가'}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Create Config Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>전략 추가</DialogTitle>
            <DialogDescription>
              {selectedStrategy?.name} 전략을 추가합니다.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">전략 이름</Label>
              <Input
                id="name"
                placeholder={selectedStrategy?.name}
                value={newConfigName}
                onChange={(e) => setNewConfigName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="symbols">거래 심볼 (쉼표로 구분)</Label>
              <Input
                id="symbols"
                placeholder="BTCUSDT, ETHUSDT"
                value={selectedSymbols}
                onChange={(e) => setSelectedSymbols(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                예: BTCUSDT, ETHUSDT, BNBUSDT
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              취소
            </Button>
            <Button onClick={handleCreateConfig}>
              추가
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
