'use client';

import { useState, useEffect } from 'react';
import { getRiskMetrics, getLiquidationPrices, RiskMetricsResponse, LiquidationPrice } from '@/lib/api/portfolio';

/**
 * Risk Management Dashboard Component
 *
 * 실시간 리스크 지표 모니터링:
 * - VaR (Value at Risk)
 * - 포지션 집중도
 * - 청산 가격
 * - 총 노출 금액
 */

interface RiskManagementProps {
  accountIds?: string[];
  token?: string;
  refreshInterval?: number;
}

export default function RiskManagement({
  accountIds,
  token,
  refreshInterval = 30000, // 30초
}: RiskManagementProps) {
  const [riskMetrics, setRiskMetrics] = useState<RiskMetricsResponse | null>(null);
  const [liquidationPrices, setLiquidationPrices] = useState<LiquidationPrice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    const fetchRiskData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [metricsData, liquidationData] = await Promise.all([
          getRiskMetrics(accountIds, 0.95, token),
          getLiquidationPrices(accountIds, 0.004, token),
        ]);

        setRiskMetrics(metricsData);
        setLiquidationPrices(liquidationData.liquidation_prices);
        setLastUpdate(new Date());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch risk data');
      } finally {
        setLoading(false);
      }
    };

    fetchRiskData();
    const intervalId = setInterval(fetchRiskData, refreshInterval);

    return () => clearInterval(intervalId);
  }, [accountIds?.join(','), token, refreshInterval]);

  if (loading && !riskMetrics) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          리스크 관리 대시보드
        </h3>
        <p className="text-gray-600">데이터 로딩 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          리스크 관리 대시보드
        </h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!riskMetrics) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          리스크 관리 대시보드
        </h3>
        <p className="text-gray-600">포지션 데이터 없음</p>
      </div>
    );
  }

  const { var: varData, concentration, total_exposure, portfolio_value } = riskMetrics;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">
          리스크 관리 대시보드
        </h3>
        {lastUpdate && (
          <span className="text-xs text-gray-500">
            마지막 업데이트: {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
        <p className="text-sm text-green-800">
          ✅ <strong>실시간 모니터링</strong>: 리스크 지표 및 자동 알림
        </p>
      </div>

      {/* Risk Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600 mb-1">총 노출 금액</div>
          <div className="text-2xl font-bold text-gray-900">
            ${total_exposure.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            레버리지 포함
          </div>
        </div>

        <div className="border border-red-200 rounded-lg p-4 bg-red-50">
          <div className="text-sm text-red-600 mb-1">Value at Risk (95%)</div>
          <div className="text-2xl font-bold text-red-600">
            ${varData.var_amount.toLocaleString()}
          </div>
          <div className="text-xs text-red-500 mt-1">
            최대 예상 손실 ({varData.var_percentage.toFixed(2)}%)
          </div>
        </div>

        <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
          <div className="text-sm text-blue-600 mb-1">포트폴리오 가치</div>
          <div className="text-2xl font-bold text-blue-600">
            ${portfolio_value.toLocaleString()}
          </div>
          <div className="text-xs text-blue-500 mt-1">
            총 포지션 가치
          </div>
        </div>
      </div>

      {/* Position Concentration */}
      <div className="mb-6">
        <h4 className="font-semibold text-gray-700 mb-3">포지션 집중도</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="border border-gray-200 rounded-lg p-3">
            <div className="text-xs text-gray-600">총 포지션</div>
            <div className="text-xl font-bold text-gray-900">
              {concentration.total_positions}개
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg p-3">
            <div className="text-xs text-gray-600">최대 포지션 비율</div>
            <div className="text-xl font-bold text-orange-600">
              {concentration.largest_position_pct.toFixed(2)}%
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg p-3">
            <div className="text-xs text-gray-600">Top 3 집중도</div>
            <div className="text-xl font-bold text-yellow-600">
              {concentration.top_3_concentration.toFixed(2)}%
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg p-3">
            <div className="text-xs text-gray-600">다각화 비율</div>
            <div className="text-xl font-bold text-green-600">
              {concentration.diversification_ratio.toFixed(2)}
            </div>
          </div>
        </div>

        <div className="mt-3 text-xs text-gray-600">
          <p>
            ⚠️ 최대 포지션 비율이 30% 이상이거나 Top 3 집중도가 70% 이상인 경우 위험도가 높습니다.
          </p>
        </div>
      </div>

      {/* Liquidation Prices */}
      {liquidationPrices.length > 0 && (
        <div className="mb-6">
          <h4 className="font-semibold text-gray-700 mb-3">청산 가격</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {liquidationPrices.map((liq, index) => {
              const isCritical = liq.distance_percentage <= 10;
              const isWarning = liq.distance_percentage <= 20;

              return (
                <div
                  key={index}
                  className={`flex items-center justify-between border rounded-lg p-3 ${
                    isCritical
                      ? 'border-red-300 bg-red-50'
                      : isWarning
                      ? 'border-yellow-300 bg-yellow-50'
                      : 'border-gray-200'
                  }`}
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-700">
                        {liq.symbol}
                      </span>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          liq.side === 'LONG'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {liq.side}
                      </span>
                      <span className="text-xs text-gray-500">
                        {liq.leverage}x
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      진입가: ${liq.entry_price.toLocaleString()} | 현재가: $
                      {liq.current_price.toLocaleString()}
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-gray-600 text-sm">청산 가격</div>
                    <div className="text-lg font-bold text-red-600">
                      ${liq.liquidation_price.toLocaleString()}
                    </div>
                    <div
                      className={`text-xs mt-1 ${
                        isCritical
                          ? 'text-red-600 font-bold'
                          : isWarning
                          ? 'text-yellow-600'
                          : 'text-gray-500'
                      }`}
                    >
                      거리: {liq.distance_percentage.toFixed(2)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-xs text-yellow-800">
              🚨 <strong>위험 알림:</strong> 청산가까지 10% 이내인 포지션은 즉시 조치가 필요합니다.
            </p>
          </div>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          ℹ️ <strong>정보:</strong> VaR는 95% 신뢰 수준에서 1일 동안 발생할 수 있는 최대 예상 손실입니다.
          포지션 집중도가 높을수록 특정 자산의 변동에 민감하게 반응합니다.
        </p>
      </div>
    </div>
  );
}
