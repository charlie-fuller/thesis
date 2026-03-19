'use client'

import { useState, useMemo } from 'react'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { PortfolioProject } from './PortfolioContent'

interface PortfolioScatterPlotProps {
  projects: PortfolioProject[]
}

type AxisField = 'effort' | 'business_value' | 'investment'

const AXIS_OPTIONS: { value: AxisField; label: string }[] = [
  { value: 'effort', label: 'Effort' },
  { value: 'business_value', label: 'Business Value' },
  { value: 'investment', label: 'Investment' },
]

// Numeric mappings for ordinal values
const EFFORT_MAP: Record<string, number> = {
  low: 1,
  medium: 2,
  high: 3,
}

const BUSINESS_VALUE_MAP: Record<string, number> = {
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
}

const INVESTMENT_MAP: Record<string, number> = {
  '0-1k': 1,
  '1k-5k': 2,
  '5k-15k': 3,
  '15k-25k': 4,
  '25k+': 5,
}

// Tick label configs per axis field
const TICK_CONFIG: Record<AxisField, { domain: [number, number]; ticks: number[]; labels: Record<number, string> }> = {
  effort: {
    domain: [0.5, 3.5],
    ticks: [1, 2, 3],
    labels: { 1: 'Low', 2: 'Medium', 3: 'High' },
  },
  business_value: {
    domain: [0.5, 4.5],
    ticks: [1, 2, 3, 4],
    labels: { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical' },
  },
  investment: {
    domain: [0.5, 5.5],
    ticks: [1, 2, 3, 4, 5],
    labels: { 1: '0-1k', 2: '1k-5k', 3: '5k-15k', 4: '15k-25k', 5: '25k+' },
  },
}

// Department color palette -- 12 distinct colors
const DEPARTMENT_COLORS = [
  '#2563eb', // blue-600
  '#dc2626', // red-600
  '#16a34a', // green-600
  '#d97706', // amber-600
  '#9333ea', // purple-600
  '#0891b2', // cyan-600
  '#e11d48', // rose-600
  '#65a30d', // lime-600
  '#c026d3', // fuchsia-600
  '#ea580c', // orange-600
  '#0d9488', // teal-600
  '#4f46e5', // indigo-600
]

function getNumericValue(field: AxisField, rawValue: string | null): number | null {
  if (!rawValue) return null
  const normalized = rawValue.toLowerCase().trim()
  switch (field) {
    case 'effort':
      return EFFORT_MAP[normalized] ?? null
    case 'business_value':
      return BUSINESS_VALUE_MAP[normalized] ?? null
    case 'investment':
      return INVESTMENT_MAP[normalized] ?? null
    default:
      return null
  }
}

interface ScatterDataPoint {
  x: number
  y: number
  project: PortfolioProject
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    payload: ScatterDataPoint
  }>
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null

  const data = payload[0].payload.project

  const formatValue = (val: string | null) => {
    if (!val) return 'N/A'
    return val.charAt(0).toUpperCase() + val.slice(1)
  }

  return (
    <div className="bg-card border border-default rounded-lg shadow-lg p-3 max-w-xs">
      <p className="font-medium text-primary text-sm mb-2">{data.name}</p>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-muted">Department:</span>
          <span className="ml-1 font-medium text-primary">{data.department}</span>
        </div>
        {data.owner && (
          <div>
            <span className="text-muted">Owner:</span>
            <span className="ml-1 font-medium text-primary">{data.owner}</span>
          </div>
        )}
        <div>
          <span className="text-muted">Status:</span>
          <span className="ml-1 font-medium text-primary">
            {data.status === 'in_progress' ? 'In Progress' : formatValue(data.status)}
          </span>
        </div>
        <div>
          <span className="text-muted">Effort:</span>
          <span className="ml-1 font-medium text-primary">{formatValue(data.effort)}</span>
        </div>
        <div>
          <span className="text-muted">Value:</span>
          <span className="ml-1 font-medium text-primary">{formatValue(data.business_value)}</span>
        </div>
        <div>
          <span className="text-muted">Investment:</span>
          <span className="ml-1 font-medium text-primary">{data.investment ?? 'N/A'}</span>
        </div>
      </div>
    </div>
  )
}

