'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  Key,
  Eye,
  EyeOff,
  Save,
  Trash2,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Shield,
  Wallet,
} from 'lucide-react';
import { maskApiKey } from '@/lib/crypto';

const apiKeysSchema = z.object({
  api_key: z
    .string()
    .min(64, 'API key must be 64 characters')
    .max(64, 'API key must be 64 characters')
    .regex(/^[A-Za-z0-9]+$/, 'API key must be alphanumeric'),
  api_secret: z
    .string()
    .min(64, 'API secret must be 64 characters')
    .max(64, 'API secret must be 64 characters')
    .regex(/^[A-Za-z0-9]+$/, 'API secret must be alphanumeric'),
});

type ApiKeysFormData = z.infer<typeof apiKeysSchema>;

interface AccountInfo {
  totalWalletBalance: string;
  availableBalance: string;
  totalUnrealizedProfit: string;
  canTrade: boolean;
  canDeposit: boolean;
  canWithdraw: boolean;
}

export default function ApiKeysPage() {
  const [hasKeys, setHasKeys] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [showApiSecret, setShowApiSecret] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [storedApiKey, setStoredApiKey] = useState('');
  const [storedApiSecret, setStoredApiSecret] = useState('');
  const [lastVerified, setLastVerified] = useState<string | null>(null);
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm<ApiKeysFormData>({
    resolver: zodResolver(apiKeysSchema),
  });

  // Load existing API keys on mount
  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      const response = await fetch('/api/keys');
      const data = await response.json();

      if (data.hasKeys) {
        setHasKeys(true);
        setStoredApiKey(data.api_key);
        setStoredApiSecret(data.api_secret);
        setLastVerified(data.last_verified);
      }
    } catch (err) {
      console.error('Failed to load API keys:', err);
    }
  };

  const onSubmit = async (data: ApiKeysFormData) => {
    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      // Save API keys
      const saveResponse = await fetch('/api/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const saveResult = await saveResponse.json();

      if (!saveResponse.ok) {
        throw new Error(saveResult.error || 'Failed to save API keys');
      }

      setSuccess('API keys saved successfully!');
      setHasKeys(true);
      setStoredApiKey(data.api_key);
      setStoredApiSecret(data.api_secret);

      // Reset form to show masked values
      reset();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyKeys = async () => {
    setIsVerifying(true);
    setError('');
    setSuccess('');
    setAccountInfo(null);

    try {
      const response = await fetch('/api/keys/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: storedApiKey,
          api_secret: storedApiSecret,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Verification failed');
      }

      setSuccess('API keys verified successfully! Connected to Binance Futures.');
      setLastVerified(new Date().toISOString());
      setAccountInfo(result.accountInfo);

      // Reload to update verification status
      await loadApiKeys();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDeleteKeys = async () => {
    if (!confirm('Are you sure you want to delete your API keys? This action cannot be undone.')) {
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/keys', {
        method: 'DELETE',
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to delete API keys');
      }

      setSuccess('API keys deleted successfully');
      setHasKeys(false);
      setStoredApiKey('');
      setStoredApiSecret('');
      setLastVerified(null);
      setAccountInfo(null);
      reset();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">API Key Management</h2>
        <p className="text-muted-foreground">
          Connect your Binance Futures account to enable automated trading
        </p>
      </div>

      {/* Security Notice */}
      <Alert>
        <Shield className="h-4 w-4" />
        <AlertDescription>
          <strong>Security Information:</strong> Your API keys are encrypted using AES-256-GCM before storage.
          We recommend creating a new API key specifically for this bot with only Futures trading permissions enabled.
        </AlertDescription>
      </Alert>

      {/* Setup Instructions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Key className="h-5 w-5" />
            <span>How to Get Your Binance API Keys</span>
          </CardTitle>
          <CardDescription>
            Follow these steps to create API keys on Binance
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="list-decimal list-inside space-y-3 text-sm">
            <li>
              Log in to your Binance account and navigate to{' '}
              <a
                href="https://www.binance.com/en/my/settings/api-management"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline inline-flex items-center"
              >
                API Management
                <ExternalLink className="ml-1 h-3 w-3" />
              </a>
            </li>
            <li>Click "Create API" and choose "System generated"</li>
            <li>Label your API key (e.g., "TradingBot AI")</li>
            <li>Complete security verification (2FA/Email)</li>
            <li>
              <strong>Important:</strong> Enable only "Enable Futures" permission
            </li>
            <li>Save your API Key and Secret Key securely</li>
            <li>
              <strong>Recommended:</strong> Add IP whitelist restrictions for additional security
            </li>
          </ol>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              <strong>Never share your API Secret Key.</strong> Our system encrypts it immediately upon submission.
              We cannot recover lost API keys - you'll need to create new ones on Binance.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Account Info (if verified) */}
      {accountInfo && (
        <Card className="border-green-600 bg-green-50 dark:bg-green-950">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-green-900 dark:text-green-100">
              <CheckCircle2 className="h-5 w-5" />
              <span>Connected to Binance Futures</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-green-700 dark:text-green-300">Total Balance</p>
                <p className="text-lg font-bold text-green-900 dark:text-green-100">
                  ${parseFloat(accountInfo.totalWalletBalance).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-green-700 dark:text-green-300">Available Balance</p>
                <p className="text-lg font-bold text-green-900 dark:text-green-100">
                  ${parseFloat(accountInfo.availableBalance).toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={accountInfo.canTrade ? 'default' : 'secondary'}>
                Trading: {accountInfo.canTrade ? 'Enabled' : 'Disabled'}
              </Badge>
              <Badge variant={accountInfo.canDeposit ? 'default' : 'secondary'}>
                Deposits: {accountInfo.canDeposit ? 'Enabled' : 'Disabled'}
              </Badge>
              <Badge variant={accountInfo.canWithdraw ? 'default' : 'secondary'}>
                Withdrawals: {accountInfo.canWithdraw ? 'Enabled' : 'Disabled'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* API Keys Form */}
      <Card>
        <CardHeader>
          <CardTitle>
            {hasKeys ? 'Update API Keys' : 'Add API Keys'}
          </CardTitle>
          <CardDescription>
            {hasKeys
              ? 'Your API keys are currently stored and encrypted'
              : 'Enter your Binance Futures API credentials'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* API Key Input */}
            <div className="space-y-2">
              <Label htmlFor="api_key">API Key</Label>
              <div className="relative">
                <Input
                  id="api_key"
                  type={showApiKey ? 'text' : 'password'}
                  placeholder={hasKeys ? maskApiKey(storedApiKey) : 'Enter your 64-character API key'}
                  {...register('api_key')}
                  disabled={isLoading}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.api_key && (
                <p className="text-sm text-destructive">{errors.api_key.message}</p>
              )}
            </div>

            {/* API Secret Input */}
            <div className="space-y-2">
              <Label htmlFor="api_secret">API Secret</Label>
              <div className="relative">
                <Input
                  id="api_secret"
                  type={showApiSecret ? 'text' : 'password'}
                  placeholder={hasKeys ? maskApiKey(storedApiSecret) : 'Enter your 64-character API secret'}
                  {...register('api_secret')}
                  disabled={isLoading}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowApiSecret(!showApiSecret)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showApiSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.api_secret && (
                <p className="text-sm text-destructive">{errors.api_secret.message}</p>
              )}
            </div>

            {/* Last Verified */}
            {lastVerified && (
              <div className="text-sm text-muted-foreground">
                Last verified: {new Date(lastVerified).toLocaleString()}
              </div>
            )}

            {/* Error/Success Messages */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="border-green-600 bg-green-50 dark:bg-green-950">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-900 dark:text-green-100">
                  {success}
                </AlertDescription>
              </Alert>
            )}

            {/* Action Buttons */}
            <div className="flex items-center space-x-3">
              <Button
                type="submit"
                disabled={isLoading || isVerifying}
                className="flex-1"
              >
                <Save className="mr-2 h-4 w-4" />
                {isLoading ? 'Saving...' : hasKeys ? 'Update Keys' : 'Save Keys'}
              </Button>

              {hasKeys && (
                <>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleVerifyKeys}
                    disabled={isLoading || isVerifying}
                  >
                    <Wallet className="mr-2 h-4 w-4" />
                    {isVerifying ? 'Verifying...' : 'Verify Connection'}
                  </Button>

                  <Button
                    type="button"
                    variant="destructive"
                    onClick={handleDeleteKeys}
                    disabled={isLoading || isVerifying}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </Button>
                </>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Best Practices */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Security Best Practices</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Create a dedicated API key for this bot (don't reuse existing keys)</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Enable only "Futures Trading" permission (disable Spot, Margin, Withdrawals)</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Add IP whitelist restrictions on Binance for enhanced security</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Never share your API Secret Key with anyone</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Regularly verify your API key status and rotate keys periodically</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
