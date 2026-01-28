'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { apiGet } from '@/lib/api'
import { logger } from '@/lib/logger'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import { AgentIcon, getAgentColor } from '@/components/AgentIcon'

interface Agent {
  id: string
  name: string
  display_name: string
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  instruction_versions_count: number
  kb_documents_count: number
  conversations_count: number
  meeting_rooms_count: number
}

export default function AgentsPage() {
  const router = useRouter()
  const { user, session, loading: authLoading } = useAuth()
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadAgentData() {
    try {
      setLoading(true)
      setError(null)
      const data = await apiGet<{ agents: Agent[] }>('/api/agents?include_inactive=true')
      setAgents(data.agents || [])
    } catch (err) {
      logger.error('Failed to fetch agents:', err)
      setError('Failed to load agents')
    } finally {
      setLoading(false)
    }
  }

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login')
    }
  }, [authLoading, user, router])

  // Load data when authenticated
  useEffect(() => {
    if (!authLoading && user && session) {
      loadAgentData()
    }
  }, [authLoading, user, session])

  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-page">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-page">
      <PageHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-primary">Agents</h1>
          <p className="text-secondary mt-1">AI agents available for chat and meeting rooms</p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center py-20">
            <p className="text-red-400">{error}</p>
            <button
              onClick={loadAgentData}
              className="mt-4 btn-primary"
            >
              Retry
            </button>
          </div>
        )}

        {/* Agent Grid */}
        {!loading && !error && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {agents.map((agent) => (
                <Link
                  key={agent.id}
                  href={`/admin/agents/${agent.id}`}
                  className="card p-6 hover:border-primary/50 transition-all group"
                >
                  {/* Agent Header */}
                  <div className="flex items-start gap-4 mb-4">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center border ${getAgentColor(agent.name)}`}>
                      <AgentIcon name={agent.name} size="lg" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-primary group-hover:text-blue-400 transition-colors">
                        {agent.display_name}
                      </h3>
                      <p className="text-sm text-secondary">
                        {agent.name}
                      </p>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${
                      agent.is_active
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {agent.is_active ? 'Active' : 'Inactive'}
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-secondary mb-4 line-clamp-2">
                    {agent.description || 'No description configured'}
                  </p>

                  {/* Stats */}
                  <div className="grid grid-cols-4 gap-3 pt-4 border-t border-border">
                    <div className="text-center">
                      <div className="text-lg font-semibold text-primary">
                        {agent.instruction_versions_count}
                      </div>
                      <div className="text-xs text-secondary">Versions</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-primary">
                        {agent.kb_documents_count}
                      </div>
                      <div className="text-xs text-secondary">KB Docs</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-primary">
                        {agent.conversations_count ?? 0}
                      </div>
                      <div className="text-xs text-secondary">Chats</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold text-primary">
                        {agent.meeting_rooms_count ?? 0}
                      </div>
                      <div className="text-xs text-secondary">Meetings</div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {agents.length === 0 && (
              <div className="text-center py-20 card">
                <p className="text-secondary">No agents configured yet</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
