/**
 * API client for TradingBot Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001';

/**
 * Market Analysis API
 */
export interface AnalyzeRequest {
  symbol: string;
  interval?: string;
  limit?: number;
}

export interface AnalyzeResponse {
  success: boolean;
  symbol: string;
  current_price: number;
  decision: {
    should_enter: boolean;
    direction: 'LONG' | 'SHORT';
    probability_up: number;
    confidence: number;
    agreement: number;
    entry_price: number;
    stop_loss: number;
    take_profit: number;
    reasoning: string;
  };
  ai_results: {
    ml: AIResult;
    gpt4: AIResult;
    llama: AIResult;
    ta: AIResult;
  };
}

export interface AIResult {
  direction: string;
  probability: number;
  confidence: number;
  reasoning: string;
}

/**
 * Analyze market using Triple AI Ensemble
 */
export async function analyzeMarket(
  request: AnalyzeRequest
): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/trading/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to analyze market: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get open positions
 */
export async function getPositions() {
  const response = await fetch(`${API_BASE_URL}/api/v1/trading/positions`);

  if (!response.ok) {
    throw new Error(`Failed to fetch positions: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get account balance
 */
export async function getBalance() {
  const response = await fetch(`${API_BASE_URL}/api/v1/trading/balance`);

  if (!response.ok) {
    throw new Error(`Failed to fetch balance: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Execute trade
 */
export interface TradeRequest {
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  leverage?: number;
}

export async function executeTrade(request: TradeRequest) {
  const response = await fetch(`${API_BASE_URL}/api/v1/trading/trade`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to execute trade: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Close position
 */
export async function closePosition(symbol: string, quantity?: number) {
  const url = new URL(`${API_BASE_URL}/api/v1/trading/close-position`);
  url.searchParams.append('symbol', symbol);
  if (quantity) {
    url.searchParams.append('quantity', quantity.toString());
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to close position: ${response.statusText}`);
  }

  return response.json();
}

/**
 * WebSocket Connection Manager
 */
export class MarketWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;

  constructor(
    private onMessage: (data: any) => void,
    private onError?: (error: Event) => void
  ) {}

  connect() {
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/ws/market`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (this.onError) {
          this.onError(error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );

      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  subscribeTicker(symbol: string) {
    this.send({
      action: 'subscribe_ticker',
      symbol,
    });
  }

  subscribeKline(symbol: string, interval: string = '1m') {
    this.send({
      action: 'subscribe_kline',
      symbol,
      interval,
    });
  }

  subscribeTrades(symbol: string) {
    this.send({
      action: 'subscribe_trades',
      symbol,
    });
  }

  unsubscribe(stream: string) {
    this.send({
      action: 'unsubscribe',
      stream,
    });
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
