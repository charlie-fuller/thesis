'use client'

import { useState } from 'react'
import { X } from 'lucide-react'

type ProcessStep = {
  id: string
  title: string
  description: string
  stage: 'discovery' | 'intelligence' | 'synthesis' | 'capabilities'
  details: string[]
}

const processSteps: ProcessStep[] = [
  // Stage 1: Discovery
  {
    id: 'discovery-prep',
    title: 'Discovery Prep',
    description: 'Analyzes uploaded documents',
    stage: 'discovery',
    details: [
      'Extracts key themes from documents',
      'Identifies stakeholders mentioned',
      'Summarizes market context',
      'Prepares context for Triage'
    ]
  },
  {
    id: 'triage',
    title: 'Triage',
    description: 'GO / NO-GO / INVESTIGATE gate',
    stage: 'discovery',
    details: [
      'Evaluates opportunity viability',
      'Assesses strategic alignment',
      'Identifies key risks and assumptions',
      'Recommends: GO, NO-GO, or INVESTIGATE'
    ]
  },
  {
    id: 'discovery-planner',
    title: 'Discovery Planner',
    description: 'Creates session agendas',
    stage: 'discovery',
    details: [
      'Designs stakeholder interview guides',
      'Identifies key questions to answer',
      'Suggests participants for each session',
      'Creates discovery session schedule'
    ]
  },
  {
    id: 'coverage-tracker',
    title: 'Coverage Tracker',
    description: 'Tracks progress: READY / GAPS',
    stage: 'discovery',
    details: [
      'Monitors topics covered vs needed',
      'Identifies information gaps',
      'Tracks stakeholder coverage',
      'Reports: READY or GAPS remaining'
    ]
  },
  // Stage 2: Intelligence
  {
    id: 'insight-extractor',
    title: 'Insight Extractor',
    description: 'Pulls patterns with evidence',
    stage: 'intelligence',
    details: [
      'Analyzes discovery session transcripts',
      'Extracts recurring themes and patterns',
      'Links insights to source evidence',
      'Categorizes by stakeholder perspective'
    ]
  },
  // Stage 3: Synthesis
  {
    id: 'consolidator',
    title: 'Consolidator',
    description: 'Creates decision document',
    stage: 'synthesis',
    details: [
      'Synthesizes all insights into cohesive narrative',
      'Identifies key decision points',
      'Creates executive summary',
      'Documents trade-offs and recommendations'
    ]
  },
  {
    id: 'strategist',
    title: 'Strategist',
    description: 'Proposes feature bundles',
    stage: 'synthesis',
    details: [
      'Groups features into coherent bundles',
      'Provides business rationale for each',
      'Estimates complexity and value',
      'Creates bundles for approval workflow'
    ]
  },
  // Stage 4: Capabilities
  {
    id: 'prd-generator',
    title: 'PRD Generator',
    description: 'Creates product requirements',
    stage: 'capabilities',
    details: [
      'Generates PRD from approved bundles',
      'Includes user stories and acceptance criteria',
      'Documents technical requirements',
      'Creates implementation roadmap'
    ]
  },
  {
    id: 'tech-evaluation',
    title: 'Tech Evaluation',
    description: 'Assesses technical feasibility',
    stage: 'capabilities',
    details: [
      'Evaluates technical approaches',
      'Identifies integration points',
      'Assesses build vs buy options',
      'Documents technical risks'
    ]
  }
]

