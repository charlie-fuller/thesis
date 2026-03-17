'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import UserMenu from './UserMenu'

interface PageHeaderProps {
  showPanelToggles?: boolean
  showLeftPanel?: boolean
  showRightPanel?: boolean
  onToggleLeftPanel?: () => void
  onToggleRightPanel?: () => void
  tabSwitcher?: React.ReactNode
  // New prop: show help toggle using context (no callback needed)
  showHelpToggle?: boolean
}

export default function PageHeader({
  showPanelToggles = false,
  showLeftPanel = false,
  showRightPanel = false,
  onToggleLeftPanel,
  onToggleRightPanel,
  tabSwitcher,
  showHelpToggle = true,
}: PageHeaderProps) {
  const { isAdmin, hasDiscoAccess } = useAuth()
  const { theme } = useTheme()
  const pathname = usePathname()
  const router = useRouter()

  // Navigation links
  const userLinks = [
    { href: '/', label: 'Dashboard' },
    { href: '/kb', label: 'KB' },
    { href: '/chat', label: 'Chat' },
    { href: '/tasks', label: 'Tasks' },
    { href: '/projects', label: 'Projects' },
    // Conditionally add Initiatives link for users with access
    ...(hasDiscoAccess ? [{ href: '/disco', label: 'Initiatives' }] : []),
    { href: '/intelligence', label: 'Intelligence' },
    { href: '/command', label: 'Command' },
    { href: '/manifesto', label: 'Manifesto' },
  ]

  const isActive = (href: string) => {
    // Home route - exact match only
    if (href === '/') {
      return pathname === '/'
    }
    // For /admin and /disco, match both exact and sub-paths
    if (href === '/admin' || href === '/disco') {
      return pathname === href || pathname?.startsWith(href + '/')
    }
    // For other routes, match exact or sub-paths
    return pathname === href || pathname?.startsWith(href + '/')
  }

  // Calculate logo max height
  const headerHeightNum = parseInt(theme.header_height) || 64
  const logoMaxHeight = Math.max(headerHeightNum - 16, 24)

  return (
    <nav
      className="border-b border-default flex-shrink-0"
      style={{
        backgroundColor: theme.header_bg_color,
        height: theme.header_height
      }}
    >
      <div className="h-full px-4">
        <div className="flex items-center h-full">
          {/* Left: UserMenu, Brand, and Navigation Links */}
          <div className="flex items-center gap-4 flex-1">
            {/* User Menu - on the left */}
            <UserMenu />

            {/* Brand / Logo */}
            <Link href="/" className="flex items-center mx-2">
              {theme.header_logo_url ? (
                <img
                  src={theme.header_logo_url}
                  alt="Logo"
                  style={{ maxHeight: `${logoMaxHeight}px`, width: 'auto' }}
                  className="object-contain"
                />
              ) : (
                <span
                  className="text-2xl font-semibold"
                  style={{
                    color: theme.header_title_color || 'var(--header-title-color)',
                  }}
                >
                  Thesis
                </span>
              )}
            </Link>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center gap-1">
              {userLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="px-3 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-hover"
                  style={{
                    color: isActive(link.href)
                      ? theme.header_nav_active_color || 'var(--header-nav-active-color)'
                      : theme.header_nav_color || 'var(--header-nav-color)'
                  }}
                >
                  {link.label}
                </Link>
              ))}
            </div>

            {/* Tab Switcher (when provided) */}
            {tabSwitcher && (
              <div className="ml-4 pl-4 border-l border-default">
                {tabSwitcher}
              </div>
            )}
          </div>

          {/* Right: Panel toggles (or empty spacer to balance centering) */}
          <div className="flex items-center gap-1">
            {showPanelToggles && onToggleLeftPanel && (
              <button
                onClick={onToggleLeftPanel}
                className={`p-1.5 rounded transition-colors ${showLeftPanel ? 'text-primary' : 'text-muted hover:text-primary'}`}
                aria-label={showLeftPanel ? 'Hide Chats' : 'Show Chats'}
                title={showLeftPanel ? 'Hide Chats' : 'Show Chats'}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <rect x="3" y="4" width="18" height="16" rx="2" />
                  <line x1="9" y1="4" x2="9" y2="20" />
                  <line x1="5" y1="8" x2="7" y2="8" />
                  <line x1="5" y1="11" x2="7" y2="11" />
                  <line x1="5" y1="14" x2="7" y2="14" />
                </svg>
              </button>
            )}
            {showPanelToggles && onToggleRightPanel && (
              <button
                onClick={onToggleRightPanel}
                className={`p-1.5 rounded transition-colors ${showRightPanel ? 'text-primary' : 'text-muted hover:text-primary'}`}
                aria-label={showRightPanel ? 'Hide Help' : 'Show Help'}
                title={showRightPanel ? 'Hide Help' : 'Show Help'}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <rect x="3" y="4" width="18" height="16" rx="2" />
                  <line x1="15" y1="4" x2="15" y2="20" />
                  <line x1="17" y1="8" x2="19" y2="8" />
                  <line x1="17" y1="11" x2="19" y2="11" />
                  <line x1="17" y1="14" x2="19" y2="14" />
                </svg>
              </button>
            )}
            {/* Help button - navigates to /help?tab=ask */}
            {showHelpToggle && (
              <button
                onClick={() => router.push('/help?tab=ask')}
                className="p-1.5 rounded transition-colors text-muted hover:text-primary"
                aria-label="Open Help"
                title="Open Help"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <circle cx="12" cy="12" r="10" />
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
