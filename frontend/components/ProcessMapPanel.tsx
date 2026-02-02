'use client'

import { useState } from 'react'

type ProcessStep = {
  id: string
  title: string
  description: string
  details: string[]
}

const processSteps: ProcessStep[] = [
  {
    id: 'vault',
    title: 'Vault',
    description: 'New transcript file detected',
    details: [
      'Meeting summaries created in vault',
      'Files saved to Meeting-summaries folder',
      'Includes transcript, participants, action items'
    ]
  },
  {
    id: 'sync',
    title: 'Sync',
    description: 'File synced to Thesis',
    details: [
      'API endpoint: POST /api/obsidian/sync',
      'File content extracted and stored',
      'Document record created in database',
      'Processing status set to "pending"'
    ]
  },
  {
    id: 'scanner',
    title: 'Scan',
    description: 'Meeting document identified',
    details: [
      'Heuristics detect meeting content',
      'Checks for: Participants, Action Items, Decisions',
      'Priority assigned (HIGH for meetings)',
      'Document marked as scanned'
    ]
  },
  {
    id: 'processor',
    title: 'Document Processor',
    description: 'Text extraction and embedding',
    details: [
      'Text extracted from document',
      'Content chunked (800 chars, 200 overlap)',
      'Voyage AI generates embeddings',
      'Chunks stored with vectors'
    ]
  },
  {
    id: 'discovery',
    title: 'Discovery Inbox',
    description: 'AI analyzes for actionable items',
    details: [
      'LLM extracts potential tasks',
      'Identifies project opportunities',
      'Detects stakeholder mentions',
      'Creates candidates for review'
    ]
  },
  {
    id: 'tasks',
    title: 'Tasks',
    description: 'Action items extracted',
    details: [
      'Task candidates created',
      'Assignee detected from context',
      'Due dates parsed if mentioned',
      'User reviews and approves'
    ]
  },
  {
    id: 'projects',
    title: 'Projects',
    description: 'Opportunities identified',
    details: [
      'Project candidates created',
      'Confidence scores calculated',
      'Goal alignment analyzed',
      'User reviews and promotes'
    ]
  },
  {
    id: 'stakeholders',
    title: 'Stakeholders',
    description: 'People and relationships tracked',
    details: [
      'Names extracted from participants',
      'Roles and departments identified',
      'Engagement levels tracked',
      'Relationship graph updated'
    ]
  }
]

// High contrast colors that work in both light and dark modes
const colors = {
  // Brand blue - visible on both backgrounds
  brand: '#3b82f6',
  brandLight: 'rgba(59, 130, 246, 0.15)',
  // Success green
  success: '#22c55e',
  successLight: 'rgba(34, 197, 94, 0.15)',
  // Text colors - using explicit values for SVG
  textPrimary: 'currentColor',
  textSecondary: '#9ca3af',
  // Arrows
  arrow: '#60a5fa',
  arrowSuccess: '#4ade80',
}

