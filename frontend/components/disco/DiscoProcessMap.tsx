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

  return (
    <div className="bg-card rounded-lg border border-default p-6">
      {/* SVG Flowchart */}
      <div className="overflow-x-auto text-primary">
        <svg
          viewBox="0 0 1000 520"
          className="w-full min-w-[800px]"
          style={{ maxHeight: '520px' }}
        >
          {/* Definitions */}
          <defs>
            {/* Discovery gradient (blue) */}
            <linearGradient id="discoveryGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
            </linearGradient>

            {/* Intelligence gradient (cyan) */}
            <linearGradient id="intelligenceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.1" />
            </linearGradient>

            {/* Synthesis gradient (green) */}
            <linearGradient id="synthesisGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0.1" />
            </linearGradient>

            {/* Capabilities gradient (rose) */}
            <linearGradient id="capabilitiesGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.2" />
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
          <text x="500" y="30" textAnchor="middle" fill={colors.textPrimary} fontSize="16" fontWeight="700">
            DISCo: 4 Agents + 4 Checkpoints
          </text>
          <text x="500" y="50" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
            Click any agent for details
          </text>

          {/* ===== AGENT 1: DISCOVERY GUIDE ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[0])}
          >
            <rect
              x="40" y="100" width="180" height="100"
              rx="10"
              fill={stageColors.discovery.fill}
              stroke={stageColors.discovery.stroke}
              strokeWidth="3"
            />
            <text x="130" y="130" textAnchor="middle" fill="#3b82f6" fontSize="12" fontWeight="700">
              D: DISCOVERY
            </text>
            <text x="130" y="155" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Discovery Guide
            </text>
            <text x="130" y="175" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Validates problem, plans
            </text>
            <text x="130" y="190" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              sessions, tracks coverage
            </text>
          </g>

          {/* Arrow: Discovery Guide -> Checkpoint 1 */}
          <path d="M 220 150 L 250 150" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 1 */}
          <g>
            <rect
              x="255" y="120" width="60" height="60"
              rx="8"
              fill="rgba(100, 116, 139, 0.1)"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="4 2"
            />
            <text x="285" y="145" textAnchor="middle" fill="#64748b" fontSize="10" fontWeight="600">
              CP 1
            </text>
            {/* Checkmark icon */}
            <g transform="translate(273, 152)">
              <circle cx="12" cy="12" r="10" fill="none" stroke="#64748b" strokeWidth="1.5" />
              <path d="M7 12 L10 15 L17 8" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          </g>

          {/* Arrow: Checkpoint 1 -> Insight Analyst */}
          <path d="M 315 150 L 345 150" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== AGENT 2: INSIGHT ANALYST ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[1])}
          >
            <rect
              x="350" y="100" width="180" height="100"
              rx="10"
              fill={stageColors.intelligence.fill}
              stroke={stageColors.intelligence.stroke}
              strokeWidth="3"
            />
            <text x="440" y="130" textAnchor="middle" fill="#06b6d4" fontSize="12" fontWeight="700">
              I: INTELLIGENCE
            </text>
            <text x="440" y="155" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Insight Analyst
            </text>
            <text x="440" y="175" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Extracts patterns,
            </text>
            <text x="440" y="190" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              creates decision doc
            </text>
          </g>

          {/* Arrow: Insight Analyst -> Checkpoint 2 */}
          <path d="M 530 150 L 560 150" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 2 */}
          <g>
            <rect
              x="565" y="120" width="60" height="60"
              rx="8"
              fill="rgba(100, 116, 139, 0.1)"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="4 2"
            />
            <text x="595" y="145" textAnchor="middle" fill="#64748b" fontSize="10" fontWeight="600">
              CP 2
            </text>
            {/* Checkmark icon */}
            <g transform="translate(583, 152)">
              <circle cx="12" cy="12" r="10" fill="none" stroke="#64748b" strokeWidth="1.5" />
              <path d="M7 12 L10 15 L17 8" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          </g>

          {/* Arrow: Checkpoint 2 -> Initiative Builder */}
          <path d="M 625 150 L 655 150" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== AGENT 3: INITIATIVE BUILDER ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[2])}
          >
            <rect
              x="660" y="100" width="180" height="100"
              rx="10"
              fill={stageColors.synthesis.fill}
              stroke={stageColors.synthesis.stroke}
              strokeWidth="3"
            />
            <text x="750" y="130" textAnchor="middle" fill="#22c55e" fontSize="12" fontWeight="700">
              S: SYNTHESIS
            </text>
            <text x="750" y="155" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Initiative Builder
            </text>
            <text x="750" y="175" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Clusters insights into
            </text>
            <text x="750" y="190" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              scored bundles
            </text>
          </g>

          {/* Arrow: Initiative Builder -> Checkpoint 3 (down) */}
          <path d="M 750 200 L 750 240 L 750 270" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 3 */}
          <g>
            <rect
              x="720" y="275" width="60" height="60"
              rx="8"
              fill="rgba(100, 116, 139, 0.1)"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="4 2"
            />
            <text x="750" y="300" textAnchor="middle" fill="#64748b" fontSize="10" fontWeight="600">
              CP 3
            </text>
            {/* Checkmark icon */}
            <g transform="translate(738, 307)">
              <circle cx="12" cy="12" r="10" fill="none" stroke="#64748b" strokeWidth="1.5" />
              <path d="M7 12 L10 15 L17 8" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          </g>

          {/* Arrow: Checkpoint 3 -> Requirements Generator (left) */}
          <path d="M 720 305 L 530 305" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== AGENT 4: REQUIREMENTS GENERATOR ===== */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[3])}
          >
            <rect
              x="350" y="255" width="180" height="100"
              rx="10"
              fill={stageColors.capabilities.fill}
              stroke={stageColors.capabilities.stroke}
              strokeWidth="3"
            />
            <text x="440" y="285" textAnchor="middle" fill="#f43f5e" fontSize="12" fontWeight="700">
              C: CAPABILITIES
            </text>
            <text x="440" y="310" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Requirements Generator
            </text>
            <text x="440" y="330" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              PRD with tech
            </text>
            <text x="440" y="345" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              recommendations
            </text>
          </g>

          {/* Arrow: Requirements Generator -> Checkpoint 4 */}
          <path d="M 350 305 L 315 305" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Checkpoint 4 */}
          <g>
            <rect
              x="255" y="275" width="60" height="60"
              rx="8"
              fill="rgba(100, 116, 139, 0.1)"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="4 2"
            />
            <text x="285" y="300" textAnchor="middle" fill="#64748b" fontSize="10" fontWeight="600">
              CP 4
            </text>
            {/* Checkmark icon */}
            <g transform="translate(273, 307)">
              <circle cx="12" cy="12" r="10" fill="none" stroke="#64748b" strokeWidth="1.5" />
              <path d="M7 12 L10 15 L17 8" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </g>
          </g>

          {/* Arrow: Checkpoint 4 -> PRD Output */}
          <path d="M 255 305 L 220 305" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Final Output: PRD */}
          <g>
            <rect
              x="40" y="265" width="180" height="80"
              rx="10"
              fill="rgba(34, 197, 94, 0.15)"
              stroke="#22c55e"
              strokeWidth="3"
            />
            <text x="130" y="295" textAnchor="middle" fill="#22c55e" fontSize="14" fontWeight="700">
              PRD Document
            </text>
            <text x="130" y="315" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Complete product spec
            </text>
            <text x="130" y="330" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              ready for development
            </text>
          </g>

          {/* ===== DOCUMENTS INPUT ===== */}
          <g>
            <rect
              x="70" y="230" width="120" height="30"
              rx="6"
              fill="rgba(100, 116, 139, 0.1)"
              stroke="#64748b"
              strokeWidth="1"
              strokeDasharray="4 2"
            />
            <text x="130" y="250" textAnchor="middle" fill="#64748b" fontSize="11" fontWeight="500">
              Documents Input
            </text>
          </g>

          {/* Arrow: Documents -> Discovery Guide (up) */}
          <path d="M 130 230 L 130 200" fill="none" stroke="#64748b" strokeWidth="1" strokeDasharray="4 2" markerEnd="url(#arrowhead)" />

          {/* ===== DISCOVERY WORKSHOP LOOP ===== */}
          <g>
            <rect
              x="840" y="210" width="140" height="90"
              rx="10"
              fill="rgba(100, 116, 139, 0.1)"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="6 3"
            />
            <text x="910" y="240" textAnchor="middle" fill={colors.textPrimary} fontSize="12" fontWeight="600">
              Discovery Sessions
            </text>
            <text x="910" y="258" textAnchor="middle" fill={colors.textSecondary} fontSize="10">
              Stakeholder interviews
            </text>
            {/* Human icons */}
            <g transform="translate(870, 268)">
              <circle cx="6" cy="4" r="4" fill="#64748b" />
              <path d="M0 14 Q6 9 12 14" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
            </g>
            <g transform="translate(895, 268)">
              <circle cx="6" cy="4" r="4" fill="#64748b" />
              <path d="M0 14 Q6 9 12 14" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
            </g>
            <g transform="translate(920, 268)">
              <circle cx="6" cy="4" r="4" fill="#64748b" />
              <path d="M0 14 Q6 9 12 14" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" />
            </g>
          </g>

          {/* Arrow: Discovery Guide -> Workshop */}
          <path d="M 220 175 L 260 175 L 260 220 L 840 220 L 840 255" fill="none" stroke="#64748b" strokeWidth="1" strokeDasharray="4 2" markerEnd="url(#arrowhead)" />

          {/* Arrow: Workshop -> Insight Analyst (feedback) */}
          <path d="M 840 255 L 840 175 L 660 175 L 660 150 L 530 150" fill="none" stroke="#64748b" strokeWidth="1" strokeDasharray="4 2" />
          <text x="700" y="165" fill="#64748b" fontSize="9">transcripts</text>

          {/* ===== LEGEND (bottom) ===== */}
          <g transform="translate(40, 420)">
            <text x="0" y="0" fill={colors.textSecondary} fontSize="13" fontWeight="700">Legend</text>

            {/* Stage colors */}
            <rect x="70" y="-12" width="18" height="14" rx="3" fill={stageColors.discovery.fill} stroke={stageColors.discovery.stroke} strokeWidth="2" />
            <text x="94" y="0" fill={colors.textSecondary} fontSize="11">Discovery</text>

            <rect x="170" y="-12" width="18" height="14" rx="3" fill={stageColors.intelligence.fill} stroke={stageColors.intelligence.stroke} strokeWidth="2" />
            <text x="194" y="0" fill={colors.textSecondary} fontSize="11">Intelligence</text>

            <rect x="280" y="-12" width="18" height="14" rx="3" fill={stageColors.synthesis.fill} stroke={stageColors.synthesis.stroke} strokeWidth="2" />
            <text x="304" y="0" fill={colors.textSecondary} fontSize="11">Synthesis</text>

            <rect x="380" y="-12" width="18" height="14" rx="3" fill={stageColors.capabilities.fill} stroke={stageColors.capabilities.stroke} strokeWidth="2" />
            <text x="404" y="0" fill={colors.textSecondary} fontSize="11">Capabilities</text>

            {/* Checkpoint and human */}
            <rect x="500" y="-12" width="18" height="14" rx="3" fill="rgba(100, 116, 139, 0.1)" stroke="#64748b" strokeWidth="2" strokeDasharray="3 2" />
            <text x="524" y="0" fill={colors.textSecondary} fontSize="11">Checkpoint / Human Review</text>
          </g>

          {/* Key insight text */}
          <g transform="translate(40, 460)">
            <text x="0" y="0" fill={colors.textSecondary} fontSize="11">
              Each agent produces output reviewed at a checkpoint before the next agent runs.
            </text>
            <text x="0" y="18" fill={colors.textSecondary} fontSize="11">
              Discovery sessions can occur any time, feeding transcripts back into the Insight Analyst.
            </text>
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
