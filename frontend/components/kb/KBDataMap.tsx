'use client'

import { useState } from 'react'
import { X } from 'lucide-react'

type DataNode = {
  id: string
  title: string
  description: string
  category: 'source' | 'storage' | 'processing' | 'output' | 'entity'
  details: string[]
}

const dataNodes: DataNode[] = [
  // Sources
  {
    id: 'upload',
    title: 'Manual Upload',
    description: 'PDF, DOCX, MD, CSV, JSON',
    category: 'source',
    details: [
      'Drag and drop or file picker',
      'Supports: PDF, DOCX, MD, TXT, CSV, JSON, XML',
      'Max file size: 50MB',
      'Batch upload supported'
    ]
  },
  {
    id: 'local_vault',
    title: 'Local Vault',
    description: 'Filesystem Sync',
    category: 'source',
    details: [
      'Bidirectional sync with local vault',
      'Watches for file changes',
      'Supports frontmatter metadata',
      'Preserves folder structure'
    ]
  },
  {
    id: 'gdrive',
    title: 'Google Drive',
    description: 'Cloud document sync',
    category: 'source',
    details: [
      'OAuth integration',
      'Selective folder sync',
      'Supports Docs, Sheets, PDFs',
      'Automatic change detection'
    ]
  },
  {
    id: 'chat',
    title: 'Chat Conversations',
    description: 'Agent interactions',
    category: 'source',
    details: [
      'User questions and agent responses',
      'Linked to specific agents',
      'Searchable message history',
      'Context for future queries'
    ]
  },
  // Storage
  {
    id: 'documents',
    title: 'Documents Table',
    description: 'Metadata & content',
    category: 'storage',
    details: [
      'Stores document metadata',
      'Links to source (vault, drive, upload)',
      'Tracks processing status',
      'Classification and tags'
    ]
  },
  {
    id: 'chunks',
    title: 'Document Chunks',
    description: 'Segmented content',
    category: 'storage',
    details: [
      'Content split into ~800 char chunks',
      '200 char overlap for context',
      'Section headers preserved',
      'Linked to parent document'
    ]
  },
  {
    id: 'embeddings',
    title: 'Vector Embeddings',
    description: 'Voyage AI vectors',
    category: 'storage',
    details: [
      'voyage-3 embedding model',
      '1024-dimensional vectors',
      'Enables semantic search',
      'Stored with chunk reference'
    ]
  },
  // Processing
  {
    id: 'classifier',
    title: 'Document Classifier',
    description: 'Agent relevance tagging',
    category: 'processing',
    details: [
      'Analyzes document content',
      'Tags with relevant agents',
      'Confidence scoring (high/medium/low)',
      'Auto-approve above 80% confidence'
    ]
  },
  {
    id: 'extractor',
    title: 'Entity Extractor',
    description: 'People, tasks, projects',
    category: 'processing',
    details: [
      'LLM-powered extraction',
      'Identifies stakeholders',
      'Finds action items',
      'Detects project mentions'
    ]
  },
  // Outputs/Entities
  {
    id: 'agents',
    title: 'Agents',
    description: '21 specialized agents',
    category: 'entity',
    details: [
      'Atlas, Capital, Guardian, etc.',
      'Use classified documents as context',
      'Smart Brevity responses',
      'Memory via Mem0'
    ]
  },
  {
    id: 'tasks',
    title: 'Tasks',
    description: 'Action items',
    category: 'entity',
    details: [
      'Extracted from documents',
      'Kanban board management',
      'Assignable to stakeholders',
      'Due date tracking'
    ]
  },
  {
    id: 'projects',
    title: 'Projects',
    description: 'AI initiatives',
    category: 'entity',
    details: [
      'Pipeline stages',
      'Scoring (ROI, effort, alignment)',
      'Tier calculation',
      'Stakeholder linkage'
    ]
  },
  {
    id: 'stakeholders',
    title: 'Stakeholders',
    description: 'People tracking',
    category: 'entity',
    details: [
      'Roles and departments',
      'Engagement levels',
      'Sentiment tracking',
      'Meeting prep context'
    ]
  },
  {
    id: 'search',
    title: 'Semantic Search',
    description: 'RAG retrieval',
    category: 'output',
    details: [
      'Query embedding generated',
      'Cosine similarity search',
      'Top-k chunk retrieval',
      'Context passed to agents'
    ]
  }
]

