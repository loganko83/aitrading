"use client";

import React, { useState } from 'react';
import { RegisterApiKeyForm } from './RegisterApiKeyForm';
import { ApiKeyList } from './ApiKeyList';

export const ApiKeyManager: React.FC = () => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleRegisterSuccess = () => {
    // 등록 성공 시 목록 새로고침
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="api-key-manager">
      <div className="header">
        <h1>거래소 API 키 관리</h1>
        <p className="subtitle">
          Binance 또는 OKX Futures API 키를 등록하고 관리합니다.
          모든 API 키는 AES-256 암호화되어 안전하게 저장됩니다.
        </p>
      </div>

      <div className="content">
        {/* 등록 폼 */}
        <section className="register-section">
          <RegisterApiKeyForm onSuccess={handleRegisterSuccess} />
        </section>

        {/* 구분선 */}
        <div className="divider" />

        {/* 목록 */}
        <section className="list-section">
          <ApiKeyList refreshTrigger={refreshTrigger} />
        </section>
      </div>

      <style jsx>{`
        .api-key-manager {
          min-height: 100vh;
          background-color: #f8f9fa;
        }

        .header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 48px 24px;
          color: white;
          text-align: center;
        }

        .header h1 {
          font-size: 36px;
          font-weight: 800;
          margin-bottom: 12px;
        }

        .subtitle {
          font-size: 16px;
          opacity: 0.95;
          max-width: 800px;
          margin: 0 auto;
          line-height: 1.6;
        }

        .content {
          max-width: 1400px;
          margin: 0 auto;
          padding: 40px 24px;
        }

        .register-section {
          background: white;
          border-radius: 16px;
          padding: 32px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
          margin-bottom: 40px;
        }

        .divider {
          height: 2px;
          background: linear-gradient(
            to right,
            transparent,
            #e0e0e0 50%,
            transparent
          );
          margin: 40px 0;
        }

        .list-section {
          background: white;
          border-radius: 16px;
          padding: 32px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        @media (max-width: 768px) {
          .header h1 {
            font-size: 28px;
          }

          .subtitle {
            font-size: 14px;
          }

          .register-section,
          .list-section {
            padding: 20px;
          }
        }
      `}</style>
    </div>
  );
};
