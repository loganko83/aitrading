import crypto from 'crypto';
import { v4 as uuidv4 } from 'uuid';

// Generate unique webhook ID
export const generateWebhookId = (): string => {
  return uuidv4();
};

// Generate secure secret key for webhook
export const generateWebhookSecret = (): string => {
  return crypto.randomBytes(32).toString('hex');
};

// Create HMAC-SHA256 signature for webhook payload
export const createWebhookSignature = (payload: string, secret: string): string => {
  return crypto.createHmac('sha256', secret).update(payload).digest('hex');
};

// Verify webhook signature
export const verifyWebhookSignature = (
  payload: string,
  signature: string,
  secret: string
): boolean => {
  const expectedSignature = createWebhookSignature(payload, secret);
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
};

// Generate webhook URL
export const generateWebhookUrl = (
  userId: string,
  webhookId: string,
  baseUrl: string = process.env.NEXT_PUBLIC_APP_URL || 'https://trendy.storydot.kr/trading'
): string => {
  return `${baseUrl}/api/webhooks/receive/${userId}/${webhookId}`;
};

// Parse TradingView webhook payload
export interface TradingViewSignal {
  action: 'BUY' | 'SELL' | 'CLOSE';
  symbol: string;
  price?: number;
  timestamp: number;
  signature?: string;
}

export const parseTradingViewSignal = (payload: string): TradingViewSignal | null => {
  try {
    const data = JSON.parse(payload);

    // Validate required fields
    if (!data.action || !data.symbol) {
      return null;
    }

    // Validate action
    if (!['BUY', 'SELL', 'CLOSE'].includes(data.action)) {
      return null;
    }

    return {
      action: data.action as 'BUY' | 'SELL' | 'CLOSE',
      symbol: data.symbol,
      price: data.price ? parseFloat(data.price) : undefined,
      timestamp: data.timestamp || Date.now(),
      signature: data.signature,
    };
  } catch (error) {
    console.error('Failed to parse TradingView signal:', error);
    return null;
  }
};

// TradingView Alert Template
export const TRADINGVIEW_ALERT_TEMPLATE = `{
  "action": "{{strategy.order.action}}",
  "symbol": "{{ticker}}",
  "price": {{close}},
  "timestamp": {{time}},
  "signature": "{{strategy.order.id}}"
}`;

// Custom Alert Template for manual signals
export const CUSTOM_ALERT_TEMPLATE = `{
  "action": "BUY",
  "symbol": "BTC/USDT",
  "price": 43500,
  "timestamp": ${Date.now()}
}`;

// Webhook event types
export type WebhookEventType =
  | 'signal_received'
  | 'position_opened'
  | 'position_closed'
  | 'error';

export interface WebhookEvent {
  id: string;
  webhook_id: string;
  user_id: string;
  type: WebhookEventType;
  signal?: TradingViewSignal;
  position_id?: string;
  error?: string;
  created_at: string;
}

// Rate limiting for webhooks (prevent spam)
const webhookRateLimit = new Map<string, { count: number; resetAt: number }>();

export const checkWebhookRateLimit = (
  webhookId: string,
  maxRequests: number = 60,
  windowMs: number = 60000 // 1 minute
): { allowed: boolean; remaining: number; resetAt: number } => {
  const now = Date.now();
  const limit = webhookRateLimit.get(webhookId);

  if (!limit || now > limit.resetAt) {
    // Reset or create new limit
    webhookRateLimit.set(webhookId, {
      count: 1,
      resetAt: now + windowMs,
    });
    return {
      allowed: true,
      remaining: maxRequests - 1,
      resetAt: now + windowMs,
    };
  }

  if (limit.count >= maxRequests) {
    return {
      allowed: false,
      remaining: 0,
      resetAt: limit.resetAt,
    };
  }

  limit.count += 1;
  return {
    allowed: true,
    remaining: maxRequests - limit.count,
    resetAt: limit.resetAt,
  };
};

// Cleanup old rate limit entries
export const cleanupRateLimits = () => {
  const now = Date.now();
  for (const [key, value] of webhookRateLimit.entries()) {
    if (now > value.resetAt) {
      webhookRateLimit.delete(key);
    }
  }
};

// Format webhook for display
export const formatWebhookUrl = (url: string, maxLength: number = 50): string => {
  if (url.length <= maxLength) return url;
  return `${url.substring(0, maxLength - 3)}...`;
};

// Validate symbol format
export const isValidSymbol = (symbol: string): boolean => {
  // Accept formats: BTC/USDT, BTCUSDT, BTC-USDT
  const symbolPattern = /^[A-Z]{2,10}[\/\-]?USDT$/;
  return symbolPattern.test(symbol);
};

// Normalize symbol to standard format (BTC/USDT)
export const normalizeSymbol = (symbol: string): string => {
  // Remove separators and add /
  const cleaned = symbol.replace(/[\-]/g, '');
  if (cleaned.includes('/')) return cleaned;

  // Add / before USDT
  return cleaned.replace('USDT', '/USDT');
};
