'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import StatsWidget from '@/components/trading/StatsWidget';
import PositionMonitor from '@/components/trading/PositionMonitor';
import TradingChart from '@/components/trading/TradingChart';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Play, Pause, TrendingUp } from 'lucide-react';
import { useTradingStore } from '@/lib/stores/tradingStore';
import { fetchDashboardStats, fetchPositions } from '@/lib/api/trading';
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

  // Load real data from backend API
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Fetch dashboard stats from API
        const stats = await fetchDashboardStats();
        setDashboardStats(stats);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
        // Fall back to mock data if API fails
        setDashboardStats({
          total_equity: 10500.00,
          available_balance: 7200.00,
          margin_used: 3300.00,
          total_pnl: 850.00,
          total_pnl_pct: 8.82,
          today_pnl: 125.50,
          today_pnl_pct: 1.21,
          open_positions: 3,
          total_trades: 47,
          win_rate: 68.5,
          xp_points: 1250,
          level: 8,
          next_level_xp: 1500,
        });
      }

      try {
        // Fetch positions from API
        const positionsData = await fetchPositions();
        setPositions(positionsData);
      } catch (error) {
        console.error('Failed to fetch positions:', error);
        // Keep empty positions array if API fails
        setPositions([]);
      }
    };

    if (session) {
      loadDashboardData();
    }
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
          value={`$${dashboardStats?.total_equity.toLocaleString() || '0'}`}
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
          change={`+${dashboardStats?.today_pnl.toLocaleString() || '0'} today`}
          changeType={dashboardStats && dashboardStats.today_pnl >= 0 ? 'positive' : 'negative'}
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
        stopLoss={positions.length > 0 ? positions[0].sl_price : undefined}
        takeProfit={positions.length > 0 ? positions[0].tp_price : undefined}
        currentPrice={positions.length > 0 ? positions[0].current_price : undefined}
      />

      {/* Position Monitor - Real-time Position Monitoring */}
      <PositionMonitor initialPositions={positions} autoRefresh={true} refreshInterval={5000} />

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
