import { create } from 'zustand';
import type { Position, TradingSettings, DashboardStats } from '@/types';

interface TradingState {
  settings: TradingSettings | null;
  positions: Position[];
  dashboardStats: DashboardStats | null;
  selectedSymbol: string;
  isAutoTrading: boolean;

  // Actions
  setSettings: (settings: TradingSettings) => void;
  setPositions: (positions: Position[]) => void;
  addPosition: (position: Position) => void;
  updatePosition: (positionId: string, updates: Partial<Position>) => void;
  removePosition: (positionId: string) => void;
  setDashboardStats: (stats: DashboardStats) => void;
  setSelectedSymbol: (symbol: string) => void;
  toggleAutoTrading: () => void;
}

export const useTradingStore = create<TradingState>((set) => ({
  settings: null,
  positions: [],
  dashboardStats: null,
  selectedSymbol: 'BTC/USDT',
  isAutoTrading: false,

  setSettings: (settings) => set({ settings }),

  setPositions: (positions) => set({ positions }),

  addPosition: (position) =>
    set((state) => ({
      positions: [...state.positions, position],
    })),

  updatePosition: (positionId, updates) =>
    set((state) => ({
      positions: state.positions.map((pos) =>
        pos.id === positionId ? { ...pos, ...updates } : pos
      ),
    })),

  removePosition: (positionId) =>
    set((state) => ({
      positions: state.positions.filter((pos) => pos.id !== positionId),
    })),

  setDashboardStats: (stats) => set({ dashboardStats: stats }),

  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),

  toggleAutoTrading: () =>
    set((state) => ({ isAutoTrading: !state.isAutoTrading })),
}));
