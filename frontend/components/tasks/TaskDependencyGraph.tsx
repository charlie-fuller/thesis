'use client'

import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import dynamic from 'next/dynamic'
import LoadingSpinner from '@/components/LoadingSpinner'

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <LoadingSpinner size="lg" />
    </div>
  ),
})

export interface TaskGraphNode {
  id: string
  title: string
  status: 'pending' | 'in_progress' | 'blocked' | 'completed' | 'backlog'
  priority: number
  assignee_name: string | null
  assignee_user_id: string | null
  assignee_stakeholder_id: string | null
  depends_on: string[]
  sequence_number: number | null
  linked_project_id: string | null
  project_title?: string | null
  // force-graph internal fields (added at runtime)
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number
  fy?: number
}

interface GraphLink {
  source: string | TaskGraphNode
  target: string | TaskGraphNode
  isBlocking: boolean
}

export interface TaskDependencyGraphProps {
  tasks: TaskGraphNode[]
  currentUserId?: string
  currentUserName?: string
  highlightMode?: 'none' | 'mine'
  onTaskClick?: (taskId: string) => void
  height?: number
  colorBy?: 'status' | 'project'
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#6b7280',
  backlog: '#6b7280',
  in_progress: '#3b82f6',
  blocked: '#f97316',
  completed: '#22c55e',
}

// Distinct project colors
const PROJECT_PALETTE = [
  '#a855f7', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444',
  '#ec4899', '#06b6d4', '#8b5cf6', '#f97316', '#10b981',
  '#6366f1', '#dc2626', '#14b8a6', '#e879f9', '#84cc16',
]

function isAssignedToUser(
  task: TaskGraphNode,
  userId?: string,
  userName?: string
): boolean {
  if (userId && task.assignee_user_id === userId) return true
  if (userId && task.assignee_stakeholder_id) return false // stakeholder match would need resolution
  if (userName && task.assignee_name) {
    return task.assignee_name.toLowerCase() === userName.toLowerCase()
  }
  return false
}

