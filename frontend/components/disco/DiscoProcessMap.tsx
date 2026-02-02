'use client'

import { useState } from 'react'
import { X } from 'lucide-react'

type ProcessStep = {
  id: string
  title: string
  description: string
  stage: 'discovery' | 'intelligence' | 'synthesis' | 'capabilities'
  details: string[]
  checkpoint?: string
}

const processSteps: ProcessStep[] = [
  // Stage 1: Discovery
  {
    id: 'discovery-guide',
    title: 'Discovery Guide',
    description: 'Validates problem & plans discovery',
    stage: 'discovery',
    details: [
      'Analyzes uploaded documents for key themes',
      'Evaluates opportunity viability (GO/NO-GO)',
      'Creates stakeholder interview guides',
      'Tracks coverage and identifies gaps'
    ],
    checkpoint: 'Checkpoint 1: Discovery Complete'
  },
  // Stage 2: Intelligence
  {
    id: 'insight-analyst',
    title: 'Insight Analyst',
    description: 'Extracts patterns & creates decision doc',
    stage: 'intelligence',
    details: [
      'Analyzes discovery session transcripts',
      'Extracts recurring themes with evidence',
      'Synthesizes insights into cohesive narrative',
      'Creates decision document with recommendations'
    ],
    checkpoint: 'Checkpoint 2: Insights Validated'
  },
  // Stage 3: Synthesis
  {
    id: 'initiative-builder',
    title: 'Initiative Builder',
    description: 'Clusters insights into scored bundles',
    stage: 'synthesis',
    details: [
      'Groups features into coherent initiative bundles',
      'Scores bundles by value and complexity',
      'Provides business rationale for each',
      'Creates bundles for approval workflow'
    ],
    checkpoint: 'Checkpoint 3: Bundles Approved'
  },
  // Stage 4: Capabilities
  {
    id: 'requirements-generator',
    title: 'Requirements Generator',
    description: 'Produces PRD with tech recommendations',
    stage: 'capabilities',
    details: [
      'Generates PRD from approved bundles',
      'Includes user stories and acceptance criteria',
      'Evaluates technical approaches',
      'Documents technical requirements and risks'
    ],
    checkpoint: 'Checkpoint 4: PRD Approved'
  }
]

// Colors by stage
const stageColors = {
  discovery: {
    fill: 'url(#discoveryGradient)',
    stroke: '#3b82f6', // blue
    text: '#3b82f6',
    light: 'rgba(59, 130, 246, 0.15)'
  },
  intelligence: {
    fill: 'url(#intelligenceGradient)',
    stroke: '#06b6d4', // cyan
    text: '#06b6d4',
    light: 'rgba(6, 182, 212, 0.15)'
  },
  synthesis: {
    fill: 'url(#synthesisGradient)',
    stroke: '#22c55e', // green
    text: '#22c55e',
    light: 'rgba(34, 197, 94, 0.15)'
  },
  capabilities: {
    fill: 'url(#capabilitiesGradient)',
    stroke: '#f43f5e', // rose
    text: '#f43f5e',
    light: 'rgba(244, 63, 94, 0.15)'
  }
}

const colors = {
  textPrimary: 'currentColor',
  textSecondary: '#9ca3af',
  arrow: '#60a5fa',
}

