'use client';

import { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickData, Time } from 'lightweight-charts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Maximize2, TrendingUp } from 'lucide-react';

interface TradingChartProps {
  symbol?: string;
  onSymbolChange?: (symbol: string) => void;
  showPositionMarkers?: boolean;
  entryPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  currentPrice?: number;
}

type Timeframe = '1m' | '15m' | '30m' | '1h' | '4h' | '1d';

const TIMEFRAMES: { value: Timeframe; label: string }[] = [
  { value: '1m', label: '1분' },
  { value: '15m', label: '15분' },
  { value: '30m', label: '30분' },
  { value: '1h', label: '1시간' },
  { value: '4h', label: '4시간' },
  { value: '1d', label: '1일' },
];

const SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT'];

// Mock OHLCV data generator
const generateMockOHLCVData = (count: number = 100): CandlestickData[] => {
  const data: CandlestickData[] = [];
  let basePrice = 43000;
  const now = Math.floor(Date.now() / 1000);

  for (let i = count; i > 0; i--) {
    const time = (now - i * 60) as Time; // 1 minute intervals
    const change = (Math.random() - 0.5) * 500;
    const open = basePrice;
    const close = basePrice + change;
    const high = Math.max(open, close) + Math.random() * 200;
    const low = Math.min(open, close) - Math.random() * 200;

    data.push({
      time,
      open,
      high,
      low,
      close,
    });

    basePrice = close;
  }

  return data;
};

// Calculate EMA (Exponential Moving Average)
const calculateEMA = (data: CandlestickData[], period: number): { time: Time; value: number }[] => {
  const ema: { time: Time; value: number }[] = [];
  const multiplier = 2 / (period + 1);

  let emaValue = data.slice(0, period).reduce((sum, d) => sum + d.close, 0) / period;

  for (let i = period; i < data.length; i++) {
    emaValue = (data[i].close - emaValue) * multiplier + emaValue;
    ema.push({ time: data[i].time, value: emaValue });
  }

  return ema;
};

export default function TradingChart({
  symbol = 'BTC/USDT',
  onSymbolChange,
  showPositionMarkers = false,
  entryPrice,
  stopLoss,
  takeProfit,
  currentPrice,
}: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const candlestickSeriesRef = useRef<any>(null);
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>('15m');
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const chart: any = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 500,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#e0e0e0',
      },
      crosshair: {
        mode: 1, // Normal mode
      },
    });

    chartRef.current = chart;

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Generate and set mock data
    const mockData = generateMockOHLCVData(200);
    candlestickSeries.setData(mockData);

    // Add EMA indicators
    const ema12Data = calculateEMA(mockData, 12);
    const ema26Data = calculateEMA(mockData, 26);
    const ema50Data = calculateEMA(mockData, 50);

    const ema12Series = chart.addLineSeries({
      color: '#2962FF',
      lineWidth: 2,
      title: 'EMA 12',
    });
    ema12Series.setData(ema12Data);

    const ema26Series = chart.addLineSeries({
      color: '#FF6D00',
      lineWidth: 2,
      title: 'EMA 26',
    });
    ema26Series.setData(ema26Data);

    const ema50Series = chart.addLineSeries({
      color: '#00E676',
      lineWidth: 2,
      title: 'EMA 50',
    });
    ema50Series.setData(ema50Data);

    // Add position markers if enabled
    if (showPositionMarkers && entryPrice) {
      // Entry price line
      candlestickSeries.createPriceLine({
        price: entryPrice,
        color: '#2196F3',
        lineWidth: 2,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: 'Entry',
      });

      // Stop loss line
      if (stopLoss) {
        candlestickSeries.createPriceLine({
          price: stopLoss,
          color: '#F44336',
          lineWidth: 2,
          lineStyle: 2,
          axisLabelVisible: true,
          title: 'Stop Loss',
        });
      }

      // Take profit line
      if (takeProfit) {
        candlestickSeries.createPriceLine({
          price: takeProfit,
          color: '#4CAF50',
          lineWidth: 2,
          lineStyle: 2,
          axisLabelVisible: true,
          title: 'Take Profit',
        });
      }

      // Current price line (if different from entry)
      if (currentPrice && currentPrice !== entryPrice) {
        candlestickSeries.createPriceLine({
          price: currentPrice,
          color: '#9C27B0',
          lineWidth: 2,
          lineStyle: 0, // Solid
          axisLabelVisible: true,
          title: 'Current',
        });
      }
    }

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [selectedSymbol, selectedTimeframe, showPositionMarkers, entryPrice, stopLoss, takeProfit, currentPrice]);

  const handleSymbolChange = (newSymbol: string) => {
    setSelectedSymbol(newSymbol);
    if (onSymbolChange) {
      onSymbolChange(newSymbol);
    }
  };

  const handleFullscreen = () => {
    if (chartContainerRef.current) {
      if (!document.fullscreenElement) {
        chartContainerRef.current.requestFullscreen();
        setIsFullscreen(true);
      } else {
        document.exitFullscreen();
        setIsFullscreen(false);
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            실시간 차트
          </CardTitle>

          <div className="flex items-center gap-3">
            {/* Symbol Selector */}
            <Select value={selectedSymbol} onValueChange={handleSymbolChange}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SYMBOLS.map((sym) => (
                  <SelectItem key={sym} value={sym}>
                    {sym}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Timeframe Selector */}
            <Select value={selectedTimeframe} onValueChange={(v) => setSelectedTimeframe(v as Timeframe)}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TIMEFRAMES.map((tf) => (
                  <SelectItem key={tf.value} value={tf.value}>
                    {tf.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Fullscreen Button */}
            <Button size="sm" variant="outline" onClick={handleFullscreen}>
              <Maximize2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div
          ref={chartContainerRef}
          className="w-full rounded-lg border border-gray-200"
          style={{ height: isFullscreen ? '100vh' : '500px' }}
        />

        {/* Legend */}
        <div className="flex items-center gap-4 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-blue-600" />
            <span className="text-gray-600">EMA 12</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-orange-600" />
            <span className="text-gray-600">EMA 26</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-green-500" />
            <span className="text-gray-600">EMA 50</span>
          </div>
          {showPositionMarkers && (
            <>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-blue-500 border-dashed border-2" />
                <span className="text-gray-600">Entry</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-red-500 border-dashed border-2" />
                <span className="text-gray-600">Stop Loss</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-0.5 bg-green-500 border-dashed border-2" />
                <span className="text-gray-600">Take Profit</span>
              </div>
            </>
          )}
        </div>

        {/* Chart Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <div className="text-xs text-gray-600">심볼</div>
            <div className="font-semibold text-gray-900">{selectedSymbol}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600">타임프레임</div>
            <div className="font-semibold text-gray-900">
              {TIMEFRAMES.find((tf) => tf.value === selectedTimeframe)?.label}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-600">지표</div>
            <div className="font-semibold text-gray-900">EMA (12, 26, 50)</div>
          </div>
          <div>
            <div className="text-xs text-gray-600">상태</div>
            <div className="font-semibold text-green-600">실시간 연결</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
