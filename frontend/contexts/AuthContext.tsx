'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { User, Session, AuthError } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';

interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';  // Simplified: only admin and user roles
  client_id?: string;  // Internal use only (auto-assigned by backend)
  avatar_url?: string;
  onboarded?: boolean;  // Has user completed onboarding?
  onboarding_preferences?: {
    notifications_enabled?: boolean;
    email_digest?: boolean;
  };
  app_access?: string[];  // Apps user can access: 'thesis', 'purdy', 'all'
}

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  session: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: AuthError | null }>;
  updatePassword: (newPassword: string) => Promise<{ error: AuthError | null }>;
  refreshProfile: () => Promise<void>;
  // Whether the user is an admin
  isAdmin: boolean;
  // App access helpers
  hasThesisAccess: boolean;
  hasPurdyAccess: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // Simple admin check - admins have full access to everything
  const isAdmin = profile?.role === 'admin';

  // App access helpers
  const appAccess = profile?.app_access || ['thesis']; // Default to thesis
  const hasThesisAccess = isAdmin || appAccess.includes('thesis') || appAccess.includes('all');
  const hasPurdyAccess = isAdmin || appAccess.includes('purdy') || appAccess.includes('all');

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchUserProfile(session.user.id);
      } else {
        setLoading(false);
      }
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchUserProfile(session.user.id);
      } else {
        setProfile(null);
        setLoading(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const fetchUserProfile = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('id, email, name, role, client_id, avatar_url, app_access')
        .eq('id', userId)
        .single();

      if (error) throw error;
      setProfile(data);
    } catch (err) {
      console.warn('Error fetching user profile:', err);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  const refreshProfile = async () => {
    if (user?.id) {
      await fetchUserProfile(user.id);
    }
  };

  const signIn = async (email: string, password: string) => {
    // Normalize email to lowercase and trim whitespace
    const normalizedEmail = email.toLowerCase().trim();

    // Clear any stale session tokens before attempting login
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (session && session.user?.email?.toLowerCase() !== normalizedEmail) {
        // Different user trying to log in, clear the old session
        await supabase.auth.signOut({ scope: 'local' });
      }
    } catch (e) {
      // Ignore errors during cleanup, proceed with login
      console.warn('[DEBUG] Session cleanup before login:', e);
    }

    const { error } = await supabase.auth.signInWithPassword({
      email: normalizedEmail,
      password,
    });
    return { error };
  };

  const signOut = async () => {
    try {
      // Check if we have a valid session before attempting remote signout
      const { data: { session } } = await supabase.auth.getSession();

      if (session) {
        // Only attempt remote signout if we have an active session
        const { error } = await supabase.auth.signOut({ scope: 'global' });

        if (error) {
          console.error('Signout error from Supabase:', error);
        }
      } else {
        // No active session - clearing local state only
      }
    } catch (error) {
      console.error('Unexpected signout error:', error);
    } finally {
      // Always clear local state regardless of remote signout result
      setUser(null);
      setProfile(null);
      setSession(null);
    }
  };

  const resetPassword = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    });
    return { error };
  };

  const updatePassword = async (newPassword: string) => {
    const { error } = await supabase.auth.updateUser({
      password: newPassword,
    });
    return { error };
  };

  const value = {
    user,
    profile,
    session,
    loading,
    signIn,
    signOut,
    resetPassword,
    updatePassword,
    refreshProfile,
    isAdmin,
    hasThesisAccess,
    hasPurdyAccess,
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
