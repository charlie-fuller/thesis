'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import UserMenu from './UserMenu'

interface PageHeaderProps {
  showPanelToggles?: boolean
  showLeftPanel?: boolean
  showRightPanel?: boolean
  onToggleLeftPanel?: () => void
  onToggleRightPanel?: () => void
}

export default function PageHeader({
  showPanelToggles = false,
  showLeftPanel = false,
  showRightPanel = false,
  onToggleLeftPanel,
  onToggleRightPanel,
}: PageHeaderProps) {
  const { isAdmin } = useAuth()
  const { theme } = useTheme()
  const pathname = usePathname()

  // User-facing navigation links
  const userLinks = [
    { href: '/', label: 'Home' },
    { href: '/chat', label: 'Chat' },
    { href: '/meeting-room', label: 'Meeting Room' },
    { href: '/stakeholders', label: 'Stakeholders' },
  ]

  // Admin navigation links
  const adminLinks = [
    { href: '/admin/agents', label: 'Agents' },
    { href: '/admin/documents', label: 'Documents' },
    { href: '/admin/conversations', label: 'Conversations' },
  ]

  const isActive = (href: string) => {
    // Home route - exact match only
    if (href === '/') {
      return pathname === '/'
    }
    // For /admin, match both exact and sub-paths (admin section)
    if (href === '/admin') {
      return pathname === href || pathname?.startsWith('/admin/')
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
          {/* Left: UserMenu and Navigation Links */}
          <div className="flex items-center gap-4">
            {/* User Menu - on the left */}
            <UserMenu />

            {/* Navigation Links */}
            <div className="hidden md:flex items-center gap-1">
              {/* User Links */}
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

              {/* Admin Links with separator */}
              {isAdmin && (
                <>
                  <div className="w-px h-6 bg-border mx-2" />
                  {adminLinks.map((link) => (
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
                </>
              )}
            </div>
          </div>

          {/* Center: Logo/Brand - truly centered between nav and right edge */}
          <div className="flex-1 flex justify-center">
            <Link href="/" className="flex items-center">
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
          </div>
        </div>
      </div>
    </nav>
  )
}
