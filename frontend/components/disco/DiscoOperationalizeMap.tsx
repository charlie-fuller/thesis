'use client'

import { useState } from 'react'
import { X } from 'lucide-react'

type OutputStep = {
  id: string
  title: string
  description: string
  category: 'input' | 'post-process' | 'destination'
  details: string[]
  color: string
}

const outputSteps: OutputStep[] = [
  // Input Document Types (from Convergence)
  {
    id: 'prd',
    title: 'PRD',
    description: 'Product Requirements Document',
    category: 'input',
    color: '#8b5cf6', // violet
    details: [
      'Generated in Convergence stage',
      'Best for: Build/development proposed initiatives',
      'Executive Summary & Problem Statement',
      'Goals, Requirements, User Stories',
      'Technical Considerations & Risks'
    ]
  },
  {
    id: 'evaluation',
    title: 'Evaluation Framework',
    description: 'Vendor/Platform Comparison',
    category: 'input',
    color: '#06b6d4', // cyan
    details: [
      'Generated in Convergence stage',
      'Best for: Tool selection, vendor comparison',
      'Weighted Scoring Matrix',
      'Platform Comparison Table',
      'Recommendation & Next Steps'
    ]
  },
  {
    id: 'decision',
    title: 'Decision Framework',
    description: 'Governance & Strategy',
    category: 'input',
    color: '#f59e0b', // amber
    details: [
      'Generated in Convergence stage',
      'Best for: Policy, strategy, governance',
      'Stakeholder Analysis',
      'Options & Risk Assessment',
      'Implementation Considerations'
    ]
  },
  // Post-Processing
  {
    id: 'project-extract',
    title: 'Project Extraction',
    description: 'AI extracts project fields from document',
    category: 'post-process',
    color: '#22c55e', // green
    details: [
      'Auto-extracts: Title, Description, Department',
      'Scores: ROI, Effort, Strategic Alignment',
      'Generates initial task list',
      'Links back to source discovery',
      'Sets project status to "identified"'
    ]
  },
  {
    id: 'exec-summary',
    title: 'Executive Summary',
    description: 'Cross-initiative leadership overview',
    category: 'post-process',
    color: '#ec4899', // pink
    details: [
      'Summarizes all approved documents',
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
      'Document becomes searchable',
      'Available via discovery chat Q&A',
      'RAG-enabled for future queries',
      'Full traceability maintained',
      'Cross-discovery knowledge reuse'
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
      'Linked to source DISCO discovery',
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
  input: {
    label: 'From Convergence'
  },
  'post-process': {
    label: 'Post-Processing'
  },
  destination: {
    label: 'Destination'
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
  const boxHeight = 45
  const startY = 55

  return (
    <div className="bg-card rounded-lg border border-default p-6">
      {/* Two-column layout: Map on left (2/3), Details on right (1/3) */}
      <div className="flex gap-6">
        {/* Left: SVG Flowchart */}
        <div className="flex-[2] text-primary">
          <svg
            viewBox="0 0 420 380"
            className="w-full max-w-[550px]"
            style={{ maxHeight: '500px' }}
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
            <text x="210" y="20" textAnchor="middle" fill={colors.textPrimary} fontSize="18" fontWeight="700">
              Operationalize Map
            </text>
            <text x="210" y="36" textAnchor="middle" fill={colors.textSecondary} fontSize="11" fontWeight="500">
              After document approval in Convergence
            </text>

            {/* ===== ROW 1: APPROVED DOCUMENT (Entry Point) ===== */}
            <text x="210" y={startY + 5} textAnchor="middle" fill={colors.textSecondary} fontSize="9" fontWeight="600">
              APPROVED DOCUMENT (from Convergence)
            </text>

            {/* Three document types as entry - dashed to show they come from Convergence */}
            {/* PRD */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[0])}
            >
              <rect
                x={20} y={startY + 15}
                width={boxWidth} height={boxHeight}
                rx="6"
                fill="rgba(139, 92, 246, 0.15)"
                stroke="#8b5cf6"
                strokeWidth="1.5"
                strokeDasharray="4 2"
              />
              <text x={70} y={startY + 32} textAnchor="middle" fill="#8b5cf6" fontSize="9" fontWeight="600">
                PRD
              </text>
              <text x={70} y={startY + 46} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Build/Dev
              </text>
            </g>

            {/* Evaluation Framework */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[1])}
            >
              <rect
                x={160} y={startY + 15}
                width={boxWidth} height={boxHeight}
                rx="6"
                fill="rgba(6, 182, 212, 0.15)"
                stroke="#06b6d4"
                strokeWidth="1.5"
                strokeDasharray="4 2"
              />
              <text x={210} y={startY + 32} textAnchor="middle" fill="#06b6d4" fontSize="9" fontWeight="600">
                Evaluation
              </text>
              <text x={210} y={startY + 46} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Compare
              </text>
            </g>

            {/* Decision Framework */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[2])}
            >
              <rect
                x={300} y={startY + 15}
                width={boxWidth} height={boxHeight}
                rx="6"
                fill="rgba(245, 158, 11, 0.15)"
                stroke="#f59e0b"
                strokeWidth="1.5"
                strokeDasharray="4 2"
              />
              <text x={350} y={startY + 32} textAnchor="middle" fill="#f59e0b" fontSize="9" fontWeight="600">
                Decision
              </text>
              <text x={350} y={startY + 46} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Govern
              </text>
            </g>

            {/* Arrows from documents to post-processing label */}
            <path d={`M 70 ${startY + 60} L 70 ${startY + 85} L 210 ${startY + 85}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" />
            <path d={`M 210 ${startY + 60} L 210 ${startY + 85}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" />
            <path d={`M 350 ${startY + 60} L 350 ${startY + 85} L 210 ${startY + 85}`} fill="none" stroke={colors.arrow} strokeWidth="1.5" />
            <path d={`M 210 ${startY + 85} L 210 ${startY + 100}`} fill="none" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrowhead-green)" />

            {/* ===== ROW 2: POST-PROCESSING OPTIONS ===== */}
            <text x={210} y={startY + 118} textAnchor="middle" fill="#f97316" fontSize="10" fontWeight="700">
              O: OPERATIONALIZE
            </text>
            <text x={210} y={startY + 132} textAnchor="middle" fill={colors.textSecondary} fontSize="9" fontWeight="500">
              Post-Processing Options
            </text>

            {/* Project Extraction */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[3])}
            >
              <rect
                x={20} y={startY + 145}
                width={boxWidth} height={boxHeight + 5}
                rx="6"
                fill="rgba(34, 197, 94, 0.15)"
                stroke="#22c55e"
                strokeWidth="2"
              />
              <text x={70} y={startY + 162} textAnchor="middle" fill="#22c55e" fontSize="8" fontWeight="700">
                AI EXTRACT
              </text>
              <text x={70} y={startY + 176} textAnchor="middle" fill={colors.textPrimary} fontSize="9" fontWeight="600">
                Project Creation
              </text>
              <text x={70} y={startY + 188} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                From document
              </text>
            </g>

            {/* Executive Summary */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[4])}
            >
              <rect
                x={160} y={startY + 145}
                width={boxWidth} height={boxHeight + 5}
                rx="6"
                fill="rgba(236, 72, 153, 0.15)"
                stroke="#ec4899"
                strokeWidth="2"
              />
              <text x={210} y={startY + 162} textAnchor="middle" fill="#ec4899" fontSize="8" fontWeight="700">
                SUMMARIZE
              </text>
              <text x={210} y={startY + 176} textAnchor="middle" fill={colors.textPrimary} fontSize="9" fontWeight="600">
                Exec Summary
              </text>
              <text x={210} y={startY + 188} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Leadership brief
              </text>
            </g>

            {/* KB Integration */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[5])}
            >
              <rect
                x={300} y={startY + 145}
                width={boxWidth} height={boxHeight + 5}
                rx="6"
                fill="rgba(59, 130, 246, 0.15)"
                stroke="#3b82f6"
                strokeWidth="2"
              />
              <text x={350} y={startY + 162} textAnchor="middle" fill="#3b82f6" fontSize="8" fontWeight="700">
                STORE
              </text>
              <text x={350} y={startY + 176} textAnchor="middle" fill={colors.textPrimary} fontSize="9" fontWeight="600">
                KB Integration
              </text>
              <text x={350} y={startY + 188} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Searchable docs
              </text>
            </g>

            {/* ===== ROW 3: DESTINATIONS ===== */}
            <text x={210} y={startY + 225} textAnchor="middle" fill={colors.textSecondary} fontSize="9" fontWeight="600">
              DESTINATIONS
            </text>

            {/* Arrows from post-processing to destinations */}
            <path d={`M 70 ${startY + 195} L 70 ${startY + 215} L 120 ${startY + 215} L 120 ${startY + 230}`} fill="none" stroke="#22c55e" strokeWidth="1.5" markerEnd="url(#arrowhead-green)" />
            <path d={`M 210 ${startY + 195} L 210 ${startY + 215} L 300 ${startY + 215} L 300 ${startY + 230}`} fill="none" stroke="#64748b" strokeWidth="1.5" />
            <path d={`M 350 ${startY + 195} L 350 ${startY + 215} L 300 ${startY + 215} L 300 ${startY + 230}`} fill="none" stroke="#64748b" strokeWidth="1.5" />

            {/* Projects Pipeline */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[6])}
            >
              <rect
                x={60} y={startY + 235}
                width={boxWidth + 20} height={boxHeight + 5}
                rx="6"
                fill="rgba(34, 197, 94, 0.2)"
                stroke="#22c55e"
                strokeWidth="2"
              />
              <text x={120} y={startY + 252} textAnchor="middle" fill="#22c55e" fontSize="8" fontWeight="700">
                EXECUTE
              </text>
              <text x={120} y={startY + 266} textAnchor="middle" fill={colors.textPrimary} fontSize="10" fontWeight="600">
                Projects Pipeline
              </text>
              <text x={120} y={startY + 278} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Kanban board
              </text>
            </g>

            {/* External Export */}
            <g
              className="cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setSelectedStep(outputSteps[7])}
            >
              <rect
                x={240} y={startY + 235}
                width={boxWidth + 20} height={boxHeight + 5}
                rx="6"
                fill="rgba(100, 116, 139, 0.2)"
                stroke="#64748b"
                strokeWidth="2"
              />
              <text x={300} y={startY + 252} textAnchor="middle" fill="#64748b" fontSize="8" fontWeight="700">
                EXPORT
              </text>
              <text x={300} y={startY + 266} textAnchor="middle" fill={colors.textPrimary} fontSize="10" fontWeight="600">
                External Systems
              </text>
              <text x={300} y={startY + 278} textAnchor="middle" fill={colors.textSecondary} fontSize="7">
                Jira, Confluence, etc.
              </text>
            </g>

            {/* Traceability note */}
            <text x={210} y={startY + 315} textAnchor="middle" fill={colors.textSecondary} fontSize="8" fontStyle="italic">
              Full traceability: Project → Document → Proposed Initiative → Insights → Discovery
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
