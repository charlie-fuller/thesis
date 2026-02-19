'use client'

import { useState } from 'react'
import {
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight
} from 'lucide-react'

// ============================================================================
// TYPES
// ============================================================================

interface ProblemStatement {
  id?: string
  text: string
  rejected?: boolean
  rejection_reason?: string
}

interface Hypothesis {
  id?: string
  statement: string
  rationale?: string
  type?: string
  rejected?: boolean
  rejection_reason?: string
}

interface Gap {
  id?: string
  description: string
  type?: string
  rejected?: boolean
  rejection_reason?: string
}

export interface Throughline {
  problem_statements?: ProblemStatement[]
  hypotheses?: Hypothesis[]
  gaps?: Gap[]
  desired_outcome_state?: string
}

interface ThroughlineEditorProps {
  throughline: Throughline
  onChange: (throughline: Throughline) => void
  corrections?: string
  onCorrectionsChange?: (val: string) => void
}

// ============================================================================
// HELPERS
// ============================================================================

const HYPOTHESIS_TYPES = [
  { value: 'assumption', label: 'Assumption' },
  { value: 'belief', label: 'Belief' },
  { value: 'prediction', label: 'Prediction' },
]

const GAP_TYPES = [
  { value: 'data', label: 'Data' },
  { value: 'people', label: 'People' },
  { value: 'process', label: 'Process' },
  { value: 'capability', label: 'Capability' },
]

// ============================================================================
// SECTION COMPONENT
// ============================================================================

function CollapsibleSection({
  title,
  count,
  defaultOpen = false,
  children,
}: {
  title: string
  count: number
  defaultOpen?: boolean
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-lg">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg"
      >
        <span className="flex items-center gap-2">
          {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          {title}
          {count > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded">
              {count}
            </span>
          )}
        </span>
      </button>
      {open && <div className="px-3 pb-3 space-y-2">{children}</div>}
    </div>
  )
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ThroughlineEditor({ throughline, onChange, corrections, onCorrectionsChange }: ThroughlineEditorProps) {
  const problems = throughline.problem_statements || []
  const hypotheses = throughline.hypotheses || []
  const gaps = throughline.gaps || []

  // Problem Statements
  const addProblem = () => {
    onChange({
      ...throughline,
      problem_statements: [...problems, { text: '' }],
    })
  }

  const updateProblem = (index: number, text: string) => {
    const updated = [...problems]
    updated[index] = { ...updated[index], text }
    onChange({ ...throughline, problem_statements: updated })
  }

  const removeProblem = (index: number) => {
    onChange({
      ...throughline,
      problem_statements: problems.filter((_, i) => i !== index),
    })
  }

  // Hypotheses
  const addHypothesis = () => {
    onChange({
      ...throughline,
      hypotheses: [...hypotheses, { statement: '', type: 'assumption' }],
    })
  }

  const updateHypothesis = (index: number, field: string, value: string) => {
    const updated = [...hypotheses]
    updated[index] = { ...updated[index], [field]: value }
    onChange({ ...throughline, hypotheses: updated })
  }

  const removeHypothesis = (index: number) => {
    onChange({
      ...throughline,
      hypotheses: hypotheses.filter((_, i) => i !== index),
    })
  }

  // Gaps
  const addGap = () => {
    onChange({
      ...throughline,
      gaps: [...gaps, { description: '', type: 'data' }],
    })
  }

  const updateGap = (index: number, field: string, value: string) => {
    const updated = [...gaps]
    updated[index] = { ...updated[index], [field]: value }
    onChange({ ...throughline, gaps: updated })
  }

  const removeGap = (index: number) => {
    onChange({
      ...throughline,
      gaps: gaps.filter((_, i) => i !== index),
    })
  }

  return (
    <div className="space-y-3">
      {/* Problem Statements */}
      <CollapsibleSection title="Problem Statements" count={problems.length} defaultOpen>
        {problems.map((ps, i) => (
          <div key={i} className="flex items-center gap-2">
            <input
              type="text"
              value={ps.text}
              onChange={(e) => updateProblem(i, e.target.value)}
              placeholder="Describe the problem..."
              className="input-field !w-auto flex-1 min-w-0 text-sm"
            />
            <button
              type="button"
              onClick={() => removeProblem(i)}
              className="p-1 text-slate-400 hover:text-red-500 shrink-0"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={addProblem}
          className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300"
        >
          <Plus className="w-3 h-3" />
          Add problem statement
        </button>
      </CollapsibleSection>

      {/* Hypotheses */}
      <CollapsibleSection title="Hypotheses" count={hypotheses.length} defaultOpen>
        {hypotheses.map((h, i) => (
          <div key={i} className="flex items-center gap-2">
            <input
              type="text"
              value={h.statement}
              onChange={(e) => updateHypothesis(i, 'statement', e.target.value)}
              placeholder="State the hypothesis..."
              className="input-field !w-auto flex-1 min-w-0 text-sm"
            />
            <select
              value={h.type || 'assumption'}
              onChange={(e) => updateHypothesis(i, 'type', e.target.value)}
              className="input-field !w-auto w-28 text-sm shrink-0"
            >
              {HYPOTHESIS_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => removeHypothesis(i)}
              className="p-1 text-slate-400 hover:text-red-500 shrink-0"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={addHypothesis}
          className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300"
        >
          <Plus className="w-3 h-3" />
          Add hypothesis
        </button>
      </CollapsibleSection>

      {/* Gaps */}
      <CollapsibleSection title="Known Gaps" count={gaps.length} defaultOpen>
        {gaps.map((g, i) => (
          <div key={i} className="flex items-center gap-2">
            <input
              type="text"
              value={g.description}
              onChange={(e) => updateGap(i, 'description', e.target.value)}
              placeholder="Describe the gap..."
              className="input-field !w-auto flex-1 min-w-0 text-sm"
            />
            <select
              value={g.type || 'data'}
              onChange={(e) => updateGap(i, 'type', e.target.value)}
              className="input-field !w-auto w-28 text-sm shrink-0"
            >
              {GAP_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => removeGap(i)}
              className="p-1 text-slate-400 hover:text-red-500 shrink-0"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={addGap}
          className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300"
        >
          <Plus className="w-3 h-3" />
          Add gap
        </button>
      </CollapsibleSection>

      {/* Desired Outcome State */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
          Desired Outcome State
        </label>
        <textarea
          value={throughline.desired_outcome_state || ''}
          onChange={(e) => onChange({ ...throughline, desired_outcome_state: e.target.value })}
          placeholder="What does the world look like when this initiative succeeds?"
          rows={3}
          className="textarea-field text-sm"
        />
      </div>

      {/* Ground-Truth Corrections */}
      {onCorrectionsChange && (
        <CollapsibleSection title="Ground-Truth Corrections" count={corrections?.trim() ? 1 : 0}>
          <div className="space-y-1">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              These corrections override conflicting information in linked documents. Agents treat them as authoritative.
            </p>
            <textarea
              value={corrections || ''}
              onChange={(e) => onCorrectionsChange(e.target.value)}
              placeholder={"e.g.\n- Our company uses Salesforce, NOT HubSpot\n- Q3 revenue was $12M (not $8M as stated in the deck)\n- The n8n integration is owned by IT, not Engineering"}
              rows={4}
              className="textarea-field text-sm"
            />
          </div>
        </CollapsibleSection>
      )}
    </div>
  )
}
