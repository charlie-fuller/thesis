'use client'

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  Label
} from 'recharts'
import { Target, TrendingUp, AlertTriangle, Info } from 'lucide-react'

// Minimal fields required for the scatter plot
interface ProjectData {
  id: string
  project_code: string
  title: string
  roi_potential: number | null
  implementation_effort: number | null
  tier: number
  status: string
  department: string | null
  owner_name: string | null
  total_score: number
}

// Accept any project that has at least the required fields
interface ProjectScatterPlotProps<T extends ProjectData> {
  projects: T[]
  onProjectClick: (project: T) => void
}

// Tier colors matching the main page
const TIER_COLORS = {
  1: '#e11d48', // rose-600
  2: '#d97706', // amber-600
  3: '#2563eb', // blue-600
  4: '#64748b', // slate-500
}

const TIER_LABELS = {
  1: 'Tier 1: Strategic Priority',
  2: 'Tier 2: High Impact',
  3: 'Tier 3: Medium Priority',
  4: 'Tier 4: Backlog',
}

// Quadrant definitions for the scatter plot
const QUADRANTS = {
  quickWins: { label: 'Quick Wins', description: 'High ROI, Low Effort', icon: TrendingUp, color: 'text-green-600' },
  strategicBets: { label: 'Strategic Bets', description: 'High ROI, High Effort', icon: Target, color: 'text-blue-600' },
  lowPriority: { label: 'Low Priority', description: 'Low ROI, Low Effort', icon: Info, color: 'text-slate-500' },
  questionable: { label: 'Questionable', description: 'Low ROI, High Effort', icon: AlertTriangle, color: 'text-amber-600' },
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    payload: ProjectData & { x: number; y: number }
  }>
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null

  const data = payload[0].payload

  return (
    <div className="bg-card border border-default rounded-lg shadow-lg p-3 max-w-xs">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-mono text-muted">{data.project_code}</span>
        <span
          className="text-xs px-1.5 py-0.5 rounded"
          style={{
            backgroundColor: `${TIER_COLORS[data.tier as 1 | 2 | 3 | 4]}20`,
            color: TIER_COLORS[data.tier as 1 | 2 | 3 | 4],
          }}
        >
          T{data.tier}
        </span>
      </div>
      <p className="font-medium text-primary text-sm mb-2">{data.title}</p>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-muted">ROI Potential:</span>
          <span className="ml-1 font-medium text-primary">{data.roi_potential ?? 'N/A'}/5</span>
        </div>
        <div>
          <span className="text-muted">Effort:</span>
          <span className="ml-1 font-medium text-primary">{data.implementation_effort ?? 'N/A'}/5</span>
        </div>
        {data.department && (
          <div className="col-span-2">
            <span className="text-muted">Department:</span>
            <span className="ml-1 font-medium text-primary capitalize">{data.department}</span>
          </div>
        )}
      </div>
      <p className="text-xs text-muted mt-2 border-t border-default pt-2">Click to view details</p>
    </div>
  )
}

