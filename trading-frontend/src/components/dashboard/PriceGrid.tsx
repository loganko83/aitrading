'use client';

import { useEffect, useState } from 'react';
import { useWebSocket, TickerData as WSTickerData } from '@/lib/hooks/useWebSocket';

interface PriceGridProps {
  exchange?: 'binance' | 'okx';
  symbols?: string[];
  useWebSocketStreaming?: boolean; // Toggle between WebSocket and HTTP polling
}

export default function PriceGrid({
  exchange = 'binance',
  symbols = ['BTC', 'ETH', 'SOL', 'ADA'],
  useWebSocketStreaming = true,
}: PriceGridProps) {
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Convert symbols to exchange format (e.g., BTC -> BTCUSDT)
  const formattedSymbols = symbols.map((s) => `${s}USDT`);

  // WebSocket integration for real-time streaming
  const { data: wsData, connected, error } = useWebSocket({
    url: `ws://localhost:8001/ws/market`,
    symbols: formattedSymbols,
    autoConnect: useWebSocketStreaming,
  });

  useEffect(() => {
    if (connected && wsData.size > 0) {
      setLoading(false);
      setLastUpdate(new Date());
    }
  }, [connected, wsData.size]);

  if (loading && wsData.size === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">
          {connected ? 'Waiting for market data...' : 'Connecting to WebSocket...'}
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">WebSocket Error: {error}</p>
        <p className="text-sm text-red-600 mt-2">
          {connected ? 'Connected but received error message' : 'Connection failed'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  // Convert WebSocket data to display format
  const mergedData = symbols.map((symbol) => {
    const fullSymbol = `${symbol}USDT`;
    const tickerData = wsData.get(fullSymbol) as WSTickerData | undefined;

    return {
      symbol,
      price: tickerData?.price || 0,
      priceChange: tickerData?.priceChange || 0,
      priceChangePercent: tickerData?.priceChangePercent || 0,
      highPrice: tickerData?.high || 0,
      lowPrice: tickerData?.low || 0,
      volume: tickerData?.volume || 0,
    };
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h2 className="text-2xl font-bold text-gray-900">
            4개 코인 실시간 가격 ({exchange.toUpperCase()})
          </h2>
          {useWebSocketStreaming && (
            <div className="flex items-center space-x-2">
              <div className={`h-2 w-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className={`text-xs ${connected ? 'text-green-600' : 'text-red-600'}`}>
                {connected ? 'WebSocket Live' : 'Disconnected'}
              </span>
            </div>
          )}
        </div>
        <div className="text-sm text-gray-500">
          마지막 업데이트: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>

      {/* Price Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {mergedData.map((coin) => (
          <div
            key={coin.symbol}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            {/* Symbol */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">{coin.symbol}/USDT</h3>
              <span className="text-xs text-gray-500">{exchange.toUpperCase()}</span>
            </div>

            {/* Current Price */}
            <div className="mb-4">
              <div className="text-3xl font-bold text-gray-900">
                ${coin.price.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 6,
                })}
              </div>
            </div>

            {/* Price Change */}
            <div className="flex items-center mb-4">
              <span
                className={`text-lg font-semibold ${
                  coin.priceChangePercent >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {coin.priceChangePercent >= 0 ? '+' : ''}
                {coin.priceChangePercent.toFixed(2)}%
              </span>
              <span
                className={`ml-2 text-sm ${
                  coin.priceChangePercent >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                ({coin.priceChange >= 0 ? '+' : ''}$
                {coin.priceChange.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 6,
                })})
              </span>
            </div>

            {/* 24h High/Low */}
            <div className="space-y-1 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>24h High:</span>
                <span className="font-semibold">
                  ${coin.highPrice.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 6,
                  })}
                </span>
              </div>
              <div className="flex justify-between">
                <span>24h Low:</span>
                <span className="font-semibold">
                  ${coin.lowPrice.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 6,
                  })}
                </span>
              </div>
              <div className="flex justify-between">
                <span>24h Volume:</span>
                <span className="font-semibold">
                  {coin.volume.toLocaleString(undefined, {
                    maximumFractionDigits: 0,
                  })}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
