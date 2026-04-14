'use client';

import { createContext, useContext, useState } from 'react';

/**
 * Stubbed AuthContext for API-key auth mode.
 * Supabase auth has been removed. This provides a no-op context so that
 * existing components that call useAuth() continue to work without changes.
 *
 * In API-key mode there is no client-side login/logout -- the API key in
 * NEXT_PUBLIC_API_KEY is sent as a Bearer token on every request.
 */

interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';
  client_id?: string;
  avatar_url?: string;
  onboarded?: boolean;
  onboarding_preferences?: {
    notifications_enabled?: boolean;
    email_digest?: boolean;
  };
  app_access?: string[];
}

interface AuthContextType {
  user: { id: string; email: string } | null;
  profile: UserProfile | null;
  session: { access_token: string } | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: Error | null }>;
  updatePassword: (newPassword: string) => Promise<{ error: Error | null }>;
  refreshProfile: () => Promise<void>;
  isAdmin: boolean;
  hasThesisAccess: boolean;
  hasDiscoAccess: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

/**
 * Stub user derived from the presence of an API key.
 * When an API key is set, we treat the session as "authenticated".
 */
const STUB_USER = API_KEY
  ? { id: 'api-key-user', email: 'api-key@local' }
  : null;

const STUB_PROFILE: UserProfile | null = API_KEY
  ? {
      id: 'api-key-user',
      email: 'api-key@local',
      name: 'API User',
      role: 'admin',
      client_id: '00000000-0000-0000-0000-000000000001',
      onboarded: true,
      app_access: ['all'],
    }
  : null;

const STUB_SESSION = API_KEY ? { access_token: API_KEY } : null;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading] = useState(false);

  const value: AuthContextType = {
    user: STUB_USER,
    profile: STUB_PROFILE,
    session: STUB_SESSION,
    loading,
    signIn: async () => ({ error: null }),
    signOut: async () => {},
    resetPassword: async () => ({ error: null }),
    updatePassword: async () => ({ error: null }),
    refreshProfile: async () => {},
    isAdmin: true,
    hasThesisAccess: true,
    hasDiscoAccess: true,
    isAuthenticated: !!API_KEY,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
