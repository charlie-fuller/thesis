'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { apiGet } from '@/lib/api'
import LoadingSpinner from './LoadingSpinner'
import toast from 'react-hot-toast'

interface Template {
  id: string
  prompt: string
  category: string
  addie_phase: string
  priority: number
  keywords: string[]
}

interface PhaseData {
  name: string
  description: string
  color: string
  categories: string[]
  template_count: number
  templates: Template[]
}

interface TemplatesByPhaseResponse {
  success: boolean
  phases: Record<string, PhaseData>
  error?: string
}

// Phase color configuration
const PHASE_COLORS: Record<string, { bg: string; text: string; border: string; badge: string }> = {
  'green': { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-200', badge: 'bg-green-100 text-green-700' },
  'blue': { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-700' },
  'purple': { bg: 'bg-purple-50', text: 'text-purple-800', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-700' },
  'orange': { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-700' },
  'pink': { bg: 'bg-pink-50', text: 'text-pink-800', border: 'border-pink-200', badge: 'bg-pink-100 text-pink-700' },
  'gray': { bg: 'bg-gray-50', text: 'text-gray-800', border: 'border-gray-200', badge: 'bg-gray-100 text-gray-700' },
}

export default function TemplateLibrary() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<TemplatesByPhaseResponse | null>(null)
  const [selectedPhase, setSelectedPhase] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [copiedId, setCopiedId] = useState<string | null>(null)

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const result = await apiGet<TemplatesByPhaseResponse>('/api/templates/by-phase')
        if (result.success) {
          setData(result)
        }
      } catch (error) {
        console.error('Failed to fetch templates:', error)
        toast.error('Failed to load templates')
      } finally {
        setLoading(false)
      }
    }

    fetchTemplates()
  }, [])

  const handleCopyPrompt = async (template: Template) => {
    try {
      await navigator.clipboard.writeText(template.prompt)
      setCopiedId(template.id)
      toast.success('Copied to clipboard')
      setTimeout(() => setCopiedId(null), 2000)
    } catch {
      toast.error('Failed to copy')
    }
  }

  const handleUseInChat = (template: Template) => {
    // Navigate to chat with the prompt pre-filled
    router.push(`/chat?prompt=${encodeURIComponent(template.prompt)}`)
  }

  // Filter templates based on search and selected phase
  const getFilteredTemplates = (phase: PhaseData) => {
    if (!searchQuery) return phase.templates

    const query = searchQuery.toLowerCase()
    return phase.templates.filter(t =>
      t.prompt.toLowerCase().includes(query) ||
      t.category.toLowerCase().includes(query) ||
      t.keywords.some(k => k.toLowerCase().includes(query))
    )
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  if (!data?.phases) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-12 text-secondary">
          No templates available.
        </div>
      </div>
    )
  }

  const phases = Object.values(data.phases)
  const phaseOrder = ['Analysis', 'Design', 'Development', 'Implementation', 'Evaluation']
  const sortedPhases = phases.sort((a, b) =>
    phaseOrder.indexOf(a.name) - phaseOrder.indexOf(b.name)
  )

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-primary mb-2">
          Template Library
        </h1>
        <p className="text-secondary">
          Browse ADDIE-based templates to jumpstart your learning design conversations
        </p>
      </div>

      {/* Search and Filter Bar */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        {/* Search */}
        <div className="flex-1 min-w-[200px] max-w-md">
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-default rounded-lg bg-card text-primary placeholder:text-secondary focus:outline-none focus:ring-2 focus:ring-brand/20 focus:border-brand"
          />
        </div>

        {/* Phase Filter Pills */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedPhase(null)}
            className={`px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
              selectedPhase === null
                ? 'bg-brand text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Phases
          </button>
          {sortedPhases.map((phase) => {
            const colors = PHASE_COLORS[phase.color] || PHASE_COLORS['gray']
            return (
              <button
                key={phase.name}
                onClick={() => setSelectedPhase(phase.name === selectedPhase ? null : phase.name)}
                className={`px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                  selectedPhase === phase.name
                    ? 'bg-brand text-white'
                    : `${colors.badge} hover:opacity-80`
                }`}
              >
                {phase.name} ({phase.template_count})
              </button>
            )
          })}
        </div>
      </div>

      {/* Template Grid by Phase */}
      <div className="space-y-8">
        {sortedPhases.map((phase) => {
          if (selectedPhase && selectedPhase !== phase.name) return null

          const colors = PHASE_COLORS[phase.color] || PHASE_COLORS['gray']
          const filteredTemplates = getFilteredTemplates(phase)

          if (filteredTemplates.length === 0 && searchQuery) return null

          return (
            <div key={phase.name} className={`rounded-xl border ${colors.border} overflow-hidden`}>
              {/* Phase Header */}
              <div className={`px-6 py-4 ${colors.bg}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className={`text-xl font-semibold ${colors.text}`}>
                      {phase.name}
                    </h2>
                    <p className="text-sm text-gray-600 mt-1">
                      {phase.description}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors.badge}`}>
                    {filteredTemplates.length} templates
                  </span>
                </div>

                {/* Categories */}
                {phase.categories.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {phase.categories.map((cat) => (
                      <span
                        key={cat}
                        className="text-xs px-2 py-1 bg-white/50 rounded text-gray-600"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Templates Grid */}
              <div className="p-4 bg-card grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {filteredTemplates.map((template) => (
                  <div
                    key={template.id}
                    className="group border border-default rounded-lg p-4 hover:border-brand/50 hover:shadow-sm transition-all bg-white"
                  >
                    {/* Category badge */}
                    <span className={`text-xs px-2 py-0.5 rounded ${colors.badge}`}>
                      {template.category}
                    </span>

                    {/* Prompt text */}
                    <p className="mt-3 text-sm text-primary font-medium leading-snug">
                      &quot;{template.prompt}&quot;
                    </p>

                    {/* Keywords */}
                    {template.keywords.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {template.keywords.slice(0, 3).map((keyword, i) => (
                          <span
                            key={i}
                            className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded"
                          >
                            {keyword}
                          </span>
                        ))}
                        {template.keywords.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{template.keywords.length - 3} more
                          </span>
                        )}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="mt-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleCopyPrompt(template)}
                        className="flex-1 px-3 py-1.5 text-xs font-medium border border-default rounded hover:bg-gray-50 transition-colors"
                      >
                        {copiedId === template.id ? 'Copied!' : 'Copy'}
                      </button>
                      <button
                        onClick={() => handleUseInChat(template)}
                        className="flex-1 px-3 py-1.5 text-xs font-medium text-white bg-brand rounded hover:bg-brand/90 transition-colors"
                      >
                        Use in Chat
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Empty state for search */}
      {searchQuery && sortedPhases.every(p => getFilteredTemplates(p).length === 0) && (
        <div className="text-center py-12 text-secondary">
          No templates match your search. Try different keywords.
        </div>
      )}
    </div>
  )
}
