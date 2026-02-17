'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { apiGet } from '@/lib/api'
import ChatInterface from './ChatInterface'
import ConversationSidebar from './ConversationSidebar'
import HelpChat from './HelpChat'
import PageHeader from './PageHeader'

interface UnifiedWorkspaceProps {
  clientId?: string  // Optional - backend auto-assigns default client
  userId: string
  conversationId?: string
  tabSwitcher?: React.ReactNode  // Optional tab switcher to display in the header area
  projectId?: string  // Optional project context filter
  initiativeId?: string  // Optional initiative context filter
}

export default function UnifiedWorkspace({
  clientId,
  userId,
  conversationId,
  tabSwitcher,
  projectId,
  initiativeId
}: UnifiedWorkspaceProps) {
  useAuth()  // Auth context is used for component initialization

  const [sidebarRefreshTrigger, setSidebarRefreshTrigger] = useState(0)

  // Track context filter state (can be changed via sidebar dropdowns)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(projectId ?? null)
  const [selectedInitiativeId, setSelectedInitiativeId] = useState<string | null>(initiativeId ?? null)

  // Sync with URL params when they change
  /* eslint-disable react-hooks/set-state-in-effect -- standard prop-to-state sync pattern */
  useEffect(() => {
    setSelectedProjectId(projectId ?? null)
    setSelectedInitiativeId(initiativeId ?? null)
  }, [projectId, initiativeId])
  /* eslint-enable react-hooks/set-state-in-effect */

  // When a project is selected but no initiative, resolve the project's linked initiative
  useEffect(() => {
    if (!selectedProjectId || selectedInitiativeId) return
    async function resolveInitiative() {
      try {
        const project = await apiGet<{ initiative_ids?: string[] }>(`/api/projects/${selectedProjectId}`)
        if (project.initiative_ids && project.initiative_ids.length > 0) {
          setSelectedInitiativeId(project.initiative_ids[0])
        }
      } catch {
        // Project fetch failed, no initiative to resolve
      }
    }
    resolveInitiative()
  }, [selectedProjectId, selectedInitiativeId])

  // Panel visibility state - left panel visible by default, right panel hidden by default
  const [showLeftPanel, setShowLeftPanel] = useState(true)
  const [showRightPanel, setShowRightPanel] = useState(false)
  const [panelStateLoaded, setPanelStateLoaded] = useState(false)

  // Load panel state from localStorage after mount (avoids hydration mismatch)
  useEffect(() => {
    // Using requestAnimationFrame to defer state updates and avoid cascading renders
    requestAnimationFrame(() => {
      const savedLeft = localStorage.getItem('thesis-show-left-panel')
      const savedRight = localStorage.getItem('thesis-show-right-panel')
      if (savedLeft !== null) setShowLeftPanel(savedLeft === 'true')
      if (savedRight !== null) setShowRightPanel(savedRight === 'true')
      setPanelStateLoaded(true)
    })
  }, [])

  // Persist panel visibility to localStorage (only after initial load)
  useEffect(() => {
    if (panelStateLoaded) {
      localStorage.setItem('thesis-show-left-panel', String(showLeftPanel))
    }
  }, [showLeftPanel, panelStateLoaded])

  useEffect(() => {
    if (panelStateLoaded) {
      localStorage.setItem('thesis-show-right-panel', String(showRightPanel))
    }
  }, [showRightPanel, panelStateLoaded])

  const handleConversationCreated = () => {
    // Trigger sidebar refresh when a new conversation is created
    setSidebarRefreshTrigger(prev => prev + 1)
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Top Header Bar - Consistent with other pages */}
      <PageHeader
        showPanelToggles={true}
        showLeftPanel={showLeftPanel}
        showRightPanel={showRightPanel}
        onToggleLeftPanel={() => setShowLeftPanel(!showLeftPanel)}
        onToggleRightPanel={() => setShowRightPanel(!showRightPanel)}
      />

      {/* Main Workspace - 3-column layout with panels extending full height */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Left Sidebar - Conversations */}
        {showLeftPanel && (
          <div className="w-80 border-r border-gray-200 h-full overflow-hidden flex-shrink-0 bg-card">
            <ConversationSidebar
              clientId={clientId}
              userId={userId}
              currentConversationId={conversationId}
              refreshTrigger={sidebarRefreshTrigger}
              className="h-full"
              projectId={selectedProjectId}
              initiativeId={selectedInitiativeId}
              onProjectChange={setSelectedProjectId}
              onInitiativeChange={setSelectedInitiativeId}
            />
          </div>
        )}

        {/* Center - Tab Switcher + Chat Interface */}
        <div className="flex-1 h-full overflow-hidden flex flex-col">
          {/* Tab Switcher (in center column only) */}
          {tabSwitcher && (
            <div className="flex-shrink-0 px-4 pt-4 bg-page">
              {tabSwitcher}
            </div>
          )}

          {/* Chat Interface */}
          <div className="flex-1 overflow-hidden">
            <ChatInterface
              clientId={clientId}
              userId={userId}
              conversationId={conversationId}
              onConversationCreated={handleConversationCreated}
              projectId={selectedProjectId ?? undefined}
              initiativeId={selectedInitiativeId ?? undefined}
              onContextRestored={(ctx) => {
                if (ctx.projectId) setSelectedProjectId(ctx.projectId)
                if (ctx.initiativeId) setSelectedInitiativeId(ctx.initiativeId)
              }}
            />
          </div>
        </div>

        {/* Help Chat Sidebar */}
        {showRightPanel && <HelpChat />}
      </div>
    </div>
  )
}
