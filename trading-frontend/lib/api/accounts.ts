/**
 * Exchange Account API Client
 *
 * All exchange account-related API calls (encrypted API keys)
 */

import { apiPost, apiGet, apiDelete } from './client';

// ==================== Types ====================

export interface RegisterAccountRequest {
  exchange: 'binance' | 'okx';
  api_key: string;
  api_secret: string;
  passphrase?: string; // OKX only
  testnet?: boolean;
}

export interface RegisterAccountResponse {
  id: string;
  exchange: string;
  testnet: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AccountListItem {
  id: string;
  exchange: string;
  testnet: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AccountListResponse {
  accounts: AccountListItem[];
  total: number;
}

export interface ToggleAccountResponse {
  success: boolean;
  account_id: string;
  is_active: boolean;
}

export interface DeleteAccountResponse {
  success: boolean;
  message: string;
}

export interface AccountBalanceResponse {
  account_id: string;
  exchange: string;
  testnet: boolean;
  asset: string;
  available_balance: string;
  total_balance: string;
}

export interface Position {
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: string;
  entry_price: string;
  mark_price: string;
  unrealized_pnl: string;
  leverage: number;
  liquidation_price?: string;
}

export interface AccountPositionsResponse {
  account_id: string;
  exchange: string;
  testnet: boolean;
  positions: Position[];
  total_count: number;
}

// ==================== API Functions ====================

/**
 * Register a new exchange account (API keys encrypted with AES-256)
 */
export async function registerAccount(
  data: RegisterAccountRequest,
  token: string
): Promise<RegisterAccountResponse> {
  return apiPost<RegisterAccountResponse>(
    '/accounts-secure/register',
    data,
    token
  );
}

/**
 * Get list of registered exchange accounts
 */
export async function getAccountList(
  token: string
): Promise<AccountListResponse> {
  return apiGet<AccountListResponse>('/accounts-secure/list', token);
}

/**
 * Delete an exchange account
 */
export async function deleteAccount(
  accountId: string,
  token: string
): Promise<DeleteAccountResponse> {
  return apiDelete<DeleteAccountResponse>(
    `/accounts-secure/${accountId}`,
    token
  );
}

/**
 * Toggle account active status
 */
export async function toggleAccount(
  accountId: string,
  token: string
): Promise<ToggleAccountResponse> {
  return apiPost<ToggleAccountResponse>(
    `/accounts-secure/${accountId}/toggle`,
    undefined,
    token
  );
}

/**
 * Get account balance
 */
export async function getAccountBalance(
  accountId: string,
  token: string
): Promise<AccountBalanceResponse> {
  return apiGet<AccountBalanceResponse>(
    `/accounts-secure/${accountId}/balance`,
    token
  );
}

/**
 * Get account positions
 */
export async function getAccountPositions(
  accountId: string,
  token: string,
  symbol?: string
): Promise<AccountPositionsResponse> {
  const endpoint = symbol
    ? `/accounts-secure/${accountId}/positions?symbol=${symbol}`
    : `/accounts-secure/${accountId}/positions`;
  return apiGet<AccountPositionsResponse>(endpoint, token);
}

export default {
  registerAccount,
  getAccountList,
  deleteAccount,
  toggleAccount,
  getAccountBalance,
  getAccountPositions,
};
