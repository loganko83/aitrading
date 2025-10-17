'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react'

interface BacktestData {
  timestamp: string
  cumulativePnl: number
  dailyPnl: number
  drawdown: number
  equity: number
  trades: number
}

interface BacktestMetrics {
  totalTrades: number
  winRate: number
  totalPnl: number
  maxDrawdown: number
  sharpeRatio: number
  avgWin: number
  avgLoss: number
  profitFactor: number
}

interface BacktestChartProps {
  data: BacktestData[]
  metrics: BacktestMetrics
}

export default function BacktestChart({ data, metrics }: BacktestChartProps) {
  const formatCurrency = (value: number) => {
    return `$${value.toFixed(2)}`
  }

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`
  }

  return (
    <div className="space-y-6">
      {/* Metrics Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 손익</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${metrics.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(metrics.totalPnl)}
            </div>
            <p className="text-xs text-muted-foreground">
              총 {metrics.totalTrades}건 거래
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">승률</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercent(metrics.winRate)}</div>
            <p className="text-xs text-muted-foreground">
              수익률 {formatPercent(metrics.profitFactor)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">최대 낙폭</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatPercent(metrics.maxDrawdown)}
            </div>
            <p className="text-xs text-muted-foreground">
              최대 손실 구간
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">샤프 지수</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.sharpeRatio.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              위험 대비 수익률
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="equity" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="equity">자산 곡선</TabsTrigger>
          <TabsTrigger value="pnl">손익 분포</TabsTrigger>
          <TabsTrigger value="drawdown">낙폭 분석</TabsTrigger>
          <TabsTrigger value="trades">거래 빈도</TabsTrigger>
        </TabsList>

        {/* Equity Curve */}
        <TabsContent value="equity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>누적 자산 곡선</CardTitle>
              <CardDescription>시간에 따른 자산 증감 추이</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="equity"
                    stroke="#8884d8"
                    fillOpacity={1}
                    fill="url(#colorEquity)"
                    name="자산"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* P&L Distribution */}
        <TabsContent value="pnl" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>일별 손익 분포</CardTitle>
              <CardDescription>일일 손익 변동성 분석</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Legend />
                  <ReferenceLine y={0} stroke="#000" />
                  <Bar
                    dataKey="dailyPnl"
                    fill="#82ca9d"
                    name="일일 손익"
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Drawdown Analysis */}
        <TabsContent value="drawdown" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>낙폭 분석</CardTitle>
              <CardDescription>최고점 대비 손실률 추적</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ff4444" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#ff4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => formatPercent(value)} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="drawdown"
                    stroke="#ff4444"
                    fillOpacity={1}
                    fill="url(#colorDrawdown)"
                    name="낙폭"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trade Frequency */}
        <TabsContent value="trades" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>거래 빈도</CardTitle>
              <CardDescription>기간별 거래 건수 분석</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="trades"
                    stroke="#ffc658"
                    strokeWidth={2}
                    name="거래 건수"
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Win/Loss Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>승/패 분석</CardTitle>
          <CardDescription>평균 승률 및 손실률 비교</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">평균 승리</span>
                <span className="text-sm text-green-600 font-bold">
                  {formatCurrency(metrics.avgWin)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">평균 손실</span>
                <span className="text-sm text-red-600 font-bold">
                  {formatCurrency(metrics.avgLoss)}
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">승률</span>
                <span className="text-sm font-bold">{formatPercent(metrics.winRate)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">수익률</span>
                <span className="text-sm font-bold">
                  {metrics.profitFactor.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
