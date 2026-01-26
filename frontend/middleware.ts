import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Routes that require thesis access (not available to disco-only users)
const thesisRoutes = ['/chat', '/admin', '/profile'];

// Routes that require disco access
const discoRoutes = ['/disco'];

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();

  // Skip middleware if Supabase is not configured (e.g., during build)
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.warn('Supabase not configured, skipping auth middleware');
    return res;
  }

  const supabase = createServerClient(
    supabaseUrl,
    supabaseKey,
    {
      cookies: {
        get(name: string) {
          return req.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          res.cookies.set({
            name,
            value,
            ...options,
          });
        },
        remove(name: string, options: CookieOptions) {
          res.cookies.set({
            name,
            value: '',
            ...options,
          });
        },
      },
    }
  );

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const pathname = req.nextUrl.pathname;

  // Protected routes that require authentication
  const protectedRoutes = [...thesisRoutes, ...discoRoutes];
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  );

  // Check route types
  const isAdminRoute = pathname.startsWith('/admin');
  const isThesisRoute = thesisRoutes.some((route) => pathname.startsWith(route));
  const isDiscoRoute = pathname.startsWith('/disco');

  // Auth routes that should redirect if already logged in
  const authRoutes = ['/auth/login'];
  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route));

  // If trying to access protected route without session, redirect to login
  if (isProtectedRoute && !session) {
    const redirectUrl = new URL('/auth/login', req.url);
    redirectUrl.searchParams.set('redirectTo', pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // Fetch user profile with role and app_access for permission checks
  let profile: { role: string; app_access: string[] | null } | null = null;
  if (session && (isProtectedRoute || isAuthRoute)) {
    const { data } = await supabase
      .from('users')
      .select('role, app_access')
      .eq('id', session.user.id)
      .single();
    profile = data;
  }

  if (session && profile) {
    const isAdmin = profile.role === 'admin';
    const appAccess = profile.app_access || ['thesis']; // Default to thesis access
    const hasThesisAccess = isAdmin || appAccess.includes('thesis') || appAccess.includes('all');
    const hasDiscoAccess = isAdmin || appAccess.includes('disco') || appAccess.includes('purdy') || appAccess.includes('all');

    // If trying to access admin route without admin role
    if (isAdminRoute && !isAdmin) {
      // Redirect based on what access they have
      const redirectPath = hasDiscoAccess && !hasThesisAccess ? '/disco' : '/chat';
      return NextResponse.redirect(new URL(redirectPath, req.url));
    }

    // If trying to access thesis routes without thesis access
    if (isThesisRoute && !hasThesisAccess) {
      // DISCo-only user trying to access thesis routes
      return NextResponse.redirect(new URL('/disco', req.url));
    }

    // If trying to access disco routes without disco access
    if (isDiscoRoute && !hasDiscoAccess) {
      // Thesis-only user trying to access disco routes
      return NextResponse.redirect(new URL('/chat', req.url));
    }

    // If on auth route with session, redirect to appropriate home
    if (isAuthRoute) {
      let redirectPath = '/chat';
      if (isAdmin) {
        redirectPath = '/admin';
      } else if (hasDiscoAccess && !hasThesisAccess) {
        redirectPath = '/disco';
      }
      return NextResponse.redirect(new URL(redirectPath, req.url));
    }
  }

  return res;
}

export const config = {
  matcher: [
    '/admin/:path*',
    '/chat/:path*',
    '/profile/:path*',
    '/auth/:path*',
    '/disco/:path*',
  ],
};
