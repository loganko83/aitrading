import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useSession } from 'next-auth/react';
import { ApiKeyList } from '../ApiKeyList';
import * as accountsApi from '@/lib/api/accounts';

// Mock next-auth
jest.mock('next-auth/react');
const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

// Mock API functions
jest.mock('@/lib/api/accounts');
const mockGetExchangeAccounts = accountsApi.getExchangeAccounts as jest.MockedFunction<
  typeof accountsApi.getExchangeAccounts
>;
const mockDeleteExchangeAccount = accountsApi.deleteExchangeAccount as jest.MockedFunction<
  typeof accountsApi.deleteExchangeAccount
>;
const mockToggleAccountStatus = accountsApi.toggleAccountStatus as jest.MockedFunction<
  typeof accountsApi.toggleAccountStatus
>;

describe('ApiKeyList', () => {
  const mockSession = {
    accessToken: 'test-token-123',
    user: { email: 'test@example.com' }
  };

  const mockAccounts = [
    {
      id: '123',
      exchange: 'binance',
      testnet: true,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z'
    },
    {
      id: '456',
      exchange: 'okx',
      testnet: false,
      is_active: false,
      created_at: '2025-01-02T00:00:00Z'
    }
  ];

  beforeEach(() => {
    mockUseSession.mockReturnValue({
      data: mockSession,
      status: 'authenticated',
      update: jest.fn()
    } as any);

    // Mock window.confirm
    global.confirm = jest.fn(() => true);
    global.alert = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should display loading state initially', () => {
    mockGetExchangeAccounts.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<ApiKeyList />);

    expect(screen.getByText(/로딩 중.../i)).toBeInTheDocument();
  });

  it('should fetch and display accounts', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/📊 Binance Futures/i)).toBeInTheDocument();
      expect(screen.getByText(/🔷 OKX Futures/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/✅ 활성/i)).toBeInTheDocument();
    expect(screen.getByText(/⚠️ 비활성/i)).toBeInTheDocument();
  });

  it('should display testnet badge', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/Testnet/i)).toBeInTheDocument();
    });
  });

  it('should display empty state when no accounts exist', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: [],
      total: 0
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/등록된 API 키가 없습니다/i)).toBeInTheDocument();
      expect(screen.getByText(/위에서 거래소 API 키를 등록해주세요/i)).toBeInTheDocument();
    });
  });

  it('should display error message on fetch failure', async () => {
    mockGetExchangeAccounts.mockRejectedValue({
      response: {
        data: {
          detail: 'Unauthorized'
        }
      }
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/❌ Unauthorized/i)).toBeInTheDocument();
    });
  });

  it('should toggle account status when toggle button is clicked', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    mockToggleAccountStatus.mockResolvedValue({
      success: true,
      data: {
        account_id: '123',
        is_active: false
      }
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/📊 Binance Futures/i)).toBeInTheDocument();
    });

    const toggleButtons = screen.getAllByRole('button', { name: /비활성화/i });
    fireEvent.click(toggleButtons[0]);

    await waitFor(() => {
      expect(mockToggleAccountStatus).toHaveBeenCalledWith('123', 'test-token-123');
    });
  });

  it('should delete account when delete button is clicked with confirmation', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    mockDeleteExchangeAccount.mockResolvedValue({
      success: true,
      message: 'Account deleted successfully'
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/📊 Binance Futures/i)).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /삭제/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalledWith(
        expect.stringContaining('정말로 이 API 키를 삭제하시겠습니까?')
      );
      expect(mockDeleteExchangeAccount).toHaveBeenCalledWith('123', 'test-token-123');
    });
  });

  it('should not delete account when confirmation is cancelled', async () => {
    (global.confirm as jest.Mock).mockReturnValue(false);

    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/📊 Binance Futures/i)).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /삭제/i });
    fireEvent.click(deleteButtons[0]);

    expect(mockDeleteExchangeAccount).not.toHaveBeenCalled();
  });

  it('should show alert on delete failure', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    mockDeleteExchangeAccount.mockRejectedValue({
      response: {
        data: {
          detail: 'Account not found'
        }
      }
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/📊 Binance Futures/i)).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /삭제/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('Account not found')
      );
    });
  });

  it('should show alert on toggle failure', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    mockToggleAccountStatus.mockRejectedValue({
      response: {
        data: {
          detail: 'Account not found'
        }
      }
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/📊 Binance Futures/i)).toBeInTheDocument();
    });

    const toggleButtons = screen.getAllByRole('button', { name: /비활성화/i });
    fireEvent.click(toggleButtons[0]);

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('Account not found')
      );
    });
  });

  it('should refresh accounts when refreshTrigger changes', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    const { rerender } = render(<ApiKeyList refreshTrigger={0} />);

    await waitFor(() => {
      expect(mockGetExchangeAccounts).toHaveBeenCalledTimes(1);
    });

    rerender(<ApiKeyList refreshTrigger={1} />);

    await waitFor(() => {
      expect(mockGetExchangeAccounts).toHaveBeenCalledTimes(2);
    });
  });

  it('should disable buttons during action', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    mockToggleAccountStatus.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/📊 Binance Futures/i)).toBeInTheDocument();
    });

    const toggleButtons = screen.getAllByRole('button', { name: /비활성화/i });
    fireEvent.click(toggleButtons[0]);

    expect(screen.getByRole('button', { name: /처리 중.../i })).toBeDisabled();
  });

  it('should display formatted creation date', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/2025년 1월 1일/i)).toBeInTheDocument();
    });
  });

  it('should display truncated account ID', async () => {
    mockGetExchangeAccounts.mockResolvedValue({
      accounts: mockAccounts,
      total: 2
    });

    render(<ApiKeyList />);

    await waitFor(() => {
      expect(screen.getByText(/123\.\.\./i)).toBeInTheDocument();
    });
  });

  it('should handle session without accessToken', async () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'unauthenticated',
      update: jest.fn()
    } as any);

    render(<ApiKeyList />);

    // Should not call API when not authenticated
    expect(mockGetExchangeAccounts).not.toHaveBeenCalled();
  });
});
