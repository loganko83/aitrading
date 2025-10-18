/**
 * Exchange Account Management API Client
 * Handles secure API key registration and management
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface RegisterAccountRequest {
  exchange: 'binance' | 'okx';
  api_key: string;
  api_secret: string;
  passphrase?: string; // Required for OKX
  testnet: boolean;
}

export interface ExchangeAccount {
  id: string;
  exchange: string;
  testnet: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AccountListResponse {
  accounts: ExchangeAccount[];
  total: number;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}

/**
 * Get authorization headers with NextAuth token
 */
const getAuthHeaders = (token: string) => ({
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
});

/**
 * Register a new exchange API key
 */
export async function registerExchangeAccount(
  data: RegisterAccountRequest,
  token: string
): Promise<ExchangeAccount> {
  const response = await axios.post<ExchangeAccount>(
    `${API_BASE_URL}/api/v1/accounts-secure/register`,
    data,
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Get list of registered exchange accounts
 */
export async function getExchangeAccounts(
  token: string
): Promise<AccountListResponse> {
  const response = await axios.get<AccountListResponse>(
    `${API_BASE_URL}/api/v1/accounts-secure/list`,
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Delete an exchange account
 */
export async function deleteExchangeAccount(
  accountId: string,
  token: string
): Promise<ApiResponse<null>> {
  const response = await axios.delete<ApiResponse<null>>(
    `${API_BASE_URL}/api/v1/accounts-secure/${accountId}`,
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Toggle account active status
 */
export async function toggleAccountStatus(
  accountId: string,
  token: string
): Promise<ApiResponse<{ account_id: string; is_active: boolean }>> {
  const response = await axios.post<ApiResponse<{ account_id: string; is_active: boolean }>>(
    `${API_BASE_URL}/api/v1/accounts-secure/${accountId}/toggle`,
    {},
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Get account balance (requires decryption on backend)
 */
export async function getAccountBalance(
  accountId: string,
  token: string
): Promise<any> {
  const response = await axios.get(
    `${API_BASE_URL}/api/v1/accounts-secure/${accountId}/balance`,
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}

/**
 * Get account positions
 */
export async function getAccountPositions(
  accountId: string,
  token: string
): Promise<any> {
  const response = await axios.get(
    `${API_BASE_URL}/api/v1/accounts-secure/${accountId}/positions`,
    { headers: getAuthHeaders(token) }
  );
  return response.data;
}
