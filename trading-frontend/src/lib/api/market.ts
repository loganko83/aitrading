/**
 * Market Data API Client
 *
 * Features:
 * - 4개 코인 실시간 가격 조회
 * - 24시간 통계 조회
 * - 멀티 거래소 지원
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface PriceData {
  symbol: string;
  exchange: string;
  price: number;
  timestamp: number;
}

export interface TickerData {
  symbol: string;
  exchange: string;
  price_change: number;
  price_change_percent: number;
  last_price: number;
  high_price: number;
  low_price: number;
  volume: number;
  quote_volume: number;
  open_time: number;
  close_time: number;
  count: number;
}

export interface MultiSymbolPriceResponse {
  prices: PriceData[];
  total: number;
}

export interface MultiSymbolTickerResponse {
  tickers: TickerData[];
  total: number;
}

/**
 * 4개 코인 실시간 가격 조회
 */
export async function getMultiSymbolPrices(
  exchange: 'binance' | 'okx' = 'binance',
  symbols?: string[]
): Promise<MultiSymbolPriceResponse> {
  const params = new URLSearchParams({
    exchange,
  });

  if (symbols && symbols.length > 0) {
    params.append('symbols', symbols.join(','));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/market/prices?${params.toString()}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch prices');
  }

  return response.json();
}

/**
 * 4개 코인 24시간 통계 조회
 */
export async function get24HStats(
  exchange: 'binance' | 'okx' = 'binance',
  symbols?: string[]
): Promise<MultiSymbolTickerResponse> {
  const params = new URLSearchParams({
    exchange,
  });

  if (symbols && symbols.length > 0) {
    params.append('symbols', symbols.join(','));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/market/24h-stats?${params.toString()}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch 24h stats');
  }

  return response.json();
}

/**
 * 단일 심볼 가격 조회
 */
export async function getSinglePrice(
  symbol: string,
  exchange: 'binance' | 'okx' = 'binance'
): Promise<{
  symbol: string;
  exchange: string;
  price: number;
  timestamp: number;
}> {
  const params = new URLSearchParams({
    exchange,
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/market/price/${symbol}?${params.toString()}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch price');
  }

  return response.json();
}

/**
 * 실시간 가격 업데이트 (폴링)
 */
export function usePricePolling(
  exchange: 'binance' | 'okx',
  symbols: string[],
  interval: number = 5000,
  onUpdate: (prices: PriceData[]) => void,
  onError?: (error: Error) => void
): () => void {
  let timeoutId: NodeJS.Timeout;

  const poll = async () => {
    try {
      const response = await getMultiSymbolPrices(exchange, symbols);
      onUpdate(response.prices);
    } catch (error) {
      if (onError) {
        onError(error as Error);
      }
    }

    timeoutId = setTimeout(poll, interval);
  };

  // 즉시 첫 호출
  poll();

  // Cleanup 함수 반환
  return () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  };
}
