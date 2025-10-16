import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  otpRequired: boolean;
  pendingUserId: string | null;

  // Actions
  setUser: (user: User | null) => void;
  setOTPRequired: (required: boolean, userId?: string) => void;
  logout: () => void;
  updateXP: (xp: number) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      otpRequired: false,
      pendingUserId: null,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
          otpRequired: false,
          pendingUserId: null,
        }),

      setOTPRequired: (required, userId) =>
        set({
          otpRequired: required,
          pendingUserId: userId || null,
        }),

      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          otpRequired: false,
          pendingUserId: null,
        }),

      updateXP: (xp) =>
        set((state) => ({
          user: state.user ? { ...state.user, xp_points: xp } : null,
        })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
