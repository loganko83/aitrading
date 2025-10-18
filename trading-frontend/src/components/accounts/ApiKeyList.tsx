"use client";

import React, { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import {
  getExchangeAccounts,
  deleteExchangeAccount,
  toggleAccountStatus,
  type ExchangeAccount
} from '@/lib/api/accounts';

interface ApiKeyListProps {
  refreshTrigger?: number;
}

export const ApiKeyList: React.FC<ApiKeyListProps> = ({ refreshTrigger = 0 }) => {
  const { data: session } = useSession();
  const [accounts, setAccounts] = useState<ExchangeAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchAccounts = async () => {
    if (!session?.accessToken) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await getExchangeAccounts(session.accessToken);
      setAccounts(result.accounts);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '계정 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, [session, refreshTrigger]);

  const handleDelete = async (accountId: string) => {
    if (!session?.accessToken) return;

    if (!confirm('정말로 이 API 키를 삭제하시겠습니까?\n삭제 후에는 복구할 수 없습니다.')) {
      return;
    }

    setActionLoading(accountId);

    try {
      await deleteExchangeAccount(accountId, session.accessToken);
      await fetchAccounts(); // 목록 새로고침
    } catch (err: any) {
      alert(`삭제 실패: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggle = async (accountId: string) => {
    if (!session?.accessToken) return;

    setActionLoading(accountId);

    try {
      await toggleAccountStatus(accountId, session.accessToken);
      await fetchAccounts(); // 목록 새로고침
    } catch (err: any) {
      alert(`상태 변경 실패: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="api-key-list">
        <h2>등록된 API 키 목록</h2>
        <div className="loading">로딩 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="api-key-list">
        <h2>등록된 API 키 목록</h2>
        <div className="error-message">❌ {error}</div>
      </div>
    );
  }

  return (
    <div className="api-key-list">
      <h2>등록된 API 키 목록</h2>

      {accounts.length === 0 ? (
        <div className="empty-state">
          <p>등록된 API 키가 없습니다.</p>
          <p>위에서 거래소 API 키를 등록해주세요.</p>
        </div>
      ) : (
        <div className="accounts-grid">
          {accounts.map((account) => (
            <div
              key={account.id}
              className={`account-card ${account.is_active ? 'active' : 'inactive'}`}
            >
              {/* 헤더 */}
              <div className="card-header">
                <div className="exchange-info">
                  <span className="exchange-name">
                    {account.exchange === 'binance' ? '📊 Binance Futures' : '🔷 OKX Futures'}
                  </span>
                  {account.testnet && (
                    <span className="testnet-badge">Testnet</span>
                  )}
                </div>
                <div className={`status-badge ${account.is_active ? 'active' : 'inactive'}`}>
                  {account.is_active ? '✅ 활성' : '⚠️ 비활성'}
                </div>
              </div>

              {/* 정보 */}
              <div className="card-body">
                <div className="info-row">
                  <span className="label">등록일:</span>
                  <span className="value">
                    {new Date(account.created_at).toLocaleDateString('ko-KR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>
                <div className="info-row">
                  <span className="label">ID:</span>
                  <span className="value id-value">
                    {account.id.substring(0, 8)}...
                  </span>
                </div>
              </div>

              {/* 액션 버튼 */}
              <div className="card-actions">
                <button
                  className="toggle-button"
                  onClick={() => handleToggle(account.id)}
                  disabled={actionLoading === account.id}
                >
                  {actionLoading === account.id ? '처리 중...' :
                   account.is_active ? '비활성화' : '활성화'}
                </button>
                <button
                  className="delete-button"
                  onClick={() => handleDelete(account.id)}
                  disabled={actionLoading === account.id}
                >
                  {actionLoading === account.id ? '삭제 중...' : '삭제'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        .api-key-list {
          max-width: 1200px;
          margin: 0 auto;
          padding: 24px;
        }

        h2 {
          margin-bottom: 24px;
          font-size: 24px;
          font-weight: 700;
        }

        .loading {
          text-align: center;
          padding: 48px;
          color: #666;
        }

        .error-message {
          padding: 16px;
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 8px;
          color: #721c24;
        }

        .empty-state {
          text-align: center;
          padding: 48px;
          background-color: #f8f9fa;
          border-radius: 12px;
          color: #666;
        }

        .empty-state p:first-child {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 8px;
        }

        .accounts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 20px;
        }

        .account-card {
          background: white;
          border: 2px solid #e0e0e0;
          border-radius: 12px;
          padding: 20px;
          transition: all 0.3s ease;
        }

        .account-card:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }

        .account-card.active {
          border-color: #4CAF50;
        }

        .account-card.inactive {
          border-color: #ff9800;
          opacity: 0.8;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 16px;
          border-bottom: 1px solid #e0e0e0;
        }

        .exchange-info {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .exchange-name {
          font-size: 18px;
          font-weight: 700;
          color: #333;
        }

        .testnet-badge {
          display: inline-block;
          padding: 4px 12px;
          background-color: #fff3cd;
          color: #856404;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }

        .status-badge {
          padding: 6px 14px;
          border-radius: 16px;
          font-size: 14px;
          font-weight: 600;
        }

        .status-badge.active {
          background-color: #d4edda;
          color: #155724;
        }

        .status-badge.inactive {
          background-color: #fff3cd;
          color: #856404;
        }

        .card-body {
          margin-bottom: 16px;
        }

        .info-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
        }

        .label {
          color: #666;
          font-size: 14px;
        }

        .value {
          color: #333;
          font-weight: 500;
          font-size: 14px;
        }

        .id-value {
          font-family: 'Courier New', monospace;
          font-size: 13px;
        }

        .card-actions {
          display: flex;
          gap: 10px;
        }

        .toggle-button,
        .delete-button {
          flex: 1;
          padding: 10px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .toggle-button {
          background-color: #2196F3;
          color: white;
        }

        .toggle-button:hover:not(:disabled) {
          background-color: #1976D2;
        }

        .delete-button {
          background-color: #f44336;
          color: white;
        }

        .delete-button:hover:not(:disabled) {
          background-color: #d32f2f;
        }

        .toggle-button:disabled,
        .delete-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        @media (max-width: 768px) {
          .accounts-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};
