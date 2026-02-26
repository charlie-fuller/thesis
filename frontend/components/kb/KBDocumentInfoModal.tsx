'use client'

import { useState, useEffect } from 'react'
import { apiGet, apiPost, apiPut, apiPatch, apiDelete, authenticatedFetch } from '@/lib/api'
import { logger } from '@/lib/logger'

interface DocumentTag {
  tag: string
  source: 'path' | 'frontmatter' | 'manual'
}

export interface Document {
  id: string
  title?: string
  filename: string
  uploaded_at: string
  original_date?: string
  processed: boolean
  processing_status?: string
  processing_error?: string
  storage_url: string
  external_url?: string
  google_drive_file_id?: string
  notion_page_id?: string
  sync_cadence?: string
  file_size?: number
  source_platform?: string
  obsidian_vault_path?: string
  obsidian_file_path?: string
  tags?: DocumentTag[]
}

interface Agent {
  id: string
  name: string
  display_name: string
}

interface KBDocumentInfoModalProps {
  isOpen: boolean
  document: Document | null
  onClose: () => void
  onSave: () => void
  onDocumentUpdate?: (updatedDoc: Document) => void
}

function formatDate(isoString: string) {
  const date = new Date(isoString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return 'Unknown'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

export default function KBDocumentInfoModal({
  isOpen,
  document: doc,
  onClose,
  onSave,
  onDocumentUpdate
}: KBDocumentInfoModalProps) {
  // Agent assignment state
  const [allAgents, setAllAgents] = useState<Agent[]>([])
  const [docIsGlobal, setDocIsGlobal] = useState<boolean>(true)
  const [docLinkedAgentIds, setDocLinkedAgentIds] = useState<Set<string>>(new Set())
  const [loadingAgentAssignments, setLoadingAgentAssignments] = useState(false)
  const [savingAgentAssignments, setSavingAgentAssignments] = useState(false)

  // Sync cadence state
  const [docSyncCadence, setDocSyncCadence] = useState<string>('manual')
  const [tempSyncCadence, setTempSyncCadence] = useState<string>('manual')

  // Original date state
  const [tempOriginalDate, setTempOriginalDate] = useState<string>('')

  // Tag management state
  const [newTagInput, setNewTagInput] = useState<string>('')
  const [addingTag, setAddingTag] = useState(false)
  const [removingTag, setRemovingTag] = useState<string | null>(null)
  const [localTags, setLocalTags] = useState<DocumentTag[]>([])

  // HTML preview state
  const [showHtmlPreview, setShowHtmlPreview] = useState(false)
  const [htmlContent, setHtmlContent] = useState<string | null>(null)
  const [loadingHtml, setLoadingHtml] = useState(false)

  // Error/success
  const [error, setError] = useState<string | null>(null)

  // Load data when modal opens
  useEffect(() => {
    if (isOpen && doc) {
      const currentCadence = doc.sync_cadence || 'manual'
      setDocSyncCadence(currentCadence)
      setTempSyncCadence(currentCadence)
      setTempOriginalDate(doc.original_date || '')
      setLocalTags(doc.tags || [])
      setNewTagInput('')
      setError(null)
      setShowHtmlPreview(false)
      setHtmlContent(null)

      // Load agents
      if (allAgents.length === 0) {
        loadAllAgents()
      }
      loadDocumentAgentAssignments(doc.id)

      // Lazy-load tags if not present
      if (!doc.tags?.length) {
        fetchTags(doc.id)
      }
    }
  }, [isOpen, doc?.id])

  async function loadAllAgents() {
    try {
      const data = await apiGet<{ agents: Agent[] }>('/api/agents?include_inactive=false')
      setAllAgents(data.agents || [])
    } catch (err) {
      logger.error('Failed to load agents:', err)
    }
  }

  async function loadDocumentAgentAssignments(documentId: string) {
    try {
      setLoadingAgentAssignments(true)
      const data = await apiGet<{
        is_global: boolean
        linked_agents: Array<{ id: string; name: string; display_name: string }>
      }>(`/api/documents/${documentId}/agents`)

      setDocIsGlobal(data.is_global)
      setDocLinkedAgentIds(new Set(data.linked_agents.map(a => a.id)))
    } catch (err) {
      logger.error('Failed to load document agent assignments:', err)
      setDocIsGlobal(true)
      setDocLinkedAgentIds(new Set())
    } finally {
      setLoadingAgentAssignments(false)
    }
  }

  async function fetchTags(documentId: string) {
    try {
      const data = await apiPost<{ tags: Record<string, DocumentTag[]> }>(
        '/api/documents/tags/batch',
        { document_ids: [documentId] }
      )
      if (data.tags?.[documentId]) {
        setLocalTags(data.tags[documentId])
      }
    } catch (err) {
      logger.error('Error fetching tags:', err)
    }
  }

  const isHtmlDoc = doc?.filename?.toLowerCase().endsWith('.html')

  async function loadHtmlPreview() {
    if (!doc?.storage_url) return
    setLoadingHtml(true)
    try {
      const res = await fetch(doc.storage_url)
      if (res.ok) {
        const text = await res.text()
        setHtmlContent(text)
        setShowHtmlPreview(true)
      }
    } catch (err) {
      logger.error('Failed to load HTML preview:', err)
    } finally {
      setLoadingHtml(false)
    }
  }

  function toggleDocAgentSelection(agentId: string) {
    setDocLinkedAgentIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(agentId)) {
        newSet.delete(agentId)
      } else {
        newSet.add(agentId)
      }
      return newSet
    })
  }

  async function handleAddTag() {
    if (!doc || !newTagInput.trim()) return

    const tag = newTagInput.trim()
    if (tag.length > 100) {
      setError('Tag must be 100 characters or less')
      setTimeout(() => setError(null), 3000)
      return
    }

    setAddingTag(true)
    try {
      await apiPost(`/api/documents/${doc.id}/tags`, { tag })
      const newTag: DocumentTag = { tag, source: 'manual' }
      setLocalTags(prev => [...prev, newTag])
      setNewTagInput('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add tag')
      setTimeout(() => setError(null), 3000)
    } finally {
      setAddingTag(false)
    }
  }

  async function handleRemoveTag(tag: string) {
    if (!doc) return

    setRemovingTag(tag)
    try {
      await apiDelete(`/api/documents/${doc.id}/tags/${encodeURIComponent(tag)}`)
      setLocalTags(prev => prev.filter(t => t.tag !== tag))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove tag')
      setTimeout(() => setError(null), 3000)
    } finally {
      setRemovingTag(null)
    }
  }

  async function handleSave() {
    if (!doc) return

    try {
      // Save sync cadence if changed
      if (tempSyncCadence !== docSyncCadence) {
        await apiPatch(`/api/documents/${doc.id}/sync-cadence`, {
          sync_cadence: tempSyncCadence
        })
        setDocSyncCadence(tempSyncCadence)
      }

      // Save original date if changed
      const currentOriginalDate = doc.original_date || ''
      if (tempOriginalDate !== currentOriginalDate) {
        await apiPatch(`/api/documents/${doc.id}/original-date`, {
          original_date: tempOriginalDate || null
        })
      }

      // Save agent assignments
      setSavingAgentAssignments(true)
      const newAgentIds = docIsGlobal ? [] : Array.from(docLinkedAgentIds)
      await apiPut(`/api/documents/${doc.id}/agents`, {
        agent_ids: newAgentIds
      })

      // Notify parent of changes
      if (onDocumentUpdate) {
        onDocumentUpdate({
          ...doc,
          sync_cadence: tempSyncCadence,
          original_date: tempOriginalDate || undefined,
          tags: localTags
        })
      }

      onSave()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update document')
      setTimeout(() => setError(null), 3000)
    } finally {
      setSavingAgentAssignments(false)
    }
  }

  if (!isOpen || !doc) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className={`bg-card rounded-lg shadow-xl w-full mx-4 p-6 max-h-[90vh] overflow-y-auto ${showHtmlPreview ? 'max-w-5xl' : 'max-w-lg'}`} onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="heading-3">Document Information</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <span className="text-sm text-red-800 dark:text-red-200">{error}</span>
          </div>
        )}

        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-secondary">Filename</label>
            <p className="text-sm text-primary mt-1">{doc.filename}</p>
          </div>

          <div>
            <label className="text-sm font-medium text-secondary">Document ID</label>
            <p className="text-xs text-muted font-mono mt-1">{doc.id}</p>
          </div>

          <div>
            <label className="text-sm font-medium text-secondary">Source</label>
            <p className="text-sm text-primary mt-1">
              {doc.source_platform === 'google_drive' ? 'Google Drive' : doc.source_platform === 'notion' ? 'Notion' : doc.source_platform === 'obsidian' ? 'Local Vault' : 'Direct Upload'}
            </p>
          </div>

          <div>
            <label className="text-sm font-medium text-secondary">Uploaded</label>
            <p className="text-sm text-primary mt-1">{formatDate(doc.uploaded_at)}</p>
          </div>

          <div>
            <label className="text-sm font-medium text-secondary">Original Document Date</label>
            <p className="text-xs text-muted mb-1">For meeting transcripts, enter the actual meeting date</p>
            <input
              type="date"
              value={tempOriginalDate}
              onChange={(e) => setTempOriginalDate(e.target.value)}
              className="w-full px-3 py-1.5 text-sm border border-default rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-card text-primary"
            />
            {tempOriginalDate && (
              <button
                type="button"
                onClick={() => setTempOriginalDate('')}
                className="mt-1 text-xs text-muted hover:text-primary"
              >
                Clear date
              </button>
            )}
          </div>

          <div>
            <label className="text-sm font-medium text-secondary">File Size</label>
            <p className="text-sm text-primary mt-1">{formatFileSize(doc.file_size)}</p>
          </div>

          {doc.external_url && (
            <div>
              <label className="text-sm font-medium text-secondary">External Link</label>
              <a
                href={doc.external_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline mt-1 inline-block"
              >
                View in {doc.source_platform === 'google_drive' ? 'Google Drive' : 'Source'}
              </a>
            </div>
          )}

          {doc.obsidian_file_path && (
            <div>
              <label className="text-sm font-medium text-secondary">Vault Path</label>
              <p className="text-sm text-primary mt-1 font-mono">{doc.obsidian_file_path}</p>
            </div>
          )}

          {/* HTML Preview Section */}
          {isHtmlDoc && doc?.storage_url && (
            <div className="border-t border-default pt-3 mt-3">
              {!showHtmlPreview ? (
                <button
                  onClick={loadHtmlPreview}
                  disabled={loadingHtml}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-blue-600 dark:text-blue-400 border border-blue-300 dark:border-blue-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors disabled:opacity-50"
                >
                  {loadingHtml ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                  Preview HTML
                </button>
              ) : (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-secondary">Preview</label>
                    <button
                      onClick={() => { setShowHtmlPreview(false); setHtmlContent(null) }}
                      className="text-xs text-muted hover:text-primary transition-colors"
                    >
                      Close preview
                    </button>
                  </div>
                  <div className="border border-default rounded-lg overflow-hidden h-[500px]">
                    {htmlContent ? (
                      <iframe
                        srcDoc={htmlContent}
                        sandbox="allow-scripts allow-same-origin"
                        className="w-full h-full border-0"
                        title={doc.filename}
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-sm text-muted">
                        Failed to load preview
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tags Section */}
          <div className="border-t border-default pt-3 mt-3">
            <label className="text-sm font-medium text-secondary block mb-2">Tags</label>

            <div className="flex flex-wrap gap-1.5 mb-3">
              {localTags.length === 0 ? (
                <span className="text-sm text-muted">No tags</span>
              ) : (
                localTags.map((t) => (
                  <span
                    key={t.tag}
                    className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded ${
                      t.source === 'path'
                        ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                        : t.source === 'frontmatter'
                          ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                          : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    }`}
                  >
                    {t.tag}
                    {t.source === 'path' || t.source === 'frontmatter' ? (
                      <span title={t.source === 'path' ? 'From folder path (read-only)' : 'From frontmatter (read-only)'}>
                        <svg className="w-3 h-3 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                        </svg>
                      </span>
                    ) : (
                      <button
                        onClick={() => handleRemoveTag(t.tag)}
                        disabled={removingTag === t.tag}
                        className="hover:text-red-600 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                        title="Remove tag"
                      >
                        {removingTag === t.tag ? (
                          <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        ) : (
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        )}
                      </button>
                    )}
                  </span>
                ))
              )}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={newTagInput}
                onChange={(e) => setNewTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    handleAddTag()
                  }
                }}
                placeholder="Add a tag..."
                className="flex-1 px-3 py-1.5 text-sm border border-default rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-card text-primary"
                maxLength={100}
              />
              <button
                onClick={handleAddTag}
                disabled={addingTag || !newTagInput.trim()}
                className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {addingTag ? 'Adding...' : 'Add'}
              </button>
            </div>
            <p className="text-xs text-muted mt-1">
              Amber tags are from folder path. Purple tags are from frontmatter. Blue tags are manually added.
            </p>
          </div>

          {/* Sync Cadence Setting */}
          {(doc.source_platform === 'google_drive' || doc.source_platform === 'notion') && (
            <div className="border-t border-default pt-3 mt-3">
              <label className="text-sm font-medium text-secondary block mb-2">
                Automatic Sync Cadence
              </label>
              <select
                value={tempSyncCadence}
                onChange={(e) => setTempSyncCadence(e.target.value)}
                className="w-full px-3 py-2 border border-default rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-card text-primary"
              >
                <option value="manual">Manual Only</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
              <p className="text-xs text-muted mt-1">
                Set how often this document should automatically sync from {doc.source_platform === 'google_drive' ? 'Google Drive' : 'Notion'}
              </p>
            </div>
          )}

          {/* Agent Assignment Section */}
          <div className="border-t border-default pt-3 mt-3">
            <label className="text-sm font-medium text-secondary block mb-2">
              Agent Visibility
            </label>

            {loadingAgentAssignments ? (
              <div className="flex items-center gap-2 text-sm text-muted py-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                Loading...
              </div>
            ) : (
              <>
                <div className="flex gap-4 mb-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="docScope"
                      checked={docIsGlobal}
                      onChange={() => setDocIsGlobal(true)}
                      className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-primary">Global (all agents)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="docScope"
                      checked={!docIsGlobal}
                      onChange={() => setDocIsGlobal(false)}
                      className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-primary">Agent-specific</span>
                  </label>
                </div>

                {!docIsGlobal && (
                  <div className="mt-2">
                    <p className="text-xs text-muted mb-2">Select which agents can access this document:</p>
                    {allAgents.length === 0 ? (
                      <p className="text-sm text-muted">Loading agents...</p>
                    ) : (
                      <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                        {allAgents.map(agent => (
                          <label
                            key={agent.id}
                            className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                              docLinkedAgentIds.has(agent.id)
                                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500'
                                : 'bg-gray-50 dark:bg-gray-800 border-default hover:border-blue-300'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={docLinkedAgentIds.has(agent.id)}
                              onChange={() => toggleDocAgentSelection(agent.id)}
                              className="w-4 h-4 text-blue-600 focus:ring-blue-500 rounded"
                            />
                            <span className="text-sm text-primary truncate">{agent.display_name}</span>
                          </label>
                        ))}
                      </div>
                    )}
                    {!docIsGlobal && docLinkedAgentIds.size === 0 && allAgents.length > 0 && (
                      <p className="text-xs text-amber-600 mt-2">
                        Select at least one agent, or choose &quot;Global&quot; to make available to all.
                      </p>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={savingAgentAssignments || (!docIsGlobal && docLinkedAgentIds.size === 0)}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {savingAgentAssignments ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
