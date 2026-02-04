'use client'

import { useState } from 'react'
import { X } from 'lucide-react'

type OutputStep = {
  id: string
  title: string
  description: string
  category: 'output' | 'post-process' | 'destination'
  details: string[]
  color: string
}

const outputSteps: OutputStep[] = [
  // Output Types
  {
    id: 'prd',
    title: 'PRD',
    description: 'Product Requirements Document',
    category: 'output',
    color: '#8b5cf6', // violet
    details: [
      'Best for: Build/development initiatives',
      'Executive Summary & Problem Statement',
      'Goals, Requirements, User Stories',
      'Technical Considerations & Risks',
      'Acceptance Criteria'
    ]
  },
  {
    id: 'evaluation',
    title: 'Evaluation Framework',
    description: 'Vendor/Platform Comparison',
    category: 'output',
    color: '#06b6d4', // cyan
    details: [
      'Best for: Tool selection, vendor comparison',
      'Evaluation Scope & Criteria',
      'Weighted Scoring Matrix',
      'Platform Comparison Table',
      'Recommendation & Next Steps'
    ]
  },
  {
    id: 'decision',
    title: 'Decision Framework',
    description: 'Governance & Strategy',
    category: 'output',
    color: '#f59e0b', // amber
    details: [
      'Best for: Policy, strategy, governance',
      'Decision Context & Stakeholder Analysis',
      'Decision Criteria & Options Analysis',
      'Risk/Benefit Assessment',
      'Implementation Considerations'
    ]
  },
  // Post-Processing
  {
    id: 'project-extract',
    title: 'Project Extraction',
    description: 'AI extracts project fields from PRD',
    category: 'post-process',
    color: '#22c55e', // green
    details: [
      'Auto-extracts: Title, Description, Department',
      'Scores: ROI, Effort, Strategic Alignment',
      'Generates initial task list',
      'Links back to source initiative',
      'Sets project status to "identified"'
    ]
  },
  {
    id: 'exec-summary',
    title: 'Executive Summary',
    description: 'Multi-bundle leadership overview',
    category: 'post-process',
    color: '#ec4899', // pink
    details: [
      'Summarizes all approved bundles',
      'Provides prioritization recommendations',
      'Strategic alignment overview',
      'Resource & timeline considerations',
      'Leadership-ready format'
    ]
  },
  {
    id: 'kb-integration',
    title: 'KB Integration',
    description: 'Promote to Knowledge Base',
    category: 'post-process',
    color: '#3b82f6', // blue
    details: [
      'Output becomes searchable document',
      'Available via initiative chat Q&A',
      'RAG-enabled for future queries',
      'Full traceability maintained',
      'Cross-initiative discovery'
    ]
  },
  // Destinations
  {
    id: 'projects',
    title: 'Projects Pipeline',
    description: 'Kanban board for execution',
    category: 'destination',
    color: '#22c55e', // green
    details: [
      'Status: Identified → Scoping → Active → Complete',
      'Linked to source DISCO initiative',
      'Task management & assignment',
      'Progress tracking & reporting',
      'Stakeholder visibility'
    ]
  },
  {
    id: 'export',
    title: 'External Export',
    description: 'Send to external systems',
    category: 'destination',
    color: '#64748b', // slate
    details: [
      'Document status → "exported"',
      'Jira, Confluence, Notion integration',
      'PDF/Markdown download',
      'API webhook triggers',
      'Audit trail maintained'
    ]
  }
]

// Colors by category
const categoryColors = {
  output: {
    fill: 'rgba(139, 92, 246, 0.15)',
    stroke: '#8b5cf6',
    text: '#8b5cf6',
    label: 'Output Types'
  },
  'post-process': {
    fill: 'rgba(34, 197, 94, 0.15)',
    stroke: '#22c55e',
    text: '#22c55e',
    label: 'Post-Processing'
  },
  destination: {
    fill: 'rgba(100, 116, 139, 0.15)',
    stroke: '#64748b',
    text: '#64748b',
    label: 'Destinations'
  }
}

const colors = {
  textPrimary: 'currentColor',
  textSecondary: '#9ca3af',
  arrow: '#60a5fa',
}

