'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import {
  Target,
  Clock,
  DollarSign,
  Activity,
  AlertCircle,
  Download,
} from 'lucide-react'
import { apiGet } from '@/lib/utils/api'
import { LoadingChart } from '@/components/LoadingState'

interface PerformanceData {
  equity_curve: {
    timestamp: string
    equity: number
    drawdown: number
  }[]
  daily_pnl: {
    date: string
    pnl: number
    trades: number
  }[]
  win_loss_distribution: {
    range: string
    count: number
    percentage: number
  }[]
  trading_hours: {
    hour: number
    trades: number
    avg_pnl: number
  }[]
  symbol_performance: {
    symbol: string
    trades: number
    win_rate: number
    total_pnl: number
    avg_pnl: number
  }[]
  metrics: {
    total_trades: number
    win_rate: number
    total_pnl: number
    avg_win: number
    avg_loss: number
    profit_factor: number
    sharpe_ratio: number
    max_drawdown: number
    avg_holding_time: number
    best_trade: number
    worst_trade: number
    consecutive_wins: number
    consecutive_losses: number
  }
}

interface PerformanceAnalyticsProps {
  strategyConfigId?: string
  timeRange?: '7d' | '30d' | '90d' | 'all'
}

export default function PerformanceAnalytics({
  strategyConfigId,
  timeRange = '30d'
}: PerformanceAnalyticsProps) {
  const [data, setData] = useState<PerformanceData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedRange, setSelectedRange] = useState(timeRange)

  // Fetch performance data with improved error handling
  const fetchPerformanceData = async () => {
    setLoading(true)
    setError(null)

    try {
      const url = strategyConfigId
        ? `/api/strategies/configs/${strategyConfigId}/performance?range=${selectedRange}`
        : `/api/performance?range=${selectedRange}`

      const result = await apiGet<PerformanceData>(url)
      setData(result)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch performance data'
      setError(errorMessage)
      console.error('Error fetching performance data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPerformanceData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strategyConfigId, selectedRange])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <LoadingChart key={i} />
          ))}
        </div>
        <LoadingChart />
      </div>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">No performance data available</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const metrics = data.metrics

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold">Performance Analytics</h3>
          <p className="text-muted-foreground">Comprehensive trading performance analysis</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
          <div className="flex items-center space-x-1 border rounded-md">
            <Button
              variant={selectedRange === '7d' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setSelectedRange('7d')}
            >
              7D
            </Button>
            <Button
              variant={selectedRange === '30d' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setSelectedRange('30d')}
            >
              30D
            </Button>
            <Button
              variant={selectedRange === '90d' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setSelectedRange('90d')}
            >
              90D
            </Button>
            <Button
              variant={selectedRange === 'all' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setSelectedRange('all')}
            >
              All
            </Button>
          </div>
        </div>
      </div>

      {/* Key Metrics Summary */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_trades}</div>
            <p className="text-xs text-muted-foreground">
              {metrics.consecutive_wins} max consecutive wins
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(metrics.win_rate * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              Profit Factor: {metrics.profit_factor.toFixed(2)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total PnL</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${metrics.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {metrics.total_pnl >= 0 ? '+' : ''}{metrics.total_pnl.toFixed(2)} USDT
            </div>
            <p className="text-xs text-muted-foreground">
              Sharpe: {metrics.sharpe_ratio.toFixed(2)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Holding</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(metrics.avg_holding_time / 60).toFixed(1)}h</div>
            <p className="text-xs text-muted-foreground">
              Max DD: {(metrics.max_drawdown * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics Tabs */}
      <Tabs defaultValue="equity" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="equity">Equity Curve</TabsTrigger>
          <TabsTrigger value="pnl">Daily PnL</TabsTrigger>
          <TabsTrigger value="distribution">Win/Loss</TabsTrigger>
          <TabsTrigger value="timing">Timing</TabsTrigger>
          <TabsTrigger value="symbols">Symbols</TabsTrigger>
        </TabsList>

        {/* Equity Curve Tab */}
        <TabsContent value="equity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Equity Curve & Drawdown</CardTitle>
              <CardDescription>Account equity progression over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={data.equity_curve}>
                  <defs>
                    <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="equity"
                    stroke="#10b981"
                    fillOpacity={1}
                    fill="url(#colorEquity)"
                    name="Equity"
                  />
                  <Area
                    yAxisId="right"
                    type="monotone"
                    dataKey="drawdown"
                    stroke="#ef4444"
                    fillOpacity={1}
                    fill="url(#colorDrawdown)"
                    name="Drawdown %"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Win/Loss Statistics */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Win Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Average Win</span>
                  <span className="text-sm font-bold text-green-600">
                    +{metrics.avg_win.toFixed(2)} USDT
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Best Trade</span>
                  <span className="text-sm font-bold text-green-600">
                    +{metrics.best_trade.toFixed(2)} USDT
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Consecutive Wins</span>
                  <span className="text-sm font-bold">{metrics.consecutive_wins}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Loss Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Average Loss</span>
                  <span className="text-sm font-bold text-red-600">
                    {metrics.avg_loss.toFixed(2)} USDT
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Worst Trade</span>
                  <span className="text-sm font-bold text-red-600">
                    {metrics.worst_trade.toFixed(2)} USDT
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Consecutive Losses</span>
                  <span className="text-sm font-bold">{metrics.consecutive_losses}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Daily PnL Tab */}
        <TabsContent value="pnl" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Daily PnL Distribution</CardTitle>
              <CardDescription>Profit and loss breakdown by day</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data.daily_pnl}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <ReferenceLine y={0} stroke="#000" />
                  <Bar
                    dataKey="pnl"
                    fill="#10b981"
                    name="Daily PnL"
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Win/Loss Distribution Tab */}
        <TabsContent value="distribution" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Win/Loss Distribution</CardTitle>
              <CardDescription>Trade outcome distribution by PnL range</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data.win_loss_distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#3b82f6" name="Trade Count" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trading Hours Tab */}
        <TabsContent value="timing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trading Hours Analysis</CardTitle>
              <CardDescription>Performance by hour of day</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={data.trading_hours}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="trades"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Trade Count"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="avg_pnl"
                    stroke="#10b981"
                    strokeWidth={2}
                    name="Avg PnL"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Symbol Performance Tab */}
        <TabsContent value="symbols" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Symbol Performance</CardTitle>
              <CardDescription>Performance breakdown by trading pair</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.symbol_performance.map((symbol, index) => (
                  <div key={symbol.symbol} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-semibold">{symbol.symbol}</h4>
                        <Badge variant="outline">{symbol.trades} trades</Badge>
                      </div>
                      <div className={`text-lg font-bold ${symbol.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {symbol.total_pnl >= 0 ? '+' : ''}{symbol.total_pnl.toFixed(2)} USDT
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Win Rate</p>
                        <p className="font-semibold">{(symbol.win_rate * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Avg PnL</p>
                        <p className={`font-semibold ${symbol.avg_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {symbol.avg_pnl >= 0 ? '+' : ''}{symbol.avg_pnl.toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Total Trades</p>
                        <p className="font-semibold">{symbol.trades}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
