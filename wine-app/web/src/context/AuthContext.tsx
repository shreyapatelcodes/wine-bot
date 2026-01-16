/**
 * Authentication context provider
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { api, getAccessToken, clearTokens } from '../services/api';
import type { UserProfile, UserProfileUpdate } from '../types';

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (idToken: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: UserProfileUpdate) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
    } catch {
      setUser(null);
      clearTokens();
    }
  }, []);

  // Check for existing session on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = getAccessToken();
      if (token) {
        await refreshUser();
      }
      setIsLoading(false);
    };
    initAuth();
  }, [refreshUser]);

  const login = async (idToken: string) => {
    setIsLoading(true);
    try {
      const response = await api.loginWithGoogle(idToken);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await api.logout();
    } finally {
      setUser(null);
      setIsLoading(false);
    }
  };

  const updateUser = async (data: UserProfileUpdate) => {
    const updated = await api.updateUser(data);
    setUser(updated);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        updateUser,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