export default function DiscoProcessMap() {
  const [selectedStep, setSelectedStep] = useState<ProcessStep | null>(null)

  // Horizontal layout constants - checkpoint beside agent
  const agentX = 30
  const agentWidth = 260
  const agentHeight = 70
  const checkpointX = 320
  const checkpointSize = 55
  const rowSpacing = 100
  const startY = 70

  return (
    <div className="bg-card rounded-lg border border-default p-6">
      {/* SVG Flowchart - Compact Layout */}
      <div className="overflow-x-auto text-primary">
        <svg
          viewBox="0 0 450 580"
          className="w-full max-w-[450px] mx-auto"
          style={{ maxHeight: '580px' }}
        >
          {/* Definitions */}
          <defs>
            {/* Discovery gradient (blue) */}
            <linearGradient id="discoveryGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
            </linearGradient>

            {/* Intelligence gradient (cyan) */}
            <linearGradient id="intelligenceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.1" />
            </linearGradient>

            {/* Synthesis gradient (green) */}
            <linearGradient id="synthesisGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0.1" />
            </linearGradient>

            {/* Capabilities gradient (rose) */}
            <linearGradient id="capabilitiesGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.1" />
            </linearGradient>

            {/* Arrow marker */}
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill={colors.arrow} />
            </marker>
          </defs>

          {/* ===== TITLE ===== */}
          <text x="225" y="25" textAnchor="middle" fill={colors.textPrimary} fontSize="16" fontWeight="700">
            DISCo Workflow
          </text>
          <text x="225" y="42" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
            4 Agents + 4 Human Checkpoints
          </text>

          {/* ===== ROW 1: DISCOVERY GUIDE + CHECKPOINT 1 ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[0])}
          >
            <rect
              x={agentX} y={startY} width={agentWidth} height={agentHeight}
              rx="10"
              fill={stageColors.discovery.fill}
              stroke={stageColors.discovery.stroke}
              strokeWidth="2"
            />
            <text x={agentX + agentWidth/2} y={startY + 18} textAnchor="middle" fill="#3b82f6" fontSize="10" fontWeight="700">
              D: DISCOVERY
            </text>
            <text x={agentX + agentWidth/2} y={startY + 36} textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Discovery Guide
            </text>
            <text x={agentX + agentWidth/2} y={startY + 52} textAnchor="middle" fill={colors.textSecondary} fontSize="9">
              Validates problem, plans sessions
            </text>
          </g>

          {/* Arrow: Agent 1 -> Checkpoint 1 (horizontal) */}
          <path d={`M ${agentX + agentWidth} ${startY + agentHeight/2} L ${checkpointX - 5} ${startY + agentHeight/2}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 1 - Human Review */}
          <g>
            <rect
              x={checkpointX} y={startY + (agentHeight - checkpointSize)/2}
              width={checkpointSize} height={checkpointSize}
              rx="8"
              fill="rgba(100, 116, 139, 0.15)"
              stroke="#64748b"
              strokeWidth="2"
            />
            <g transform={`translate(${checkpointX + 14}, ${startY + (agentHeight - checkpointSize)/2 + 8})`}>
              <circle cx="13" cy="10" r="8" fill="#64748b" />
              <path d="M0 35 Q13 22 26 35" fill="none" stroke="#64748b" strokeWidth="3" strokeLinecap="round" />
            </g>
            <text x={checkpointX + checkpointSize + 8} y={startY + agentHeight/2 + 4} fill="#64748b" fontSize="10" fontWeight="600">
              CP1
            </text>
          </g>

          {/* Arrow: Row 1 -> Row 2 (vertical) */}
          <path d={`M ${agentX + agentWidth/2} ${startY + agentHeight} L ${agentX + agentWidth/2} ${startY + rowSpacing - 5}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== AGENT 2: INSIGHT ANALYST ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[1])}
          >
            <rect
              x={centerX - agentWidth/2} y={80 + rowSpacing*2} width={agentWidth} height={agentHeight}
              rx="12"
              fill={stageColors.intelligence.fill}
              stroke={stageColors.intelligence.stroke}
              strokeWidth="3"
            />
            <text x={centerX} y={80 + rowSpacing*2 + 25} textAnchor="middle" fill="#06b6d4" fontSize="11" fontWeight="700">
              I: INTELLIGENCE
            </text>
            <text x={centerX} y={80 + rowSpacing*2 + 45} textAnchor="middle" fill={colors.textPrimary} fontSize="15" fontWeight="600">
              Insight Analyst
            </text>
            <text x={centerX} y={80 + rowSpacing*2 + 65} textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Extracts patterns, creates decision document
            </text>
          </g>

          {/* Arrow: Agent 2 -> Checkpoint 2 */}
          <path d={`M ${centerX} ${80 + rowSpacing*2 + agentHeight} L ${centerX} ${80 + rowSpacing*2 + agentHeight + 15}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 2 - Human Review */}
          <g>
            <rect
              x={centerX - checkpointSize/2} y={80 + rowSpacing*2 + agentHeight + 20}
              width={checkpointSize} height={checkpointSize}
              rx="10"
              fill="rgba(100, 116, 139, 0.15)"
              stroke="#64748b"
              strokeWidth="2"
            />
            {/* Large person icon */}
            <g transform={`translate(${centerX - 15}, ${80 + rowSpacing*2 + agentHeight + 30})`}>
              <circle cx="15" cy="12" r="10" fill="#64748b" />
              <path d="M0 45 Q15 30 30 45" fill="none" stroke="#64748b" strokeWidth="4" strokeLinecap="round" />
            </g>
            <text x={centerX} y={80 + rowSpacing*2 + agentHeight + 85} textAnchor="middle" fill="#64748b" fontSize="10" fontWeight="600">
              CP 2
            </text>
          </g>

          {/* Arrow: Checkpoint 2 -> Agent 3 */}
          <path d={`M ${centerX} ${80 + rowSpacing*2 + agentHeight + 20 + checkpointSize} L ${centerX} ${80 + rowSpacing*4 - 5}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== AGENT 3: INITIATIVE BUILDER ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[2])}
          >
            <rect
              x={centerX - agentWidth/2} y={80 + rowSpacing*4} width={agentWidth} height={agentHeight}
              rx="12"
              fill={stageColors.synthesis.fill}
              stroke={stageColors.synthesis.stroke}
              strokeWidth="3"
            />
            <text x={centerX} y={80 + rowSpacing*4 + 25} textAnchor="middle" fill="#22c55e" fontSize="11" fontWeight="700">
              S: SYNTHESIS
            </text>
            <text x={centerX} y={80 + rowSpacing*4 + 45} textAnchor="middle" fill={colors.textPrimary} fontSize="15" fontWeight="600">
              Initiative Builder
            </text>
            <text x={centerX} y={80 + rowSpacing*4 + 65} textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Clusters insights into scored bundles
            </text>
          </g>

          {/* Arrow: Agent 3 -> Checkpoint 3 */}
          <path d={`M ${centerX} ${80 + rowSpacing*4 + agentHeight} L ${centerX} ${80 + rowSpacing*4 + agentHeight + 15}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 3 - Human Review */}
          <g>
            <rect
              x={centerX - checkpointSize/2} y={80 + rowSpacing*4 + agentHeight + 20}
              width={checkpointSize} height={checkpointSize}
              rx="10"
              fill="rgba(100, 116, 139, 0.15)"
              stroke="#64748b"
              strokeWidth="2"
            />
            {/* Large person icon */}
            <g transform={`translate(${centerX - 15}, ${80 + rowSpacing*4 + agentHeight + 30})`}>
              <circle cx="15" cy="12" r="10" fill="#64748b" />
              <path d="M0 45 Q15 30 30 45" fill="none" stroke="#64748b" strokeWidth="4" strokeLinecap="round" />
            </g>
            <text x={centerX} y={80 + rowSpacing*4 + agentHeight + 85} textAnchor="middle" fill="#64748b" fontSize="10" fontWeight="600">
              CP 3
            </text>
          </g>

          {/* Arrow: Checkpoint 3 -> Agent 4 */}
          <path d={`M ${centerX} ${80 + rowSpacing*4 + agentHeight + 20 + checkpointSize} L ${centerX} ${80 + rowSpacing*6 - 5}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== AGENT 4: REQUIREMENTS GENERATOR ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[3])}
          >
            <rect
              x={centerX - agentWidth/2} y={80 + rowSpacing*6} width={agentWidth} height={agentHeight}
              rx="12"
              fill={stageColors.capabilities.fill}
              stroke={stageColors.capabilities.stroke}
              strokeWidth="3"
            />
            <text x={centerX} y={80 + rowSpacing*6 + 25} textAnchor="middle" fill="#f43f5e" fontSize="11" fontWeight="700">
              C: CAPABILITIES
            </text>
            <text x={centerX} y={80 + rowSpacing*6 + 45} textAnchor="middle" fill={colors.textPrimary} fontSize="15" fontWeight="600">
              Requirements Generator
            </text>
            <text x={centerX} y={80 + rowSpacing*6 + 65} textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Produces PRD with tech recommendations
            </text>
          </g>

          {/* Arrow: Agent 4 -> Checkpoint 4 */}
          <path d={`M ${centerX} ${80 + rowSpacing*6 + agentHeight} L ${centerX} ${80 + rowSpacing*6 + agentHeight + 15}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 4 - Human Review */}
          <g>
            <rect
              x={centerX - checkpointSize/2} y={80 + rowSpacing*6 + agentHeight + 20}
              width={checkpointSize} height={checkpointSize}
              rx="10"
              fill="rgba(100, 116, 139, 0.15)"
              stroke="#64748b"
              strokeWidth="2"
            />
            {/* Large person icon */}
            <g transform={`translate(${centerX - 15}, ${80 + rowSpacing*6 + agentHeight + 30})`}>
              <circle cx="15" cy="12" r="10" fill="#64748b" />
              <path d="M0 45 Q15 30 30 45" fill="none" stroke="#64748b" strokeWidth="4" strokeLinecap="round" />
            </g>
            <text x={centerX} y={80 + rowSpacing*6 + agentHeight + 85} textAnchor="middle" fill="#64748b" fontSize="10" fontWeight="600">
              CP 4
            </text>
          </g>

          {/* Arrow: Checkpoint 4 -> PRD Output */}
          <path d={`M ${centerX} ${80 + rowSpacing*6 + agentHeight + 20 + checkpointSize} L ${centerX} ${80 + rowSpacing*8 - 5}`} fill="none" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Final Output: PRD */}
          <g>
            <rect
              x={centerX - agentWidth/2} y={80 + rowSpacing*8}
              width={agentWidth} height="60"
              rx="12"
              fill="rgba(34, 197, 94, 0.2)"
              stroke="#22c55e"
              strokeWidth="3"
            />
            <text x={centerX} y={80 + rowSpacing*8 + 28} textAnchor="middle" fill="#22c55e" fontSize="16" fontWeight="700">
              PRD Document
            </text>
            <text x={centerX} y={80 + rowSpacing*8 + 48} textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Complete spec ready for development
            </text>
          </g>

          {/* ===== LEGEND (bottom) ===== */}
          <g transform="translate(60, 960)">
            <rect x="0" y="-12" width="16" height="16" rx="4" fill="rgba(100, 116, 139, 0.15)" stroke="#64748b" strokeWidth="2" />
            <text x="24" y="2" fill={colors.textSecondary} fontSize="11">= Human checkpoint (approval required)</text>

            <text x="280" y="2" fill={colors.textSecondary} fontSize="11">Click agents for details</text>
          </g>
        </svg>
      </div>

      {/* Details Panel */}
      {selectedStep && (
        <div className="mt-6 p-4 bg-hover rounded-lg border border-default">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-primary">{selectedStep.title}</h3>
                <span
                  className="px-2 py-0.5 rounded text-xs font-medium"
                  style={{
                    backgroundColor: stageColors[selectedStep.stage].light,
                    color: stageColors[selectedStep.stage].text
                  }}
                >
                  {selectedStep.stage.charAt(0).toUpperCase() + selectedStep.stage.slice(1)}
                </span>
              </div>
              <p className="text-sm text-secondary mt-1">{selectedStep.description}</p>
            </div>
            <button
              onClick={() => setSelectedStep(null)}
              className="text-muted hover:text-primary"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <ul className="mt-3 space-y-1">
            {selectedStep.details.map((detail, index) => (
              <li key={index} className="text-sm text-secondary flex items-start">
                <span className="mr-2" style={{ color: stageColors[selectedStep.stage].text }}>-</span>
                {detail}
              </li>
            ))}
          </ul>
          {selectedStep.checkpoint && (
            <div className="mt-3 pt-3 border-t border-default">
              <p className="text-xs text-muted flex items-center gap-2">
                <span className="inline-block w-3 h-3 border-2 border-slate-400 rounded-sm" />
                {selectedStep.checkpoint}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
