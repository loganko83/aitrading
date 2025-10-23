/**
 * Trading API Client
 * Connects to trading-backend API endpoints
 */

import { getSession } from 'next-auth/react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

interface ApiRequestOptions extends RequestInit {
  requireAuth?: boolean;
}

/**
 * Make authenticated API request
 */
async function apiRequest<T>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const { requireAuth = true, ...fetchOptions } = options;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  };

  // Add authentication token if required
  if (requireAuth) {
    const session = await getSession();
    if (session?.accessToken) {
      headers['Authorization'] = `Bearer ${session.accessToken}`;
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API request failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Dashboard Stats API
 */
export interface DashboardStats {
  total_equity: number;
  available_balance: number;
  margin_used: number;
  total_pnl: number;
  total_pnl_pct: number;
  today_pnl: number;
  today_pnl_pct: number;
  open_positions: number;
  total_trades: number;
  win_rate: number;
  xp_points?: number;
  level?: number;
  next_level_xp?: number;
}

export async function fetchDashboardStats(accountId?: string): Promise<DashboardStats> {
  const endpoint = accountId
    ? `/api/v1/performance/stats?account_id=${accountId}`
    : '/api/v1/performance/stats';

  return apiRequest<DashboardStats>(endpoint);
}

/**
 * Position Data API
 */
export interface Position {
  id: string;
  user_id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  quantity: number;
  entry_price: number;
  current_price: number;
  sl_price?: number;
  tp_price?: number;
  leverage: number;
  current_pnl: number;
  current_pnl_pct: number;
  status: 'OPEN' | 'CLOSED';
  opened_at: string;
  closed_at?: string;
  ai_analysis?: {
    P_up_final: number;
    P_down_final: number;
    confidence: number;
    model_agreement: number;
    breakdown: {
      ml: { prob: number; conf: number; weight: number };
      gpt: { prob: number; conf: number; weight: number };
      llama: { prob: number; conf: number; weight: number };
      ta: { prob: number; conf: number; weight: number };
    };
    reasoning: {
      ml: string;
      gpt: string;
      llama: string;
      ta: string;
    };
  };
}

export async function fetchPositions(accountId?: string): Promise<Position[]> {
  const endpoint = accountId
    ? `/api/v1/positions?account_id=${accountId}`
    : '/api/v1/positions';

  const response = await apiRequest<{ positions: Position[] }>(endpoint);
  return response.positions || [];
}

/**
 * Portfolio Analysis API
 */
export interface PortfolioAnalysis {
  total_value: number;
  total_pnl: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
  positions_summary: {
    open: number;
    closed: number;
    winning: number;
    losing: number;
  };
  performance_chart: {
    date: string;
    value: number;
  }[];
}

export async function fetchPortfolioAnalysis(accountId?: string): Promise<PortfolioAnalysis> {
  const endpoint = accountId
    ? `/api/v1/portfolio/analysis?account_id=${accountId}`
    : '/api/v1/portfolio/analysis';

  return apiRequest<PortfolioAnalysis>(endpoint);
}

/**
 * Trade History API
 */
export interface Trade {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_pct: number;
  opened_at: string;
  closed_at: string;
  duration_minutes: number;
}

export async function fetchTradeHistory(
  accountId?: string,
  limit: number = 50
): Promise<Trade[]> {
  const endpoint = accountId
    ? `/api/v1/trades?account_id=${accountId}&limit=${limit}`
    : `/api/v1/trades?limit=${limit}`;

  const response = await apiRequest<{ trades: Trade[] }>(endpoint);
  return response.trades || [];
}

/**
 * Market Data API
 */
export interface MarketData {
  symbol: string;
  current_price: number;
  price_change_24h: number;
  price_change_pct_24h: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
}

export async function fetchMarketData(symbol: string): Promise<MarketData> {
  return apiRequest<MarketData>(`/api/v1/market/${symbol}`, { requireAuth: false });
}

/**
 * Real-time Trading Signals API
 */
export interface TradingSignal {
  symbol: string;
  action: 'LONG' | 'SHORT' | 'CLOSE' | 'HOLD';
  confidence: number;
  ai_analysis: {
    P_up_final: number;
    P_down_final: number;
    model_agreement: number;
  };
  timestamp: string;
}

export async function fetchTradingSignal(
  symbol: string,
  accountId?: string
): Promise<TradingSignal> {
  const endpoint = accountId
    ? `/api/v1/signal/generate?symbol=${symbol}&account_id=${accountId}`
    : `/api/v1/signal/generate?symbol=${symbol}`;

  return apiRequest<TradingSignal>(endpoint);
}

/**
 * Auto-Trading Control API
 */
export interface AutoTradingStatus {
  enabled: boolean;
  account_id: string;
  strategy_id?: string;
  active_since?: string;
}

export async function toggleAutoTrading(
  enabled: boolean,
  accountId: string
): Promise<AutoTradingStatus> {
  return apiRequest<AutoTradingStatus>('/api/v1/trading/auto-trading/toggle', {
    method: 'POST',
    body: JSON.stringify({ enabled, account_id: accountId }),
  });
}

export async function getAutoTradingStatus(accountId: string): Promise<AutoTradingStatus> {
  return apiRequest<AutoTradingStatus>(`/api/v1/trading/auto-trading/status?account_id=${accountId}`);
}