export default function PortfolioScatterPlot({ projects }: PortfolioScatterPlotProps) {
  const [xAxis, setXAxis] = useState<AxisField>('effort')
  const [yAxis, setYAxis] = useState<AxisField>('business_value')

  // Build department -> color map
  const departmentColorMap = useMemo(() => {
    const depts = [...new Set(projects.map((p) => p.department).filter(Boolean))].sort()
    const map: Record<string, string> = {}
    depts.forEach((dept, i) => {
      map[dept] = DEPARTMENT_COLORS[i % DEPARTMENT_COLORS.length]
    })
    return map
  }, [projects])

  // Transform data for scatter plot
  const scatterData = useMemo(() => {
    const points: ScatterDataPoint[] = []
    for (const project of projects) {
      const xVal = getNumericValue(xAxis, project[xAxis])
      const yVal = getNumericValue(yAxis, project[yAxis])
      if (xVal !== null && yVal !== null) {
        points.push({ x: xVal, y: yVal, project })
      }
    }
    return points
  }, [projects, xAxis, yAxis])

  const xConfig = TICK_CONFIG[xAxis]
  const yConfig = TICK_CONFIG[yAxis]

  const xLabel = AXIS_OPTIONS.find((o) => o.value === xAxis)?.label ?? ''
  const yLabel = AXIS_OPTIONS.find((o) => o.value === yAxis)?.label ?? ''

  if (scatterData.length === 0) {
    return (
      <div className="bg-card border border-default rounded-lg p-6">
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-muted uppercase tracking-wider">X-Axis</label>
            <select
              value={xAxis}
              onChange={(e) => setXAxis(e.target.value as AxisField)}
              className="bg-card border border-default rounded-lg px-2 py-1 text-sm text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {AXIS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-muted uppercase tracking-wider">Y-Axis</label>
            <select
              value={yAxis}
              onChange={(e) => setYAxis(e.target.value as AxisField)}
              className="bg-card border border-default rounded-lg px-2 py-1 text-sm text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {AXIS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="py-12 text-center">
          <h3 className="text-lg font-medium text-primary mb-2">No data to display</h3>
          <p className="text-muted text-sm">
            No projects have values for both {xLabel} and {yLabel}.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card border border-default rounded-lg p-6">
      {/* Axis selectors and legend */}
      <div className="flex flex-wrap items-center gap-4 mb-4">
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-muted uppercase tracking-wider">X-Axis</label>
          <select
            value={xAxis}
            onChange={(e) => setXAxis(e.target.value as AxisField)}
            className="bg-card border border-default rounded-lg px-2 py-1 text-sm text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {AXIS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-muted uppercase tracking-wider">Y-Axis</label>
          <select
            value={yAxis}
            onChange={(e) => setYAxis(e.target.value as AxisField)}
            className="bg-card border border-default rounded-lg px-2 py-1 text-sm text-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {AXIS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Department color legend */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {Object.entries(departmentColorMap).map(([dept, color]) => (
          <div key={dept} className="flex items-center gap-1.5">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-xs text-muted">{dept}</span>
          </div>
        ))}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            className="stroke-gray-200 dark:stroke-gray-700"
          />
          <XAxis
            type="number"
            dataKey="x"
            domain={xConfig.domain}
            ticks={xConfig.ticks}
            tickFormatter={(value: number) => xConfig.labels[value] || ''}
            tick={{ fill: 'currentColor', fontSize: 12 }}
            label={{
              value: xLabel,
              position: 'bottom',
              offset: 20,
              style: { fill: 'currentColor', fontSize: 12 },
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={yConfig.domain}
            ticks={yConfig.ticks}
            tickFormatter={(value: number) => yConfig.labels[value] || ''}
            tick={{ fill: 'currentColor', fontSize: 12 }}
            label={{
              value: yLabel,
              angle: -90,
              position: 'left',
              offset: 20,
              style: { fill: 'currentColor', fontSize: 12 },
            }}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ strokeDasharray: '3 3' }}
          />
          <Scatter data={scatterData}>
            {scatterData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={departmentColorMap[entry.project.department] || '#64748b'}
                fillOpacity={0.8}
                stroke={departmentColorMap[entry.project.department] || '#64748b'}
                strokeWidth={2}
                r={8}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}
