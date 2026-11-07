"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { UserResponse, authApi } from './api/auth';
import { clearAuthToken, getAuthToken, setAuthToken } from './api/client';
import { useRouter, usePathname } from 'next/navigation';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken();
      if (token) {
        try {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        } catch (error) {
          clearAuthToken();
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (token: string) => {
    setAuthToken(token);
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      router.push('/dashboard');
    } catch (error) {
      clearAuthToken();
      throw error;
    }
  };

  const logout = () => {
    clearAuthToken();
    setUser(null);
    router.push('/login');
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    if (permission === 'admin_only') return user.role?.toLowerCase() === 'admin';
    // For admin role or direct permission match
    if (user.role?.toLowerCase() === 'admin' || user.permissions?.includes('*')) return true;
    return user.permissions?.includes(permission) || false;
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Protected Route Wrapper Component
export const ProtectedRoute = ({ children, requiredPermission }: { children: ReactNode, requiredPermission?: string }) => {
  const { isAuthenticated, isLoading, hasPermission } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    } else if (!isLoading && isAuthenticated && requiredPermission && !hasPermission(requiredPermission)) {
      router.push('/dashboard'); // Or an unauthorized page
    }
  }, [isLoading, isAuthenticated, hasPermission, requiredPermission, pathname, router]);

  if (isLoading) {
    return <div className="flex h-screen w-full items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return null; // Will redirect
  }

  return <>{children}</>;
};