// Colors by stage
const stageColors = {
  discovery: {
    fill: 'url(#discoveryGradient)',
    stroke: '#f59e0b', // amber
    text: '#f59e0b',
    light: 'rgba(245, 158, 11, 0.15)'
  },
  intelligence: {
    fill: 'url(#intelligenceGradient)',
    stroke: '#14b8a6', // teal
    text: '#14b8a6',
    light: 'rgba(20, 184, 166, 0.15)'
  },
  synthesis: {
    fill: 'url(#synthesisGradient)',
    stroke: '#8b5cf6', // violet
    text: '#8b5cf6',
    light: 'rgba(139, 92, 246, 0.15)'
  },
  capabilities: {
    fill: 'url(#capabilitiesGradient)',
    stroke: '#22c55e', // green
    text: '#22c55e',
    light: 'rgba(34, 197, 94, 0.15)'
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
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-primary">DISCo Workflow</h2>
        <p className="text-sm text-secondary mt-1">
          8 specialized agents across 4 stages: Discovery, Intelligence, Synthesis, Capabilities
        </p>
      </div>

      {/* SVG Flowchart */}
      <div className="overflow-x-auto text-primary">
        <svg
          viewBox="0 0 1200 580"
          className="w-full min-w-[900px]"
          style={{ maxHeight: '580px' }}
        >
          {/* Definitions */}
          <defs>
            {/* Discovery gradient (amber) */}
            <linearGradient id="discoveryGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.1" />
            </linearGradient>

            {/* Intelligence gradient (teal) */}
            <linearGradient id="intelligenceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#14b8a6" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#14b8a6" stopOpacity="0.1" />
            </linearGradient>

            {/* Synthesis gradient (violet) */}
            <linearGradient id="synthesisGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.1" />
            </linearGradient>

            {/* Capabilities gradient (green) */}
            <linearGradient id="capabilitiesGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0.1" />
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

          {/* ===== STAGE LABELS ===== */}
          <text x="280" y="30" textAnchor="middle" fill="#f59e0b" fontSize="14" fontWeight="700">
            Stage 1: DISCOVERY
          </text>
          <text x="590" y="30" textAnchor="middle" fill="#14b8a6" fontSize="14" fontWeight="700">
            Stage 2: INTELLIGENCE
          </text>
          <text x="820" y="30" textAnchor="middle" fill="#8b5cf6" fontSize="14" fontWeight="700">
            Stage 3: SYNTHESIS
          </text>
          <text x="1050" y="30" textAnchor="middle" fill="#22c55e" fontSize="14" fontWeight="700">
            Stage 4: CAPABILITIES
          </text>

          {/* ===== STAGE 1: DISCOVERY (4 agents) ===== */}

          {/* Discovery Prep */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[0])}
          >
            <rect
              x="50" y="60" width="140" height="70"
              rx="8"
              fill={stageColors.discovery.fill}
              stroke={stageColors.discovery.stroke}
              strokeWidth="2"
            />
            <text x="120" y="90" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Discovery Prep
            </text>
            <text x="120" y="110" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Analyze documents
            </text>
          </g>

          {/* Arrow: Prep -> Triage */}
          <path d="M 190 95 L 220 95" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Triage (central, larger) */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[1])}
          >
            <rect
              x="230" y="50" width="160" height="90"
              rx="10"
              fill={stageColors.discovery.fill}
              stroke={stageColors.discovery.stroke}
              strokeWidth="3"
            />
            <text x="310" y="80" textAnchor="middle" fill={colors.textPrimary} fontSize="15" fontWeight="700">
              Triage
            </text>
            <text x="310" y="100" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              GO / NO-GO gate
            </text>
            {/* Decision badges */}
            <rect x="250" y="112" width="35" height="18" rx="4" fill="#22c55e" fillOpacity="0.3" />
            <text x="267" y="125" textAnchor="middle" fill="#22c55e" fontSize="10" fontWeight="600">GO</text>
            <rect x="292" y="112" width="50" height="18" rx="4" fill="#ef4444" fillOpacity="0.3" />
            <text x="317" y="125" textAnchor="middle" fill="#ef4444" fontSize="10" fontWeight="600">NO-GO</text>
            <rect x="349" y="112" width="30" height="18" rx="4" fill="#f59e0b" fillOpacity="0.3" />
            <text x="364" y="125" textAnchor="middle" fill="#f59e0b" fontSize="9" fontWeight="600">?</text>
          </g>

          {/* Arrow: Triage -> Discovery Planner (down) */}
          <path d="M 310 140 L 310 170" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Discovery Planner */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[2])}
          >
            <rect
              x="200" y="180" width="140" height="70"
              rx="8"
              fill={stageColors.discovery.fill}
              stroke={stageColors.discovery.stroke}
              strokeWidth="2"
            />
            <text x="270" y="210" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Discovery Planner
            </text>
            <text x="270" y="230" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Session agendas
            </text>
          </g>

          {/* Arrow: Planner -> Coverage Tracker */}
          <path d="M 340 215 L 370 215" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Coverage Tracker */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[3])}
          >
            <rect
              x="380" y="180" width="140" height="70"
              rx="8"
              fill={stageColors.discovery.fill}
              stroke={stageColors.discovery.stroke}
              strokeWidth="2"
            />
            <text x="450" y="210" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Coverage Tracker
            </text>
            <text x="450" y="230" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              READY / GAPS
            </text>
          </g>

          {/* ===== STAGE 2: INTELLIGENCE (1 agent) ===== */}

          {/* Arrow: Coverage -> Insight Extractor */}
          <path d="M 520 215 L 540 215" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Insight Extractor */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[4])}
          >
            <rect
              x="550" y="165" width="160" height="100"
              rx="10"
              fill={stageColors.intelligence.fill}
              stroke={stageColors.intelligence.stroke}
              strokeWidth="3"
            />
            <text x="630" y="200" textAnchor="middle" fill={colors.textPrimary} fontSize="15" fontWeight="700">
              Insight Extractor
            </text>
            <text x="630" y="220" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              Patterns with evidence
            </text>
            <text x="630" y="245" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              from transcripts
            </text>
          </g>

          {/* ===== STAGE 3: SYNTHESIS (2 agents) ===== */}

          {/* Arrow: Insight -> Consolidator */}
          <path d="M 710 215 L 740 215" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Consolidator */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[5])}
          >
            <rect
              x="750" y="165" width="140" height="70"
              rx="8"
              fill={stageColors.synthesis.fill}
              stroke={stageColors.synthesis.stroke}
              strokeWidth="2"
            />
            <text x="820" y="195" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Consolidator
            </text>
            <text x="820" y="215" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Decision document
            </text>
          </g>

          {/* Arrow: Consolidator -> Strategist (down) */}
          <path d="M 820 235 L 820 270" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Strategist */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[6])}
          >
            <rect
              x="750" y="280" width="140" height="70"
              rx="8"
              fill={stageColors.synthesis.fill}
              stroke={stageColors.synthesis.stroke}
              strokeWidth="2"
            />
            <text x="820" y="310" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Strategist
            </text>
            <text x="820" y="330" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Feature bundles
            </text>
          </g>

          {/* ===== STAGE 4: CAPABILITIES (2 agents) ===== */}

          {/* Arrow: Strategist -> PRD Generator */}
          <path d="M 890 315 L 960 315" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* PRD Generator */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[7])}
          >
            <rect
              x="970" y="280" width="140" height="70"
              rx="8"
              fill={stageColors.capabilities.fill}
              stroke={stageColors.capabilities.stroke}
              strokeWidth="2"
            />
            <text x="1040" y="310" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              PRD Generator
            </text>
            <text x="1040" y="330" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Product requirements
            </text>
          </g>

          {/* Arrow: Consolidator -> Tech Evaluation (side route) */}
          <path d="M 890 200 L 960 200" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* Tech Evaluation */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedStep(processSteps[8])}
          >
            <rect
              x="970" y="165" width="140" height="70"
              rx="8"
              fill={stageColors.capabilities.fill}
              stroke={stageColors.capabilities.stroke}
              strokeWidth="2"
            />
            <text x="1040" y="195" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Tech Evaluation
            </text>
            <text x="1040" y="215" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Technical feasibility
            </text>
          </g>

          {/* ===== DOCUMENTS INPUT ===== */}
          <g>
            <rect
              x="50" y="180" width="120" height="50"
              rx="6"
              fill="rgba(100, 116, 139, 0.1)"
              stroke="#64748b"
              strokeWidth="1"
              strokeDasharray="4 2"
            />
            <text x="110" y="200" textAnchor="middle" fill="#64748b" fontSize="11" fontWeight="500">
              Documents
            </text>
            <text x="110" y="215" textAnchor="middle" fill="#64748b" fontSize="10">
              (uploaded)
            </text>
          </g>

          {/* Arrow: Documents -> Prep */}
          <path d="M 110 180 L 110 140 L 120 130" fill="none" stroke="#64748b" strokeWidth="1" strokeDasharray="4 2" markerEnd="url(#arrowhead)" />

          {/* ===== OUTPUTS ===== */}

          {/* Approved Bundles */}
          <g>
            <rect
              x="750" y="380" width="140" height="50"
              rx="6"
              fill="rgba(139, 92, 246, 0.1)"
              stroke="#8b5cf6"
              strokeWidth="1"
              strokeDasharray="4 2"
            />
            <text x="820" y="400" textAnchor="middle" fill="#8b5cf6" fontSize="11" fontWeight="500">
              Approved Bundles
            </text>
            <text x="820" y="415" textAnchor="middle" fill="#8b5cf6" fontSize="10">
              (user review)
            </text>
          </g>

          {/* Arrow: Strategist -> Approved */}
          <path d="M 820 350 L 820 375" fill="none" stroke="#8b5cf6" strokeWidth="1" strokeDasharray="4 2" markerEnd="url(#arrowhead)" />

          {/* Arrow: Approved -> PRD */}
          <path d="M 890 405 L 940 405 L 940 340 L 970 340" fill="none" stroke="#8b5cf6" strokeWidth="1" strokeDasharray="4 2" markerEnd="url(#arrowhead)" />

          {/* Final Output: PRD */}
          <g>
            <rect
              x="970" y="380" width="140" height="50"
              rx="6"
              fill="rgba(34, 197, 94, 0.15)"
              stroke="#22c55e"
              strokeWidth="2"
            />
            <text x="1040" y="402" textAnchor="middle" fill="#22c55e" fontSize="12" fontWeight="600">
              PRD Document
            </text>
            <text x="1040" y="418" textAnchor="middle" fill="#22c55e" fontSize="10">
              Ready for dev
            </text>
          </g>

          {/* Arrow: PRD Generator -> PRD Output */}
          <path d="M 1040 350 L 1040 375" fill="none" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrowhead)" />

          {/* ===== LEGEND ===== */}
          <g transform="translate(50, 460)">
            <text x="0" y="0" fill={colors.textSecondary} fontSize="12" fontWeight="600">Legend</text>

            <rect x="0" y="15" width="16" height="12" rx="2" fill={stageColors.discovery.fill} stroke={stageColors.discovery.stroke} strokeWidth="1" />
            <text x="22" y="25" fill={colors.textSecondary} fontSize="11">Discovery (4 agents)</text>

            <rect x="130" y="15" width="16" height="12" rx="2" fill={stageColors.intelligence.fill} stroke={stageColors.intelligence.stroke} strokeWidth="1" />
            <text x="152" y="25" fill={colors.textSecondary} fontSize="11">Intelligence (1 agent)</text>

            <rect x="280" y="15" width="16" height="12" rx="2" fill={stageColors.synthesis.fill} stroke={stageColors.synthesis.stroke} strokeWidth="1" />
            <text x="302" y="25" fill={colors.textSecondary} fontSize="11">Synthesis (2 agents)</text>

            <rect x="420" y="15" width="16" height="12" rx="2" fill={stageColors.capabilities.fill} stroke={stageColors.capabilities.stroke} strokeWidth="1" />
            <text x="442" y="25" fill={colors.textSecondary} fontSize="11">Capabilities (2 agents)</text>

            <text x="600" y="25" fill={colors.textSecondary} fontSize="11">Click any box for details</text>
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
        </div>
      )}
    </div>
  )
}