export default function ProjectScatterPlot<T extends ProjectData>({
  projects,
  onProjectClick,
}: ProjectScatterPlotProps<T>) {
  // Transform data for scatter plot
  // X-axis: Implementation Effort (1=hard, 5=easy) - we'll invert display so left=easy, right=hard
  // Y-axis: ROI Potential (1=low, 5=high)
  const scatterData = projects
    .filter((proj) => proj.roi_potential !== null && proj.implementation_effort !== null)
    .map((proj) => ({
      ...proj,
      // Invert effort so that 5 (easy) appears on the left, 1 (hard) on the right
      x: 6 - (proj.implementation_effort ?? 3),
      y: proj.roi_potential ?? 3,
    }))

  const missingDataCount = projects.length - scatterData.length

  // Count projects in each quadrant
  const quadrantCounts = {
    quickWins: scatterData.filter((d) => d.y > 3 && d.x < 3).length,
    strategicBets: scatterData.filter((d) => d.y > 3 && d.x >= 3).length,
    lowPriority: scatterData.filter((d) => d.y <= 3 && d.x < 3).length,
    questionable: scatterData.filter((d) => d.y <= 3 && d.x >= 3).length,
  }

  if (scatterData.length === 0) {
    return (
      <div className="bg-card border border-default rounded-lg p-8 text-center">
        <Target className="w-12 h-12 text-muted mx-auto mb-4" />
        <h3 className="text-lg font-medium text-primary mb-2">No data to display</h3>
        <p className="text-muted text-sm">
          Opportunities need ROI Potential and Implementation Effort scores to appear on the chart.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Quadrant Legend */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(QUADRANTS).map(([key, config]) => {
          const Icon = config.icon
          const count = quadrantCounts[key as keyof typeof quadrantCounts]
          return (
            <div
              key={key}
              className="bg-card border border-default rounded-lg p-4"
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon className={`w-4 h-4 ${config.color}`} />
                <span className="font-medium text-primary text-sm">{config.label}</span>
              </div>
              <p className="text-xs text-muted mb-2">{config.description}</p>
              <p className="text-2xl font-bold text-primary">{count}</p>
            </div>
          )
        })}
      </div>

      {/* Scatter Plot */}
      <div className="bg-card border border-default rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-primary">ROI vs Effort Matrix</h3>
            <p className="text-sm text-muted">Click any point to view project details</p>
          </div>
          {/* Tier Legend */}
          <div className="flex items-center gap-4">
            {([1, 2, 3, 4] as const).map((tier) => (
              <div key={tier} className="flex items-center gap-1.5">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: TIER_COLORS[tier] }}
                />
                <span className="text-xs text-muted">T{tier}</span>
              </div>
            ))}
          </div>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              className="stroke-gray-200 dark:stroke-gray-700"
            />
            <XAxis
              type="number"
              dataKey="x"
              domain={[0.5, 5.5]}
              ticks={[1, 2, 3, 4, 5]}
              tickFormatter={(value) => {
                const labels: Record<number, string> = {
                  1: 'Easy',
                  2: '',
                  3: 'Medium',
                  4: '',
                  5: 'Hard',
                }
                return labels[value] || ''
              }}
              tick={{ fill: 'currentColor', fontSize: 12 }}
            >
              <Label
                value="Implementation Effort"
                position="bottom"
                offset={20}
                style={{ fill: 'currentColor', fontSize: 12 }}
              />
            </XAxis>
            <YAxis
              type="number"
              dataKey="y"
              domain={[0.5, 5.5]}
              ticks={[1, 2, 3, 4, 5]}
              tickFormatter={(value) => {
                const labels: Record<number, string> = {
                  1: 'Low',
                  2: '',
                  3: 'Med',
                  4: '',
                  5: 'High',
                }
                return labels[value] || ''
              }}
              tick={{ fill: 'currentColor', fontSize: 12 }}
            >
              <Label
                value="ROI Potential"
                angle={-90}
                position="left"
                offset={20}
                style={{ fill: 'currentColor', fontSize: 12 }}
              />
            </YAxis>
            {/* Reference lines to create quadrants */}
            <ReferenceLine
              x={3}
              stroke="#94a3b8"
              strokeDasharray="5 5"
              strokeWidth={1}
            />
            <ReferenceLine
              y={3}
              stroke="#94a3b8"
              strokeDasharray="5 5"
              strokeWidth={1}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ strokeDasharray: '3 3' }}
            />
            <Scatter
              data={scatterData}
              cursor="pointer"
              onClick={(data) => {
                if (data) {
                  // The data includes our extra x/y fields, but the original project is preserved
                  onProjectClick(data as unknown as T)
                }
              }}
            >
              {scatterData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={TIER_COLORS[entry.tier as 1 | 2 | 3 | 4] || TIER_COLORS[4]}
                  fillOpacity={0.8}
                  stroke={TIER_COLORS[entry.tier as 1 | 2 | 3 | 4] || TIER_COLORS[4]}
                  strokeWidth={2}
                  r={8}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>

        {/* Quadrant labels on chart */}
        <div className="grid grid-cols-2 gap-4 mt-4 text-xs text-muted">
          <div className="text-left">
            <span className="text-green-600 font-medium">Quick Wins</span> (top-left)
          </div>
          <div className="text-right">
            <span className="text-blue-600 font-medium">Strategic Bets</span> (top-right)
          </div>
          <div className="text-left">
            <span className="text-slate-500 font-medium">Low Priority</span> (bottom-left)
          </div>
          <div className="text-right">
            <span className="text-amber-600 font-medium">Questionable</span> (bottom-right)
          </div>
        </div>
      </div>

      {/* Missing data warning */}
      {missingDataCount > 0 && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span className="text-amber-700 dark:text-amber-300">
            {missingDataCount} {missingDataCount === 1 ? 'project is' : 'projects are'} missing
            ROI or Effort scores and {missingDataCount === 1 ? "isn't" : "aren't"} shown on the chart.
          </span>
        </div>
      )}
    </div>
  )
}
