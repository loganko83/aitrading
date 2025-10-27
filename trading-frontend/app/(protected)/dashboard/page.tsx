'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  RefreshCw,
  Play,
  Pause,
  TrendingUp,
  Wallet,
  Target,
  AlertCircle,
  TrendingDown,
  DollarSign,
Activity, ExternalLink } from 'lucide-react';
import {
  getAccountList,
  getAccountBalance,
  getAccountPositions,
  type Position,
  type AccountBalanceResponse,
} from '@/lib/api/accounts';
import { TransferModal } from '@/app/components/modals/TransferModal';

interface DashboardStats {
  total_balance: number;
  available_balance: number;
  total_unrealized_pnl: number;
  active_positions: number;
  active_accounts: number;
}

export default function DashboardPage() {
  const { data: session } = useSession();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [accounts, setAccounts] = useState<string[]>([]);
  const [accountBalances, setAccountBalances] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [selectedTransferAccount, setSelectedTransferAccount] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true);

  const loadDashboardData = async () => {
    if (!session?.user?.accessToken) {
      setError('Please log in to view dashboard');
      setIsLoading(false);
      return;
    }

    try {
      setError('');

      // Get list of accounts
      const accountsData = await getAccountList(session.user.accessToken);

      if (accountsData.accounts.length === 0) {
        setStats({
          total_balance: 0,
          available_balance: 0,
          total_unrealized_pnl: 0,
          active_positions: 0,
          active_accounts: 0,
        });
        setPositions([]);
        setAccounts([]);
        setIsLoading(false);
        return;
      }

      // Fetch balance and positions for each account
      const balancePromises = accountsData.accounts.map(acc =>
        getAccountBalance(acc.id, session.user.accessToken).catch(err => {
          console.error(`Failed to get balance for ${acc.id}:`, err);
          return null;
        })
      );

      const positionPromises = accountsData.accounts.map(acc =>
        getAccountPositions(acc.id, session.user.accessToken).catch(err => {
          console.error(`Failed to get positions for ${acc.id}:`, err);
          return null;
        })
      );

      const [balances, positionsData] = await Promise.all([
        Promise.all(balancePromises),
        Promise.all(positionPromises),
      ]);

      // Calculate total stats
      let totalBalance = 0;
      let availableBalance = 0;
      let totalUnrealizedPnl = 0;
      let allPositions: Position[] = [];

      balances.forEach(balance => {
        if (balance) {
          totalBalance += parseFloat(balance.total_balance || '0');
          availableBalance += parseFloat(balance.available_balance || '0');
        }
      });

      positionsData.forEach(posData => {
        if (posData && posData.positions) {
          posData.positions.forEach(pos => {
            totalUnrealizedPnl += parseFloat(pos.unrealized_pnl || '0');
          });
          allPositions.push(...posData.positions);
        }
      });

      setStats({
        total_balance: totalBalance,
        available_balance: availableBalance,
        total_unrealized_pnl: totalUnrealizedPnl,
        active_positions: allPositions.length,
        active_accounts: accountsData.accounts.length,
      });

      setPositions(allPositions);
      
      // Store detailed account balances
      const accountBalancesWithInfo = accountsData.accounts.map((acc, index) => ({
        ...acc,
        balance: balances[index]
      })).filter(item => item.balance !== null);
      setAccountBalances(accountBalancesWithInfo);
      setAccounts(accountsData.accounts.map(acc => `${acc.exchange.toUpperCase()} (${acc.testnet ? 'Testnet' : 'Mainnet'})`));

    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
      setLastUpdated(new Date());
    }
  };

  useEffect(() => {
    loadDashboardData();

    // Auto-refresh every 30 seconds if enabled
    if (isAutoRefreshEnabled) {
      const interval = setInterval(() => {
        loadDashboardData();
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [session, isAutoRefreshEnabled]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadDashboardData();
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
          <h2 className="text-3xl font-bold tracking-tight">Trading Dashboard</h2>
          <p className="text-muted-foreground">
            Monitor your positions and track your performance
          </p>
          {lastUpdated && (
            <p className="text-xs text-muted-foreground mt-1">
              Last updated: {lastUpdated.toLocaleTimeString()}
              {isAutoRefreshEnabled && (
                <span className="ml-2 text-green-600">● Auto-refreshing every 30s</span>
              )}
            </p>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={isAutoRefreshEnabled ? "default" : "outline"}
            size="sm"
            onClick={() => setIsAutoRefreshEnabled(!isAutoRefreshEnabled)}
          >
            {isAutoRefreshEnabled ? <Pause className="h-3 w-3 mr-1" /> : <Play className="h-3 w-3 mr-1" />}
            {isAutoRefreshEnabled ? 'Auto' : 'Manual'}
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* No Accounts Notice */}
      {!isLoading && stats && stats.active_accounts === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No exchange accounts registered. Please add your API keys in the{' '}
            <a href="/api-keys" className="text-primary hover:underline font-semibold">
              API Keys
            </a>{' '}
            page to start trading.
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Widgets */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
              <Wallet className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${stats.total_balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.active_accounts} active account{stats.active_accounts !== 1 ? 's' : ''}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Available Balance</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${stats.available_balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <p className="text-xs text-muted-foreground">
                Ready for trading
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
              <CardTitle className="text-sm font-medium">Active Positions</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_positions}</div>
              <p className="text-xs text-muted-foreground">
                Open trades
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Active Positions */}
      {positions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Positions</CardTitle>
            <CardDescription>Your current open positions across all accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {positions.map((position, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold">{position.symbol}</span>
                        <Badge variant={position.side === 'LONG' ? 'default' : 'secondary'}>
                          {position.side}
                        </Badge>
                        <Badge variant="outline">{position.leverage}x</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        Entry: ${parseFloat(position.entry_price).toLocaleString()} |
                        Mark: ${parseFloat(position.mark_price).toLocaleString()} |
                        Size: {position.size}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${parseFloat(position.unrealized_pnl) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {parseFloat(position.unrealized_pnl) >= 0 ? '+' : ''}
                      ${parseFloat(position.unrealized_pnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    {position.liquidation_price && (
                      <div className="text-xs text-muted-foreground">
                        Liq: ${parseFloat(position.liquidation_price).toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Account Balances by Type */}
      {accountBalances.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Account Balances</CardTitle>
            <CardDescription>Detailed balance breakdown by exchange and account type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {accountBalances.map((account) => {
                const structure = account.balance?.account_structure || {};
                const exchange = account.exchange.toUpperCase();
                
                return (
                  <div key={account.id} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Wallet className="h-4 w-4 text-primary" />
                        <span className="font-semibold">{exchange}</span>
                        <Badge variant="outline">{account.testnet ? 'Testnet' : 'Mainnet'}</Badge>
                      </div>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      {exchange === 'BINANCE' && (
                        <>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Futures:</span>
                            <span className="font-medium">${structure.futures?.usdt_total?.toFixed(2) || '0.00'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Spot:</span>
                            <span className="font-medium">${structure.spot?.usdt_total?.toFixed(2) || '0.00'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Funding:</span>
                            <span className="font-medium">${structure.funding?.usdt_total?.toFixed(2) || '0.00'}</span>
                          </div>
                        </>
                      )}
                      {exchange === 'OKX' && (
                        <>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Trading:</span>
                            <span className="font-medium">${structure.trading?.usdt_total?.toFixed(2) || '0.00'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Funding:</span>
                            <span className="font-medium">${structure.funding?.usdt_total?.toFixed(2) || '0.00'}</span>
                          </div>
                        </>
                      )}
                      <div className="pt-2 border-t flex justify-between">
                        <span className="font-semibold">Total:</span>
                        <span className="font-bold">${parseFloat(account.balance?.total_balance || '0').toFixed(2)}</span>
                      </div>
                    </div>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => {
                        setSelectedTransferAccount(account);
                        setIsTransferModalOpen(true);
                      }}
                    >
                      <RefreshCw className="h-3 w-3 mr-2" />
                      Transfer Assets
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      
      {accounts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Connected Accounts</CardTitle>
            <CardDescription>Your registered exchange accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {accounts.map((account, index) => (
                <Badge key={index} variant="secondary">
                  {account}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}


      {/* Transfer Modal */}
      {isTransferModalOpen && selectedTransferAccount && (
        <TransferModal
          isOpen={isTransferModalOpen}
          onClose={() => setIsTransferModalOpen(false)}
          accountId={selectedTransferAccount.id}
          exchange={selectedTransferAccount.exchange}
          currentBalances={selectedTransferAccount.balance}
        />
      )}
    </div>
  );
}
