'use client';

import { useState, useEffect } from 'react';
import { calculateRebalancing, RebalancingOrder, RebalancingResponse } from '@/lib/api/portfolio';

/**
 * Portfolio Rebalancing Component
 *
 * 포트폴리오 리밸런싱:
 * - 목표 비율 설정
 * - 현재 배분 vs 목표 배분
 * - 리밸런싱 주문 계산
 * - 실행 가능한 주문 리스트
 */

interface PortfolioRebalancingProps {
  accountIds?: string[];
  token?: string;
}

export default function PortfolioRebalancing({
  accountIds,
  token,
}: PortfolioRebalancingProps) {
  const symbols = ['BTC', 'ETH', 'SOL', 'ADA'];

  // Target allocation state
  const [targetAllocation, setTargetAllocation] = useState<{ [symbol: string]: number }>({
    BTC: 40,
    ETH: 30,
    SOL: 20,
    ADA: 10,
  });

  // Rebalancing result state
  const [rebalancingData, setRebalancingData] = useState<RebalancingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSliderChange = (symbol: string, value: number) => {
    setTargetAllocation((prev) => ({
      ...prev,
      [symbol]: value,
    }));
  };

  const handleCalculateRebalancing = async () => {
    // Validate total allocation
    const total = Object.values(targetAllocation).reduce((sum, val) => sum + val, 0);
    if (Math.abs(total - 100) > 0.1) {
      setError(`목표 배분의 합은 100%여야 합니다. 현재: ${total.toFixed(1)}%`);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await calculateRebalancing(
        {
          target_allocation: targetAllocation,
          account_ids: accountIds,
          min_order_value: 10,
        },
        token
      );

      setRebalancingData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate rebalancing');
    } finally {
      setLoading(false);
    }
  };

  const totalAllocation = Object.values(targetAllocation).reduce((sum, val) => sum + val, 0);
  const isValidAllocation = Math.abs(totalAllocation - 100) < 0.1;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">
        포트폴리오 리밸런싱
      </h3>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
        <p className="text-sm text-green-800">
          ✅ <strong>리밸런싱 계산기</strong>: 목표 배분 비율에 따른 필요 주문 계산
        </p>
      </div>

      {/* Target Allocation Sliders */}
      <div className="space-y-4 mb-6">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold text-gray-700">목표 배분 비율</h4>
          <span
            className={`text-sm font-semibold ${
              isValidAllocation ? 'text-green-600' : 'text-red-600'
            }`}
          >
            합계: {totalAllocation.toFixed(1)}%
          </span>
        </div>

        {symbols.map((symbol) => (
          <div key={symbol} className="flex items-center space-x-4">
            <label className="w-20 text-gray-700 font-medium">{symbol}:</label>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              value={targetAllocation[symbol]}
              onChange={(e) => handleSliderChange(symbol, parseInt(e.target.value))}
              className="flex-1"
            />
            <input
              type="number"
              min="0"
              max="100"
              step="1"
              value={targetAllocation[symbol]}
              onChange={(e) => handleSliderChange(symbol, parseInt(e.target.value) || 0)}
              className="w-16 px-2 py-1 border border-gray-300 rounded text-right"
            />
            <span className="w-8 text-right text-gray-700">%</span>
          </div>
        ))}
      </div>

      {/* Calculate Button */}
      <div className="mb-6">
        <button
          onClick={handleCalculateRebalancing}
          disabled={loading || !isValidAllocation}
          className={`w-full px-6 py-3 rounded-lg font-bold transition-colors ${
            loading || !isValidAllocation
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {loading ? '계산 중...' : '리밸런싱 계산'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      )}

      {/* Rebalancing Results */}
      {rebalancingData && (
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-700">리밸런싱 결과</h4>

          {/* Portfolio Value */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-blue-700 font-medium">포트폴리오 총 가치</span>
              <span className="text-2xl font-bold text-blue-900">
                ${rebalancingData.portfolio_value.toLocaleString()}
              </span>
            </div>
          </div>

          {/* Current vs Target Allocation */}
          <div className="grid grid-cols-2 gap-4">
            <div className="border border-gray-200 rounded-lg p-4">
              <h5 className="text-sm font-semibold text-gray-700 mb-2">현재 배분</h5>
              <div className="space-y-1">
                {Object.entries(rebalancingData.current_allocation).map(([symbol, pct]) => (
                  <div key={symbol} className="flex justify-between text-sm">
                    <span className="text-gray-600">{symbol}</span>
                    <span className="font-medium">{pct.toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-4">
              <h5 className="text-sm font-semibold text-gray-700 mb-2">목표 배분</h5>
              <div className="space-y-1">
                {Object.entries(rebalancingData.target_allocation).map(([symbol, pct]) => (
                  <div key={symbol} className="flex justify-between text-sm">
                    <span className="text-gray-600">{symbol}</span>
                    <span className="font-medium">{pct.toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Rebalancing Orders */}
          {rebalancingData.orders.length > 0 ? (
            <div>
              <h5 className="font-semibold text-gray-700 mb-2">
                필요한 주문 ({rebalancingData.total_orders}개)
              </h5>
              <div className="space-y-2">
                {rebalancingData.orders.map((order, index) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-4 ${
                      order.action === 'BUY'
                        ? 'border-green-200 bg-green-50'
                        : 'border-red-200 bg-red-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className="font-bold text-gray-900">{order.symbol}</span>
                        <span
                          className={`px-3 py-1 rounded text-sm font-semibold ${
                            order.action === 'BUY'
                              ? 'bg-green-600 text-white'
                              : 'bg-red-600 text-white'
                          }`}
                        >
                          {order.action}
                        </span>
                        <span className="text-sm text-gray-600">
                          {order.percentage_diff > 0 ? '+' : ''}
                          {order.percentage_diff.toFixed(2)}%
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900">
                          ${Math.abs(order.diff_value).toLocaleString()}
                        </div>
                        <div className="text-xs text-gray-500">
                          @ ${order.price.toLocaleString()}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                      <div>
                        <div className="text-gray-500">현재</div>
                        <div className="font-medium">
                          {order.current_percentage.toFixed(2)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-500">목표</div>
                        <div className="font-medium">
                          {order.target_percentage.toFixed(2)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-500">수량</div>
                        <div className="font-medium">{order.quantity.toFixed(4)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  ℹ️ <strong>안내:</strong> 위 주문은 계산 결과이며, 실제 주문 실행은 별도로 진행해야 합니다.
                  리밸런싱 전에 수수료와 슬리피지를 고려하시기 바랍니다.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-green-800">
                ✅ <strong>리밸런싱 불필요:</strong> 현재 배분이 목표 배분과 일치합니다.
              </p>
            </div>
          )}
        </div>
      )}

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          ℹ️ <strong>리밸런싱 팁:</strong> 0.5% 이상 차이나는 심볼만 리밸런싱 대상으로 포함되며,
          최소 주문 금액은 $10입니다. 리밸런싱은 시장 상황을 고려하여 신중하게 진행하세요.
        </p>
      </div>
    </div>
  );
}
