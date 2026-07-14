import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, UserLogin, UserCreate, TokenResponse } from '@/types';
import { APIClient } from '@/lib/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (credentials: UserLogin) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
  getCurrentUser: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null,

      // Actions
      login: async (credentials: UserLogin) => {
        set({ loading: true, error: null });
        
        try {
          const tokens = await APIClient.login(credentials);
          const user = await APIClient.getCurrentUser();
          
          set({
            user,
            isAuthenticated: true,
            loading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            loading: false,
            error: error.response?.data?.error?.message || 'Login failed',
            isAuthenticated: false,
            user: null,
          });
          throw error;
        }
      },

      register: async (userData: UserCreate) => {
        set({ loading: true, error: null });
        
        try {
          const result = await APIClient.register(userData);
          
          set({
            user: result.user,
            isAuthenticated: true,
            loading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            loading: false,
            error: error.response?.data?.error?.message || 'Registration failed',
            isAuthenticated: false,
            user: null,
          });
          throw error;
        }
      },

      logout: () => {
        APIClient.logout().catch(() => {
          // Ignore errors during logout
        });
        
        set({
          user: null,
          isAuthenticated: false,
          loading: false,
          error: null,
        });
      },

      getCurrentUser: async () => {
        if (!APIClient.isAuthenticated()) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ loading: true });
        
        try {
          const user = await APIClient.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            loading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            loading: false,
            error: null, // Don't show error for auth check failures
            isAuthenticated: false,
            user: null,
          });
          
          // Clear auth data if token is invalid
          APIClient.clearAuth();
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ loading });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        // Only persist user and auth status
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Selectors for easy access
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useAuthLoading = () => useAuthStore((state) => state.loading);
export const useAuthError = () => useAuthStore((state) => state.error);