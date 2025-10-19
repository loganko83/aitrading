/**
 * WebSocket Hook for Real-time Market Data
 *
 * 실시간 가격 데이터를 WebSocket으로 스트리밍합니다.
 *
 * Features:
 * - Auto-reconnection with exponential backoff
 * - Subscription management for multiple symbols
 * - Heartbeat/ping-pong for connection health
 * - Clean disconnect on unmount
 *
 * Usage:
 * const { data, connected, subscribe, unsubscribe } = useWebSocket({
 *   url: 'ws://localhost:8001/ws/market',
 *   symbols: ['BTCUSDT', 'ETHUSDT'],
 *   autoConnect: true
 * });
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export interface TickerData {
  type: 'ticker';
  symbol: string;
  price: number;
  priceChange: number;
  priceChangePercent: number;
  volume: number;
  high: number;
  low: number;
  timestamp: number;
}

export interface KlineData {
  type: 'kline';
  symbol: string;
  interval: string;
  openTime: number;
  closeTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  isClosed: boolean;
}

export interface TradeData {
  type: 'trade';
  symbol: string;
  price: number;
  quantity: number;
  time: number;
  isBuyerMaker: boolean;
}

export type MarketData = TickerData | KlineData | TradeData;

interface UseWebSocketOptions {
  url: string;
  symbols?: string[];
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

interface UseWebSocketReturn {
  data: Map<string, MarketData>;
  connected: boolean;
  error: string | null;
  subscribe: (symbol: string, type?: 'ticker' | 'kline' | 'trades', interval?: string) => void;
  unsubscribe: (stream: string) => void;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket({
  url,
  symbols = [],
  autoConnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 10,
  heartbeatInterval = 30000,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [data, setData] = useState<Map<string, MarketData>>(new Map());
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Subscribe to initial symbols
        symbols.forEach((symbol) => {
          ws.send(JSON.stringify({
            action: 'subscribe_ticker',
            symbol: symbol
          }));
        });

        // Start heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
        }
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'ping' }));
          }
        }, heartbeatInterval);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          // Handle different message types
          if (message.type === 'ticker' || message.type === 'kline' || message.type === 'trade') {
            setData((prev) => {
              const newMap = new Map(prev);
              newMap.set(message.symbol, message as MarketData);
              return newMap;
            });
          } else if (message.type === 'pong') {
            // Heartbeat response
            console.debug('Heartbeat received');
          } else if (message.status) {
            // Subscription confirmation
            console.log(`Subscription status: ${message.status}`, message);
          } else if (message.error) {
            console.error('WebSocket error message:', message.error);
            setError(message.error);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);

        // Cleanup heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Auto-reconnect with exponential backoff
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(
            reconnectInterval * Math.pow(2, reconnectAttemptsRef.current),
            30000
          );

          console.log(`Reconnecting in ${delay}ms... (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, delay);
        } else {
          setError('Max reconnection attempts reached');
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, [url, symbols.join(','), reconnectInterval, maxReconnectAttempts, heartbeatInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
  }, []);

  const subscribe = useCallback((symbol: string, type: 'ticker' | 'kline' | 'trades' = 'ticker', interval: string = '1m') => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      let action = '';
      const payload: any = { symbol };

      if (type === 'ticker') {
        action = 'subscribe_ticker';
      } else if (type === 'kline') {
        action = 'subscribe_kline';
        payload.interval = interval;
      } else if (type === 'trades') {
        action = 'subscribe_trades';
      }

      wsRef.current.send(JSON.stringify({ action, ...payload }));
    } else {
      console.warn('WebSocket not connected. Cannot subscribe.');
    }
  }, []);

  const unsubscribe = useCallback((stream: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        stream: stream
      }));
    }
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    data,
    connected,
    error,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  };
}
