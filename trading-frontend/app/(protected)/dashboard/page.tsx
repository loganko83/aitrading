'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import StatsWidget from '@/components/trading/StatsWidget';
import PositionCard from '@/components/trading/PositionCard';
import TradingChart from '@/components/trading/TradingChart';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Play, Pause, TrendingUp } from 'lucide-react';
import { useTradingStore } from '@/lib/stores/tradingStore';
import type { Position } from '@/types';

export default function DashboardPage() {
  const { data: session } = useSession();
  const {
    positions,
    dashboardStats,
    isAutoTrading,
    setPositions,
    setDashboardStats,
    toggleAutoTrading,
  } = useTradingStore();

  const [isRefreshing, setIsRefreshing] = useState(false);

  // Mock data for development
  useEffect(() => {
    // Simulate loading dashboard data
    const mockStats = {
      total_balance: 10500.00,
      available_balance: 7200.00,
      total_pnl: 850.00,
      daily_pnl: 125.50,
      win_rate: 68.5,
      total_trades: 47,
      active_positions: 3,
    };

    const mockPositions: Position[] = [
      {
        id: '1',
        user_id: session?.user?.id || '',
        symbol: 'BTC/USDT',
        side: 'LONG',
        quantity: 0.025,
        entry_price: 42000,
        current_price: 43500,
        stop_loss: 40500,
        take_profit: 45000,
        leverage: 5,
        unrealized_pnl: 37.50,
        status: 'OPEN',
        opened_at: new Date(Date.now() - 3600000 * 4).toISOString(),
        closed_at: null,
        ai_confidence: 0.85,
      },
      {
        id: '2',
        user_id: session?.user?.id || '',
        symbol: 'ETH/USDT',
        side: 'LONG',
        quantity: 0.5,
        entry_price: 2280,
        current_price: 2350,
        stop_loss: 2200,
        take_profit: 2450,
        leverage: 5,
        unrealized_pnl: 35.00,
        status: 'OPEN',
        opened_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        closed_at: null,
        ai_confidence: 0.78,
      },
      {
        id: '3',
        user_id: session?.user?.id || '',
        symbol: 'SOL/USDT',
        side: 'SHORT',
        quantity: 5,
        entry_price: 105,
        current_price: 102,
        stop_loss: 108,
        take_profit: 98,
        leverage: 5,
        unrealized_pnl: 15.00,
        status: 'OPEN',
        opened_at: new Date(Date.now() - 3600000).toISOString(),
        closed_at: null,
        ai_confidence: 0.82,
      },
    ];

    setDashboardStats(mockStats);
    setPositions(mockPositions);
  }, [session, setDashboardStats, setPositions]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // TODO: Implement actual data refresh from backend
    setTimeout(() => {
      setIsRefreshing(false);
    }, 1000);
  };

  const handleToggleAutoTrading = () => {
    toggleAutoTrading();
    // TODO: Implement actual auto-trading toggle API call
  };

  const handleClosePosition = async (positionId: string) => {
    // TODO: Implement position closing logic
    console.log('Closing position:', positionId);
  };

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Trading Dashboard</h2>
          <p className="text-muted-foreground">
            Monitor your positions and track your performance
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
          <Button
            onClick={handleToggleAutoTrading}
            variant={isAutoTrading ? 'destructive' : 'default'}
            className="min-w-[140px]"
          >
            {isAutoTrading ? (
              <>
                <Pause className="mr-2 h-4 w-4" />
                Stop Trading
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Start Trading
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Auto-Trading Status Banner */}
      {isAutoTrading && (
        <Card className="border-green-600 bg-green-50 dark:bg-green-950">
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-3">
              <div className="h-3 w-3 rounded-full bg-green-600 animate-pulse"></div>
              <div>
                <p className="font-semibold text-green-900 dark:text-green-100">
                  Auto-Trading Active
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  AI is monitoring markets and executing trades based on your settings
                </p>
              </div>
            </div>
            <Badge variant="secondary" className="bg-green-600 text-white">
              <TrendingUp className="mr-1 h-3 w-3" />
              Live
            </Badge>
          </CardContent>
        </Card>
      )}

      {/* Stats Widgets */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsWidget
          title="Total Balance"
          value={`$${dashboardStats?.total_balance.toLocaleString() || '0'}`}
          icon="wallet"
        />
        <StatsWidget
          title="Available Balance"
          value={`$${dashboardStats?.available_balance.toLocaleString() || '0'}`}
          icon="wallet"
        />
        <StatsWidget
          title="Total PnL"
          value={`$${dashboardStats?.total_pnl.toLocaleString() || '0'}`}
          change={`+${dashboardStats?.daily_pnl.toLocaleString() || '0'} today`}
          changeType={dashboardStats && dashboardStats.daily_pnl >= 0 ? 'positive' : 'negative'}
          icon="trending-up"
        />
        <StatsWidget
          title="Win Rate"
          value={`${dashboardStats?.win_rate.toFixed(1) || '0'}%`}
          change={`${dashboardStats?.total_trades || 0} trades`}
          changeType="neutral"
          icon="target"
        />
      </div>

      {/* Trading Chart */}
      <TradingChart
        symbol="BTC/USDT"
        showPositionMarkers={positions.length > 0}
        entryPrice={positions.length > 0 ? positions[0].entry_price : undefined}
        stopLoss={positions.length > 0 ? positions[0].stop_loss : undefined}
        takeProfit={positions.length > 0 ? positions[0].take_profit : undefined}
        currentPrice={positions.length > 0 ? positions[0].current_price : undefined}
      />

      {/* Active Positions */}
      <div>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Active Positions</CardTitle>
                <CardDescription>
                  {positions.length} open position{positions.length !== 1 ? 's' : ''}
                </CardDescription>
              </div>
              <Badge variant="outline">
                {positions.length} / 10 max
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {positions.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">No active positions</p>
                <p className="text-sm text-muted-foreground">
                  {isAutoTrading
                    ? 'AI is monitoring markets for trading opportunities'
                    : 'Start auto-trading to let AI open positions for you'}
                </p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {positions.map((position) => (
                  <PositionCard
                    key={position.id}
                    position={position}
                    onClose={handleClosePosition}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest trades and system events</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b">
              <div className="flex items-center space-x-3">
                <div className="h-2 w-2 rounded-full bg-green-600"></div>
                <div>
                  <p className="text-sm font-medium">Position Opened: BTC/USDT LONG</p>
                  <p className="text-xs text-muted-foreground">4 hours ago</p>
                </div>
              </div>
              <Badge variant="secondary">+$37.50</Badge>
            </div>
            <div className="flex items-center justify-between py-3 border-b">
              <div className="flex items-center space-x-3">
                <div className="h-2 w-2 rounded-full bg-green-600"></div>
                <div>
                  <p className="text-sm font-medium">Position Opened: ETH/USDT LONG</p>
                  <p className="text-xs text-muted-foreground">2 hours ago</p>
                </div>
              </div>
              <Badge variant="secondary">+$35.00</Badge>
            </div>
            <div className="flex items-center justify-between py-3">
              <div className="flex items-center space-x-3">
                <div className="h-2 w-2 rounded-full bg-green-600"></div>
                <div>
                  <p className="text-sm font-medium">Position Opened: SOL/USDT SHORT</p>
                  <p className="text-xs text-muted-foreground">1 hour ago</p>
                </div>
              </div>
              <Badge variant="secondary">+$15.00</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
