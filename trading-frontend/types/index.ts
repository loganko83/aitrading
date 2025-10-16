// User and Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  xp_points: number;
  level: number;
  google_otp_enabled: boolean;
  created_at: string;
  last_login: string;
}

export interface SignupData {
  email: string;
  password: string;
  name: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface OTPVerification {
  userId: string;
  otp_code: string;
}

// Trading Types
export interface BinanceAPIKey {
  id: string;
  user_id: string;
  api_key: string;  // Encrypted
  api_secret_masked: string;  // Last 4 characters only
  is_active: boolean;
  created_at: string;
}

export interface TradingSettings {
  id: string;
  user_id: string;
  leverage: number;  // 1-5
  position_size_pct: number;  // 0.01-0.20 (1%-20%)
  coins: string[];  // ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
  stop_loss_atr_multiplier: number;  // 1.0-2.0
  take_profit_atr_multiplier: number;  // 2.0-4.0
  entry_probability_threshold: number;  // 0.70-0.90
  entry_confidence_threshold: number;  // 0.60-0.90
  risk_tolerance: 'low' | 'medium' | 'high';
  auto_trade_enabled: boolean;
}

export interface Position {
  id: string;
  user_id: string;
  symbol: string;  // 'BTC/USDT'
  side: 'LONG' | 'SHORT';
  entry_price: number;
  quantity: number;
  leverage: number;
  tp_price: number;
  sl_price: number;
  current_price?: number;
  current_pnl: number;
  current_pnl_pct: number;
  status: 'OPEN' | 'CLOSED' | 'LIQUIDATED';
  ai_analysis: AIAnalysis;
  opened_at: string;
  closed_at?: string;
  close_reason?: string;
}

export interface AIAnalysis {
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
}

export interface TradeHistory {
  id: string;
  user_id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_pct: number;
  win: boolean;
  opened_at: string;
  closed_at: string;
  duration_minutes: number;
}

// Webhook Types
export interface Webhook {
  id: string;
  user_id: string;
  webhook_url: string;
  secret_token: string;
  is_active: boolean;
  last_triggered?: string;
  total_triggers: number;
  created_at: string;
}

export interface WebhookSignal {
  symbol: string;
  action: 'BUY' | 'SELL' | 'CLOSE';
  price?: number;
  timestamp: string;
  signature: string;
}

// Leaderboard Types
export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  avatar?: string;
  total_pnl: number;
  total_pnl_pct: number;
  win_rate: number;
  total_trades: number;
  xp_points: number;
  level: number;
  badges: Badge[];
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  earned_at: string;
}

// Dashboard Types
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
  xp_points: number;
  level: number;
  next_level_xp: number;
}

// Chart Types
export interface OHLCVData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// API Response Types
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Notification Types
export interface Notification {
  id: string;
  user_id: string;
  type: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

// Risk Tolerance Presets
export const RISK_PRESETS = {
  low: {
    leverage: 3,
    position_size_pct: 0.05,
    entry_probability_threshold: 0.85,
    entry_confidence_threshold: 0.80,
  },
  medium: {
    leverage: 5,
    position_size_pct: 0.10,
    entry_probability_threshold: 0.80,
    entry_confidence_threshold: 0.70,
  },
  high: {
    leverage: 5,
    position_size_pct: 0.15,
    entry_probability_threshold: 0.75,
    entry_confidence_threshold: 0.65,
  },
} as const;

// Available Coins
export const AVAILABLE_COINS = [
  'BTC/USDT',
  'ETH/USDT',
  'BNB/USDT',
  'SOL/USDT',
] as const;

export type CoinSymbol = typeof AVAILABLE_COINS[number];
