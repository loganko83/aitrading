/**
 * Portfolio Analysis API Client
 *
 * 포트폴리오 고급 분석 기능:
 * - 상관관계 분석
 * - VaR, MDD, Sharpe Ratio
 * - 리밸런싱 계산
 * - 포지션 집중도
 * - 청산 가격
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// ============================================================================
// TypeScript Types
// ============================================================================

export interface CorrelationMatrix {
  [symbol: string]: {
    [symbol: string]: number;
  };
}

export interface CorrelationResponse {
  correlation_matrix: CorrelationMatrix;
  symbols: string[];
  data_points: number;
}

export interface VaRData {
  var_amount: number;
  var_percentage: number;
  confidence_level: number;
  time_horizon_days: number;
  portfolio_value: number;
}

export interface MDDData {
  mdd_percentage: number;
  mdd_amount: number;
  peak_value: number;
  trough_value: number;
}

export interface ConcentrationData {
  total_positions: number;
  largest_position_pct: number;
  top_3_concentration: number;
  herfindahl_index: number;
  diversification_ratio: number;
  total_value: number;
}

export interface RiskMetricsResponse {
  var: VaRData;
  mdd?: MDDData;
  sharpe_ratio?: number;
  concentration: ConcentrationData;
  total_exposure: number;
  portfolio_value: number;
}

export interface RebalancingOrder {
  symbol: string;
  action: 'BUY' | 'SELL';
  percentage_diff: number;
  current_percentage: number;
  target_percentage: number;
  current_value: number;
  target_value: number;
  diff_value: number;
  price: number;
  quantity: number;
}

export interface RebalancingRequest {
  target_allocation: { [symbol: string]: number };
  account_ids?: string[];
  min_order_value?: number;
}

export interface RebalancingResponse {
  orders: RebalancingOrder[];
  current_allocation: { [symbol: string]: number };
  target_allocation: { [symbol: string]: number };
  portfolio_value: number;
  total_orders: number;
}

export interface LiquidationPrice {
  symbol: string;
  side: string;
  entry_price: number;
  current_price: number;
  liquidation_price: number;
  distance_percentage: number;
  leverage: number;
  size: number;
}

export interface LiquidationPricesResponse {
  liquidation_prices: LiquidationPrice[];
  total_positions: number;
  critical_positions: LiquidationPrice[];
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * 상관관계 매트릭스 조회
 */
export async function getCorrelationMatrix(
  exchange: 'binance' | 'okx' = 'binance',
  symbols?: string[],
  days: number = 30
): Promise<CorrelationResponse> {
  const params = new URLSearchParams({ exchange, days: days.toString() });

  if (symbols && symbols.length > 0) {
    params.append('symbols', symbols.join(','));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/portfolio/correlation?${params.toString()}`,
    {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch correlation matrix');
  }

  return response.json();
}

/**
 * 리스크 지표 조회
 */
export async function getRiskMetrics(
  accountIds?: string[],
  confidenceLevel: number = 0.95,
  token?: string
): Promise<RiskMetricsResponse> {
  const params = new URLSearchParams({
    confidence_level: confidenceLevel.toString(),
  });

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
    `${API_BASE_URL}/api/v1/portfolio/risk-metrics?${params.toString()}`,
    { method: 'GET', headers }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch risk metrics');
  }

  return response.json();
}

/**
 * 리밸런싱 주문 계산
 */
export async function calculateRebalancing(
  request: RebalancingRequest,
  token?: string
): Promise<RebalancingResponse> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/portfolio/rebalancing`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to calculate rebalancing');
  }

  return response.json();
}

/**
 * 청산 가격 조회
 */
export async function getLiquidationPrices(
  accountIds?: string[],
  maintenanceMarginRate: number = 0.004,
  token?: string
): Promise<LiquidationPricesResponse> {
  const params = new URLSearchParams({
    maintenance_margin_rate: maintenanceMarginRate.toString(),
  });

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
    `${API_BASE_URL}/api/v1/portfolio/liquidation?${params.toString()}`,
    { method: 'GET', headers }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch liquidation prices');
  }

  return response.json();
}

/**
 * 포지션 집중도 분석
 */
export async function getPositionConcentration(
  accountIds?: string[],
  token?: string
): Promise<ConcentrationData> {
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
    `${API_BASE_URL}/api/v1/portfolio/concentration?${params.toString()}`,
    { method: 'GET', headers }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch position concentration');
  }

  return response.json();
}
