"use client";

import React, { useState } from 'react';
import { useSession } from 'next-auth/react';
import { registerExchangeAccount } from '@/lib/api/accounts';

interface RegisterApiKeyFormProps {
  onSuccess?: () => void;
}

export const RegisterApiKeyForm: React.FC<RegisterApiKeyFormProps> = ({ onSuccess }) => {
  const { data: session } = useSession();
  const [formData, setFormData] = useState({
    exchange: 'binance' as 'binance' | 'okx',
    api_key: '',
    api_secret: '',
    passphrase: '',
    testnet: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!session?.accessToken) {
      setError('로그인이 필요합니다.');
      return;
    }

    // Validate inputs
    if (!formData.api_key || !formData.api_secret) {
      setError('API 키와 시크릿을 모두 입력해주세요.');
      return;
    }

    if (formData.exchange === 'okx' && !formData.passphrase) {
      setError('OKX는 Passphrase가 필수입니다.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await registerExchangeAccount(
        {
          exchange: formData.exchange,
          api_key: formData.api_key,
          api_secret: formData.api_secret,
          passphrase: formData.exchange === 'okx' ? formData.passphrase : undefined,
          testnet: formData.testnet
        },
        session.accessToken
      );

      setSuccess(true);
      setFormData({
        exchange: 'binance',
        api_key: '',
        api_secret: '',
        passphrase: '',
        testnet: true
      });

      if (onSuccess) {
        setTimeout(onSuccess, 1500);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'API 키 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-api-key-form">
      <h2>거래소 API 키 등록</h2>

      {success && (
        <div className="success-message">
          ✅ API 키가 안전하게 등록되었습니다!
        </div>
      )}

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* 거래소 선택 */}
        <div className="form-group">
          <label htmlFor="exchange">거래소</label>
          <select
            id="exchange"
            value={formData.exchange}
            onChange={(e) => setFormData({
              ...formData,
              exchange: e.target.value as 'binance' | 'okx',
              passphrase: '' // 거래소 변경 시 passphrase 초기화
            })}
            disabled={loading}
          >
            <option value="binance">Binance Futures</option>
            <option value="okx">OKX Futures</option>
          </select>
        </div>

        {/* API 키 */}
        <div className="form-group">
          <label htmlFor="api_key">API Key</label>
          <input
            type="text"
            id="api_key"
            value={formData.api_key}
            onChange={(e) => setFormData({...formData, api_key: e.target.value})}
            placeholder="거래소에서 발급받은 API Key"
            disabled={loading}
            required
          />
        </div>

        {/* API 시크릿 */}
        <div className="form-group">
          <label htmlFor="api_secret">API Secret</label>
          <input
            type="password"
            id="api_secret"
            value={formData.api_secret}
            onChange={(e) => setFormData({...formData, api_secret: e.target.value})}
            placeholder="거래소에서 발급받은 API Secret"
            disabled={loading}
            required
          />
        </div>

        {/* OKX Passphrase (OKX 선택 시에만 표시) */}
        {formData.exchange === 'okx' && (
          <div className="form-group">
            <label htmlFor="passphrase">Passphrase (OKX 전용)</label>
            <input
              type="password"
              id="passphrase"
              value={formData.passphrase}
              onChange={(e) => setFormData({...formData, passphrase: e.target.value})}
              placeholder="OKX API 생성 시 설정한 Passphrase"
              disabled={loading}
              required
            />
          </div>
        )}

        {/* 테스트넷 옵션 */}
        <div className="form-group checkbox-group">
          <label htmlFor="testnet">
            <input
              type="checkbox"
              id="testnet"
              checked={formData.testnet}
              onChange={(e) => setFormData({...formData, testnet: e.target.checked})}
              disabled={loading}
            />
            <span>테스트넷 사용 (실제 자금 없이 테스트, 권장)</span>
          </label>
        </div>

        {/* 보안 안내 */}
        <div className="security-notice">
          <h4>🔒 보안 안내</h4>
          <ul>
            <li>API 키는 AES-256 암호화되어 안전하게 저장됩니다.</li>
            <li>출금 권한은 절대 부여하지 마세요.</li>
            <li>테스트넷으로 충분히 테스트 후 실계좌 연결을 권장합니다.</li>
            {formData.exchange === 'binance' && (
              <li>Binance: Enable Futures 권한만 활성화하세요.</li>
            )}
            {formData.exchange === 'okx' && (
              <li>OKX: Trade 권한만 활성화하세요.</li>
            )}
          </ul>
        </div>

        {/* 제출 버튼 */}
        <button
          type="submit"
          className="submit-button"
          disabled={loading}
        >
          {loading ? '등록 중...' : 'API 키 등록'}
        </button>
      </form>

      <style jsx>{`
        .register-api-key-form {
          max-width: 600px;
          margin: 0 auto;
          padding: 24px;
        }

        h2 {
          margin-bottom: 24px;
          font-size: 24px;
          font-weight: 700;
        }

        .success-message {
          padding: 16px;
          background-color: #d4edda;
          border: 1px solid #c3e6cb;
          border-radius: 8px;
          color: #155724;
          margin-bottom: 24px;
        }

        .error-message {
          padding: 16px;
          background-color: #f8d7da;
          border: 1px solid #f5c6cb;
          border-radius: 8px;
          color: #721c24;
          margin-bottom: 24px;
        }

        .form-group {
          margin-bottom: 20px;
        }

        label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
          color: #333;
        }

        input[type="text"],
        input[type="password"],
        select {
          width: 100%;
          padding: 12px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 16px;
          transition: border-color 0.2s;
        }

        input[type="text"]:focus,
        input[type="password"]:focus,
        select:focus {
          outline: none;
          border-color: #4CAF50;
        }

        input:disabled,
        select:disabled {
          background-color: #f5f5f5;
          cursor: not-allowed;
        }

        .checkbox-group label {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        input[type="checkbox"] {
          width: 20px;
          height: 20px;
          cursor: pointer;
        }

        .security-notice {
          background-color: #e3f2fd;
          border: 1px solid #90caf9;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 24px;
        }

        .security-notice h4 {
          margin-top: 0;
          margin-bottom: 12px;
          color: #1976d2;
        }

        .security-notice ul {
          margin: 0;
          padding-left: 20px;
        }

        .security-notice li {
          margin-bottom: 8px;
          color: #0d47a1;
        }

        .submit-button {
          width: 100%;
          padding: 14px;
          background-color: #4CAF50;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .submit-button:hover:not(:disabled) {
          background-color: #45a049;
        }

        .submit-button:disabled {
          background-color: #cccccc;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};
