'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function UserMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, profile, signOut } = useAuth();
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside or pressing Escape
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen]);

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      // signOut already handles errors, this is just defensive
      console.warn('Error during sign out:', error);
    } finally {
      // Always redirect to login even if there were errors
      router.push('/auth/login');
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      {/* Menu Button with Hamburger Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1 p-2 rounded-lg hover:bg-hover transition-colors focus-ring"
        aria-label="User menu"
        aria-expanded={isOpen}
      >
        {/* Hamburger menu icon */}
        <svg
          className="w-6 h-6 text-secondary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>

        {/* Dropdown icon */}
        <svg
          className={`w-4 h-4 icon-muted transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-72 card shadow-card-hover overflow-hidden z-50">
          {/* User Info Section */}
          <div className="px-4 py-3 bg-hover border-b border-default">
            <div className="flex items-center gap-3 mb-2">
              {/* Avatar in dropdown */}
              {profile?.avatar_url ? (
                <img
                  src={profile.avatar_url}
                  alt={profile?.name || 'User'}
                  className="w-12 h-12 rounded-full object-cover border-2 border-default"
                />
              ) : (
                <div className="avatar-primary w-12 h-12 text-lg">
                  {profile?.name ? profile.name.charAt(0).toUpperCase() : '?'}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-primary truncate">
                  {profile?.name || 'User'}
                </p>
                <p className="text-xs text-muted truncate mt-0.5">
                  {user?.email}
                </p>
              </div>
            </div>
            {profile?.role && (
              <span className="badge-primary capitalize">
                {profile.role.replace('_', ' ')}
              </span>
            )}
          </div>

          {/* Menu Items */}
          <div className="py-1">
            {/* Profile Link - for all users */}
            <Link
              href="/profile"
              className="sidebar-item flex items-center w-full text-sm"
              onClick={() => setIsOpen(false)}
            >
              <svg className="w-5 h-5 mr-3 icon-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Profile Settings
            </Link>

            {/* Divider */}
            <div className="my-1 divider"></div>

            {/* Sign Out */}
            <button
              onClick={handleSignOut}
              className="w-full flex items-center px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
