'use client'

import { useHelpChat } from '@/contexts/HelpChatContext'
import PageHeader from './PageHeader'
import HelpChat from './HelpChat'

interface PageLayoutProps {
  children: React.ReactNode
  // Optional: pass through to PageHeader
  tabSwitcher?: React.ReactNode
  // For pages that have their own panel toggles (like chat page)
  showPanelToggles?: boolean
  showLeftPanel?: boolean
  showRightPanel?: boolean
  onToggleLeftPanel?: () => void
  onToggleRightPanel?: () => void
  // Set to false to disable help sidebar on specific pages
  showHelpSidebar?: boolean
}

export default function PageLayout({
  children,
  tabSwitcher,
  showPanelToggles = false,
  showLeftPanel,
  showRightPanel,
  onToggleLeftPanel,
  onToggleRightPanel,
  showHelpSidebar = true,
}: PageLayoutProps) {
  const { isOpen: helpPanelOpen } = useHelpChat()

  // If the page manages its own panels (like chat), use those props
  // Otherwise, use the context-based help toggle
  const useOwnPanelControls = showPanelToggles && onToggleRightPanel

  return (
    <div className="flex flex-col h-screen bg-page">
      <PageHeader
        showPanelToggles={showPanelToggles}
        showLeftPanel={showLeftPanel}
        showRightPanel={showRightPanel}
        onToggleLeftPanel={onToggleLeftPanel}
        onToggleRightPanel={onToggleRightPanel}
        tabSwitcher={tabSwitcher}
        // Show help toggle only if page doesn't manage its own panels
        showHelpToggle={showHelpSidebar && !useOwnPanelControls}
      />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-auto">
          {children}
        </div>
        {/* Show help sidebar when open (and enabled for this page) */}
        {showHelpSidebar && helpPanelOpen && !useOwnPanelControls && <HelpChat />}
      </div>
    </div>
  )
}
