// API Request/Response Type Definitions

// ===== Auth Types =====
export interface SignupRequest {
  username: string
  email: string
  password: string
}

export interface SignupResponse {
  success: boolean
  message: string
  user_id?: string
}

export interface VerifyOtpRequest {
  user_id: string
  otp_code: string
}

export interface VerifyOtpResponse {
  success: boolean
  message: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    username: string
    email: string
  }
}

// ===== API Keys Types =====
export interface ApiKeyRequest {
  binance_api_key: string
  binance_api_secret: string
}

export interface ApiKeyResponse {
  success: boolean
  message: string
  api_key_id?: string
}

export interface ApiKeyVerifyResponse {
  valid: boolean
  message: string
  account_info?: {
    total_balance: number
    available_balance: number
    positions_count: number
  }
}

// ===== Strategy Types =====
export interface StrategyConfig {
  id: string
  user_id: string
  name: string
  description?: string
  leverage: number
  position_size_pct: number
  coins: string[]
  stop_loss_atr_multiplier: number
  take_profit_atr_multiplier: number
  entry_probability_threshold: number
  entry_confidence_threshold: number
  risk_tolerance: 'low' | 'medium' | 'high'
  auto_trade_enabled: boolean
  created_at: string
  updated_at: string
}

export interface CreateStrategyRequest {
  name: string
  description?: string
  leverage: number
  position_size_pct: number
  coins: string[]
  stop_loss_atr_multiplier: number
  take_profit_atr_multiplier: number
  entry_probability_threshold: number
  entry_confidence_threshold: number
  risk_tolerance: 'low' | 'medium' | 'high'
  auto_trade_enabled: boolean
}

export interface UpdateStrategyRequest extends Partial<CreateStrategyRequest> {}

export interface StrategyResponse {
  success: boolean
  message: string
  config?: StrategyConfig
}

export interface StrategiesListResponse {
  strategies: StrategyConfig[]
  total: number
}

// ===== Backtest Types =====
export interface BacktestResult {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_pnl: number
  total_pnl_percentage: number
  sharpe_ratio: number
  max_drawdown: number
  avg_trade_duration: number
  best_trade: number
  worst_trade: number
  profit_factor: number
  trades: BacktestTrade[]
}

export interface BacktestTrade {
  symbol: string
  entry_time: string
  exit_time: string
  entry_price: number
  exit_price: number
  quantity: number
  side: 'long' | 'short'
  pnl: number
  pnl_percentage: number
  duration_minutes: number
}

// ===== Performance Types =====
export interface PerformanceData {
  equity_curve: EquityPoint[]
  daily_pnl: DailyPnL[]
  trade_distribution: TradeDistribution
  hourly_performance: HourlyPerformance[]
  symbol_performance: SymbolPerformance[]
  summary: PerformanceSummary
}

export interface EquityPoint {
  timestamp: string
  equity: number
  cumulative_pnl: number
}

export interface DailyPnL {
  date: string
  pnl: number
  trades_count: number
  win_rate: number
}

export interface TradeDistribution {
  profit_ranges: {
    range: string
    count: number
    percentage: number
  }[]
  duration_ranges: {
    range: string
    count: number
    percentage: number
  }[]
}

export interface HourlyPerformance {
  hour: number
  avg_pnl: number
  trades_count: number
  win_rate: number
}

export interface SymbolPerformance {
  symbol: string
  total_trades: number
  winning_trades: number
  win_rate: number
  total_pnl: number
  avg_pnl: number
}

export interface PerformanceSummary {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_pnl: number
  avg_pnl: number
  best_trade: number
  worst_trade: number
  sharpe_ratio: number
  max_drawdown: number
}

// ===== Position Types =====
export interface Position {
  id: string
  symbol: string
  side: 'long' | 'short'
  entry_price: number
  current_price: number
  quantity: number
  leverage: number
  unrealized_pnl: number
  unrealized_pnl_percentage: number
  liquidation_price: number
  margin_used: number
  opened_at: string
  stop_loss?: number
  take_profit?: number
}

export interface PositionsResponse {
  positions: Position[]
  total_unrealized_pnl: number
  total_margin_used: number
}

// ===== Webhook Types =====
export interface Webhook {
  id: string
  user_id: string
  name: string
  url: string
  secret?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateWebhookRequest {
  name: string
  secret?: string
}

export interface UpdateWebhookRequest extends Partial<CreateWebhookRequest> {
  is_active?: boolean
}

export interface WebhookResponse {
  success: boolean
  message: string
  webhook?: Webhook
}

export interface WebhooksListResponse {
  webhooks: Webhook[]
  total: number
}

export interface WebhookPayload {
  timestamp: string
  strategy_id?: string
  action: 'open_long' | 'open_short' | 'close_position'
  symbol: string
  price?: number
  quantity?: number
  metadata?: Record<string, unknown>
}

// ===== Settings Types =====
export interface TradingSettings {
  leverage: number
  position_size_pct: number
  coins: string[]
  stop_loss_atr_multiplier: number
  take_profit_atr_multiplier: number
  entry_probability_threshold: number
  entry_confidence_threshold: number
  risk_tolerance: 'low' | 'medium' | 'high'
  auto_trade_enabled: boolean
}

export interface SettingsResponse {
  success: boolean
  message: string
  settings?: TradingSettings
}

// ===== Leaderboard Types =====
export interface LeaderboardEntry {
  rank: number
  user_id: string
  username: string
  total_pnl: number
  total_pnl_percentage: number
  win_rate: number
  total_trades: number
  sharpe_ratio: number
  max_drawdown: number
  level: number
  level_title: string
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[]
  total: number
  current_user_rank?: number
}

// ===== Error Response =====
export interface ErrorResponse {
  error: string
  message?: string
  details?: unknown
  status?: number
}
