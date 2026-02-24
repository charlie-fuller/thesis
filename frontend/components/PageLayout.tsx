'use client'

import PageHeader from './PageHeader'

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
  // Set to false to hide the "?" help button in header
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
  // If the page manages its own panels (like chat), use those props
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
        showHelpToggle={showHelpSidebar && !useOwnPanelControls}
      />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </div>
    </div>
  )
}
