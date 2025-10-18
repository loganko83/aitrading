import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useSession } from 'next-auth/react';
import { RegisterApiKeyForm } from '../RegisterApiKeyForm';
import * as accountsApi from '@/lib/api/accounts';

// Mock next-auth
jest.mock('next-auth/react');
const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

// Mock API functions
jest.mock('@/lib/api/accounts');
const mockRegisterExchangeAccount = accountsApi.registerExchangeAccount as jest.MockedFunction<
  typeof accountsApi.registerExchangeAccount
>;

describe('RegisterApiKeyForm', () => {
  const mockSession = {
    accessToken: 'test-token-123',
    user: { email: 'test@example.com' }
  };

  beforeEach(() => {
    mockUseSession.mockReturnValue({
      data: mockSession,
      status: 'authenticated',
      update: jest.fn()
    } as any);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render the form with all required fields', () => {
    render(<RegisterApiKeyForm />);

    expect(screen.getByLabelText(/거래소/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/API Key/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/API Secret/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /API 키 등록/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/테스트넷 사용/i)).toBeInTheDocument();
  });

  it('should show Binance as default exchange', () => {
    render(<RegisterApiKeyForm />);

    const exchangeSelect = screen.getByLabelText(/거래소/i) as HTMLSelectElement;
    expect(exchangeSelect.value).toBe('binance');
  });

  it('should show passphrase field when OKX is selected', () => {
    render(<RegisterApiKeyForm />);

    const exchangeSelect = screen.getByLabelText(/거래소/i);
    fireEvent.change(exchangeSelect, { target: { value: 'okx' } });

    expect(screen.getByLabelText(/Passphrase/i)).toBeInTheDocument();
  });

  it('should not show passphrase field when Binance is selected', () => {
    render(<RegisterApiKeyForm />);

    const exchangeSelect = screen.getByLabelText(/거래소/i);
    fireEvent.change(exchangeSelect, { target: { value: 'binance' } });

    expect(screen.queryByLabelText(/Passphrase/i)).not.toBeInTheDocument();
  });

  it('should display error when API key is empty', async () => {
    render(<RegisterApiKeyForm />);

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/API 키와 시크릿을 모두 입력해주세요/i)).toBeInTheDocument();
    });
  });

  it('should display error when API secret is empty', async () => {
    render(<RegisterApiKeyForm />);

    const apiKeyInput = screen.getByLabelText(/API Key/i);
    fireEvent.change(apiKeyInput, { target: { value: 'test-api-key' } });

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/API 키와 시크릿을 모두 입력해주세요/i)).toBeInTheDocument();
    });
  });

  it('should display error when OKX passphrase is empty', async () => {
    render(<RegisterApiKeyForm />);

    const exchangeSelect = screen.getByLabelText(/거래소/i);
    fireEvent.change(exchangeSelect, { target: { value: 'okx' } });

    const apiKeyInput = screen.getByLabelText(/API Key/i);
    fireEvent.change(apiKeyInput, { target: { value: 'test-api-key' } });

    const apiSecretInput = screen.getByLabelText(/API Secret/i);
    fireEvent.change(apiSecretInput, { target: { value: 'test-secret' } });

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/OKX는 Passphrase가 필수입니다/i)).toBeInTheDocument();
    });
  });

  it('should successfully register Binance API key', async () => {
    const mockResponse = {
      id: '123',
      exchange: 'binance',
      testnet: true,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z'
    };

    mockRegisterExchangeAccount.mockResolvedValue(mockResponse);

    render(<RegisterApiKeyForm />);

    const apiKeyInput = screen.getByLabelText(/API Key/i);
    fireEvent.change(apiKeyInput, { target: { value: 'binance-key' } });

    const apiSecretInput = screen.getByLabelText(/API Secret/i);
    fireEvent.change(apiSecretInput, { target: { value: 'binance-secret' } });

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockRegisterExchangeAccount).toHaveBeenCalledWith(
        {
          exchange: 'binance',
          api_key: 'binance-key',
          api_secret: 'binance-secret',
          passphrase: undefined,
          testnet: true
        },
        'test-token-123'
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/API 키가 안전하게 등록되었습니다/i)).toBeInTheDocument();
    });
  });

  it('should successfully register OKX API key with passphrase', async () => {
    const mockResponse = {
      id: '456',
      exchange: 'okx',
      testnet: true,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z'
    };

    mockRegisterExchangeAccount.mockResolvedValue(mockResponse);

    render(<RegisterApiKeyForm />);

    const exchangeSelect = screen.getByLabelText(/거래소/i);
    fireEvent.change(exchangeSelect, { target: { value: 'okx' } });

    const apiKeyInput = screen.getByLabelText(/API Key/i);
    fireEvent.change(apiKeyInput, { target: { value: 'okx-key' } });

    const apiSecretInput = screen.getByLabelText(/API Secret/i);
    fireEvent.change(apiSecretInput, { target: { value: 'okx-secret' } });

    const passphraseInput = screen.getByLabelText(/Passphrase/i);
    fireEvent.change(passphraseInput, { target: { value: 'okx-pass' } });

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockRegisterExchangeAccount).toHaveBeenCalledWith(
        {
          exchange: 'okx',
          api_key: 'okx-key',
          api_secret: 'okx-secret',
          passphrase: 'okx-pass',
          testnet: true
        },
        'test-token-123'
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/API 키가 안전하게 등록되었습니다/i)).toBeInTheDocument();
    });
  });

  it('should display error message on API failure', async () => {
    mockRegisterExchangeAccount.mockRejectedValue({
      response: {
        data: {
          detail: 'Invalid API credentials'
        }
      }
    });

    render(<RegisterApiKeyForm />);

    const apiKeyInput = screen.getByLabelText(/API Key/i);
    fireEvent.change(apiKeyInput, { target: { value: 'invalid-key' } });

    const apiSecretInput = screen.getByLabelText(/API Secret/i);
    fireEvent.change(apiSecretInput, { target: { value: 'invalid-secret' } });

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Invalid API credentials/i)).toBeInTheDocument();
    });
  });

  it('should call onSuccess callback after successful registration', async () => {
    const mockOnSuccess = jest.fn();
    const mockResponse = {
      id: '123',
      exchange: 'binance',
      testnet: true,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z'
    };

    mockRegisterExchangeAccount.mockResolvedValue(mockResponse);

    render(<RegisterApiKeyForm onSuccess={mockOnSuccess} />);

    const apiKeyInput = screen.getByLabelText(/API Key/i);
    fireEvent.change(apiKeyInput, { target: { value: 'test-key' } });

    const apiSecretInput = screen.getByLabelText(/API Secret/i);
    fireEvent.change(apiSecretInput, { target: { value: 'test-secret' } });

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
    }, { timeout: 2000 });
  });

  it('should reset form after successful registration', async () => {
    const mockResponse = {
      id: '123',
      exchange: 'binance',
      testnet: true,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z'
    };

    mockRegisterExchangeAccount.mockResolvedValue(mockResponse);

    render(<RegisterApiKeyForm />);

    const apiKeyInput = screen.getByLabelText(/API Key/i) as HTMLInputElement;
    fireEvent.change(apiKeyInput, { target: { value: 'test-key' } });

    const apiSecretInput = screen.getByLabelText(/API Secret/i) as HTMLInputElement;
    fireEvent.change(apiSecretInput, { target: { value: 'test-secret' } });

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(apiKeyInput.value).toBe('');
      expect(apiSecretInput.value).toBe('');
    });
  });

  it('should disable form during submission', async () => {
    mockRegisterExchangeAccount.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<RegisterApiKeyForm />);

    const apiKeyInput = screen.getByLabelText(/API Key/i);
    fireEvent.change(apiKeyInput, { target: { value: 'test-key' } });

    const apiSecretInput = screen.getByLabelText(/API Secret/i);
    fireEvent.change(apiSecretInput, { target: { value: 'test-secret' } });

    const submitButton = screen.getByRole('button', { name: /API 키 등록/i });
    fireEvent.click(submitButton);

    expect(screen.getByRole('button', { name: /등록 중.../i })).toBeDisabled();
  });

  it('should display security notice', () => {
    render(<RegisterApiKeyForm />);

    expect(screen.getByText(/보안 안내/i)).toBeInTheDocument();
    expect(screen.getByText(/AES-256 암호화되어 안전하게 저장됩니다/i)).toBeInTheDocument();
    expect(screen.getByText(/출금 권한은 절대 부여하지 마세요/i)).toBeInTheDocument();
  });
});
