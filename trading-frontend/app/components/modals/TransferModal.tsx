'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';

interface TransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  accountId: string;
  exchange: string;
  currentBalances: any;
}

export function TransferModal({ isOpen, onClose, accountId, exchange, currentBalances }: TransferModalProps) {
  const [fromAccount, setFromAccount] = useState('');
  const [toAccount, setToAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [isTransferring, setIsTransferring] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [availableBalance, setAvailableBalance] = useState(0);

  // Account options based on exchange
  const accountOptions = exchange.toUpperCase() === 'BINANCE'
    ? ['SPOT', 'FUTURES']
    : ['FUNDING', 'TRADING'];

  // Update available balance when from account changes
  useEffect(() => {
    if (!fromAccount || !currentBalances?.account_structure) return;

    const structure = currentBalances.account_structure;
    if (exchange.toUpperCase() === 'BINANCE') {
      const balance = fromAccount === 'SPOT'
        ? structure.spot?.usdt_available
        : structure.futures?.usdt_available;
      setAvailableBalance(balance || 0);
    } else {
      const balance = fromAccount === 'FUNDING'
        ? structure.funding?.usdt_available
        : structure.trading?.usdt_available;
      setAvailableBalance(balance || 0);
    }
  }, [fromAccount, currentBalances, exchange]);

  const handleTransfer = async () => {
    if (!fromAccount || !toAccount || !amount) {
      setMessage({ type: 'error', text: 'Please fill in all fields' });
      return;
    }

    if (parseFloat(amount) <= 0) {
      setMessage({ type: 'error', text: 'Amount must be greater than 0' });
      return;
    }

    if (parseFloat(amount) > availableBalance) {
      setMessage({ type: 'error', text: `Insufficient balance. Available: ${availableBalance.toFixed(2)} USDT` });
      return;
    }

    setIsTransferring(true);
    setMessage(null);

    try {
      const res = await fetch('/api/wallet/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: accountId,
          from_account: fromAccount,
          to_account: toAccount,
          asset: 'USDT',
          amount: parseFloat(amount)
        })
      });

      const result = await res.json();

      if (result.success) {
        setMessage({ type: 'success', text: `Successfully transferred ${amount} USDT from ${fromAccount} to ${toAccount}` });
        setAmount('');
        setTimeout(() => {
          onClose();
          window.location.reload(); // Refresh to show updated balances
        }, 2000);
      } else {
        setMessage({ type: 'error', text: result.message || 'Transfer failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error occurred' });
    } finally {
      setIsTransferring(false);
    }
  };

  const handleMaxClick = () => {
    setAmount(availableBalance.toString());
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Transfer Assets</DialogTitle>
          <DialogDescription>
            Move USDT between {exchange.toUpperCase()} accounts
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {message && (
            <div
              className={`flex items-center gap-2 p-3 rounded-lg ${
                message.type === 'success'
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {message.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <AlertCircle className="w-4 h-4" />
              )}
              <span className="text-sm">{message.text}</span>
            </div>
          )}

          {/* From Account */}
          <div className="space-y-2">
            <Label>From Account</Label>
            <Select value={fromAccount} onValueChange={setFromAccount}>
              <SelectTrigger>
                <SelectValue placeholder="Select source account" />
              </SelectTrigger>
              <SelectContent>
                {accountOptions.map((acc) => (
                  <SelectItem key={acc} value={acc} disabled={acc === toAccount}>
                    {acc}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {fromAccount && (
              <p className="text-sm text-gray-500">
                Available: <span className="font-semibold">{availableBalance.toFixed(2)} USDT</span>
              </p>
            )}
          </div>

          <div className="flex justify-center py-2">
            <ArrowRight className="w-6 h-6 text-gray-400" />
          </div>

          {/* To Account */}
          <div className="space-y-2">
            <Label>To Account</Label>
            <Select value={toAccount} onValueChange={setToAccount}>
              <SelectTrigger>
                <SelectValue placeholder="Select destination account" />
              </SelectTrigger>
              <SelectContent>
                {accountOptions.map((acc) => (
                  <SelectItem key={acc} value={acc} disabled={acc === fromAccount}>
                    {acc}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Amount */}
          <div className="space-y-2">
            <Label>Amount (USDT)</Label>
            <div className="flex gap-2">
              <Input
                type="number"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                min="0"
                step="0.01"
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleMaxClick}
                disabled={!fromAccount}
              >
                Max
              </Button>
            </div>
          </div>

          {/* Transfer Button */}
          <Button
            onClick={handleTransfer}
            disabled={!fromAccount || !toAccount || !amount || isTransferring}
            className="w-full"
            size="lg"
          >
            {isTransferring ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Transferring...
              </>
            ) : (
              'Transfer'
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
