'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Target,
  AlertCircle,
  DollarSign,
  BarChart3,
  Activity,
  Percent,
} from 'lucide-react';
import {
  getAccountList,
  getAccountPositions,
  type Position,
} from '@/lib/api/accounts';

interface AnalyticsData {
  total_positions: number;
  winning_positions: number;
  losing_positions: number;
  win_rate: number;
  total_pnl: number;
  average_pnl: number;
  largest_win: number;
  largest_loss: number;
  profit_factor: number;
  long_win_rate: number;
  short_win_rate: number;
  positions_by_symbol: Record<string, number>;
  pnl_by_exchange: Record<string, number>;
}

export default function AnalyticsPage() {
  const { data: session } = useSession();
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAnalyticsData();
  }, [session]);

  const loadAnalyticsData = async () => {
    if (!session?.user?.accessToken) {
      setError('Please log in to view analytics');
      setIsLoading(false);
      return;
    }

    try {
      setError('');

      // Get list of accounts
      const accountsData = await getAccountList(session.user.accessToken);

      if (accountsData.accounts.length === 0) {
        setAnalytics(null);
        setPositions([]);
        setIsLoading(false);
        return;
      }

      // Fetch positions for each account
      const positionPromises = accountsData.accounts.map(acc =>
        getAccountPositions(acc.id, session.user.accessToken)
          .then(data => ({
            exchange: acc.exchange,
            positions: data.positions,
          }))
          .catch(err => {
            console.error(`Failed to get positions for ${acc.id}:`, err);
            return null;
          })
      );

      const positionsData = await Promise.all(positionPromises);

      // Aggregate all positions
      const allPositions: (Position & { exchange: string })[] = [];
      positionsData.forEach(data => {
        if (data && data.positions) {
          data.positions.forEach(pos => {
            allPositions.push({
              ...pos,
              exchange: data.exchange,
            });
          });
        }
      });

      setPositions(allPositions);

      // Calculate analytics
      const winningPositions = allPositions.filter(p => parseFloat(p.unrealized_pnl) > 0);
      const losingPositions = allPositions.filter(p => parseFloat(p.unrealized_pnl) < 0);

      const totalPnl = allPositions.reduce((sum, p) => sum + parseFloat(p.unrealized_pnl), 0);
      const averagePnl = allPositions.length > 0 ? totalPnl / allPositions.length : 0;

      const pnlValues = allPositions.map(p => parseFloat(p.unrealized_pnl));
      const largestWin = pnlValues.length > 0 ? Math.max(...pnlValues) : 0;
      const largestLoss = pnlValues.length > 0 ? Math.min(...pnlValues) : 0;

      const totalWinAmount = winningPositions.reduce((sum, p) => sum + parseFloat(p.unrealized_pnl), 0);
      const totalLossAmount = Math.abs(losingPositions.reduce((sum, p) => sum + parseFloat(p.unrealized_pnl), 0));
      const profitFactor = totalLossAmount > 0 ? totalWinAmount / totalLossAmount : totalWinAmount > 0 ? 999 : 0;

      // Long/Short win rates
      const longPositions = allPositions.filter(p => p.side === 'LONG');
      const shortPositions = allPositions.filter(p => p.side === 'SHORT');
      const longWinning = longPositions.filter(p => parseFloat(p.unrealized_pnl) > 0);
      const shortWinning = shortPositions.filter(p => parseFloat(p.unrealized_pnl) > 0);

      const longWinRate = longPositions.length > 0 ? (longWinning.length / longPositions.length) * 100 : 0;
      const shortWinRate = shortPositions.length > 0 ? (shortWinning.length / shortPositions.length) * 100 : 0;

      // Positions by symbol
      const positionsBySymbol: Record<string, number> = {};
      allPositions.forEach(p => {
        positionsBySymbol[p.symbol] = (positionsBySymbol[p.symbol] || 0) + 1;
      });

      // PnL by exchange
      const pnlByExchange: Record<string, number> = {};
      allPositions.forEach(p => {
        const pos = p as Position & { exchange: string };
        pnlByExchange[pos.exchange] = (pnlByExchange[pos.exchange] || 0) + parseFloat(p.unrealized_pnl);
      });

      setAnalytics({
        total_positions: allPositions.length,
        winning_positions: winningPositions.length,
        losing_positions: losingPositions.length,
        win_rate: allPositions.length > 0 ? (winningPositions.length / allPositions.length) * 100 : 0,
        total_pnl: totalPnl,
        average_pnl: averagePnl,
        largest_win: largestWin,
        largest_loss: largestLoss,
        profit_factor: profitFactor,
        long_win_rate: longWinRate,
        short_win_rate: shortWinRate,
        positions_by_symbol: positionsBySymbol,
        pnl_by_exchange: pnlByExchange,
      });

    } catch (err: any) {
      console.error('Failed to load analytics data:', err);
      setError(err.message || 'Failed to load analytics data');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadAnalyticsData();
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Performance Analytics</h2>
          <p className="text-muted-foreground">
            Comprehensive analysis of your trading performance
          </p>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={handleRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {analytics ? (
        <>
          {/* Key Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
                <Percent className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {analytics.win_rate.toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {analytics.winning_positions} wins / {analytics.losing_positions} losses
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total PnL</CardTitle>
                {analytics.total_pnl >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${analytics.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {analytics.total_pnl >= 0 ? '+' : ''}
                  ${analytics.total_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <p className="text-xs text-muted-foreground">
                  Unrealized from {analytics.total_positions} positions
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Average PnL</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${analytics.average_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {analytics.average_pnl >= 0 ? '+' : ''}
                  ${analytics.average_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <p className="text-xs text-muted-foreground">
                  Per position
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Profit Factor</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {analytics.profit_factor > 100 ? '999+' : analytics.profit_factor.toFixed(2)}
                </div>
                <p className="text-xs text-muted-foreground">
                  {analytics.profit_factor >= 2 ? 'Excellent' : analytics.profit_factor >= 1.5 ? 'Good' : analytics.profit_factor >= 1 ? 'Break-even' : 'Needs improvement'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Win/Loss Analysis */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Best & Worst Trades</CardTitle>
                <CardDescription>Largest winning and losing positions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Largest Win</span>
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="text-2xl font-bold text-green-600">
                    +${analytics.largest_win.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Largest Loss</span>
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  </div>
                  <div className="text-2xl font-bold text-red-600">
                    ${analytics.largest_loss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Long vs Short Performance</CardTitle>
                <CardDescription>Win rates by position type</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Long Positions</span>
                    <Badge variant="default">{analytics.long_win_rate.toFixed(1)}%</Badge>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${Math.min(analytics.long_win_rate, 100)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Short Positions</span>
                    <Badge variant="secondary">{analytics.short_win_rate.toFixed(1)}%</Badge>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-red-600 h-2 rounded-full"
                      style={{ width: `${Math.min(analytics.short_win_rate, 100)}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Symbol Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Positions by Symbol</CardTitle>
              <CardDescription>Distribution of active positions across trading pairs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(analytics.positions_by_symbol)
                  .sort((a, b) => b[1] - a[1])
                  .map(([symbol, count]) => (
                    <div key={symbol} className="flex items-center justify-between">
                      <span className="font-medium">{symbol}</span>
                      <div className="flex items-center space-x-4">
                        <div className="w-48 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${(count / analytics.total_positions) * 100}%` }}
                          />
                        </div>
                        <Badge variant="outline">{count} position{count > 1 ? 's' : ''}</Badge>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Exchange Performance */}
          <Card>
            <CardHeader>
              <CardTitle>Performance by Exchange</CardTitle>
              <CardDescription>PnL breakdown across different exchanges</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(analytics.pnl_by_exchange).map(([exchange, pnl]) => (
                  <div key={exchange} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <BarChart3 className="h-5 w-5 text-muted-foreground" />
                      <span className="font-medium">{exchange.toUpperCase()}</span>
                    </div>
                    <div className={`text-xl font-bold ${pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {pnl >= 0 ? '+' : ''}
                      ${pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Performance Insights */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Insights</CardTitle>
              <CardDescription>Automated analysis of your trading performance</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics.win_rate >= 60 && (
                  <Alert className="border-green-500 bg-green-50 text-green-900">
                    <TrendingUp className="h-4 w-4 text-green-600" />
                    <AlertDescription>
                      <strong>Excellent Win Rate!</strong> Your win rate of {analytics.win_rate.toFixed(1)}% is above 60%, indicating strong trading strategy performance.
                    </AlertDescription>
                  </Alert>
                )}

                {analytics.profit_factor >= 2 && (
                  <Alert className="border-green-500 bg-green-50 text-green-900">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <AlertDescription>
                      <strong>Great Profit Factor!</strong> A profit factor of {analytics.profit_factor.toFixed(2)} shows your winning trades significantly outweigh your losses.
                    </AlertDescription>
                  </Alert>
                )}

                {analytics.win_rate < 40 && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Low Win Rate:</strong> Your win rate of {analytics.win_rate.toFixed(1)}% is below 40%. Consider reviewing your entry criteria and strategy.
                    </AlertDescription>
                  </Alert>
                )}

                {analytics.profit_factor < 1 && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Negative Profit Factor:</strong> Your losses exceed your wins. Review risk management and consider reducing position sizes.
                    </AlertDescription>
                  </Alert>
                )}

                {analytics.long_win_rate > analytics.short_win_rate + 20 && (
                  <Alert>
                    <Target className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Long Bias:</strong> Your long positions ({analytics.long_win_rate.toFixed(1)}%) perform significantly better than shorts ({analytics.short_win_rate.toFixed(1)}%). Consider focusing on long strategies.
                    </AlertDescription>
                  </Alert>
                )}

                {analytics.short_win_rate > analytics.long_win_rate + 20 && (
                  <Alert>
                    <Target className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Short Bias:</strong> Your short positions ({analytics.short_win_rate.toFixed(1)}%) perform significantly better than longs ({analytics.long_win_rate.toFixed(1)}%). Consider focusing on short strategies.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="space-y-2">
              <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground" />
              <p className="text-muted-foreground">
                No trading data available yet. Start trading to see your analytics here.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
