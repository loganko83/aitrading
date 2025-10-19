'use client';

import { useState, useEffect } from 'react';
import { getCorrelationMatrix, CorrelationMatrix } from '@/lib/api/portfolio';

/**
 * Correlation Analysis Component
 *
 * 4개 코인 간 가격 상관관계 분석 (실제 데이터 기반)
 */

interface CorrelationAnalysisProps {
  exchange?: 'binance' | 'okx';
  symbols?: string[];
  days?: number;
  refreshInterval?: number;
}

export default function CorrelationAnalysis({
  exchange = 'binance',
  symbols = ['BTC', 'ETH', 'SOL', 'ADA'],
  days = 30,
  refreshInterval = 60000, // 1분
}: CorrelationAnalysisProps) {
  const [correlationMatrix, setCorrelationMatrix] = useState<CorrelationMatrix | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    const fetchCorrelation = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getCorrelationMatrix(exchange, symbols, days);
        setCorrelationMatrix(data.correlation_matrix);
        setLastUpdate(new Date());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch correlation data');
      } finally {
        setLoading(false);
      }
    };

    fetchCorrelation();
    const intervalId = setInterval(fetchCorrelation, refreshInterval);

    return () => clearInterval(intervalId);
  }, [exchange, symbols.join(','), days, refreshInterval]);

  const getColorClass = (value: number) => {
    if (value >= 0.8) return 'bg-green-500';
    if (value >= 0.6) return 'bg-green-300';
    if (value >= 0.4) return 'bg-yellow-300';
    return 'bg-red-300';
  };

  if (loading && !correlationMatrix) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">상관관계 분석</h3>
        <p className="text-gray-600">데이터 로딩 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">상관관계 분석</h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      </div>
    );
  }

  if (!correlationMatrix) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">상관관계 분석</h3>
        <p className="text-gray-600">데이터 없음</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">상관관계 분석</h3>
        {lastUpdate && (
          <span className="text-xs text-gray-500">
            마지막 업데이트: {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
        <p className="text-sm text-green-800">
          ✅ <strong>실시간 분석</strong>: {days}일 가격 데이터 기반 상관관계 매트릭스
        </p>
      </div>

      {/* Correlation Matrix */}
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr>
              <th className="border px-4 py-2"></th>
              {symbols.map((symbol) => (
                <th key={symbol} className="border px-4 py-2 font-semibold">
                  {symbol}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {symbols.map((sym1) => (
              <tr key={sym1}>
                <th className="border px-4 py-2 font-semibold">{sym1}</th>
                {symbols.map((sym2) => {
                  const value = correlationMatrix[sym1][sym2];
                  return (
                    <td
                      key={sym2}
                      className={`border px-4 py-2 text-center text-white font-semibold ${getColorClass(value)}`}
                    >
                      {value.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-sm text-gray-600">
        <p>
          <strong>상관계수 범위:</strong>
        </p>
        <ul className="list-disc list-inside space-y-1">
          <li>
            <span className="inline-block w-4 h-4 bg-green-500"></span> 0.8 - 1.0: 강한
            양의 상관관계
          </li>
          <li>
            <span className="inline-block w-4 h-4 bg-green-300"></span> 0.6 - 0.8: 중간
            양의 상관관계
          </li>
          <li>
            <span className="inline-block w-4 h-4 bg-yellow-300"></span> 0.4 - 0.6: 약한
            양의 상관관계
          </li>
          <li>
            <span className="inline-block w-4 h-4 bg-red-300"></span> 0.0 - 0.4: 낮은
            상관관계
          </li>
        </ul>
      </div>

      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          ℹ️ <strong>정보:</strong> 상관관계는 {days}일간의 가격 변동 데이터를 기반으로 계산됩니다.
          높은 상관관계는 두 자산이 비슷한 움직임을 보인다는 것을 의미하며, 포트폴리오 다각화에 참고할 수 있습니다.
        </p>
      </div>
    </div>
  );
}
