'use client';

import Link from 'next/link';

/**
 * Reset password page -- stubbed out after Supabase removal.
 * Password reset is no longer available in API-key auth mode.
 */
export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center page-bg px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary mb-2">Thesis</h1>
          <p className="text-secondary">Password reset is not available</p>
        </div>

        <div className="card p-8 text-center">
          <p className="text-secondary mb-6">
            Authentication is now handled via API key. Password reset is no longer supported.
          </p>
          <Link href="/auth/login" className="text-sm link font-medium">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}
