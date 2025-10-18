import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import {
  registerExchangeAccount,
  getExchangeAccounts,
  deleteExchangeAccount,
  toggleAccountStatus,
  getAccountBalance,
  getAccountPositions
} from '../accounts';

const mock = new MockAdapter(axios);
const BASE_URL = 'http://localhost:8001/api/v1';
const TEST_TOKEN = 'test-jwt-token';

describe('Accounts API', () => {
  afterEach(() => {
    mock.reset();
  });

  describe('registerExchangeAccount', () => {
    it('should register a new Binance account successfully', async () => {
      const requestData = {
        exchange: 'binance' as const,
        api_key: 'test_api_key',
        api_secret: 'test_secret',
        testnet: true
      };

      const responseData = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        exchange: 'binance',
        testnet: true,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z'
      };

      mock.onPost(`${BASE_URL}/accounts-secure/register`).reply(200, responseData);

      const result = await registerExchangeAccount(requestData, TEST_TOKEN);

      expect(result).toEqual(responseData);
      expect(mock.history.post[0].headers?.Authorization).toBe(`Bearer ${TEST_TOKEN}`);
    });

    it('should register a new OKX account with passphrase', async () => {
      const requestData = {
        exchange: 'okx' as const,
        api_key: 'okx_api_key',
        api_secret: 'okx_secret',
        passphrase: 'okx_pass',
        testnet: true
      };

      const responseData = {
        id: '123e4567-e89b-12d3-a456-426614174001',
        exchange: 'okx',
        testnet: true,
        is_active: true,
        created_at: '2025-01-01T00:00:00Z'
      };

      mock.onPost(`${BASE_URL}/accounts-secure/register`).reply(200, responseData);

      const result = await registerExchangeAccount(requestData, TEST_TOKEN);

      expect(result).toEqual(responseData);
      expect(JSON.parse(mock.history.post[0].data)).toHaveProperty('passphrase', 'okx_pass');
    });

    it('should throw error when API key is invalid', async () => {
      const requestData = {
        exchange: 'binance' as const,
        api_key: 'invalid_key',
        api_secret: 'invalid_secret',
        testnet: true
      };

      mock.onPost(`${BASE_URL}/accounts-secure/register`).reply(400, {
        detail: 'Invalid API credentials'
      });

      await expect(registerExchangeAccount(requestData, TEST_TOKEN)).rejects.toThrow();
    });

    it('should throw error when unauthorized', async () => {
      const requestData = {
        exchange: 'binance' as const,
        api_key: 'test_key',
        api_secret: 'test_secret',
        testnet: true
      };

      mock.onPost(`${BASE_URL}/accounts-secure/register`).reply(401, {
        detail: 'Unauthorized'
      });

      await expect(registerExchangeAccount(requestData, TEST_TOKEN)).rejects.toThrow();
    });
  });

  describe('getExchangeAccounts', () => {
    it('should fetch all exchange accounts', async () => {
      const responseData = {
        accounts: [
          {
            id: '123e4567-e89b-12d3-a456-426614174000',
            exchange: 'binance',
            testnet: true,
            is_active: true,
            created_at: '2025-01-01T00:00:00Z'
          },
          {
            id: '123e4567-e89b-12d3-a456-426614174001',
            exchange: 'okx',
            testnet: false,
            is_active: false,
            created_at: '2025-01-02T00:00:00Z'
          }
        ],
        total: 2
      };

      mock.onGet(`${BASE_URL}/accounts-secure/list`).reply(200, responseData);

      const result = await getExchangeAccounts(TEST_TOKEN);

      expect(result.accounts).toHaveLength(2);
      expect(result.total).toBe(2);
      expect(result.accounts[0].exchange).toBe('binance');
      expect(result.accounts[1].exchange).toBe('okx');
    });

    it('should return empty array when no accounts exist', async () => {
      const responseData = {
        accounts: [],
        total: 0
      };

      mock.onGet(`${BASE_URL}/accounts-secure/list`).reply(200, responseData);

      const result = await getExchangeAccounts(TEST_TOKEN);

      expect(result.accounts).toHaveLength(0);
      expect(result.total).toBe(0);
    });

    it('should throw error when unauthorized', async () => {
      mock.onGet(`${BASE_URL}/accounts-secure/list`).reply(401, {
        detail: 'Unauthorized'
      });

      await expect(getExchangeAccounts(TEST_TOKEN)).rejects.toThrow();
    });
  });

  describe('deleteExchangeAccount', () => {
    const accountId = '123e4567-e89b-12d3-a456-426614174000';

    it('should delete an account successfully', async () => {
      const responseData = {
        success: true,
        message: 'Account deleted successfully'
      };

      mock.onDelete(`${BASE_URL}/accounts-secure/${accountId}`).reply(200, responseData);

      const result = await deleteExchangeAccount(accountId, TEST_TOKEN);

      expect(result.success).toBe(true);
      expect(result.message).toBe('Account deleted successfully');
    });

    it('should throw error when account not found', async () => {
      mock.onDelete(`${BASE_URL}/accounts-secure/${accountId}`).reply(404, {
        detail: 'Account not found'
      });

      await expect(deleteExchangeAccount(accountId, TEST_TOKEN)).rejects.toThrow();
    });

    it('should throw error when deleting another user\'s account', async () => {
      mock.onDelete(`${BASE_URL}/accounts-secure/${accountId}`).reply(403, {
        detail: 'Forbidden'
      });

      await expect(deleteExchangeAccount(accountId, TEST_TOKEN)).rejects.toThrow();
    });
  });

  describe('toggleAccountStatus', () => {
    const accountId = '123e4567-e89b-12d3-a456-426614174000';

    it('should activate an inactive account', async () => {
      const responseData = {
        success: true,
        account_id: accountId,
        is_active: true
      };

      mock.onPost(`${BASE_URL}/accounts-secure/${accountId}/toggle`).reply(200, responseData);

      const result = await toggleAccountStatus(accountId, TEST_TOKEN);

      expect(result.success).toBe(true);
      expect(result.data?.is_active).toBe(true);
    });

    it('should deactivate an active account', async () => {
      const responseData = {
        success: true,
        account_id: accountId,
        is_active: false
      };

      mock.onPost(`${BASE_URL}/accounts-secure/${accountId}/toggle`).reply(200, responseData);

      const result = await toggleAccountStatus(accountId, TEST_TOKEN);

      expect(result.success).toBe(true);
      expect(result.data?.is_active).toBe(false);
    });

    it('should throw error when account not found', async () => {
      mock.onPost(`${BASE_URL}/accounts-secure/${accountId}/toggle`).reply(404, {
        detail: 'Account not found'
      });

      await expect(toggleAccountStatus(accountId, TEST_TOKEN)).rejects.toThrow();
    });
  });

  describe('getAccountBalance', () => {
    const accountId = '123e4567-e89b-12d3-a456-426614174000';

    it('should fetch account balance successfully', async () => {
      const responseData = {
        totalWalletBalance: '10000.00',
        availableBalance: '8000.00',
        totalUnrealizedProfit: '500.00',
        assets: [
          {
            asset: 'USDT',
            walletBalance: '10000.00',
            unrealizedProfit: '500.00'
          }
        ]
      };

      mock.onGet(`${BASE_URL}/accounts-secure/${accountId}/balance`).reply(200, responseData);

      const result = await getAccountBalance(accountId, TEST_TOKEN);

      expect(result.totalWalletBalance).toBe('10000.00');
      expect(result.assets).toHaveLength(1);
      expect(result.assets[0].asset).toBe('USDT');
    });

    it('should throw error when account is inactive', async () => {
      mock.onGet(`${BASE_URL}/accounts-secure/${accountId}/balance`).reply(400, {
        detail: 'Account is not active'
      });

      await expect(getAccountBalance(accountId, TEST_TOKEN)).rejects.toThrow();
    });
  });

  describe('getAccountPositions', () => {
    const accountId = '123e4567-e89b-12d3-a456-426614174000';

    it('should fetch account positions successfully', async () => {
      const responseData = [
        {
          symbol: 'BTCUSDT',
          positionAmt: '0.5',
          entryPrice: '45000.00',
          markPrice: '46000.00',
          unRealizedProfit: '500.00',
          leverage: '10',
          positionSide: 'LONG'
        }
      ];

      mock.onGet(`${BASE_URL}/accounts-secure/${accountId}/positions`).reply(200, responseData);

      const result = await getAccountPositions(accountId, TEST_TOKEN);

      expect(result).toHaveLength(1);
      expect(result[0].symbol).toBe('BTCUSDT');
      expect(result[0].positionSide).toBe('LONG');
    });

    it('should return empty array when no positions exist', async () => {
      mock.onGet(`${BASE_URL}/accounts-secure/${accountId}/positions`).reply(200, []);

      const result = await getAccountPositions(accountId, TEST_TOKEN);

      expect(result).toHaveLength(0);
    });
  });
});
