import { createBrowserClient } from '@supabase/ssr';
import { logger } from './logger';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  const errorMsg = 'CRITICAL: Missing Supabase environment variables. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env.local file.';
  logger.error(errorMsg);
  // In development, throw error to make misconfiguration obvious
  if (process.env.NODE_ENV === 'development') {
    throw new Error(errorMsg);
  }
}

// Use placeholder values during build-time prerendering when env vars are unavailable.
// The client will never be used server-side -- all pages using it are 'use client'.
export const supabase = createBrowserClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-key'
);
