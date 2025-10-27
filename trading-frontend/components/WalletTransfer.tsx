'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, CheckCircle2, Loader2, ArrowRightLeft, DollarSign, Wallet } from 'lucide-react';
import { useSession } from 'next-auth/react';

interface ExchangeAccount {
  id: string;
  exchange: string;
  testnet: boolean;
  is_active: boolean;
  created_at: string;
}

interface AccountBalance {
  asset: string;
  available_balance: number;
  total_balance: number;
  account_structure?: {
    funding?: {
      usdt_available: number;
      usdt_total: number;
    };
    trading?: {
      usdt_available: number;
      usdt_total: number;
    };
    futures?: {
      usdt_available: number;
      usdt_total: number;
    };
  };
  all_assets?: Array<{
    asset: string;
    available_balance: number;
    total_balance: number;
    account_type: string;
  }>;
}

export default function WalletTransfer() {
  const { data: session } = useSession();
  const [accounts, setAccounts] = useState<ExchangeAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [balance, setBalance] = useState<AccountBalance | null>(null);
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true);
  const [isLoadingBalance, setIsLoadingBalance] = useState(false);
  const [isTransferring, setIsTransferring] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Transfer form state
  const [currency, setCurrency] = useState('USDT');
  const [amount, setAmount] = useState('');
  const [fromAccount, setFromAccount] = useState('funding');
  const [toAccount, setToAccount] = useState('trading');

  // CSRF token
  const [csrfToken, setCsrfToken] = useState<string>('');

  useEffect(() => {
    fetchCsrfToken();
    fetchAccounts();
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchBalance(selectedAccount);
    }
  }, [selectedAccount]);

  const fetchCsrfToken = async () => {
    try {
      const res = await fetch('/api/accounts-secure/csrf-token', {
        credentials: 'include',
      });
      const data = await res.json();
      setCsrfToken(data.token);
    } catch (error) {
      console.error('Failed to fetch CSRF token:', error);
    }
  };

  const fetchAccounts = async () => {
    setIsLoadingAccounts(true);
    try {
      const res = await fetch('/api/accounts-secure/list', {
        headers: {
          'Authorization': `Bearer ${session?.accessToken}`,
        },
      });
      const result = await res.json();

      if (result.accounts && result.accounts.length > 0) {
        setAccounts(result.accounts);
        // Auto-select first OKX account (only OKX supports transfers)
        const firstOkxAccount = result.accounts.find((acc: ExchangeAccount) => acc.exchange === 'okx');
        if (firstOkxAccount) {
          setSelectedAccount(firstOkxAccount.id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    } finally {
      setIsLoadingAccounts(false);
    }
  };

  const fetchBalance = async (accountId: string) => {
    setIsLoadingBalance(true);
    setMessage(null);
    try {
      const res = await fetch(`/api/accounts-secure/${accountId}/balance`, {
        headers: {
          'Authorization': `Bearer ${session?.accessToken}`,
        },
      });

      if (!res.ok) {
        throw new Error('Failed to fetch balance');
      }

      const result = await res.json();
      setBalance(result);
    } catch (error) {
      console.error('Failed to fetch balance:', error);
      setMessage({ type: 'error', text: 'Failed to load account balance' });
    } finally {
      setIsLoadingBalance(false);
    }
  };

  const handleTransfer = async () => {
    if (!selectedAccount || !currency || !amount || !fromAccount || !toAccount) {
      setMessage({ type: 'error', text: 'Please fill in all fields' });
      return;
    }

    if (parseFloat(amount) <= 0) {
      setMessage({ type: 'error', text: 'Amount must be greater than 0' });
      return;
    }

    if (fromAccount === toAccount) {
      setMessage({ type: 'error', text: 'From and To accounts must be different' });
      return;
    }

    setIsTransferring(true);
    setMessage(null);

    try {
      const res = await fetch(`/api/accounts-secure/${selectedAccount}/transfer`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.accessToken}`,
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify({
          currency,
          amount: parseFloat(amount),
          from_account: fromAccount,
          to_account: toAccount,
        }),
      });

      const result = await res.json();

      if (res.ok && result.success) {
        setMessage({
          type: 'success',
          text: `Successfully transferred ${amount} ${currency} from ${fromAccount} to ${toAccount}`
        });
        setAmount(''); // Reset amount

        // Refresh balance
        if (selectedAccount) {
          await fetchBalance(selectedAccount);
        }
      } else {
        setMessage({
          type: 'error',
          text: result.detail || 'Transfer failed'
        });
      }
    } catch (error) {
      console.error('Transfer error:', error);
      setMessage({ type: 'error', text: 'Network error occurred' });
    } finally {
      setIsTransferring(false);
    }
  };

  // Get selected account details
  const selectedAccountDetails = accounts.find(acc => acc.id === selectedAccount);
  const isOkxAccount = selectedAccountDetails?.exchange === 'okx';

  if (isLoadingAccounts) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </CardContent>
      </Card>
    );
  }

  if (accounts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Wallet Transfer
          </CardTitle>
          <CardDescription>
            Transfer assets between funding and trading wallets
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            No exchange accounts registered. Please register an account first.
          </div>
        </CardContent>
      </Card>
    );
  }

  const okxAccounts = accounts.filter(acc => acc.exchange === 'okx');
  if (okxAccounts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Wallet Transfer
          </CardTitle>
          <CardDescription>
            Transfer assets between funding and trading wallets
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            Wallet transfer is only supported for OKX accounts.
            <br />
            Binance automatically allocates funds for trading.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="w-5 h-5" />
          Wallet Transfer (OKX Only)
        </CardTitle>
        <CardDescription>
          Transfer assets between Funding (deposit/withdrawal) and Trading (trading) accounts
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {message && (
          <div
            className={`flex items-center gap-3 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            <span>{message.text}</span>
          </div>
        )}

        {/* Account Selection */}
        <div className="space-y-2">
          <Label htmlFor="account">Select OKX Account</Label>
          <Select value={selectedAccount} onValueChange={setSelectedAccount}>
            <SelectTrigger>
              <SelectValue placeholder="Choose an account" />
            </SelectTrigger>
            <SelectContent>
              {okxAccounts.map((account) => (
                <SelectItem key={account.id} value={account.id}>
                  {account.exchange.toUpperCase()} {account.testnet ? '(Testnet)' : '(Mainnet)'}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Balance Display */}
        {isLoadingBalance ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : balance && isOkxAccount && (
          <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <div className="text-sm font-semibold text-gray-600">Funding Account</div>
              <div className="text-2xl font-bold text-blue-600 mt-2">
                {balance.account_structure?.funding?.usdt_available.toFixed(4)} USDT
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Available for withdrawal
              </div>
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-600">Trading Account</div>
              <div className="text-2xl font-bold text-green-600 mt-2">
                {balance.account_structure?.trading?.usdt_available.toFixed(4)} USDT
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Available for trading
              </div>
            </div>
          </div>
        )}

        {/* Transfer Form */}
        {selectedAccount && isOkxAccount && (
          <div className="space-y-4 p-4 border border-gray-200 rounded-lg">
            <div className="text-sm font-semibold text-gray-700">Transfer Details</div>

            {/* Currency */}
            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Select value={currency} onValueChange={setCurrency}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USDT">USDT</SelectItem>
                  <SelectItem value="BTC">BTC</SelectItem>
                  <SelectItem value="ETH">ETH</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Amount */}
            <div className="space-y-2">
              <Label htmlFor="amount">Amount</Label>
              <Input
                id="amount"
                type="number"
                step="0.00000001"
                min="0"
                placeholder="Enter amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </div>

            {/* From Account */}
            <div className="space-y-2">
              <Label htmlFor="from-account">From</Label>
              <Select value={fromAccount} onValueChange={setFromAccount}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="funding">Funding Account</SelectItem>
                  <SelectItem value="trading">Trading Account</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Arrow Icon */}
            <div className="flex justify-center">
              <ArrowRightLeft className="w-6 h-6 text-gray-400" />
            </div>

            {/* To Account */}
            <div className="space-y-2">
              <Label htmlFor="to-account">To</Label>
              <Select value={toAccount} onValueChange={setToAccount}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="funding">Funding Account</SelectItem>
                  <SelectItem value="trading">Trading Account</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Transfer Button */}
            <Button
              onClick={handleTransfer}
              disabled={isTransferring || !amount || parseFloat(amount) <= 0}
              className="w-full"
              size="lg"
            >
              {isTransferring ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Transferring...
                </>
              ) : (
                <>
                  <DollarSign className="w-4 h-4 mr-2" />
                  Transfer {amount || '0'} {currency}
                </>
              )}
            </Button>
          </div>
        )}

        {/* Help Text */}
        <div className="text-xs text-gray-500 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <strong>💡 Tip:</strong> Transfer funds from Funding to Trading account before trading.
          Transfer back to Funding account when you want to withdraw.
        </div>
      </CardContent>
    </Card>
  );
}