export default function TaskDependencyGraph({
  tasks,
  currentUserId,
  currentUserName,
  highlightMode = 'none',
  onTaskClick,
  height,
  colorBy = 'status',
}: TaskDependencyGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: height || 500 })
  const [showMyBlockers, setShowMyBlockers] = useState(highlightMode === 'mine')

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setDimensions({
          width: rect.width,
          height: height || Math.max(rect.height, 400),
        })
      }
    }
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [height])

  // Build project color map
  const projectColorMap = useMemo(() => {
    const map = new Map<string, string>()
    const projectIds = [...new Set(tasks.map(t => t.linked_project_id).filter(Boolean))]
    projectIds.forEach((pid, i) => {
      map.set(pid!, PROJECT_PALETTE[i % PROJECT_PALETTE.length])
    })
    return map
  }, [tasks])

  // Build graph data from tasks
  const graphData = useMemo(() => {
    const taskMap = new Map(tasks.map(t => [t.id, t]))

    const links: GraphLink[] = []
    for (const task of tasks) {
      if (task.depends_on && task.depends_on.length > 0) {
        for (const depId of task.depends_on) {
          if (taskMap.has(depId)) {
            const source = taskMap.get(depId)!
            const isBlocking = source.status !== 'completed'
            links.push({
              source: depId,
              target: task.id,
              isBlocking,
            })
          }
        }
      }
    }

    return { nodes: tasks, links }
  }, [tasks])

  // Compute "ball in my court" stats
  const myStats = useMemo(() => {
    if (!showMyBlockers) return null

    let waitingOnMe = 0
    let imBlocking = 0
    const taskMap = new Map(tasks.map(t => [t.id, t]))

    for (const task of tasks) {
      const isMine = isAssignedToUser(task, currentUserId, currentUserName)
      if (!isMine || task.status === 'completed') continue

      waitingOnMe++

      // Check if any other task depends on this one
      for (const other of tasks) {
        if (other.depends_on?.includes(task.id) && other.status !== 'completed') {
          imBlocking++
          break
        }
      }
    }

    return { waitingOnMe, imBlocking }
  }, [tasks, showMyBlockers, currentUserId, currentUserName])

  // Build set of "my task" IDs and "blocking downstream" IDs
  const { myTaskIds, blockingIds } = useMemo(() => {
    if (!showMyBlockers) return { myTaskIds: new Set<string>(), blockingIds: new Set<string>() }

    const myIds = new Set<string>()
    const blkIds = new Set<string>()

    for (const task of tasks) {
      if (isAssignedToUser(task, currentUserId, currentUserName) && task.status !== 'completed') {
        myIds.add(task.id)

        for (const other of tasks) {
          if (other.depends_on?.includes(task.id) && other.status !== 'completed') {
            blkIds.add(task.id)
            break
          }
        }
      }
    }

    return { myTaskIds: myIds, blockingIds: blkIds }
  }, [tasks, showMyBlockers, currentUserId, currentUserName])

  const getNodeColor = useCallback((node: TaskGraphNode): string => {
    if (colorBy === 'project' && node.linked_project_id) {
      return projectColorMap.get(node.linked_project_id) || '#6b7280'
    }
    return STATUS_COLORS[node.status] || '#6b7280'
  }, [colorBy, projectColorMap])

  // Canvas node drawing
  const nodeCanvasObject = useCallback((node: TaskGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const x = node.x || 0
    const y = node.y || 0
    const baseSize = Math.max(4, Math.min(8, node.priority * 1.5 + 2))
    const fontSize = 11 / globalScale
    const color = getNodeColor(node)

    const isDimmed = showMyBlockers && !myTaskIds.has(node.id) && !blockingIds.has(node.id)
    const isMine = showMyBlockers && myTaskIds.has(node.id)
    const isBlockingDownstream = showMyBlockers && blockingIds.has(node.id)

    ctx.globalAlpha = isDimmed ? 0.3 : 1

    // Unassigned dashed border
    if (!node.assignee_name && !node.assignee_user_id && !node.assignee_stakeholder_id) {
      ctx.beginPath()
      ctx.arc(x, y, baseSize + 2, 0, 2 * Math.PI)
      ctx.setLineDash([3 / globalScale, 3 / globalScale])
      ctx.strokeStyle = '#9ca3af'
      ctx.lineWidth = 1.5 / globalScale
      ctx.stroke()
      ctx.setLineDash([])
    }

    // "My task" bright ring
    if (isMine && !isBlockingDownstream) {
      ctx.beginPath()
      ctx.arc(x, y, baseSize + 3, 0, 2 * Math.PI)
      ctx.strokeStyle = '#fbbf24'
      ctx.lineWidth = 2.5 / globalScale
      ctx.stroke()
    }

    // "Blocking downstream" red ring
    if (isBlockingDownstream) {
      ctx.beginPath()
      ctx.arc(x, y, baseSize + 3, 0, 2 * Math.PI)
      ctx.strokeStyle = '#ef4444'
      ctx.lineWidth = 3 / globalScale
      ctx.stroke()
    }

    // Node circle
    ctx.beginPath()
    ctx.arc(x, y, baseSize, 0, 2 * Math.PI)
    ctx.fillStyle = color
    ctx.fill()

    // Completed check mark overlay
    if (node.status === 'completed') {
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 1.5 / globalScale
      ctx.beginPath()
      ctx.moveTo(x - baseSize * 0.3, y)
      ctx.lineTo(x - baseSize * 0.05, y + baseSize * 0.3)
      ctx.lineTo(x + baseSize * 0.35, y - baseSize * 0.3)
      ctx.stroke()
    }

    // Label
    if (globalScale > 0.5) {
      ctx.font = `${fontSize}px -apple-system, BlinkMacSystemFont, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillStyle = isDimmed ? 'rgba(229, 229, 229, 0.3)' : '#e5e5e5'

      const label = node.title.length > 30 ? node.title.slice(0, 28) + '...' : node.title
      ctx.fillText(label, x, y + baseSize + 3)

      // Assignee sub-label
      if (node.assignee_name && globalScale > 0.8) {
        const subFontSize = 9 / globalScale
        ctx.font = `${subFontSize}px -apple-system, BlinkMacSystemFont, sans-serif`
        ctx.fillStyle = isDimmed ? 'rgba(156, 163, 175, 0.3)' : '#9ca3af'
        ctx.fillText(node.assignee_name, x, y + baseSize + 3 + fontSize + 2)
      }
    }

    ctx.globalAlpha = 1
  }, [showMyBlockers, myTaskIds, blockingIds, getNodeColor])

  const linkColor = useCallback((link: GraphLink) => {
    if (link.isBlocking) return '#ef4444'
    return '#4b5563'
  }, [])

  const handleNodeClick = useCallback((node: TaskGraphNode) => {
    onTaskClick?.(node.id)
  }, [onTaskClick])

  const handleResetZoom = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400)
    }
  }, [])

  // Check if there are any dependencies to show
  const hasDependencies = tasks.some(t => t.depends_on && t.depends_on.length > 0)

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 border border-dashed border-default rounded-lg">
        <p className="text-sm text-muted">No tasks to display.</p>
      </div>
    )
  }

  if (!hasDependencies) {
    return (
      <div className="flex items-center justify-center h-64 border border-dashed border-default rounded-lg">
        <div className="text-center">
          <p className="text-sm text-muted">No dependencies found between tasks.</p>
          <p className="text-xs text-muted mt-1">
            Use Taskmaster to generate tasks with dependency chains.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="relative w-full bg-card rounded-lg overflow-hidden" style={{ height: height || 500 }}>
      {/* Toolbar */}
      <div className="absolute top-3 left-3 right-3 z-10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {(currentUserId || currentUserName) && (
            <button
              onClick={() => setShowMyBlockers(!showMyBlockers)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                showMyBlockers
                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border border-amber-300 dark:border-amber-700'
                  : 'bg-hover text-muted hover:text-primary border border-default'
              }`}
            >
              {showMyBlockers ? 'Showing my blockers' : 'Show my blockers'}
            </button>
          )}
          {showMyBlockers && myStats && (
            <span className="text-xs text-muted bg-card/80 px-2 py-1 rounded">
              {myStats.waitingOnMe} task{myStats.waitingOnMe !== 1 ? 's' : ''} on you
              {myStats.imBlocking > 0 && (
                <span className="text-red-500 ml-1">
                  | {myStats.imBlocking} blocking others
                </span>
              )}
            </span>
          )}
        </div>
        <button
          onClick={handleResetZoom}
          className="px-3 py-1.5 bg-hover hover:bg-border text-primary text-xs rounded-md transition-colors border border-default"
        >
          Reset View
        </button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 z-10 flex items-center gap-3 bg-card/90 px-3 py-2 rounded text-xs text-muted">
        {colorBy === 'status' ? (
          <>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gray-500 inline-block" /> Pending</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /> In Progress</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500 inline-block" /> Blocked</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> Done</span>
          </>
        ) : (
          <>
            {[...projectColorMap.entries()].slice(0, 6).map(([pid, color]) => {
              const task = tasks.find(t => t.linked_project_id === pid)
              const label = task?.project_title || pid.slice(0, 8)
              return (
                <span key={pid} className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: color }} />
                  {label.length > 15 ? label.slice(0, 13) + '...' : label}
                </span>
              )
            })}
          </>
        )}
        <span className="flex items-center gap-1 border-l border-default pl-3">
          <span className="w-4 border-t border-red-500 inline-block" /> Blocking
        </span>
      </div>

      {/* Stats */}
      <div className="absolute bottom-3 right-3 z-10 text-xs text-muted bg-card/80 px-3 py-2 rounded">
        {graphData.nodes.length} tasks / {graphData.links.length} dependencies
      </div>

      {/* Graph */}
      {/* eslint-disable @typescript-eslint/no-explicit-any */}
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        nodeId="id"
        nodeCanvasObject={nodeCanvasObject as any}
        nodePointerAreaPaint={((node: any, color: string, ctx: CanvasRenderingContext2D) => {
          ctx.beginPath()
          ctx.arc(node.x || 0, node.y || 0, 12, 0, 2 * Math.PI)
          ctx.fillStyle = color
          ctx.fill()
        }) as any}
        linkColor={linkColor as any}
        linkWidth={(link: any) => link.isBlocking ? 2 : 1}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
        linkDirectionalParticles={(link: any) => link.isBlocking ? 2 : 0}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleSpeed={0.005}
        onNodeClick={handleNodeClick as any}
        cooldownTicks={100}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        dagMode="lr"
        dagLevelDistance={80}
      />
    </div>
  )
}