// Category colors
const categoryColors = {
  source: {
    fill: 'url(#sourceGradient)',
    stroke: '#3b82f6', // blue
    text: '#3b82f6',
    light: 'rgba(59, 130, 246, 0.15)'
  },
  storage: {
    fill: 'url(#storageGradient)',
    stroke: '#8b5cf6', // violet
    text: '#8b5cf6',
    light: 'rgba(139, 92, 246, 0.15)'
  },
  processing: {
    fill: 'url(#processingGradient)',
    stroke: '#f59e0b', // amber
    text: '#f59e0b',
    light: 'rgba(245, 158, 11, 0.15)'
  },
  entity: {
    fill: 'url(#entityGradient)',
    stroke: '#22c55e', // green
    text: '#22c55e',
    light: 'rgba(34, 197, 94, 0.15)'
  },
  output: {
    fill: 'url(#outputGradient)',
    stroke: '#14b8a6', // teal
    text: '#14b8a6',
    light: 'rgba(20, 184, 166, 0.15)'
  }
}

const colors = {
  textPrimary: 'currentColor',
  textSecondary: '#9ca3af',
  arrow: '#60a5fa',
  arrowLight: '#94a3b8',
}

export default function KBDataMap() {
  const [selectedNode, setSelectedNode] = useState<DataNode | null>(null)

  return (
    <div className="bg-card rounded-lg border border-default p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-primary">Knowledge Base Data Flow</h2>
        <p className="text-sm text-secondary mt-1">Click any box for details</p>
      </div>

      {/* SVG Data Map */}
      <div className="overflow-x-auto text-primary">
        <svg
          viewBox="0 0 1100 540"
          className="w-full min-w-[900px]"
          style={{ maxHeight: '540px' }}
        >
          {/* Definitions */}
          <defs>
            {/* Source gradient (blue) */}
            <linearGradient id="sourceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
            </linearGradient>

            {/* Storage gradient (violet) */}
            <linearGradient id="storageGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.1" />
            </linearGradient>

            {/* Processing gradient (amber) */}
            <linearGradient id="processingGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.1" />
            </linearGradient>

            {/* Entity gradient (green) */}
            <linearGradient id="entityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0.1" />
            </linearGradient>

            {/* Output gradient (teal) */}
            <linearGradient id="outputGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#14b8a6" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#14b8a6" stopOpacity="0.1" />
            </linearGradient>

            {/* Arrow markers */}
            <marker id="arrowBlue" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill={colors.arrow} />
            </marker>
            <marker id="arrowLight" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill={colors.arrowLight} />
            </marker>
          </defs>

          {/* ===== COLUMN LABELS ===== */}
          <text x="120" y="30" textAnchor="middle" fill="#3b82f6" fontSize="18" fontWeight="700">
            SOURCES
          </text>
          <text x="380" y="30" textAnchor="middle" fill="#8b5cf6" fontSize="18" fontWeight="700">
            STORAGE
          </text>
          <text x="640" y="30" textAnchor="middle" fill="#f59e0b" fontSize="18" fontWeight="700">
            PROCESSING
          </text>
          <text x="910" y="30" textAnchor="middle" fill="#22c55e" fontSize="18" fontWeight="700">
            ENTITIES / OUTPUTS
          </text>

          {/* ===== SOURCES (left column) ===== */}

          {/* Manual Upload */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[0])}
          >
            <rect x="40" y="60" width="160" height="60" rx="8"
              fill={categoryColors.source.fill} stroke={categoryColors.source.stroke} strokeWidth="2" />
            <text x="120" y="85" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Manual Upload
            </text>
            <text x="120" y="102" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              PDF, DOCX, MD, CSV
            </text>
          </g>

          {/* Local Vault */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[1])}
          >
            <rect x="40" y="140" width="160" height="60" rx="8"
              fill={categoryColors.source.fill} stroke={categoryColors.source.stroke} strokeWidth="2" />
            <text x="120" y="165" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Local Vault
            </text>
            <text x="120" y="182" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Filesystem Sync
            </text>
          </g>

          {/* Google Drive */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[2])}
          >
            <rect x="40" y="220" width="160" height="60" rx="8"
              fill={categoryColors.source.fill} stroke={categoryColors.source.stroke} strokeWidth="2" />
            <text x="120" y="245" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Google Drive
            </text>
            <text x="120" y="262" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Cloud sync
            </text>
          </g>

          {/* Chat Conversations */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[3])}
          >
            <rect x="40" y="300" width="160" height="60" rx="8"
              fill={categoryColors.source.fill} stroke={categoryColors.source.stroke} strokeWidth="2" />
            <text x="120" y="325" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Chat Conversations
            </text>
            <text x="120" y="342" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Agent interactions
            </text>
          </g>

          {/* ===== ARROWS: Sources -> Documents ===== */}
          <path d="M 200 90 L 280 180" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />
          <path d="M 200 170 L 280 180" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />
          <path d="M 200 250 L 280 210" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />
          <path d="M 200 330 L 280 220" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />

          {/* ===== STORAGE (middle-left) ===== */}

          {/* Documents Table (central hub) */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[4])}
          >
            <rect x="290" y="150" width="180" height="100" rx="10"
              fill={categoryColors.storage.fill} stroke={categoryColors.storage.stroke} strokeWidth="3" />
            <text x="380" y="185" textAnchor="middle" fill={colors.textPrimary} fontSize="15" fontWeight="700">
              Documents Table
            </text>
            <text x="380" y="205" textAnchor="middle" fill={colors.textSecondary} fontSize="12">
              Metadata & content
            </text>
            <text x="380" y="235" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              (Supabase)
            </text>
          </g>

          {/* Document Chunks */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[5])}
          >
            <rect x="290" y="280" width="180" height="70" rx="8"
              fill={categoryColors.storage.fill} stroke={categoryColors.storage.stroke} strokeWidth="2" />
            <text x="380" y="310" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Document Chunks
            </text>
            <text x="380" y="330" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              ~800 char segments
            </text>
          </g>

          {/* Vector Embeddings */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[6])}
          >
            <rect x="290" y="380" width="180" height="70" rx="8"
              fill={categoryColors.storage.fill} stroke={categoryColors.storage.stroke} strokeWidth="2" />
            <text x="380" y="410" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Vector Embeddings
            </text>
            <text x="380" y="430" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Voyage AI (1024-dim)
            </text>
          </g>

          {/* Arrows: Documents -> Chunks -> Embeddings */}
          <path d="M 380 250 L 380 275" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />
          <path d="M 380 350 L 380 375" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />

          {/* ===== PROCESSING (middle-right) ===== */}

          {/* Document Classifier */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[7])}
          >
            <rect x="550" y="150" width="180" height="70" rx="8"
              fill={categoryColors.processing.fill} stroke={categoryColors.processing.stroke} strokeWidth="2" />
            <text x="640" y="180" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Document Classifier
            </text>
            <text x="640" y="200" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Agent relevance tagging
            </text>
          </g>

          {/* Entity Extractor */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[8])}
          >
            <rect x="550" y="250" width="180" height="70" rx="8"
              fill={categoryColors.processing.fill} stroke={categoryColors.processing.stroke} strokeWidth="2" />
            <text x="640" y="280" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Entity Extractor
            </text>
            <text x="640" y="300" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Tasks, Projects, People
            </text>
          </g>

          {/* Arrows: Documents -> Processing */}
          <path d="M 470 185 L 545 185" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />
          <path d="M 470 200 L 500 200 L 500 285 L 545 285" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />

          {/* ===== SEMANTIC SEARCH (bottom center) ===== */}

          {/* Semantic Search */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[13])}
          >
            <rect x="550" y="380" width="180" height="70" rx="8"
              fill={categoryColors.output.fill} stroke={categoryColors.output.stroke} strokeWidth="2" />
            <text x="640" y="410" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Semantic Search
            </text>
            <text x="640" y="430" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              RAG retrieval
            </text>
          </g>

          {/* Arrow: Embeddings -> Search */}
          <path d="M 470 415 L 545 415" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />

          {/* ===== ENTITIES (right column) ===== */}

          {/* Agents */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[9])}
          >
            <rect x="820" y="100" width="180" height="80" rx="8"
              fill={categoryColors.entity.fill} stroke={categoryColors.entity.stroke} strokeWidth="2" />
            <text x="910" y="130" textAnchor="middle" fill={colors.textPrimary} fontSize="14" fontWeight="600">
              Agents
            </text>
            <text x="910" y="150" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              21 specialized agents
            </text>
            <text x="910" y="168" textAnchor="middle" fill={colors.textSecondary} fontSize="10">
              Atlas, Capital, Guardian...
            </text>
          </g>

          {/* Tasks */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[10])}
          >
            <rect x="820" y="200" width="180" height="70" rx="8"
              fill={categoryColors.entity.fill} stroke={categoryColors.entity.stroke} strokeWidth="2" />
            <text x="910" y="230" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Tasks
            </text>
            <text x="910" y="250" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              Action items
            </text>
          </g>

          {/* Projects */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[11])}
          >
            <rect x="820" y="290" width="180" height="70" rx="8"
              fill={categoryColors.entity.fill} stroke={categoryColors.entity.stroke} strokeWidth="2" />
            <text x="910" y="320" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Projects
            </text>
            <text x="910" y="340" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              AI initiatives
            </text>
          </g>

          {/* Stakeholders */}
          <g
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setSelectedNode(dataNodes[12])}
          >
            <rect x="820" y="380" width="180" height="70" rx="8"
              fill={categoryColors.entity.fill} stroke={categoryColors.entity.stroke} strokeWidth="2" />
            <text x="910" y="410" textAnchor="middle" fill={colors.textPrimary} fontSize="13" fontWeight="600">
              Stakeholders
            </text>
            <text x="910" y="430" textAnchor="middle" fill={colors.textSecondary} fontSize="11">
              People tracking
            </text>
          </g>

          {/* ===== ARROWS: Processing -> Entities ===== */}

          {/* Classifier -> Agents */}
          <path d="M 730 175 L 770 175 L 770 140 L 815 140" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />

          {/* Extractor -> Tasks, Projects, Stakeholders */}
          <path d="M 730 285 L 770 285 L 770 235 L 815 235" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />
          <path d="M 730 285 L 770 285 L 770 325 L 815 325" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />
          <path d="M 730 285 L 770 285 L 770 415 L 815 415" fill="none" stroke={colors.arrow} strokeWidth="2" markerEnd="url(#arrowBlue)" />

          {/* Search -> Agents (context) */}
          <path d="M 730 400 L 780 400 L 780 160 L 815 160" fill="none" stroke={categoryColors.output.stroke} strokeWidth="2" strokeDasharray="4 2" markerEnd="url(#arrowBlue)" />

          {/* ===== Chat -> Agents (routed around outside bottom) ===== */}
          <path d="M 120 360 L 120 500 L 1050 500 L 1050 140 L 1005 140" fill="none" stroke={colors.arrowLight} strokeWidth="1" strokeDasharray="4 2" markerEnd="url(#arrowLight)" />
        </svg>
      </div>

      {/* Details Panel */}
      {selectedNode && (
        <div className="mt-6 p-4 bg-hover rounded-lg border border-default">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-primary">{selectedNode.title}</h3>
                <span
                  className="px-2 py-0.5 rounded text-xs font-medium capitalize"
                  style={{
                    backgroundColor: categoryColors[selectedNode.category].light,
                    color: categoryColors[selectedNode.category].text
                  }}
                >
                  {selectedNode.category}
                </span>
              </div>
              <p className="text-sm text-secondary mt-1">{selectedNode.description}</p>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-muted hover:text-primary"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <ul className="mt-3 space-y-1">
            {selectedNode.details.map((detail, index) => (
              <li key={index} className="text-sm text-secondary flex items-start">
                <span className="mr-2" style={{ color: categoryColors[selectedNode.category].text }}>-</span>
                {detail}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
