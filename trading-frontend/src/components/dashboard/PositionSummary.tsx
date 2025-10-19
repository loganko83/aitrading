'use client';

import { useEffect, useState } from 'react';
import { getPortfolioSummary, PortfolioSummary } from '@/lib/api/positions';

interface PositionSummaryProps {
  accountIds?: string[];
  token?: string;
  refreshInterval?: number;
}

export default function PositionSummary({
  accountIds,
  token,
  refreshInterval = 10000,
}: PositionSummaryProps) {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getPortfolioSummary(accountIds, token);
        setSummary(data);
        setLastUpdate(new Date());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch summary');
      } finally {
        setLoading(false);
      }
    };

    // 초기 로드
    fetchSummary();

    // 주기적 업데이트
    const intervalId = setInterval(fetchSummary, refreshInterval);

    return () => clearInterval(intervalId);
  }, [accountIds?.join(','), token, refreshInterval]);

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading portfolio...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  const profitColor = summary.total_unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600';

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">포트폴리오 요약</h2>
        <div className="text-sm text-gray-500">
          마지막 업데이트: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Balance */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-600 mb-2">총 잔액 (USDT)</div>
          <div className="text-3xl font-bold text-gray-900">
            ${summary.total_balance.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
        </div>

        {/* Total Unrealized PnL */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-600 mb-2">미실현 손익 (USDT)</div>
          <div className={`text-3xl font-bold ${profitColor}`}>
            {summary.total_unrealized_pnl >= 0 ? '+' : ''}$
            {summary.total_unrealized_pnl.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
        </div>

        {/* Total Positions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-sm text-gray-600 mb-2">총 포지션 수</div>
          <div className="text-3xl font-bold text-gray-900">
            {summary.total_positions}
          </div>
        </div>
      </div>

      {/* Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Positions by Symbol */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">심볼별 포지션</h3>
          <div className="space-y-2">
            {Object.entries(summary.positions_by_symbol).length > 0 ? (
              Object.entries(summary.positions_by_symbol).map(([symbol, count]) => (
                <div key={symbol} className="flex justify-between items-center">
                  <span className="text-gray-700">{symbol}/USDT</span>
                  <span className="font-semibold text-gray-900">{count}개</span>
                </div>
              ))
            ) : (
              <div className="text-gray-500 text-center py-4">
                보유 포지션 없음
              </div>
            )}
          </div>
        </div>

        {/* Positions by Exchange */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">거래소별 포지션</h3>
          <div className="space-y-2">
            {Object.entries(summary.positions_by_exchange).length > 0 ? (
              Object.entries(summary.positions_by_exchange).map(([exchange, count]) => (
                <div key={exchange} className="flex justify-between items-center">
                  <span className="text-gray-700">{exchange.toUpperCase()}</span>
                  <span className="font-semibold text-gray-900">{count}개</span>
                </div>
              ))
            ) : (
              <div className="text-gray-500 text-center py-4">
                보유 포지션 없음
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Account Details */}
      {summary.accounts.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">계정별 상세 정보</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-4 text-sm font-semibold text-gray-700">
                    계정 ID
                  </th>
                  <th className="text-left py-2 px-4 text-sm font-semibold text-gray-700">
                    거래소
                  </th>
                  <th className="text-right py-2 px-4 text-sm font-semibold text-gray-700">
                    잔액 (USDT)
                  </th>
                  <th className="text-right py-2 px-4 text-sm font-semibold text-gray-700">
                    미실현 손익
                  </th>
                  <th className="text-center py-2 px-4 text-sm font-semibold text-gray-700">
                    포지션 수
                  </th>
                  <th className="text-center py-2 px-4 text-sm font-semibold text-gray-700">
                    환경
                  </th>
                </tr>
              </thead>
              <tbody>
                {summary.accounts.map((account) => {
                  const accountPnlColor =
                    account.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600';

                  return (
                    <tr key={account.account_id} className="border-b border-gray-100">
                      <td className="py-2 px-4 text-sm text-gray-700">
                        {account.account_id.substring(0, 8)}...
                      </td>
                      <td className="py-2 px-4 text-sm text-gray-700">
                        {account.exchange.toUpperCase()}
                      </td>
                      <td className="py-2 px-4 text-sm text-right text-gray-900">
                        ${account.balance.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td className={`py-2 px-4 text-sm text-right font-semibold ${accountPnlColor}`}>
                        {account.unrealized_pnl >= 0 ? '+' : ''}$
                        {account.unrealized_pnl.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td className="py-2 px-4 text-sm text-center text-gray-900">
                        {account.positions}
                      </td>
                      <td className="py-2 px-4 text-sm text-center">
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            account.testnet
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {account.testnet ? 'Testnet' : 'Live'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
