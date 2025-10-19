/**
 * Position Management API Client
 *
 * Features:
 * - 멀티 심볼 포지션 조회
 * - 포트폴리오 요약
 * - 전체 포지션 일괄 청산
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface PositionData {
  symbol: string;
  exchange: string;
  account_id: string;
  position_amt: number;
  entry_price: number;
  unrealized_pnl: number;
  leverage: number;
  side: string;
}

export interface PortfolioSummary {
  total_balance: number;
  total_unrealized_pnl: number;
  total_positions: number;
  positions_by_symbol: Record<string, number>;
  positions_by_exchange: Record<string, number>;
  accounts: Array<{
    account_id: string;
    exchange: string;
    balance: number;
    unrealized_pnl: number;
    positions: number;
    testnet: boolean;
  }>;
}

export interface MultiSymbolPositionsResponse {
  positions: PositionData[];
  total: number;
  summary: {
    total_unrealized_pnl: number;
    positions_by_symbol: Record<string, number>;
    positions_by_exchange: Record<string, number>;
  };
}

export interface CloseAllResponse {
  success: boolean;
  closed_positions: number;
  failed_positions: number;
  results: Array<{
    account_id: string;
    exchange?: string;
    symbol?: string;
    success: boolean;
    message?: string;
    error?: string;
  }>;
}

/**
 * 멀티 심볼 포지션 조회
 */
export async function getMultiSymbolPositions(
  accountIds?: string[],
  symbols?: string[],
  token?: string
): Promise<MultiSymbolPositionsResponse> {
  const params = new URLSearchParams();

  if (accountIds && accountIds.length > 0) {
    params.append('account_ids', accountIds.join(','));
  }

  if (symbols && symbols.length > 0) {
    params.append('symbols', symbols.join(','));
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/positions/multi-symbol?${params.toString()}`,
    {
      method: 'GET',
      headers,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch positions');
  }

  return response.json();
}

/**
 * 포트폴리오 요약 조회
 */
export async function getPortfolioSummary(
  accountIds?: string[],
  token?: string
): Promise<PortfolioSummary> {
  const params = new URLSearchParams();

  if (accountIds && accountIds.length > 0) {
    params.append('account_ids', accountIds.join(','));
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/positions/summary?${params.toString()}`,
    {
      method: 'GET',
      headers,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch summary');
  }

  return response.json();
}

/**
 * 전체 포지션 일괄 청산
 */
export async function closeAllSymbols(
  accountIds?: string[],
  symbols?: string[],
  token?: string
): Promise<CloseAllResponse> {
  const params = new URLSearchParams();

  if (accountIds && accountIds.length > 0) {
    params.append('account_ids', accountIds.join(','));
  }

  if (symbols && symbols.length > 0) {
    params.append('symbols', symbols.join(','));
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/positions/close-all-symbols?${params.toString()}`,
    {
      method: 'POST',
      headers,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to close positions');
  }

  return response.json();
}
