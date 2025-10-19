'use client';

import { useState } from 'react';
import PriceGrid from '@/components/dashboard/PriceGrid';
import PositionSummary from '@/components/dashboard/PositionSummary';

export default function DashboardPage() {
  const [exchange, setExchange] = useState<'binance' | 'okx'>('binance');
  const [showPositions, setShowPositions] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900">Trading Dashboard</h1>
            <p className="text-gray-600 mt-2">4개 코인 실시간 모니터링</p>
          </div>

          {/* Exchange Selector */}
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700">거래소:</label>
            <select
              value={exchange}
              onChange={(e) => setExchange(e.target.value as 'binance' | 'okx')}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="binance">Binance</option>
              <option value="okx">OKX</option>
            </select>

            <button
              onClick={() => setShowPositions(!showPositions)}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                showPositions
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {showPositions ? '가격 보기' : '포지션 보기'}
            </button>
          </div>
        </div>

        {/* Main Content */}
        {showPositions ? (
          // Position Summary
          <PositionSummary refreshInterval={10000} />
        ) : (
          // Price Grid
          <PriceGrid
            exchange={exchange}
            symbols={['BTC', 'ETH', 'SOL', 'ADA']}
            refreshInterval={5000}
          />
        )}

        {/* Info Panel */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-blue-900 mb-2">
            📊 대시보드 기능
          </h3>
          <ul className="space-y-1 text-blue-800">
            <li>✓ BTC, ETH, SOL, ADA 실시간 가격 모니터링</li>
            <li>✓ 24시간 가격 변동률 및 거래량</li>
            <li>✓ Binance / OKX 거래소 지원</li>
            <li>✓ 5초마다 자동 업데이트</li>
            <li>✓ 포트폴리오 요약 (로그인 필요)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