export default function ProcessMapPanel() {
  const [selectedStep, setSelectedStep] = useState<ProcessStep | null>(null)

  return (
    <div className="bg-card rounded-lg border border-default p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-primary">Document Processing Flow</h2>
        <p className="text-sm text-secondary mt-1">
          How meeting transcripts flow through discovery to populate tasks, projects, and stakeholders
        </p>
      </div>

      {/* SVG Flowchart */}
      <div className="overflow-x-auto text-primary">
        <svg
          viewBox="0 0 1200 500"
          className="w-full min-w-[800px]"
          style={{ maxHeight: '500px' }}
        >
          {/* Definitions */}
          <defs>
            {/* Gradient for main flow boxes */}
            <linearGradient id="boxGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={colors.brand} stopOpacity="0.2" />
              <stop offset="100%" stopColor={colors.brand} stopOpacity="0.1" />
            </linearGradient>

            {/* Gradient for output boxes */}
            <linearGradient id="outputGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={colors.success} stopOpacity="0.2" />
              <stop offset="100%" stopColor={colors.success} stopOpacity="0.1" />
            </linearGradient>

            {/* Arrow marker - brand */}
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill={colors.arrow}
              />
            </marker>

            {/* Arrow marker - success */}
            <marker
              id="arrowheadSuccess"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill={colors.arrowSuccess}
              />
            </marker>
          </defs>

          {/* ===== ROW 1: Input Sources ===== */}

          {/* Local Vault */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[0])}
          >
            <rect
              x="50" y="60" width="160" height="80"
              rx="8"
              fill="url(#boxGradient)"
              stroke={colors.brand}
              strokeWidth="2"
            />
            <text x="130" y="92" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Vault
            </text>
            <text x="130" y="112" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              New transcript file
            </text>
            <text x="130" y="128" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              detected
            </text>
          </g>

          {/* Arrow: Vault -> Sync */}
          <path
            d="M 210 100 L 270 100"
            fill="none"
            stroke={colors.arrow}
            strokeWidth="2"
            markerEnd="url(#arrowhead)"
          />

          {/* Vault Sync */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[1])}
          >
            <rect
              x="280" y="60" width="160" height="80"
              rx="8"
              fill="url(#boxGradient)"
              stroke={colors.brand}
              strokeWidth="2"
            />
            <text x="360" y="92" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Sync
            </text>
            <text x="360" y="112" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              File synced to Thesis
            </text>
            <text x="360" y="128" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              database
            </text>
          </g>

          {/* Arrow: Sync -> Scanner */}
          <path
            d="M 440 100 L 500 100"
            fill="none"
            stroke={colors.arrow}
            strokeWidth="2"
            markerEnd="url(#arrowhead)"
          />

          {/* Granola Scanner */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[2])}
          >
            <rect
              x="510" y="60" width="160" height="80"
              rx="8"
              fill="url(#boxGradient)"
              stroke={colors.brand}
              strokeWidth="2"
            />
            <text x="590" y="92" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Scan
            </text>
            <text x="590" y="112" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              Meeting document
            </text>
            <text x="590" y="128" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              identified
            </text>
          </g>

          {/* Arrow: Scanner -> Processor */}
          <path
            d="M 670 100 L 730 100"
            fill="none"
            stroke={colors.arrow}
            strokeWidth="2"
            markerEnd="url(#arrowhead)"
          />

          {/* Document Processor */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[3])}
          >
            <rect
              x="740" y="60" width="160" height="80"
              rx="8"
              fill="url(#boxGradient)"
              stroke={colors.brand}
              strokeWidth="2"
            />
            <text x="820" y="92" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Document Processor
            </text>
            <text x="820" y="112" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              Text extraction
            </text>
            <text x="820" y="128" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              and embedding
            </text>
          </g>

          {/* Arrow: Processor -> Discovery (down) */}
          <path
            d="M 820 140 L 820 180 L 590 180 L 590 220"
            fill="none"
            stroke={colors.arrow}
            strokeWidth="2"
            markerEnd="url(#arrowhead)"
          />

          {/* ===== ROW 2: Discovery ===== */}

          {/* Discovery Inbox - Central hub - AI extraction */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[4])}
          >
            <rect
              x="480" y="230" width="220" height="100"
              rx="12"
              fill="url(#boxGradient)"
              stroke={colors.brand}
              strokeWidth="3"
            />
            <text x="590" y="268" textAnchor="middle" fill={colors.textPrimary} fontSize="16" fontWeight="700">
              Discovery Inbox
            </text>
            <text x="590" y="292" textAnchor="middle" fill={colors.textSecondary} fontSize="13">
              AI analyzes for actionable items
            </text>
            <text x="590" y="312" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              (LLM extraction)
            </text>
          </g>

          {/* ===== ROW 3: Outputs ===== */}

          {/* Arrow: Discovery -> Tasks */}
          <path
            d="M 520 330 L 520 360 L 230 360 L 230 400"
            fill="none"
            stroke={colors.arrowSuccess}
            strokeWidth="2"
            markerEnd="url(#arrowheadSuccess)"
          />

          {/* Arrow: Discovery -> Projects */}
          <path
            d="M 590 330 L 590 400"
            fill="none"
            stroke={colors.arrowSuccess}
            strokeWidth="2"
            markerEnd="url(#arrowheadSuccess)"
          />

          {/* Arrow: Discovery -> Stakeholders */}
          <path
            d="M 660 330 L 660 360 L 950 360 L 950 400"
            fill="none"
            stroke={colors.arrowSuccess}
            strokeWidth="2"
            markerEnd="url(#arrowheadSuccess)"
          />

          {/* Tasks Output - Human approves candidates */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[5])}
          >
            <rect
              x="130" y="410" width="200" height="70"
              rx="8"
              fill="url(#outputGradient)"
              stroke={colors.success}
              strokeWidth="2"
            />
            <text x="230" y="442" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Tasks
            </text>
            <text x="230" y="462" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              Action items extracted
            </text>
            {/* Human icon - user approves task candidates */}
            <g transform="translate(310, 418)">
              <circle cx="6" cy="4" r="4" fill={colors.success} />
              <path d="M0 16 Q6 10 12 16" fill="none" stroke={colors.success} strokeWidth="2" strokeLinecap="round" />
            </g>
          </g>

          {/* Projects Output - Human approves candidates */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[6])}
          >
            <rect
              x="490" y="410" width="200" height="70"
              rx="8"
              fill="url(#outputGradient)"
              stroke={colors.success}
              strokeWidth="2"
            />
            <text x="590" y="442" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Projects
            </text>
            <text x="590" y="462" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              Opportunities identified
            </text>
            {/* Human icon - user approves project candidates */}
            <g transform="translate(670, 418)">
              <circle cx="6" cy="4" r="4" fill={colors.success} />
              <path d="M0 16 Q6 10 12 16" fill="none" stroke={colors.success} strokeWidth="2" strokeLinecap="round" />
            </g>
          </g>

          {/* Stakeholders Output - Human approves candidates */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[7])}
          >
            <rect
              x="850" y="410" width="200" height="70"
              rx="8"
              fill="url(#outputGradient)"
              stroke={colors.success}
              strokeWidth="2"
            />
            <text x="950" y="442" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Stakeholders
            </text>
            <text x="950" y="462" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              People and relationships
            </text>
            {/* Human icon - user approves stakeholder candidates */}
            <g transform="translate(1030, 418)">
              <circle cx="6" cy="4" r="4" fill={colors.success} />
              <path d="M0 16 Q6 10 12 16" fill="none" stroke={colors.success} strokeWidth="2" strokeLinecap="round" />
            </g>
          </g>

          {/* Legend */}
          <g transform="translate(970, 60)">
            <text x="0" y="0" fill={colors.textSecondary} fontSize="12" fontWeight="500">Legend</text>

            <rect x="0" y="15" width="20" height="12" rx="2" fill="url(#boxGradient)" stroke={colors.brand} strokeWidth="1" />
            <text x="28" y="25" fill={colors.textSecondary} fontSize="11">Processing Step</text>

            <rect x="0" y="40" width="20" height="12" rx="2" fill="url(#outputGradient)" stroke={colors.success} strokeWidth="1" />
            <text x="28" y="50" fill={colors.textSecondary} fontSize="11">Output Entity</text>

            {/* Human icon in legend */}
            <g transform="translate(0, 60)">
              <circle cx="6" cy="4" r="4" fill={colors.success} />
              <path d="M0 14 Q6 9 12 14" fill="none" stroke={colors.success} strokeWidth="1.5" strokeLinecap="round" />
            </g>
            <text x="28" y="75" fill={colors.textSecondary} fontSize="11">Human Approval</text>

            <text x="0" y="100" fill={colors.textSecondary} fontSize="11">Click any box for details</text>
          </g>
        </svg>
      </div>

      {/* Details Panel */}
      {selectedStep && (
        <div className="mt-6 p-4 bg-hover rounded-lg border border-default">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-primary">{selectedStep.title}</h3>
              <p className="text-sm text-secondary mt-1">{selectedStep.description}</p>
            </div>
            <button
              onClick={() => setSelectedStep(null)}
              className="text-muted hover:text-primary"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <ul className="mt-3 space-y-1">
            {selectedStep.details.map((detail, index) => (
              <li key={index} className="text-sm text-secondary flex items-start">
                <span className="text-brand mr-2">-</span>
                {detail}
              </li>
            ))}
          </ul>
        </div>
      )}

    </div>
  )
}
