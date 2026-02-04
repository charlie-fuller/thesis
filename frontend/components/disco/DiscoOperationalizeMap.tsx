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

  // Layout constants - compact version
  const boxWidth = 100
  const boxHeight = 50
  const startY = 60

  return (
    <div className="bg-card rounded-lg border border-default p-6">
      {/* Two-column layout: Map on left (2/3), Details on right (1/3) */}
      <div className="flex gap-6">
        {/* Left: SVG Flowchart */}
        <div className="flex-[2] text-primary">
          <svg
            viewBox="0 0 420 450"
            className="w-full max-w-[550px]"
            style={{ maxHeight: '600px' }}
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
            <text x="210" y="22" textAnchor="middle" fill={colors.textPrimary} fontSize="18" fontWeight="700">
              Operationalize Map
            </text>
            <text x="210" y="38" textAnchor="middle" fill={colors.textSecondary} fontSize="11" fontWeight="500">
              Exit paths from DISCO Convergence
            </text>

            {/* ===== ROW 1: APPROVED BUNDLE (Entry Point) ===== */}
            <g>
              <rect
                x={160} y={startY}
                width={boxWidth} height={boxHeight}
                rx="6"
                fill="rgba(249, 115, 22, 0.2)"
                stroke="#f97316"
                strokeWidth="2"
              />
              <text x={210} y={startY + 18} textAnchor="middle" fill="#f97316" fontSize="8" fontWeight="700">
                FROM CONVERGENCE
              </text>
              <text x={210} y={startY + 32} textAnchor="middle" fill={colors.textPrimary} fontSize="10" fontWeight="600">
                Approved Bundle
              </text>
              <text x={210} y={startY + 44} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Select output type
              </text>
            </g>

            {/* Arrows from bundle to 3 output types */}
            <path d={`M 160 ${startY + boxHeight/2} L 70 ${startY + boxHeight/2} L 70 ${startY + 70}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" markerEnd="url(#arrowhead-op)" />
            <path d={`M 210 ${startY + boxHeight} L 210 ${startY + 70}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" markerEnd="url(#arrowhead-op)" />
            <path d={`M 260 ${startY + boxHeight/2} L 350 ${startY + boxHeight/2} L 350 ${startY + 70}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" markerEnd="url(#arrowhead-op)" />

            {/* ===== ROW 2: THREE OUTPUT TYPES ===== */}
            {/* PRD */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[0])}
            >
              <rect
                x={20} y={startY + 75}
                width={boxWidth} height={boxHeight + 5}
                rx="6"
                fill="rgba(139, 92, 246, 0.15)"
                stroke="#8b5cf6"
                strokeWidth="2"
              />
              <text x={70} y={startY + 90} textAnchor="middle" fill="#8b5cf6" fontSize="8" fontWeight="700">
                BUILD/DEV
              </text>
              <text x={70} y={startY + 104} textAnchor="middle" fill={colors.textPrimary} fontSize="10" fontWeight="600">
                PRD
              </text>
              <text x={70} y={startY + 116} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Product Requirements
              </text>
            </g>

            {/* Evaluation Framework */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[1])}
            >
              <rect
                x={160} y={startY + 75}
                width={boxWidth} height={boxHeight + 5}
                rx="6"
                fill="rgba(6, 182, 212, 0.15)"
                stroke="#06b6d4"
                strokeWidth="2"
              />
              <text x={210} y={startY + 90} textAnchor="middle" fill="#06b6d4" fontSize="8" fontWeight="700">
                COMPARE
              </text>
              <text x={210} y={startY + 104} textAnchor="middle" fill={colors.textPrimary} fontSize="10" fontWeight="600">
                Evaluation
              </text>
              <text x={210} y={startY + 116} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Framework
              </text>
            </g>

            {/* Decision Framework */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[2])}
            >
              <rect
                x={300} y={startY + 75}
                width={boxWidth} height={boxHeight + 5}
                rx="6"
                fill="rgba(245, 158, 11, 0.15)"
                stroke="#f59e0b"
                strokeWidth="2"
              />
              <text x={350} y={startY + 90} textAnchor="middle" fill="#f59e0b" fontSize="8" fontWeight="700">
                GOVERN
              </text>
              <text x={350} y={startY + 104} textAnchor="middle" fill={colors.textPrimary} fontSize="10" fontWeight="600">
                Decision
              </text>
              <text x={350} y={startY + 116} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Framework
              </text>
            </g>

            {/* Human Checkpoint - Document Review */}
            <g>
              <rect
                x={160} y={startY + 150}
                width={boxWidth} height={40}
                rx="6"
                fill="rgba(100, 116, 139, 0.15)"
                stroke="#64748b"
                strokeWidth="2"
              />
              <g transform={`translate(${170}, ${startY + 156})`}>
                <circle cx="8" cy="6" r="5" fill="#64748b" />
                <path d="M0 20 Q8 12 16 20" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
              </g>
              <text x={220} y={startY + 168} textAnchor="start" fill="#64748b" fontSize="8" fontWeight="600">
                Human Review
              </text>
              <text x={220} y={startY + 180} textAnchor="start" fill={colors.textSecondary} fontSize="7">
                Approve / Edit
              </text>
            </g>

            {/* Arrows from outputs to checkpoint */}
            <path d={`M 70 ${startY + 130} L 70 ${startY + 170} L 155 ${startY + 170}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" markerEnd="url(#arrowhead-op)" />
            <path d={`M 210 ${startY + 130} L 210 ${startY + 145}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" markerEnd="url(#arrowhead-op)" />
            <path d={`M 350 ${startY + 130} L 350 ${startY + 170} L 265 ${startY + 170}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" markerEnd="url(#arrowhead-op)" />

            {/* Arrow from checkpoint to post-processing */}
            <path d={`M 210 ${startY + 190} L 210 ${startY + 215}`} fill="none" stroke="#22c55e" strokeWidth="1.5" markerEnd="url(#arrowhead-green)" />

            {/* ===== ROW 3: POST-PROCESSING OPTIONS ===== */}
            <text x={210} y={startY + 230} textAnchor="middle" fill={colors.textSecondary} fontSize="9" fontWeight="600">
              POST-PROCESSING
            </text>

            {/* Project Extraction */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[3])}
            >
              <rect
                x={20} y={startY + 240}
                width={boxWidth} height={boxHeight}
                rx="6"
                fill="rgba(34, 197, 94, 0.15)"
                stroke="#22c55e"
                strokeWidth="2"
              />
              <text x={70} y={startY + 256} textAnchor="middle" fill="#22c55e" fontSize="8" fontWeight="700">
                AI EXTRACT
              </text>
              <text x={70} y={startY + 270} textAnchor="middle" fill={colors.textPrimary} fontSize="9" fontWeight="600">
                Project Creation
              </text>
              <text x={70} y={startY + 282} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                From PRD fields
              </text>
            </g>

            {/* Executive Summary */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[4])}
            >
              <rect
                x={160} y={startY + 240}
                width={boxWidth} height={boxHeight}
                rx="6"
                fill="rgba(236, 72, 153, 0.15)"
                stroke="#ec4899"
                strokeWidth="2"
              />
              <text x={210} y={startY + 256} textAnchor="middle" fill="#ec4899" fontSize="8" fontWeight="700">
                SUMMARIZE
              </text>
              <text x={210} y={startY + 270} textAnchor="middle" fill={colors.textPrimary} fontSize="9" fontWeight="600">
                Exec Summary
              </text>
              <text x={210} y={startY + 282} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Leadership brief
              </text>
            </g>

            {/* KB Integration */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[5])}
            >
              <rect
                x={300} y={startY + 240}
                width={boxWidth} height={boxHeight}
                rx="6"
                fill="rgba(59, 130, 246, 0.15)"
                stroke="#3b82f6"
                strokeWidth="2"
              />
              <text x={350} y={startY + 256} textAnchor="middle" fill="#3b82f6" fontSize="8" fontWeight="700">
                STORE
              </text>
              <text x={350} y={startY + 270} textAnchor="middle" fill={colors.textPrimary} fontSize="9" fontWeight="600">
                KB Integration
              </text>
              <text x={350} y={startY + 282} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Searchable docs
              </text>
            </g>

            {/* Arrows from checkpoint to post-processing */}
            <path d={`M 170 ${startY + 190} L 70 ${startY + 210} L 70 ${startY + 235}`} fill="none" stroke="#22c55e" strokeWidth="1.5" markerEnd="url(#arrowhead-green)" />
            <path d={`M 250 ${startY + 190} L 350 ${startY + 210} L 350 ${startY + 235}`} fill="none" stroke="#22c55e" strokeWidth="1.5" markerEnd="url(#arrowhead-green)" />

            {/* ===== ROW 4: DESTINATIONS ===== */}
            <text x={210} y={startY + 315} textAnchor="middle" fill={colors.textSecondary} fontSize="9" fontWeight="600">
              DESTINATIONS
            </text>

            {/* Projects Pipeline */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[6])}
            >
              <rect
                x={60} y={startY + 325}
                width={boxWidth + 20} height={boxHeight}
                rx="6"
                fill="rgba(34, 197, 94, 0.2)"
                stroke="#22c55e"
                strokeWidth="2"
              />
              <text x={120} y={startY + 342} textAnchor="middle" fill="#22c55e" fontSize="8" fontWeight="700">
                EXECUTE
              </text>
              <text x={120} y={startY + 356} textAnchor="middle" fill={colors.textPrimary} fontSize="10" fontWeight="600">
                Projects Pipeline
              </text>
              <text x={120} y={startY + 368} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Kanban board
              </text>
            </g>

            {/* External Export */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[7])}
            >
              <rect
                x={240} y={startY + 325}
                width={boxWidth + 20} height={boxHeight}
                rx="6"
                fill="rgba(100, 116, 139, 0.2)"
                stroke="#64748b"
                strokeWidth="2"
              />
              <text x={300} y={startY + 342} textAnchor="middle" fill="#64748b" fontSize="8" fontWeight="700">
                EXPORT
              </text>
              <text x={300} y={startY + 356} textAnchor="middle" fill={colors.textPrimary} fontSize="10" fontWeight="600">
                External Systems
              </text>
              <text x={300} y={startY + 368} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Jira, Confluence, etc.
              </text>
            </g>

            {/* Arrows from post-processing to destinations */}
            <path d={`M 70 ${startY + 290} L 70 ${startY + 308} L 120 ${startY + 308} L 120 ${startY + 320}`} fill="none" stroke="#22c55e" strokeWidth="1.5" markerEnd="url(#arrowhead-green)" />
            <path d={`M 210 ${startY + 290} L 210 ${startY + 308} L 300 ${startY + 308} L 300 ${startY + 320}`} fill="none" stroke="#64748b" strokeWidth="1.5" />
            <path d={`M 350 ${startY + 290} L 350 ${startY + 308} L 300 ${startY + 308} L 300 ${startY + 320}`} fill="none" stroke="#64748b" strokeWidth="1.5" />

            {/* Traceability note */}
            <text x={210} y={startY + 398} textAnchor="middle" fill={colors.textSecondary} fontSize="8" fontStyle="italic">
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
