'use client';

import { useState } from 'react';
import { closeAllSymbols } from '@/lib/api/positions';

interface MultiSymbolOrderProps {
  token?: string;
}

export default function MultiSymbolOrder({ token }: MultiSymbolOrderProps) {
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const symbols = ['BTC', 'ETH', 'SOL', 'ADA'];

  const toggleSymbol = (symbol: string) => {
    setSelectedSymbols((prev) =>
      prev.includes(symbol) ? prev.filter((s) => s !== symbol) : [...prev, symbol]
    );
  };

  const selectAll = () => {
    setSelectedSymbols(symbols);
  };

  const clearAll = () => {
    setSelectedSymbols([]);
  };

  const handleClosePositions = async () => {
    if (selectedSymbols.length === 0) {
      setError('최소 1개 심볼을 선택하세요');
      return;
    }

    if (!window.confirm(`${selectedSymbols.join(', ')} 심볼의 모든 포지션을 청산하시겠습니까?`)) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await closeAllSymbols(undefined, selectedSymbols, token);

      if (response.success) {
        setResult(
          `성공적으로 ${response.closed_positions}개 포지션을 청산했습니다.`
        );
      } else {
        setResult(
          `${response.closed_positions}개 청산 성공, ${response.failed_positions}개 실패`
        );
      }

      // 3초 후 결과 초기화
      setTimeout(() => {
        setResult(null);
        setSelectedSymbols([]);
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to close positions');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">멀티 심볼 포지션 청산</h3>

      {/* Symbol Selection */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-gray-700">심볼 선택:</label>
          <div className="space-x-2">
            <button
              onClick={selectAll}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              전체 선택
            </button>
            <button
              onClick={clearAll}
              className="text-sm text-gray-600 hover:text-gray-700"
            >
              선택 해제
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {symbols.map((symbol) => (
            <button
              key={symbol}
              onClick={() => toggleSymbol(symbol)}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                selectedSymbols.includes(symbol)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {symbol}/USDT
            </button>
          ))}
        </div>
      </div>

      {/* Action Button */}
      <div className="mb-4">
        <button
          onClick={handleClosePositions}
          disabled={loading || selectedSymbols.length === 0}
          className={`w-full px-6 py-3 rounded-lg font-bold transition-colors ${
            loading || selectedSymbols.length === 0
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-red-600 text-white hover:bg-red-700'
          }`}
        >
          {loading ? '처리 중...' : `선택한 심볼 포지션 청산 (${selectedSymbols.length}개)`}
        </button>
      </div>

      {/* Result/Error Messages */}
      {result && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800">{result}</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      )}

      {/* Warning */}
      <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          ⚠️ <strong>주의:</strong> 이 작업은 되돌릴 수 없습니다. 선택한 심볼의 모든 포지션이 시장가로 청산됩니다.
        </p>
      </div>
    </div>
  );
}
