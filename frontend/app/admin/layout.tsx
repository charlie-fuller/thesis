'use client';

import { useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import PageHeader from '@/components/PageHeader';
import LoadingSpinner from '@/components/LoadingSpinner';
import HelpChat from '@/components/HelpChat';
import { useHelpChat } from '@/contexts/HelpChatContext';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, profile, loading, isAdmin } = useAuth();
  const { isOpen: helpChatOpen } = useHelpChat();
  const router = useRouter();

  // Check admin access
  useEffect(() => {
    if (!loading) {
      // Not logged in - redirect to login
      if (!user) {
        router.push('/auth/login');
        return;
      }

      // Not an admin - redirect to home
      if (profile && !isAdmin) {
        router.push('/');
        return;
      }
    }
  }, [loading, user, profile, router, isAdmin]);

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-page">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-muted mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  // Show loading state while redirecting non-admin users
  if (!user || !isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-page">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-muted mt-4">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-page flex flex-col">
      {/* Top Navigation - using shared PageHeader with help panel toggle */}
      <PageHeader showHelpToggle />

      {/* Main Content Area with Help Panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>

        {/* Help Chat Sidebar */}
        {helpChatOpen && <HelpChat />}
      </div>
    </div>
  );
}
