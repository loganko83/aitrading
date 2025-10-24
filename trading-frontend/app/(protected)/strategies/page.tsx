'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  RefreshCw,
  Copy,
  Check,
  TrendingUp,
  BarChart3,
  Sparkles,
  Code,
  AlertCircle,
  ChevronRight,
  Filter,
} from 'lucide-react';
import {
  getStrategyList,
  customizeStrategy,
  type StrategyTemplate,
  type CustomizeStrategyRequest,
} from '@/lib/api/strategies';
import { getAccountList } from '@/lib/api/accounts';

export default function StrategiesPage() {
  const { data: session } = useSession();
  const [strategies, setStrategies] = useState<StrategyTemplate[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyTemplate | null>(null);
  const [customizationOpen, setCustomizationOpen] = useState(false);
  const [pineScriptCode, setPineScriptCode] = useState('');
  const [copiedCode, setCopiedCode] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [filterDifficulty, setFilterDifficulty] = useState<string>('');

  useEffect(() => {
    loadData();
  }, [session, filterCategory, filterDifficulty]);

  const loadData = async () => {
    if (!session?.user?.accessToken) {
      setError('Please log in to view strategies');
      setIsLoading(false);
      return;
    }

    try {
      setError('');

      // Load strategies and accounts in parallel
      const [strategiesData, accountsData] = await Promise.all([
        getStrategyList(
          filterCategory || undefined,
          filterDifficulty || undefined,
          0
        ),
        getAccountList(session.user.accessToken),
      ]);

      setStrategies(strategiesData);
      setAccounts(accountsData.accounts);
    } catch (err: any) {
      console.error('Failed to load data:', err);
      setError(err.message || 'Failed to load strategies');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCustomizeStrategy = async (strategy: StrategyTemplate) => {
    setSelectedStrategy(strategy);

    if (accounts.length === 0) {
      setError('No API keys registered. Please add your exchange API keys first.');
      return;
    }

    setCustomizationOpen(true);
  };

  const generatePineScript = async (accountId: string, webhookSecret: string) => {
    if (!selectedStrategy) return;

    try {
      const request: CustomizeStrategyRequest = {
        strategy_id: selectedStrategy.id,
        account_id: accountId,
        webhook_secret: webhookSecret,
        symbol: 'BTCUSDT',
      };

      const response = await customizeStrategy(request);
      setPineScriptCode(response.pine_script_code);
      setCustomizationOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to customize strategy');
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(pineScriptCode);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner':
        return 'bg-green-500';
      case 'Intermediate':
        return 'bg-yellow-500';
      case 'Advanced':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Trend Following':
        return <TrendingUp className="h-5 w-5" />;
      case 'Mean Reversion':
        return <BarChart3 className="h-5 w-5" />;
      default:
        return <Sparkles className="h-5 w-5" />;
    }
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
          <h2 className="text-3xl font-bold tracking-tight">Trading Strategies</h2>
          <p className="text-muted-foreground">
            Choose from verified strategies or create your own with AI
          </p>
        </div>
        <Button variant="outline" size="icon" onClick={loadData}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="border rounded-md px-3 py-2 text-sm"
          >
            <option value="">All Categories</option>
            <option value="Trend Following">Trend Following</option>
            <option value="Mean Reversion">Mean Reversion</option>
            <option value="Breakout">Breakout</option>
          </select>
        </div>

        <select
          value={filterDifficulty}
          onChange={(e) => setFilterDifficulty(e.target.value)}
          className="border rounded-md px-3 py-2 text-sm"
        >
          <option value="">All Levels</option>
          <option value="Beginner">Beginner</option>
          <option value="Intermediate">Intermediate</option>
          <option value="Advanced">Advanced</option>
        </select>
      </div>

      {/* Strategy Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {strategies.map((strategy) => (
          <Card key={strategy.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  {getCategoryIcon(strategy.category)}
                  <CardTitle className="text-lg">{strategy.name}</CardTitle>
                </div>
                <Badge className={getDifficultyColor(strategy.difficulty)}>
                  {strategy.difficulty}
                </Badge>
              </div>
              <CardDescription className="line-clamp-2">
                {strategy.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Indicators */}
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Indicators:</p>
                  <div className="flex flex-wrap gap-1">
                    {strategy.indicators.map((indicator) => (
                      <Badge key={indicator} variant="outline" className="text-xs">
                        {indicator}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Backtest Results */}
                {strategy.backtest_results && (
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground text-xs">Win Rate</p>
                      <p className="font-semibold text-green-600">
                        {(strategy.backtest_results.win_rate! * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Profit Factor</p>
                      <p className="font-semibold">
                        {strategy.backtest_results.profit_factor?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Sharpe Ratio</p>
                      <p className="font-semibold">
                        {strategy.backtest_results.sharpe_ratio?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Max Drawdown</p>
                      <p className="font-semibold text-red-600">
                        {(strategy.backtest_results.max_drawdown! * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                )}

                {/* Popularity */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-muted-foreground">Popularity:</span>
                    <div className="flex">
                      {[...Array(5)].map((_, i) => (
                        <span
                          key={i}
                          className={`text-xs ${
                            i < strategy.popularity_score / 20 ? 'text-yellow-500' : 'text-gray-300'
                          }`}
                        >
                          ★
                        </span>
                      ))}
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {strategy.category}
                  </Badge>
                </div>

                {/* Actions */}
                <Button
                  className="w-full"
                  onClick={() => handleCustomizeStrategy(strategy)}
                >
                  <Code className="h-4 w-4 mr-2" />
                  Get Pine Script
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* No Strategies */}
      {strategies.length === 0 && !isLoading && (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground">
              No strategies found matching your filters.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Customization Modal - Simple version */}
      {customizationOpen && selectedStrategy && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg mx-4">
            <CardHeader>
              <CardTitle>Customize {selectedStrategy.name}</CardTitle>
              <CardDescription>
                Select an account and generate Pine Script with webhook integration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {accounts.length > 0 ? (
                <>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Select Account:</label>
                    {accounts.map((account) => (
                      <Button
                        key={account.id}
                        variant="outline"
                        className="w-full justify-start"
                        onClick={() => generatePineScript(account.id, 'your_webhook_secret')}
                      >
                        {account.exchange.toUpperCase()} ({account.testnet ? 'Testnet' : 'Mainnet'})
                      </Button>
                    ))}
                  </div>
                  <Button variant="ghost" onClick={() => setCustomizationOpen(false)} className="w-full">
                    Cancel
                  </Button>
                </>
              ) : (
                <div>
                  <p className="text-sm text-muted-foreground mb-4">
                    No API keys registered. Please add your exchange API keys first.
                  </p>
                  <Button onClick={() => (window.location.href = '/api-keys')} className="w-full">
                    Go to API Keys
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Pine Script Code Modal */}
      {pineScriptCode && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Pine Script Code</CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyToClipboard}
                  className="gap-2"
                >
                  {copiedCode ? (
                    <>
                      <Check className="h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy Code
                    </>
                  )}
                </Button>
              </div>
              <CardDescription>
                Copy this code and paste it into TradingView Pine Editor
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                <code>{pineScriptCode}</code>
              </pre>

              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Next Steps:</strong>
                  <ol className="list-decimal list-inside mt-2 space-y-1 text-sm">
                    <li>Open TradingView Pine Editor</li>
                    <li>Paste the code above</li>
                    <li>Click "Add to chart"</li>
                    <li>Create alert with Webhook URL: <code className="bg-muted px-1 py-0.5 rounded">http://YOUR_SERVER:8001/api/v1/webhook/tradingview</code></li>
                    <li>Test in Testnet first!</li>
                  </ol>
                </AlertDescription>
              </Alert>

              <Button onClick={() => setPineScriptCode('')} className="w-full">
                Close
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
