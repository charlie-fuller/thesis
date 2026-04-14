import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware stub -- Supabase auth removed.
 * With API-key auth, there is no server-side session to validate.
 * All route protection is handled by the backend via the API key.
 */
export async function middleware(_req: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/admin/:path*',
    '/chat/:path*',
    '/profile/:path*',
    '/auth/:path*',
    '/disco/:path*',
    '/kb/:path*',
    '/kb',
    '/tasks/:path*',
    '/tasks',
    '/projects/:path*',
    '/projects',
    '/stakeholders/:path*',
    '/stakeholders',
    '/meeting-room/:path*',
    '/meeting-room',
    '/pipeline/:path*',
    '/pipeline',
    '/transcripts/:path*',
    '/transcripts',
    '/intelligence/:path*',
    '/intelligence',
  ],
};
