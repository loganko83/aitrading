'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  AlertCircle,
  RefreshCw,
  BarChart3
} from 'lucide-react'
import { apiGet } from '@/lib/utils/api'
import type { Position } from '@/types'

interface PositionMonitorProps {
  initialPositions?: Position[]
  autoRefresh?: boolean
  refreshInterval?: number
}

interface PositionsResponse {
  positions: Position[]
}

export default function PositionMonitor({
  initialPositions = [],
  autoRefresh = true,
  refreshInterval = 5000
}: PositionMonitorProps) {
  const [positions, setPositions] = useState<Position[]>(initialPositions)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  // Fetch positions from API with improved error handling
  const fetchPositions = async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await apiGet<PositionsResponse>('/api/positions')
      setPositions(data.positions || [])
      setLastUpdate(new Date())
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch positions'
      setError(errorMessage)
      console.error('Error fetching positions:', err)
    } finally {
      setLoading(false)
    }
  }

  // Auto-refresh positions
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchPositions, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  // Calculate aggregated metrics
  const metrics = positions.reduce((acc, pos) => {
    acc.totalPnl += pos.current_pnl
    acc.totalValue += (pos.current_price || pos.entry_price) * pos.quantity
    if (pos.current_pnl > 0) acc.profitableCount++
    return acc
  }, { totalPnl: 0, totalValue: 0, profitableCount: 0 })

  const winRate = positions.length > 0
    ? ((metrics.profitableCount / positions.length) * 100).toFixed(1)
    : '0.0'

  // Group positions by status
  const openPositions = positions.filter(p => p.status === 'OPEN')
  const longPositions = openPositions.filter(p => p.side === 'LONG')
  const shortPositions = openPositions.filter(p => p.side === 'SHORT')

  // Risk metrics
  const totalMarginUsed = openPositions.reduce((sum, pos) => {
    return sum + (pos.entry_price * pos.quantity / pos.leverage)
  }, 0)

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Positions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{openPositions.length}</div>
            <p className="text-xs text-muted-foreground">
              {longPositions.length} LONG · {shortPositions.length} SHORT
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Unrealized PnL</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${metrics.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {metrics.totalPnl >= 0 ? '+' : ''}{metrics.totalPnl.toFixed(2)} USDT
            </div>
            <p className="text-xs text-muted-foreground">
              Position Value: ${metrics.totalValue.toLocaleString()}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{winRate}%</div>
            <p className="text-xs text-muted-foreground">
              {metrics.profitableCount} of {positions.length} profitable
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Margin Used</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalMarginUsed.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              Avg Leverage: {openPositions.length > 0
                ? (openPositions.reduce((sum, p) => sum + p.leverage, 0) / openPositions.length).toFixed(1)
                : '0.0'}x
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Position List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Active Positions</CardTitle>
              <CardDescription>
                Real-time position monitoring · Last updated: {lastUpdate.toLocaleTimeString()}
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchPositions}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="all" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="all">All ({openPositions.length})</TabsTrigger>
              <TabsTrigger value="long">LONG ({longPositions.length})</TabsTrigger>
              <TabsTrigger value="short">SHORT ({shortPositions.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="space-y-4 mt-4">
              {openPositions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No open positions</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {openPositions.map(position => (
                    <PositionRow key={position.id} position={position} />
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="long" className="space-y-4 mt-4">
              {longPositions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No LONG positions</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {longPositions.map(position => (
                    <PositionRow key={position.id} position={position} />
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="short" className="space-y-4 mt-4">
              {shortPositions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No SHORT positions</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {shortPositions.map(position => (
                    <PositionRow key={position.id} position={position} />
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

// Position Row Component
function PositionRow({ position }: { position: Position }) {
  const isProfit = position.current_pnl >= 0
  const pnlPercentage = position.current_pnl_pct.toFixed(2)
  const currentPrice = position.current_price || position.entry_price
  const priceChange = ((currentPrice - position.entry_price) / position.entry_price * 100).toFixed(2)

  // Calculate distance to SL/TP
  const distanceToSL = position.sl_price
    ? ((Math.abs(currentPrice - position.sl_price) / currentPrice) * 100).toFixed(2)
    : null
  const distanceToTP = position.tp_price
    ? ((Math.abs(position.tp_price - currentPrice) / currentPrice) * 100).toFixed(2)
    : null

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          {/* Left: Symbol and Side */}
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <h4 className="font-semibold text-lg">{position.symbol}</h4>
              <Badge variant={position.side === 'LONG' ? 'default' : 'destructive'}>
                {position.side}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {position.leverage}x
              </Badge>
            </div>
            <div className="text-sm text-muted-foreground">
              Qty: {position.quantity} · Entry: ${position.entry_price.toLocaleString()}
            </div>
          </div>

          {/* Right: PnL */}
          <div className="text-right">
            <div className="flex items-center justify-end space-x-1">
              {isProfit ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <span className={`text-lg font-bold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                {isProfit ? '+' : ''}{position.current_pnl.toFixed(2)} USDT
              </span>
            </div>
            <div className={`text-sm ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
              {isProfit ? '+' : ''}{pnlPercentage}%
            </div>
          </div>
        </div>

        {/* Middle: Price Info */}
        <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t">
          <div>
            <p className="text-xs text-muted-foreground">Current Price</p>
            <p className="text-sm font-semibold">${currentPrice.toLocaleString()}</p>
            <p className={`text-xs ${Number(priceChange) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {Number(priceChange) >= 0 ? '+' : ''}{priceChange}%
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">Stop Loss</p>
            <p className="text-sm font-semibold text-red-600">
              ${position.sl_price?.toLocaleString() || 'N/A'}
            </p>
            {distanceToSL && (
              <p className="text-xs text-muted-foreground">{distanceToSL}% away</p>
            )}
          </div>

          <div>
            <p className="text-xs text-muted-foreground">Take Profit</p>
            <p className="text-sm font-semibold text-green-600">
              ${position.tp_price?.toLocaleString() || 'N/A'}
            </p>
            {distanceToTP && (
              <p className="text-xs text-muted-foreground">{distanceToTP}% away</p>
            )}
          </div>
        </div>

        {/* AI Analysis Summary */}
        {position.ai_analysis && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2">
                <span className="text-muted-foreground">AI Confidence:</span>
                <Badge variant="outline" className="text-xs">
                  {(position.ai_analysis.confidence * 100).toFixed(0)}%
                </Badge>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-muted-foreground">Model Agreement:</span>
                <Badge variant="outline" className="text-xs">
                  {(position.ai_analysis.model_agreement * 100).toFixed(0)}%
                </Badge>
              </div>
              <div className="text-muted-foreground">
                Opened: {new Date(position.opened_at).toLocaleTimeString()}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
