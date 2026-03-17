'use client'

import { useRef, useState, useEffect, useCallback } from 'react'
import PageHeader from './PageHeader'
import HelpChat from './HelpChat'
import { useHelpChat } from '@/contexts/HelpChatContext'

const MIN_WIDTH = 280
const MAX_WIDTH = 700
const DEFAULT_WIDTH = 400

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
  const { isOpen } = useHelpChat()
  // If the page manages its own panels (like chat), use those props
  const useOwnPanelControls = showPanelToggles && onToggleRightPanel

  const [panelWidth, setPanelWidth] = useState(DEFAULT_WIDTH)
  const dragging = useRef(false)
  const startX = useRef(0)
  const startWidth = useRef(0)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    dragging.current = true
    startX.current = e.clientX
    startWidth.current = panelWidth
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [panelWidth])

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return
      const delta = startX.current - e.clientX
      const next = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth.current + delta))
      setPanelWidth(next)
    }
    const onMouseUp = () => {
      if (!dragging.current) return
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [])

  const showPanel = showHelpSidebar && isOpen

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
      <div className="flex flex-1 overflow-hidden relative">
        <div className="flex-1 overflow-auto">
          {children}
        </div>

        {/* Help panel -- slides in from the right */}
        <div
          className={`absolute top-0 right-0 h-full bg-card border-l border-default shadow-lg z-30 transform transition-transform duration-200 ease-in-out ${
            showPanel ? 'translate-x-0' : 'translate-x-full'
          }`}
          style={{ width: panelWidth }}
        >
          {/* Drag handle */}
          <div
            onMouseDown={onMouseDown}
            className="absolute top-0 left-0 w-1.5 h-full cursor-col-resize hover:bg-blue-500/30 active:bg-blue-500/50 transition-colors z-40"
          />

          {showPanel && <HelpChat />}
        </div>
      </div>
    </div>
  )
}
