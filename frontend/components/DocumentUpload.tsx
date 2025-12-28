'use client'

import { useState, useRef, useEffect } from 'react'
import { API_BASE_URL } from '@/lib/config'
import { authenticatedFetch, apiGet } from '@/lib/api'

interface Agent {
  id: string
  name: string
  display_name: string
  is_active: boolean
}

interface DocumentUploadProps {
  clientId?: string  // Optional - backend auto-assigns default client
  apiBaseUrl?: string
  onUploadComplete?: () => void
  showAgentSelector?: boolean  // Whether to show agent assignment options
}

interface UploadStatus {
  status: 'idle' | 'uploading' | 'processing' | 'complete' | 'error'
  message: string
  progress?: number
}

export default function DocumentUpload({
  clientId: _clientId,
  apiBaseUrl = API_BASE_URL,
  onUploadComplete,
  showAgentSelector = false
}: DocumentUploadProps) {
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    status: 'idle',
    message: ''
  })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Agent selection state
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgentIds, setSelectedAgentIds] = useState<Set<string>>(new Set())
  const [isGlobal, setIsGlobal] = useState(true)
  const [loadingAgents, setLoadingAgents] = useState(false)

  // Load agents when agent selector is enabled
  useEffect(() => {
    if (showAgentSelector) {
      loadAgents()
    }
  }, [showAgentSelector])

  async function loadAgents() {
    try {
      setLoadingAgents(true)
      const data = await apiGet<{ agents: Agent[] }>('/api/agents?include_inactive=false')
      setAgents(data.agents || [])
    } catch (err) {
      console.error('Failed to load agents:', err)
    } finally {
      setLoadingAgents(false)
    }
  }

  function toggleAgentSelection(agentId: string) {
    setSelectedAgentIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(agentId)) {
        newSet.delete(agentId)
      } else {
        newSet.add(agentId)
      }
      return newSet
    })
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setUploadStatus({ status: 'idle', message: '' })
    }
  }

  async function handleUpload() {
    if (!selectedFile) return

    // Check if file is empty
    if (selectedFile.size === 0) {
      setUploadStatus({
        status: 'error',
        message: 'Error: File is empty. Please select a file with content.',
        progress: 0
      })
      return
    }

    try {
      // Step 1: Upload file
      setUploadStatus({
        status: 'uploading',
        message: `Uploading ${selectedFile.name}...`,
        progress: 0
      })

      const formData = new FormData()
      formData.append('file', selectedFile)

      // Add agent IDs if not global and agents are selected
      if (showAgentSelector && !isGlobal && selectedAgentIds.size > 0) {
        formData.append('agent_ids', JSON.stringify(Array.from(selectedAgentIds)))
      }

      const uploadResponse = await authenticatedFetch(`${apiBaseUrl}/api/documents/upload`, {
        method: 'POST',
        body: formData
      })

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`)
      }

      const uploadData = await uploadResponse.json()
      const documentId = uploadData.document_id

      setUploadStatus({
        status: 'uploading',
        message: 'Upload complete! Processing document...',
        progress: 50
      })

      // Step 2: Process document (chunk and embed)
      setUploadStatus({
        status: 'processing',
        message: 'Chunking text and generating embeddings...',
        progress: 60
      })

      const processResponse = await authenticatedFetch(
        `${apiBaseUrl}/api/documents/${documentId}/process`,
        {
          method: 'POST'
        }
      )

      if (!processResponse.ok) {
        throw new Error(`Processing failed: ${processResponse.statusText}`)
      }

      const processData = await processResponse.json()

      setUploadStatus({
        status: 'complete',
        message: `Success! Created ${processData.chunks_created} searchable chunks`,
        progress: 100
      })

      // Clear the file input after successful upload
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // Notify parent component
      if (onUploadComplete) {
        onUploadComplete()
      }

      // Reset after 3 seconds
      setTimeout(() => {
        setUploadStatus({ status: 'idle', message: '' })
      }, 3000)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setUploadStatus({
        status: 'error',
        message: `Error: ${errorMessage}`,
        progress: 0
      })
    }
  }

  return (
    <div>
      {/* File Input */}
      <div className="mb-4">
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.docx,.doc,.csv,.json,.xml"
          onChange={handleFileSelect}
          disabled={uploadStatus.status === 'uploading' || uploadStatus.status === 'processing'}
          className="block w-full text-sm text-primary border border-default rounded-lg cursor-pointer bg-tertiary focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-brand file:text-white hover:file:bg-brand-hover"
        />
        {selectedFile && (
          <p className="text-sm text-secondary mt-2">
            Selected: <span className="font-medium">{selectedFile.name}</span> ({(selectedFile.size / 1024).toFixed(1)} KB)
          </p>
        )}
      </div>

      {/* Agent Assignment Selector */}
      {showAgentSelector && (
        <div className="mb-4 p-4 bg-tertiary rounded-lg border border-default">
          <label className="block text-sm font-medium text-primary mb-3">Document Availability</label>

          {/* Global vs Agent-specific toggle */}
          <div className="flex gap-4 mb-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="documentScope"
                checked={isGlobal}
                onChange={() => setIsGlobal(true)}
                className="w-4 h-4 text-brand focus:ring-brand"
              />
              <span className="text-sm text-primary">Global (all agents)</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="documentScope"
                checked={!isGlobal}
                onChange={() => setIsGlobal(false)}
                className="w-4 h-4 text-brand focus:ring-brand"
              />
              <span className="text-sm text-primary">Agent-specific</span>
            </label>
          </div>

          {/* Agent selection (only shown when agent-specific is selected) */}
          {!isGlobal && (
            <div className="mt-3 pt-3 border-t border-default">
              <p className="text-xs text-muted mb-2">Select which agents can access this document:</p>
              {loadingAgents ? (
                <div className="flex items-center gap-2 text-sm text-muted">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-brand"></div>
                  Loading agents...
                </div>
              ) : agents.length === 0 ? (
                <p className="text-sm text-muted">No agents available</p>
              ) : (
                <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                  {agents.map(agent => (
                    <label
                      key={agent.id}
                      className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                        selectedAgentIds.has(agent.id)
                          ? 'bg-brand/10 border-brand'
                          : 'bg-secondary border-default hover:border-brand/50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedAgentIds.has(agent.id)}
                        onChange={() => toggleAgentSelection(agent.id)}
                        className="w-4 h-4 text-brand focus:ring-brand rounded"
                      />
                      <span className="text-sm text-primary truncate">{agent.display_name}</span>
                    </label>
                  ))}
                </div>
              )}
              {!isGlobal && selectedAgentIds.size === 0 && agents.length > 0 && (
                <p className="text-xs text-amber-600 mt-2">Select at least one agent, or choose &quot;Global&quot; to make available to all.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={!selectedFile || uploadStatus.status === 'uploading' || uploadStatus.status === 'processing'}
        className="w-full btn-primary"
      >
        {uploadStatus.status === 'uploading' ? 'Uploading...' :
         uploadStatus.status === 'processing' ? 'Processing...' :
         'Upload & Process'}
      </button>

      {/* Progress Bar */}
      {(uploadStatus.status === 'uploading' || uploadStatus.status === 'processing') && uploadStatus.progress !== undefined && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-teal-400 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadStatus.progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Status Message */}
      {uploadStatus.message && (
        <div className={`mt-4 p-3 rounded-lg text-sm ${
          uploadStatus.status === 'complete' ? 'bg-teal-50 text-teal-700' :
          uploadStatus.status === 'error' ? 'bg-red-50 text-red-800' :
          'bg-teal-100 text-teal-700'
        }`}>
          {uploadStatus.message}
        </div>
      )}

      {/* Supported Formats */}
      <div className="mt-4 text-xs text-gray-500">
        <p className="font-semibold mb-1">Supported formats:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Plain text (.txt, .md)</li>
          <li>Word documents (.docx, .doc)</li>
          <li>Structured data (.csv, .json, .xml)</li>
          <li>Any UTF-8 text file</li>
        </ul>
      </div>
    </div>
  )
}
