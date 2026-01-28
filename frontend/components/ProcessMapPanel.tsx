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
    title: 'Obsidian Vault',
    description: 'New transcript file detected',
    details: [
      'Granola creates meeting summaries in vault',
      'Files saved to Granola/Meeting-summaries folder',
      'Includes transcript, participants, action items'
    ]
  },
  {
    id: 'sync',
    title: 'Obsidian Sync',
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
    title: 'Granola Scanner',
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
      <div className="overflow-x-auto">
        <svg
          viewBox="0 0 1200 500"
          className="w-full min-w-[800px]"
          style={{ maxHeight: '500px' }}
        >
          {/* Background */}
          <defs>
            {/* Gradient for main flow boxes */}
            <linearGradient id="boxGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="var(--color-brand)" stopOpacity="0.1" />
              <stop offset="100%" stopColor="var(--color-brand)" stopOpacity="0.05" />
            </linearGradient>

            {/* Gradient for output boxes */}
            <linearGradient id="outputGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="var(--color-success)" stopOpacity="0.15" />
              <stop offset="100%" stopColor="var(--color-success)" stopOpacity="0.05" />
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
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="var(--color-brand)"
                fillOpacity="0.6"
              />
            </marker>
          </defs>

          {/* ===== ROW 1: Input Sources ===== */}

          {/* Obsidian Vault */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[0])}
          >
            <rect
              x="50" y="60" width="160" height="80"
              rx="8"
              fill="url(#boxGradient)"
              stroke="var(--color-brand)"
              strokeWidth="2"
            />
            <text x="130" y="90" textAnchor="middle" className="fill-primary text-sm font-semibold">
              Obsidian Vault
            </text>
            <text x="130" y="115" textAnchor="middle" className="fill-secondary text-xs">
              New transcript file
            </text>
            <text x="130" y="130" textAnchor="middle" className="fill-secondary text-xs">
              detected
            </text>
          </g>

          {/* Arrow: Vault -> Sync */}
          <path
            d="M 210 100 L 270 100"
            fill="none"
            stroke="var(--color-brand)"
            strokeWidth="2"
            strokeOpacity="0.6"
            markerEnd="url(#arrowhead)"
          />

          {/* Obsidian Sync */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[1])}
          >
            <rect
              x="280" y="60" width="160" height="80"
              rx="8"
              fill="url(#boxGradient)"
              stroke="var(--color-brand)"
              strokeWidth="2"
            />
            <text x="360" y="90" textAnchor="middle" className="fill-primary text-sm font-semibold">
              Obsidian Sync
            </text>
            <text x="360" y="115" textAnchor="middle" className="fill-secondary text-xs">
              File synced to Thesis
            </text>
            <text x="360" y="130" textAnchor="middle" className="fill-secondary text-xs">
              database
            </text>
          </g>

          {/* Arrow: Sync -> Scanner */}
          <path
            d="M 440 100 L 500 100"
            fill="none"
            stroke="var(--color-brand)"
            strokeWidth="2"
            strokeOpacity="0.6"
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
              stroke="var(--color-brand)"
              strokeWidth="2"
            />
            <text x="590" y="90" textAnchor="middle" className="fill-primary text-sm font-semibold">
              Granola Scanner
            </text>
            <text x="590" y="115" textAnchor="middle" className="fill-secondary text-xs">
              Meeting document
            </text>
            <text x="590" y="130" textAnchor="middle" className="fill-secondary text-xs">
              identified
            </text>
          </g>

          {/* Arrow: Scanner -> Processor */}
          <path
            d="M 670 100 L 730 100"
            fill="none"
            stroke="var(--color-brand)"
            strokeWidth="2"
            strokeOpacity="0.6"
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
              stroke="var(--color-brand)"
              strokeWidth="2"
            />
            <text x="820" y="90" textAnchor="middle" className="fill-primary text-sm font-semibold">
              Document Processor
            </text>
            <text x="820" y="115" textAnchor="middle" className="fill-secondary text-xs">
              Text extraction
            </text>
            <text x="820" y="130" textAnchor="middle" className="fill-secondary text-xs">
              and embedding
            </text>
          </g>

          {/* Arrow: Processor -> Discovery (down) */}
          <path
            d="M 820 140 L 820 180 L 590 180 L 590 220"
            fill="none"
            stroke="var(--color-brand)"
            strokeWidth="2"
            strokeOpacity="0.6"
            markerEnd="url(#arrowhead)"
          />

          {/* ===== ROW 2: Discovery ===== */}

          {/* Discovery Inbox - Central hub */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[4])}
          >
            <rect
              x="480" y="230" width="220" height="100"
              rx="12"
              fill="url(#boxGradient)"
              stroke="var(--color-brand)"
              strokeWidth="3"
            />
            <text x="590" y="265" textAnchor="middle" className="fill-primary font-bold">
              Discovery Inbox
            </text>
            <text x="590" y="290" textAnchor="middle" className="fill-secondary text-sm">
              AI analyzes for actionable items
            </text>
            <text x="590" y="310" textAnchor="middle" className="fill-secondary text-xs">
              (LLM extraction)
            </text>
          </g>

          {/* ===== ROW 3: Outputs ===== */}

          {/* Arrow: Discovery -> Tasks */}
          <path
            d="M 520 330 L 520 360 L 230 360 L 230 400"
            fill="none"
            stroke="var(--color-success)"
            strokeWidth="2"
            strokeOpacity="0.6"
            markerEnd="url(#arrowhead)"
          />

          {/* Arrow: Discovery -> Projects */}
          <path
            d="M 590 330 L 590 400"
            fill="none"
            stroke="var(--color-success)"
            strokeWidth="2"
            strokeOpacity="0.6"
            markerEnd="url(#arrowhead)"
          />

          {/* Arrow: Discovery -> Stakeholders */}
          <path
            d="M 660 330 L 660 360 L 950 360 L 950 400"
            fill="none"
            stroke="var(--color-success)"
            strokeWidth="2"
            strokeOpacity="0.6"
            markerEnd="url(#arrowhead)"
          />

          {/* Tasks Output */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[5])}
          >
            <rect
              x="130" y="410" width="200" height="70"
              rx="8"
              fill="url(#outputGradient)"
              stroke="var(--color-success)"
              strokeWidth="2"
            />
            <text x="230" y="440" textAnchor="middle" className="fill-primary text-sm font-semibold">
              Tasks
            </text>
            <text x="230" y="460" textAnchor="middle" className="fill-secondary text-xs">
              Action items extracted
            </text>
          </g>

          {/* Projects Output */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[6])}
          >
            <rect
              x="490" y="410" width="200" height="70"
              rx="8"
              fill="url(#outputGradient)"
              stroke="var(--color-success)"
              strokeWidth="2"
            />
            <text x="590" y="440" textAnchor="middle" className="fill-primary text-sm font-semibold">
              Projects
            </text>
            <text x="590" y="460" textAnchor="middle" className="fill-secondary text-xs">
              Opportunities identified
            </text>
          </g>

          {/* Stakeholders Output */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[7])}
          >
            <rect
              x="850" y="410" width="200" height="70"
              rx="8"
              fill="url(#outputGradient)"
              stroke="var(--color-success)"
              strokeWidth="2"
            />
            <text x="950" y="440" textAnchor="middle" className="fill-primary text-sm font-semibold">
              Stakeholders
            </text>
            <text x="950" y="460" textAnchor="middle" className="fill-secondary text-xs">
              People and relationships
            </text>
          </g>

          {/* Legend */}
          <g transform="translate(970, 60)">
            <text x="0" y="0" className="fill-muted text-xs font-medium">Legend</text>

            <rect x="0" y="15" width="20" height="12" rx="2" fill="url(#boxGradient)" stroke="var(--color-brand)" strokeWidth="1" />
            <text x="28" y="25" className="fill-secondary text-xs">Processing Step</text>

            <rect x="0" y="40" width="20" height="12" rx="2" fill="url(#outputGradient)" stroke="var(--color-success)" strokeWidth="1" />
            <text x="28" y="50" className="fill-secondary text-xs">Output Entity</text>

            <text x="0" y="75" className="fill-muted text-xs">Click any box for details</text>
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

      {/* Process Summary */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-hover rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-brand"></div>
            <span className="text-sm font-medium text-primary">Ingestion</span>
          </div>
          <p className="text-xs text-secondary">
            Files from Obsidian vault are synced, scanned for meeting content, and processed into searchable chunks with embeddings.
          </p>
        </div>
        <div className="p-4 bg-hover rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-warning"></div>
            <span className="text-sm font-medium text-primary">Discovery</span>
          </div>
          <p className="text-xs text-secondary">
            AI analyzes document content to extract actionable items, identify opportunities, and detect stakeholder mentions.
          </p>
        </div>
        <div className="p-4 bg-hover rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-success"></div>
            <span className="text-sm font-medium text-primary">Population</span>
          </div>
          <p className="text-xs text-secondary">
            Extracted items create candidates for tasks, projects, and stakeholders. Users review and approve to finalize.
          </p>
        </div>
      </div>
    </div>
  )
}
