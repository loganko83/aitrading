'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  Power,
  PowerOff,
} from 'lucide-react';
import {
  registerAccount,
  getAccountList,
  deleteAccount,
  toggleAccount,
  type AccountListItem,
} from '@/lib/api/accounts';

const apiKeysSchema = z.object({
  exchange: z.enum(['binance', 'okx'], {
    required_error: 'Please select an exchange',
  }),
  api_key: z
    .string()
    .min(16, 'API key is too short')
    .max(256, 'API key is too long'),
  api_secret: z
    .string()
    .min(16, 'API secret is too short')
    .max(256, 'API secret is too long'),
  passphrase: z.string().optional(),
  testnet: z.boolean().default(true),
});

type ApiKeysFormData = z.infer<typeof apiKeysSchema>;

export default function ApiKeysPage() {
  const { data: session } = useSession();
  const [accounts, setAccounts] = useState<AccountListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [showApiSecret, setShowApiSecret] = useState(false);
  const [showPassphrase, setShowPassphrase] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedExchange, setSelectedExchange] = useState<'binance' | 'okx'>('binance');
  const [isTestnet, setIsTestnet] = useState(true);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm<ApiKeysFormData>({
    resolver: zodResolver(apiKeysSchema),
    defaultValues: {
      exchange: 'binance',
      testnet: true,
    },
  });

  const watchExchange = watch('exchange');

  // Load existing accounts on mount
  useEffect(() => {
    if (session?.user?.accessToken) {
      loadAccounts();
    }
  }, [session]);

  const loadAccounts = async () => {
    if (!session?.user?.accessToken) {
      setError('Please log in to manage API keys');
      return;
    }

    try {
      const data = await getAccountList(session.user.accessToken);
      setAccounts(data.accounts);
    } catch (err: any) {
      console.error('Failed to load accounts:', err);
      setError(err.message || 'Failed to load accounts');
    }
  };

  const onSubmit = async (data: ApiKeysFormData) => {
    if (!session?.user?.accessToken) {
      setError('Please log in to add API keys');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      // OKX requires passphrase
      if (data.exchange === 'okx' && !data.passphrase) {
        throw new Error('Passphrase is required for OKX');
      }

      await registerAccount(
        {
          exchange: data.exchange,
          api_key: data.api_key,
          api_secret: data.api_secret,
          passphrase: data.passphrase,
          testnet: data.testnet,
        },
        session.user.accessToken
      );

      setSuccess(`${data.exchange.toUpperCase()} API keys registered successfully!`);

      // Reload accounts list
      await loadAccounts();

      // Reset form
      reset();
      setShowApiKey(false);
      setShowApiSecret(false);
      setShowPassphrase(false);
    } catch (err: any) {
      setError(err.message || 'Failed to register API keys');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleAccount = async (accountId: string) => {
    if (!session?.user?.accessToken) return;

    try {
      await toggleAccount(accountId, session.user.accessToken);
      setSuccess('Account status updated');
      await loadAccounts();
    } catch (err: any) {
      setError(err.message || 'Failed to toggle account');
    }
  };

  const handleDeleteAccount = async (accountId: string, exchange: string) => {
    if (
      !confirm(
        `Are you sure you want to delete this ${exchange.toUpperCase()} account? This action cannot be undone.`
      )
    ) {
      return;
    }

    if (!session?.user?.accessToken) return;

    try {
      await deleteAccount(accountId, session.user.accessToken);
      setSuccess('Account deleted successfully');
      await loadAccounts();
    } catch (err: any) {
      setError(err.message || 'Failed to delete account');
    }
  };

  const maskKey = (key: string) => {
    if (key.length <= 8) return '****';
    return key.substring(0, 4) + '****' + key.substring(key.length - 4);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">API Key Management</h2>
        <p className="text-muted-foreground">
          Connect your exchange accounts to enable automated trading
        </p>
      </div>

      {/* Security Notice */}
      <Alert>
        <Shield className="h-4 w-4" />
        <AlertDescription>
          <strong>Security Information:</strong> Your API keys are encrypted using AES-256 before storage.
          Create dedicated API keys for this bot with only Futures trading permissions enabled.
        </AlertDescription>
      </Alert>

      {/* Registered Accounts */}
      {accounts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Registered Accounts</CardTitle>
            <CardDescription>
              Manage your connected exchange accounts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {accounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <div className="flex flex-col">
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold">
                          {account.exchange.toUpperCase()}
                        </span>
                        <Badge variant={account.testnet ? 'secondary' : 'default'}>
                          {account.testnet ? 'Testnet' : 'Mainnet'}
                        </Badge>
                        <Badge
                          variant={account.is_active ? 'default' : 'outline'}
                          className={account.is_active ? 'bg-green-600' : ''}
                        >
                          {account.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        Registered: {new Date(account.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleToggleAccount(account.id)}
                    >
                      {account.is_active ? (
                        <>
                          <PowerOff className="h-4 w-4 mr-1" />
                          Disable
                        </>
                      ) : (
                        <>
                          <Power className="h-4 w-4 mr-1" />
                          Enable
                        </>
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteAccount(account.id, account.exchange)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Setup Instructions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Key className="h-5 w-5" />
            <span>How to Get Your API Keys</span>
          </CardTitle>
          <CardDescription>
            Follow these steps to create API keys on your exchange
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Binance Instructions */}
          <div>
            <h3 className="font-semibold mb-2">Binance</h3>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>
                Log in to{' '}
                <a
                  href="https://www.binance.com/en/my/settings/api-management"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline inline-flex items-center"
                >
                  Binance API Management
                  <ExternalLink className="ml-1 h-3 w-3" />
                </a>
              </li>
              <li>Create API and choose "System generated"</li>
              <li>Enable only "Enable Futures" permission</li>
              <li>Save your API Key and Secret Key</li>
            </ol>
          </div>

          {/* OKX Instructions */}
          <div>
            <h3 className="font-semibold mb-2">OKX</h3>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>
                Log in to{' '}
                <a
                  href="https://www.okx.com/account/my-api"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline inline-flex items-center"
                >
                  OKX API Management
                  <ExternalLink className="ml-1 h-3 w-3" />
                </a>
              </li>
              <li>Create API Key and set permissions to "Trade" only</li>
              <li>Save API Key, Secret Key, and Passphrase</li>
            </ol>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              <strong>Never share your API Secret Key or Passphrase.</strong> Our system encrypts them
              immediately. We cannot recover lost keys - you'll need to create new ones.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Add New Account Form */}
      <Card>
        <CardHeader>
          <CardTitle>Add New Account</CardTitle>
          <CardDescription>
            Register a new exchange account for automated trading
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Exchange Selection */}
            <div className="space-y-2">
              <Label htmlFor="exchange">Exchange</Label>
              <Select
                value={selectedExchange}
                onValueChange={(value: 'binance' | 'okx') => {
                  setSelectedExchange(value);
                  setValue('exchange', value);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select exchange" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="binance">Binance Futures</SelectItem>
                  <SelectItem value="okx">OKX Futures</SelectItem>
                </SelectContent>
              </Select>
              {errors.exchange && (
                <p className="text-sm text-destructive">{errors.exchange.message}</p>
              )}
            </div>

            {/* Testnet Toggle */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="testnet"
                checked={isTestnet}
                onChange={(e) => {
                  setIsTestnet(e.target.checked);
                  setValue('testnet', e.target.checked);
                }}
                className="rounded"
              />
              <Label htmlFor="testnet">Use Testnet (Recommended for testing)</Label>
            </div>

            {/* API Key Input */}
            <div className="space-y-2">
              <Label htmlFor="api_key">API Key</Label>
              <div className="relative">
                <Input
                  id="api_key"
                  type={showApiKey ? 'text' : 'password'}
                  placeholder="Enter your API key"
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
                  placeholder="Enter your API secret"
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

            {/* Passphrase Input (OKX only) */}
            {watchExchange === 'okx' && (
              <div className="space-y-2">
                <Label htmlFor="passphrase">Passphrase (OKX Required)</Label>
                <div className="relative">
                  <Input
                    id="passphrase"
                    type={showPassphrase ? 'text' : 'password'}
                    placeholder="Enter your passphrase"
                    {...register('passphrase')}
                    disabled={isLoading}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassphrase(!showPassphrase)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showPassphrase ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.passphrase && (
                  <p className="text-sm text-destructive">{errors.passphrase.message}</p>
                )}
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

            {/* Submit Button */}
            <Button type="submit" disabled={isLoading} className="w-full">
              <Save className="mr-2 h-4 w-4" />
              {isLoading ? 'Registering...' : 'Register Account'}
            </Button>
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
              <span>Create dedicated API keys for this bot (don't reuse existing keys)</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Enable only "Futures Trading" permission (disable Spot, Margin, Withdrawals)</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Add IP whitelist restrictions on your exchange for enhanced security</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Test with Testnet first before using real funds</span>
            </li>
            <li className="flex items-start space-x-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Never share your API Secret Key or Passphrase with anyone</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
