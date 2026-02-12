'use client'

import { useState } from 'react'
import { X } from 'lucide-react'

type ProcessStep = {
  id: string
  title: string
  description: string
  stage: 'discovery' | 'intelligence' | 'synthesis' | 'convergence'
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
    description: 'Clusters insights into scored proposed initiatives',
    stage: 'synthesis',
    details: [
      'Groups features into coherent proposed initiatives',
      'Scores proposed initiatives by value and complexity',
      'Provides business rationale for each',
      'Creates proposed initiatives for approval workflow'
    ],
    checkpoint: 'Checkpoint 3: Proposed Initiatives Approved'
  },
  // Stage 4: Convergence
  {
    id: 'requirements-generator',
    title: 'Requirements Generator',
    description: 'Generates output document from proposed initiative',
    stage: 'convergence',
    details: [
      'User selects output type: PRD, Evaluation, or Decision Framework',
      'PRD: For build/development proposed initiatives',
      'Evaluation: For vendor/tool comparisons',
      'Decision: For governance/policy decisions'
    ],
    checkpoint: 'Checkpoint 4: Document Approved'
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
  convergence: {
    fill: 'url(#convergenceGradient)',
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
  const rowSpacing = 120
  const startY = 70

  return (
    <div className="bg-card rounded-lg border border-default p-6">
      {/* Two-column layout: Map on left (2/3), Details on right (1/3) */}
      <div className="flex gap-6">
        {/* Left: SVG Flowchart - enlarged by 20% */}
        <div className="flex-[2] text-primary">
          <svg
            viewBox="0 0 450 670"
            className="w-full max-w-[600px]"
            style={{ maxHeight: '800px' }}
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

            {/* Convergence gradient (rose) */}
            <linearGradient id="convergenceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
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

          {/* ===== TITLE - centered over workflow content ===== */}
          <text x="200" y="28" textAnchor="middle" fill={colors.textPrimary} fontSize="22" fontWeight="700">
            DISCO Workflow
          </text>
          <text x="200" y="48" textAnchor="middle" fill={colors.textSecondary} fontSize="14" fontWeight="500">
            Click agents for details
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
            <text x={checkpointX + checkpointSize + 8} y={startY + agentHeight/2 - 4} fill="#64748b" fontSize="9" fontWeight="500">
              Human
            </text>
            <text x={checkpointX + checkpointSize + 8} y={startY + agentHeight/2 + 8} fill="#64748b" fontSize="9" fontWeight="600">
              Checkpoint
            </text>
          </g>

          {/* Arrow: Checkpoint 1 -> Agent 2 (from checkpoint down to next agent) */}
          <path d={`M ${checkpointX + checkpointSize/2} ${startY + (agentHeight - checkpointSize)/2 + checkpointSize} L ${checkpointX + checkpointSize/2} ${startY + rowSpacing - 15} L ${agentX + agentWidth/2} ${startY + rowSpacing - 15} L ${agentX + agentWidth/2} ${startY + rowSpacing - 5}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== ROW 2: INSIGHT ANALYST + CHECKPOINT 2 ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[1])}
          >
            <rect
              x={agentX} y={startY + rowSpacing} width={agentWidth} height={agentHeight}
              rx="10"
              fill={stageColors.intelligence.fill}
              stroke={stageColors.intelligence.stroke}
              strokeWidth="2"
            />
            <text x={agentX + agentWidth/2} y={startY + rowSpacing + 18} textAnchor="middle" fill="#06b6d4" fontSize="10" fontWeight="700">
              I: INTELLIGENCE
            </text>
            <text x={agentX + agentWidth/2} y={startY + rowSpacing + 36} textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Insight Analyst
            </text>
            <text x={agentX + agentWidth/2} y={startY + rowSpacing + 52} textAnchor="middle" fill={colors.textSecondary} fontSize="9">
              Extracts patterns, creates decision doc
            </text>
          </g>

          {/* Arrow: Agent 2 -> Checkpoint 2 (horizontal) */}
          <path d={`M ${agentX + agentWidth} ${startY + rowSpacing + agentHeight/2} L ${checkpointX - 5} ${startY + rowSpacing + agentHeight/2}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 2 - Human Review */}
          <g>
            <rect
              x={checkpointX} y={startY + rowSpacing + (agentHeight - checkpointSize)/2}
              width={checkpointSize} height={checkpointSize}
              rx="8"
              fill="rgba(100, 116, 139, 0.15)"
              stroke="#64748b"
              strokeWidth="2"
            />
            <g transform={`translate(${checkpointX + 14}, ${startY + rowSpacing + (agentHeight - checkpointSize)/2 + 8})`}>
              <circle cx="13" cy="10" r="8" fill="#64748b" />
              <path d="M0 35 Q13 22 26 35" fill="none" stroke="#64748b" strokeWidth="3" strokeLinecap="round" />
            </g>
            <text x={checkpointX + checkpointSize + 8} y={startY + rowSpacing + agentHeight/2 - 4} fill="#64748b" fontSize="9" fontWeight="500">
              Human
            </text>
            <text x={checkpointX + checkpointSize + 8} y={startY + rowSpacing + agentHeight/2 + 8} fill="#64748b" fontSize="9" fontWeight="600">
              Checkpoint
            </text>
          </g>

          {/* Arrow: Checkpoint 2 -> Agent 3 (from checkpoint down to next agent) */}
          <path d={`M ${checkpointX + checkpointSize/2} ${startY + rowSpacing + (agentHeight - checkpointSize)/2 + checkpointSize} L ${checkpointX + checkpointSize/2} ${startY + rowSpacing*2 - 15} L ${agentX + agentWidth/2} ${startY + rowSpacing*2 - 15} L ${agentX + agentWidth/2} ${startY + rowSpacing*2 - 5}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== ROW 3: INITIATIVE BUILDER + CHECKPOINT 3 ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[2])}
          >
            <rect
              x={agentX} y={startY + rowSpacing*2} width={agentWidth} height={agentHeight}
              rx="10"
              fill={stageColors.synthesis.fill}
              stroke={stageColors.synthesis.stroke}
              strokeWidth="2"
            />
            <text x={agentX + agentWidth/2} y={startY + rowSpacing*2 + 18} textAnchor="middle" fill="#22c55e" fontSize="10" fontWeight="700">
              S: SYNTHESIS
            </text>
            <text x={agentX + agentWidth/2} y={startY + rowSpacing*2 + 36} textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Initiative Builder
            </text>
            <text x={agentX + agentWidth/2} y={startY + rowSpacing*2 + 52} textAnchor="middle" fill={colors.textSecondary} fontSize="9">
              Clusters insights into proposed initiatives
            </text>
          </g>

          {/* Arrow: Agent 3 -> Checkpoint 3 (horizontal) */}
          <path d={`M ${agentX + agentWidth} ${startY + rowSpacing*2 + agentHeight/2} L ${checkpointX - 5} ${startY + rowSpacing*2 + agentHeight/2}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 3 - Human Review */}
          <g>
            <rect
              x={checkpointX} y={startY + rowSpacing*2 + (agentHeight - checkpointSize)/2}
              width={checkpointSize} height={checkpointSize}
              rx="8"
              fill="rgba(100, 116, 139, 0.15)"
              stroke="#64748b"
              strokeWidth="2"
            />
            <g transform={`translate(${checkpointX + 14}, ${startY + rowSpacing*2 + (agentHeight - checkpointSize)/2 + 8})`}>
              <circle cx="13" cy="10" r="8" fill="#64748b" />
              <path d="M0 35 Q13 22 26 35" fill="none" stroke="#64748b" strokeWidth="3" strokeLinecap="round" />
            </g>
            <text x={checkpointX + checkpointSize + 8} y={startY + rowSpacing*2 + agentHeight/2 - 4} fill="#64748b" fontSize="9" fontWeight="500">
              Human
            </text>
            <text x={checkpointX + checkpointSize + 8} y={startY + rowSpacing*2 + agentHeight/2 + 8} fill="#64748b" fontSize="9" fontWeight="600">
              Checkpoint
            </text>
          </g>

          {/* Arrow: Checkpoint 3 -> Agent 4 (from checkpoint down to next agent) */}
          <path d={`M ${checkpointX + checkpointSize/2} ${startY + rowSpacing*2 + (agentHeight - checkpointSize)/2 + checkpointSize} L ${checkpointX + checkpointSize/2} ${startY + rowSpacing*3 - 15} L ${agentX + agentWidth/2} ${startY + rowSpacing*3 - 15} L ${agentX + agentWidth/2} ${startY + rowSpacing*3 - 5}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== ROW 4: REQUIREMENTS GENERATOR + CHECKPOINT 4 ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[3])}
          >
            <rect
              x={agentX} y={startY + rowSpacing*3} width={agentWidth} height={agentHeight}
              rx="10"
              fill={stageColors.convergence.fill}
              stroke={stageColors.convergence.stroke}
              strokeWidth="2"
            />
            <text x={agentX + agentWidth/2} y={startY + rowSpacing*3 + 18} textAnchor="middle" fill="#f43f5e" fontSize="10" fontWeight="700">
              C: CONVERGENCE
            </text>
            <text x={agentX + agentWidth/2} y={startY + rowSpacing*3 + 36} textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Requirements Generator
            </text>
            <text x={agentX + agentWidth/2} y={startY + rowSpacing*3 + 52} textAnchor="middle" fill={colors.textSecondary} fontSize="9">
              PRD / Evaluation / Decision output
            </text>
          </g>

          {/* Arrow: Agent 4 -> Checkpoint 4 (horizontal) */}
          <path d={`M ${agentX + agentWidth} ${startY + rowSpacing*3 + agentHeight/2} L ${checkpointX - 5} ${startY + rowSpacing*3 + agentHeight/2}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 4 - Human Review */}
          <g>
            <rect
              x={checkpointX} y={startY + rowSpacing*3 + (agentHeight - checkpointSize)/2}
              width={checkpointSize} height={checkpointSize}
              rx="8"
              fill="rgba(100, 116, 139, 0.15)"
              stroke="#64748b"
              strokeWidth="2"
            />
            <g transform={`translate(${checkpointX + 14}, ${startY + rowSpacing*3 + (agentHeight - checkpointSize)/2 + 8})`}>
              <circle cx="13" cy="10" r="8" fill="#64748b" />
              <path d="M0 35 Q13 22 26 35" fill="none" stroke="#64748b" strokeWidth="3" strokeLinecap="round" />
            </g>
            <text x={checkpointX + checkpointSize + 8} y={startY + rowSpacing*3 + agentHeight/2 - 4} fill="#64748b" fontSize="9" fontWeight="500">
              Human
            </text>
            <text x={checkpointX + checkpointSize + 8} y={startY + rowSpacing*3 + agentHeight/2 + 8} fill="#64748b" fontSize="9" fontWeight="600">
              Checkpoint
            </text>
          </g>

          {/* Arrow: Checkpoint 4 -> PRD Output (from checkpoint down to PRD) */}
          <path d={`M ${checkpointX + checkpointSize/2} ${startY + rowSpacing*3 + (agentHeight - checkpointSize)/2 + checkpointSize} L ${checkpointX + checkpointSize/2} ${startY + rowSpacing*4 - 15} L ${agentX + agentWidth/2} ${startY + rowSpacing*4 - 15} L ${agentX + agentWidth/2} ${startY + rowSpacing*4 - 5}`} fill="none" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Final Output: Approved Documents - matches Operationalize Map entry */}
          <text x={agentX + agentWidth/2} y={startY + rowSpacing*4 + 5} textAnchor="middle" fill={colors.textSecondary} fontSize="9" fontWeight="600">
            APPROVED DOCUMENT
          </text>

          {/* Three document type boxes - matching Operationalize Map colors */}
          {/* PRD - violet */}
          <g>
            <rect
              x={agentX} y={startY + rowSpacing*4 + 12}
              width="80" height="35"
              rx="6"
              fill="rgba(139, 92, 246, 0.15)"
              stroke="#8b5cf6"
              strokeWidth="1.5"
              strokeDasharray="4 2"
            />
            <text x={agentX + 40} y={startY + rowSpacing*4 + 28} textAnchor="middle" fill="#8b5cf6" fontSize="9" fontWeight="600">
              PRD
            </text>
            <text x={agentX + 40} y={startY + rowSpacing*4 + 40} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
              Build/Dev
            </text>
          </g>

          {/* Evaluation - cyan */}
          <g>
            <rect
              x={agentX + 90} y={startY + rowSpacing*4 + 12}
              width="80" height="35"
              rx="6"
              fill="rgba(6, 182, 212, 0.15)"
              stroke="#06b6d4"
              strokeWidth="1.5"
              strokeDasharray="4 2"
            />
            <text x={agentX + 130} y={startY + rowSpacing*4 + 28} textAnchor="middle" fill="#06b6d4" fontSize="9" fontWeight="600">
              Evaluation
            </text>
            <text x={agentX + 130} y={startY + rowSpacing*4 + 40} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
              Compare
            </text>
          </g>

          {/* Decision - amber */}
          <g>
            <rect
              x={agentX + 180} y={startY + rowSpacing*4 + 12}
              width="80" height="35"
              rx="6"
              fill="rgba(245, 158, 11, 0.15)"
              stroke="#f59e0b"
              strokeWidth="1.5"
              strokeDasharray="4 2"
            />
            <text x={agentX + 220} y={startY + rowSpacing*4 + 28} textAnchor="middle" fill="#f59e0b" fontSize="9" fontWeight="600">
              Decision
            </text>
            <text x={agentX + 220} y={startY + rowSpacing*4 + 40} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
              Govern
            </text>
          </g>

          {/* Pointer to Operationalize Map */}
          <text x={agentX + agentWidth/2} y={startY + rowSpacing*4 + 62} textAnchor="middle" fill="#f97316" fontSize="9" fontWeight="500">
            See Operationalize Map tab →
          </text>

        </svg>
      </div>

        {/* Right: Details Panel - larger default, centered, color matches stage */}
        <div className="flex-1 w-[380px] max-w-[415px] mx-auto">
          {selectedStep ? (
            <div
              className="p-4 rounded-lg border-2 h-full flex flex-col justify-center"
              style={{
                backgroundColor: stageColors[selectedStep.stage].light,
                borderColor: stageColors[selectedStep.stage].stroke
              }}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-primary">{selectedStep.title}</h3>
                    <span
                      className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{
                        backgroundColor: stageColors[selectedStep.stage].light,
                        color: stageColors[selectedStep.stage].text,
                        border: `1px solid ${stageColors[selectedStep.stage].stroke}`
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
              <ul className="mt-4 space-y-2">
                {selectedStep.details.map((detail, index) => (
                  <li key={index} className="text-sm text-secondary flex items-start">
                    <span className="mr-2 mt-0.5" style={{ color: stageColors[selectedStep.stage].text }}>-</span>
                    {detail}
                  </li>
                ))}
              </ul>
              {selectedStep.checkpoint && (
                <div className="mt-4 pt-4 border-t border-default">
                  <p className="text-sm text-muted flex items-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-slate-400 rounded" />
                    {selectedStep.checkpoint}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 bg-hover rounded-lg border border-default border-dashed h-full flex items-center justify-center">
              <p className="text-sm text-muted text-center">
                Click an agent in the workflow<br />to see details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