export default function DiscoOperationalizeMap() {
  const [selectedStep, setSelectedStep] = useState<OutputStep | null>(null)

  // Layout constants
  const boxWidth = 120
  const boxHeight = 60
  const startY = 80

  return (
    <div className="bg-card rounded-lg border border-default p-6">
      {/* Two-column layout: Map on left (2/3), Details on right (1/3) */}
      <div className="flex gap-6">
        {/* Left: SVG Flowchart */}
        <div className="flex-[2] text-primary">
          <svg
            viewBox="0 0 500 520"
            className="w-full max-w-[650px]"
            style={{ maxHeight: '650px' }}
          >
            {/* Definitions */}
            <defs>
              {/* Arrow marker */}
              <marker
                id="arrowhead-op"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill={colors.arrow} />
              </marker>
              {/* Green arrow marker */}
              <marker
                id="arrowhead-green"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#22c55e" />
              </marker>
            </defs>

            {/* Title */}
            <text x="250" y="28" textAnchor="middle" fill={colors.textPrimary} fontSize="22" fontWeight="700">
              Operationalize Map
            </text>
            <text x="250" y="48" textAnchor="middle" fill={colors.textSecondary} fontSize="14" fontWeight="500">
              Exit paths from DISCO Convergence
            </text>

            {/* ===== ROW 1: APPROVED BUNDLE (Entry Point) ===== */}
            <g>
              <rect
                x={190} y={startY}
                width={boxWidth} height={boxHeight}
                rx="8"
                fill="rgba(249, 115, 22, 0.2)"
                stroke="#f97316"
                strokeWidth="2"
              />
              <text x={250} y={startY + 22} textAnchor="middle" fill="#f97316" fontSize="9" fontWeight="700">
                FROM CONVERGENCE
              </text>
              <text x={250} y={startY + 38} textAnchor="middle" fill={colors.textPrimary} fontSize="11" fontWeight="600">
                Approved Bundle
              </text>
              <text x={250} y={startY + 52} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Select output type
              </text>
            </g>

            {/* Arrows from bundle to 3 output types */}
            <path d={`M 190 ${startY + boxHeight/2} L 80 ${startY + boxHeight/2} L 80 ${startY + 95}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead-op)" />
            <path d={`M 250 ${startY + boxHeight} L 250 ${startY + 95}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead-op)" />
            <path d={`M 310 ${startY + boxHeight/2} L 420 ${startY + boxHeight/2} L 420 ${startY + 95}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead-op)" />

            {/* ===== ROW 2: THREE OUTPUT TYPES ===== */}
            {/* PRD */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[0])}
            >
              <rect
                x={20} y={startY + 100}
                width={boxWidth} height={boxHeight + 10}
                rx="8"
                fill="rgba(139, 92, 246, 0.15)"
                stroke="#8b5cf6"
                strokeWidth="2"
              />
              <text x={80} y={startY + 118} textAnchor="middle" fill="#8b5cf6" fontSize="9" fontWeight="700">
                BUILD/DEV
              </text>
              <text x={80} y={startY + 136} textAnchor="middle" fill={colors.textPrimary} fontSize="12" fontWeight="600">
                PRD
              </text>
              <text x={80} y={startY + 150} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Product Requirements
              </text>
              <text x={80} y={startY + 162} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Document
              </text>
            </g>

            {/* Evaluation Framework */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[1])}
            >
              <rect
                x={190} y={startY + 100}
                width={boxWidth} height={boxHeight + 10}
                rx="8"
                fill="rgba(6, 182, 212, 0.15)"
                stroke="#06b6d4"
                strokeWidth="2"
              />
              <text x={250} y={startY + 118} textAnchor="middle" fill="#06b6d4" fontSize="9" fontWeight="700">
                COMPARE
              </text>
              <text x={250} y={startY + 136} textAnchor="middle" fill={colors.textPrimary} fontSize="12" fontWeight="600">
                Evaluation
              </text>
              <text x={250} y={startY + 150} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Framework
              </text>
              <text x={250} y={startY + 162} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                (Vendor/Tool)
              </text>
            </g>

            {/* Decision Framework */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[2])}
            >
              <rect
                x={360} y={startY + 100}
                width={boxWidth} height={boxHeight + 10}
                rx="8"
                fill="rgba(245, 158, 11, 0.15)"
                stroke="#f59e0b"
                strokeWidth="2"
              />
              <text x={420} y={startY + 118} textAnchor="middle" fill="#f59e0b" fontSize="9" fontWeight="700">
                GOVERN
              </text>
              <text x={420} y={startY + 136} textAnchor="middle" fill={colors.textPrimary} fontSize="12" fontWeight="600">
                Decision
              </text>
              <text x={420} y={startY + 150} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Framework
              </text>
              <text x={420} y={startY + 162} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                (Policy/Strategy)
              </text>
            </g>

            {/* Human Checkpoint - Document Review */}
            <g>
              <rect
                x={190} y={startY + 195}
                width={boxWidth} height={50}
                rx="8"
                fill="rgba(100, 116, 139, 0.15)"
                stroke="#64748b"
                strokeWidth="2"
              />
              <g transform={`translate(${202}, ${startY + 203})`}>
                <circle cx="10" cy="8" r="6" fill="#64748b" />
                <path d="M0 26 Q10 16 20 26" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
              </g>
              <text x={260} y={startY + 218} textAnchor="start" fill="#64748b" fontSize="9" fontWeight="600">
                Human Review
              </text>
              <text x={260} y={startY + 232} textAnchor="start" fill={colors.textSecondary} fontSize="8">
                Approve / Edit
              </text>
            </g>

            {/* Arrows from outputs to checkpoint */}
            <path d={`M 80 ${startY + 170} L 80 ${startY + 220} L 185 ${startY + 220}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead-op)" />
            <path d={`M 250 ${startY + 170} L 250 ${startY + 190}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead-op)" />
            <path d={`M 420 ${startY + 170} L 420 ${startY + 220} L 315 ${startY + 220}`} fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead-op)" />

            {/* Arrow from checkpoint to post-processing */}
            <path d={`M 250 ${startY + 245} L 250 ${startY + 275}`} fill="none" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrowhead-green)" />

            {/* ===== ROW 3: POST-PROCESSING OPTIONS ===== */}
            <text x={250} y={startY + 295} textAnchor="middle" fill={colors.textSecondary} fontSize="10" fontWeight="600">
              POST-PROCESSING
            </text>

            {/* Project Extraction */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[3])}
            >
              <rect
                x={20} y={startY + 305}
                width={boxWidth} height={boxHeight}
                rx="8"
                fill="rgba(34, 197, 94, 0.15)"
                stroke="#22c55e"
                strokeWidth="2"
              />
              <text x={80} y={startY + 325} textAnchor="middle" fill="#22c55e" fontSize="9" fontWeight="700">
                AI EXTRACT
              </text>
              <text x={80} y={startY + 343} textAnchor="middle" fill={colors.textPrimary} fontSize="11" fontWeight="600">
                Project Creation
              </text>
              <text x={80} y={startY + 357} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                From PRD fields
              </text>
            </g>

            {/* Executive Summary */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[4])}
            >
              <rect
                x={190} y={startY + 305}
                width={boxWidth} height={boxHeight}
                rx="8"
                fill="rgba(236, 72, 153, 0.15)"
                stroke="#ec4899"
                strokeWidth="2"
              />
              <text x={250} y={startY + 325} textAnchor="middle" fill="#ec4899" fontSize="9" fontWeight="700">
                SUMMARIZE
              </text>
              <text x={250} y={startY + 343} textAnchor="middle" fill={colors.textPrimary} fontSize="11" fontWeight="600">
                Exec Summary
              </text>
              <text x={250} y={startY + 357} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Leadership brief
              </text>
            </g>

            {/* KB Integration */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[5])}
            >
              <rect
                x={360} y={startY + 305}
                width={boxWidth} height={boxHeight}
                rx="8"
                fill="rgba(59, 130, 246, 0.15)"
                stroke="#3b82f6"
                strokeWidth="2"
              />
              <text x={420} y={startY + 325} textAnchor="middle" fill="#3b82f6" fontSize="9" fontWeight="700">
                STORE
              </text>
              <text x={420} y={startY + 343} textAnchor="middle" fill={colors.textPrimary} fontSize="11" fontWeight="600">
                KB Integration
              </text>
              <text x={420} y={startY + 357} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Searchable docs
              </text>
            </g>

            {/* Arrows from checkpoint to post-processing */}
            <path d={`M 200 ${startY + 245} L 80 ${startY + 270} L 80 ${startY + 300}`} fill="none" stroke="#22c55e" strokeWidth="1.5" markerEnd="url(#arrowhead-green)" />
            <path d={`M 300 ${startY + 245} L 420 ${startY + 270} L 420 ${startY + 300}`} fill="none" stroke="#22c55e" strokeWidth="1.5" markerEnd="url(#arrowhead-green)" />

            {/* ===== ROW 4: DESTINATIONS ===== */}
            <text x={250} y={startY + 395} textAnchor="middle" fill={colors.textSecondary} fontSize="10" fontWeight="600">
              DESTINATIONS
            </text>

            {/* Projects Pipeline */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[6])}
            >
              <rect
                x={80} y={startY + 405}
                width={boxWidth + 30} height={boxHeight}
                rx="8"
                fill="rgba(34, 197, 94, 0.2)"
                stroke="#22c55e"
                strokeWidth="2"
              />
              <text x={145} y={startY + 425} textAnchor="middle" fill="#22c55e" fontSize="9" fontWeight="700">
                EXECUTE
              </text>
              <text x={145} y={startY + 443} textAnchor="middle" fill={colors.textPrimary} fontSize="12" fontWeight="600">
                Projects Pipeline
              </text>
              <text x={145} y={startY + 457} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Kanban board
              </text>
            </g>

            {/* External Export */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[7])}
            >
              <rect
                x={290} y={startY + 405}
                width={boxWidth + 30} height={boxHeight}
                rx="8"
                fill="rgba(100, 116, 139, 0.2)"
                stroke="#64748b"
                strokeWidth="2"
              />
              <text x={355} y={startY + 425} textAnchor="middle" fill="#64748b" fontSize="9" fontWeight="700">
                EXPORT
              </text>
              <text x={355} y={startY + 443} textAnchor="middle" fill={colors.textPrimary} fontSize="12" fontWeight="600">
                External Systems
              </text>
              <text x={355} y={startY + 457} textAnchor="middle" fill={colors.textSecondary} fontSize="8">
                Jira, Confluence, etc.
              </text>
            </g>

            {/* Arrows from post-processing to destinations */}
            <path d={`M 80 ${startY + 365} L 80 ${startY + 385} L 145 ${startY + 385} L 145 ${startY + 400}`} fill="none" stroke="#22c55e" strokeWidth="1.5" markerEnd="url(#arrowhead-green)" />
            <path d={`M 250 ${startY + 365} L 250 ${startY + 385} L 355 ${startY + 385} L 355 ${startY + 400}`} fill="none" stroke="#64748b" strokeWidth="1.5" />
            <path d={`M 420 ${startY + 365} L 420 ${startY + 385} L 355 ${startY + 385} L 355 ${startY + 400}`} fill="none" stroke="#64748b" strokeWidth="1.5" />

            {/* Traceability note */}
            <text x={250} y={startY + 490} textAnchor="middle" fill={colors.textSecondary} fontSize="9" fontStyle="italic">
              Full traceability: Project → PRD → Bundle → Insights → Discovery
            </text>

          </svg>
        </div>

        {/* Right: Details Panel */}
        <div className="flex-1 w-[380px] max-w-[415px] mx-auto">
          {selectedStep ? (
            <div
              className="p-4 rounded-lg border-2 h-full flex flex-col justify-center"
              style={{
                backgroundColor: `${selectedStep.color}15`,
                borderColor: selectedStep.color
              }}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-primary">{selectedStep.title}</h3>
                    <span
                      className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{
                        backgroundColor: `${selectedStep.color}20`,
                        color: selectedStep.color,
                        border: `1px solid ${selectedStep.color}`
                      }}
                    >
                      {categoryColors[selectedStep.category].label}
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
                    <span className="mr-2 mt-0.5" style={{ color: selectedStep.color }}>-</span>
                    {detail}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="p-4 bg-hover rounded-lg border border-default border-dashed h-full flex items-center justify-center">
              <p className="text-sm text-muted text-center">
                Click an element in the map<br />to see details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
