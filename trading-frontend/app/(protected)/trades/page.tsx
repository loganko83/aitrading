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
  Filter,
  DollarSign,
} from 'lucide-react';
import {
  getAccountList,
  getAccountPositions,
  type Position,
} from '@/lib/api/accounts';

interface TradeStats {
  total_positions: number;
  long_positions: number;
  short_positions: number;
  total_unrealized_pnl: number;
  positive_pnl_count: number;
  negative_pnl_count: number;
  win_rate: number;
}

interface PositionWithAccount extends Position {
  account_exchange: string;
  account_testnet: boolean;
}

export default function TradesPage() {
  const { data: session } = useSession();
  const [positions, setPositions] = useState<PositionWithAccount[]>([]);
  const [filteredPositions, setFilteredPositions] = useState<PositionWithAccount[]>([]);
  const [stats, setStats] = useState<TradeStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');

  // Filters
  const [filterExchange, setFilterExchange] = useState<string>('');
  const [filterSymbol, setFilterSymbol] = useState<string>('');
  const [filterSide, setFilterSide] = useState<string>('');

  useEffect(() => {
    loadTradesData();
  }, [session]);

  useEffect(() => {
    applyFilters();
  }, [positions, filterExchange, filterSymbol, filterSide]);

  const loadTradesData = async () => {
    if (!session?.user?.accessToken) {
      setError('Please log in to view trades');
      setIsLoading(false);
      return;
    }

    try {
      setError('');

      // Get list of accounts
      const accountsData = await getAccountList(session.user.accessToken);

      if (accountsData.accounts.length === 0) {
        setPositions([]);
        setFilteredPositions([]);
        setStats({
          total_positions: 0,
          long_positions: 0,
          short_positions: 0,
          total_unrealized_pnl: 0,
          positive_pnl_count: 0,
          negative_pnl_count: 0,
          win_rate: 0,
        });
        setIsLoading(false);
        return;
      }

      // Fetch positions for each account
      const positionPromises = accountsData.accounts.map(acc =>
        getAccountPositions(acc.id, session.user.accessToken)
          .then(data => ({
            exchange: acc.exchange,
            testnet: acc.testnet,
            positions: data.positions,
          }))
          .catch(err => {
            console.error(`Failed to get positions for ${acc.id}:`, err);
            return null;
          })
      );

      const positionsData = await Promise.all(positionPromises);

      // Aggregate all positions with account info
      const allPositions: PositionWithAccount[] = [];
      positionsData.forEach(data => {
        if (data && data.positions) {
          data.positions.forEach(pos => {
            allPositions.push({
              ...pos,
              account_exchange: data.exchange,
              account_testnet: data.testnet,
            });
          });
        }
      });

      // Calculate statistics
      const longCount = allPositions.filter(p => p.side === 'LONG').length;
      const shortCount = allPositions.filter(p => p.side === 'SHORT').length;
      const totalPnl = allPositions.reduce((sum, p) => sum + parseFloat(p.unrealized_pnl || '0'), 0);
      const positiveCount = allPositions.filter(p => parseFloat(p.unrealized_pnl || '0') > 0).length;
      const negativeCount = allPositions.filter(p => parseFloat(p.unrealized_pnl || '0') < 0).length;

      setPositions(allPositions);
      setStats({
        total_positions: allPositions.length,
        long_positions: longCount,
        short_positions: shortCount,
        total_unrealized_pnl: totalPnl,
        positive_pnl_count: positiveCount,
        negative_pnl_count: negativeCount,
        win_rate: allPositions.length > 0 ? (positiveCount / allPositions.length) * 100 : 0,
      });

    } catch (err: any) {
      console.error('Failed to load trades data:', err);
      setError(err.message || 'Failed to load trades data');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...positions];

    if (filterExchange) {
      filtered = filtered.filter(p => p.account_exchange === filterExchange);
    }

    if (filterSymbol) {
      filtered = filtered.filter(p => p.symbol.toLowerCase().includes(filterSymbol.toLowerCase()));
    }

    if (filterSide) {
      filtered = filtered.filter(p => p.side === filterSide);
    }

    setFilteredPositions(filtered);
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadTradesData();
  };

  const getUniqueSortedSymbols = () => {
    const symbols = new Set(positions.map(p => p.symbol));
    return Array.from(symbols).sort();
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
          <h2 className="text-3xl font-bold tracking-tight">Trades & Positions</h2>
          <p className="text-muted-foreground">
            Monitor your current positions and trading performance
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

      {/* Statistics Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Positions</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_positions}</div>
              <p className="text-xs text-muted-foreground">
                {stats.long_positions} Long / {stats.short_positions} Short
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unrealized PnL</CardTitle>
              {stats.total_unrealized_pnl >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${stats.total_unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {stats.total_unrealized_pnl >= 0 ? '+' : ''}
                ${stats.total_unrealized_pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <p className="text-xs text-muted-foreground">
                From open positions
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.win_rate.toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                Based on current PnL
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Win/Loss</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.positive_pnl_count} / {stats.negative_pnl_count}
              </div>
              <p className="text-xs text-muted-foreground">
                Profitable / Loss positions
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      {positions.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Filters</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="text-sm font-medium mb-2 block">Exchange</label>
                <select
                  value={filterExchange}
                  onChange={(e) => setFilterExchange(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                >
                  <option value="">All Exchanges</option>
                  <option value="binance">Binance</option>
                  <option value="okx">OKX</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Symbol</label>
                <select
                  value={filterSymbol}
                  onChange={(e) => setFilterSymbol(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                >
                  <option value="">All Symbols</option>
                  {getUniqueSortedSymbols().map(symbol => (
                    <option key={symbol} value={symbol}>{symbol}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Side</label>
                <select
                  value={filterSide}
                  onChange={(e) => setFilterSide(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                >
                  <option value="">All Sides</option>
                  <option value="LONG">Long</option>
                  <option value="SHORT">Short</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Positions Table */}
      {filteredPositions.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Current Positions ({filteredPositions.length})</CardTitle>
            <CardDescription>Your active positions across all exchanges</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredPositions.map((position, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex-1 space-y-2">
                    {/* Symbol and Badges */}
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-lg">{position.symbol}</span>
                      <Badge variant={position.side === 'LONG' ? 'default' : 'secondary'}>
                        {position.side}
                      </Badge>
                      <Badge variant="outline">{position.leverage}x</Badge>
                      <Badge variant="secondary">
                        {position.account_exchange.toUpperCase()}
                        {position.account_testnet && ' (Testnet)'}
                      </Badge>
                    </div>

                    {/* Price Info */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Entry:</span>
                        <span className="ml-2 font-medium">
                          ${parseFloat(position.entry_price).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Mark:</span>
                        <span className="ml-2 font-medium">
                          ${parseFloat(position.mark_price).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Size:</span>
                        <span className="ml-2 font-medium">{position.size}</span>
                      </div>
                      {position.liquidation_price && (
                        <div>
                          <span className="text-muted-foreground">Liq:</span>
                          <span className="ml-2 font-medium text-red-600">
                            ${parseFloat(position.liquidation_price).toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* PnL */}
                  <div className="text-right">
                    <div className={`text-xl font-bold ${parseFloat(position.unrealized_pnl) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {parseFloat(position.unrealized_pnl) >= 0 ? '+' : ''}
                      ${parseFloat(position.unrealized_pnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-xs text-muted-foreground">Unrealized PnL</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="space-y-2">
              <Target className="h-12 w-12 mx-auto text-muted-foreground" />
              <p className="text-muted-foreground">
                {positions.length === 0
                  ? 'No open positions. Start trading to see your positions here.'
                  : 'No positions match your filters.'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Alert */}
      {positions.length === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Positions are updated in real-time from your connected exchange accounts.
            Make sure you have registered API keys and have active positions on your exchanges.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
