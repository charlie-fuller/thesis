'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
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

interface FileUploadStatus {
  file: File
  status: 'pending' | 'uploading' | 'processing' | 'complete' | 'error'
  message: string
  progress: number
  documentId?: string
  chunksCreated?: number
}

export default function DocumentUpload({
  clientId: _clientId,
  apiBaseUrl = API_BASE_URL,
  onUploadComplete,
  showAgentSelector = false
}: DocumentUploadProps) {
  const [fileQueue, setFileQueue] = useState<FileUploadStatus[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropZoneRef = useRef<HTMLDivElement>(null)

  // Agent selection state
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgentIds, setSelectedAgentIds] = useState<Set<string>>(new Set())
  const [isGlobal, setIsGlobal] = useState(true)
  const [loadingAgents, setLoadingAgents] = useState(false)

  // Original date for documents (e.g., meeting date for transcripts)
  const [originalDate, setOriginalDate] = useState<string>('')

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

  const ACCEPTED_EXTENSIONS = ['.txt', '.md', '.docx', '.doc', '.csv', '.json', '.xml', '.pdf']
  const ACCEPTED_MIME_TYPES = [
    'text/plain',
    'text/markdown',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'text/csv',
    'application/json',
    'text/xml',
    'application/xml',
    'application/pdf'
  ]

  function isValidFile(file: File): boolean {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()
    return ACCEPTED_EXTENSIONS.includes(extension) || ACCEPTED_MIME_TYPES.includes(file.type)
  }

  function addFilesToQueue(files: FileList | File[]) {
    const newFiles: FileUploadStatus[] = []
    const invalidFiles: string[] = []

    Array.from(files).forEach(file => {
      // Check if file is already in queue
      const alreadyInQueue = fileQueue.some(f => f.file.name === file.name && f.file.size === file.size)
      if (alreadyInQueue) return

      if (isValidFile(file)) {
        if (file.size === 0) {
          invalidFiles.push(`${file.name} (empty file)`)
        } else {
          newFiles.push({
            file,
            status: 'pending',
            message: 'Ready to upload',
            progress: 0
          })
        }
      } else {
        invalidFiles.push(`${file.name} (unsupported format)`)
      }
    })

    if (invalidFiles.length > 0) {
      console.warn('Skipped invalid files:', invalidFiles)
    }

    if (newFiles.length > 0) {
      setFileQueue(prev => [...prev, ...newFiles])
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files
    if (files && files.length > 0) {
      addFilesToQueue(files)
    }
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  function removeFromQueue(index: number) {
    setFileQueue(prev => prev.filter((_, i) => i !== index))
  }

  function clearCompleted() {
    setFileQueue(prev => prev.filter(f => f.status !== 'complete' && f.status !== 'error'))
  }

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    // Only set dragOver to false if we're leaving the drop zone entirely
    if (dropZoneRef.current && !dropZoneRef.current.contains(e.relatedTarget as Node)) {
      setIsDragOver(false)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  // Recursively get all files from a directory entry
  async function getFilesFromEntry(entry: FileSystemEntry): Promise<File[]> {
    if (entry.isFile) {
      return new Promise((resolve) => {
        (entry as FileSystemFileEntry).file(
          (file) => resolve([file]),
          () => resolve([])
        )
      })
    } else if (entry.isDirectory) {
      const dirReader = (entry as FileSystemDirectoryEntry).createReader()
      const files: File[] = []

      // Read entries in batches (readEntries may not return all at once)
      const readEntries = (): Promise<FileSystemEntry[]> => {
        return new Promise((resolve) => {
          dirReader.readEntries(
            (entries) => resolve(entries),
            () => resolve([])
          )
        })
      }

      let entries = await readEntries()
      while (entries.length > 0) {
        for (const childEntry of entries) {
          const childFiles = await getFilesFromEntry(childEntry)
          files.push(...childFiles)
        }
        entries = await readEntries()
      }

      return files
    }
    return []
  }

  // Extract all files from dropped items (handles both files and folders)
  async function getFilesFromDataTransfer(dataTransfer: DataTransfer): Promise<File[]> {
    const files: File[] = []
    const items = dataTransfer.items

    // Use DataTransferItemList if available (supports folders)
    if (items && items.length > 0) {
      const entries: FileSystemEntry[] = []

      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.kind === 'file') {
          const entry = item.webkitGetAsEntry?.()
          if (entry) {
            entries.push(entry)
          } else {
            // Fallback for browsers without webkitGetAsEntry
            const file = item.getAsFile()
            if (file) files.push(file)
          }
        }
      }

      // Process all entries (files and directories)
      for (const entry of entries) {
        const entryFiles = await getFilesFromEntry(entry)
        files.push(...entryFiles)
      }
    } else if (dataTransfer.files.length > 0) {
      // Fallback to files list (doesn't support folders)
      files.push(...Array.from(dataTransfer.files))
    }

    return files
  }

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const files = await getFilesFromDataTransfer(e.dataTransfer)
    if (files.length > 0) {
      addFilesToQueue(files)
    }
  }, [fileQueue])

  async function uploadSingleFile(fileStatus: FileUploadStatus, index: number): Promise<boolean> {
    const { file } = fileStatus

    try {
      // Update status to uploading
      setFileQueue(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'uploading', message: 'Uploading...', progress: 10 } : f
      ))

      const formData = new FormData()
      formData.append('file', file)

      // Add agent IDs if not global and agents are selected
      if (showAgentSelector && !isGlobal && selectedAgentIds.size > 0) {
        formData.append('agent_ids', JSON.stringify(Array.from(selectedAgentIds)))
      }

      // Add original date if specified
      if (originalDate) {
        formData.append('original_date', originalDate)
      }

      const uploadResponse = await authenticatedFetch(`${apiBaseUrl}/api/documents/upload`, {
        method: 'POST',
        body: formData
      })

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || `Upload failed: ${uploadResponse.statusText}`)
      }

      const uploadData = await uploadResponse.json()
      const documentId = uploadData.document_id

      // Update to processing
      setFileQueue(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'processing', message: 'Processing...', progress: 50, documentId } : f
      ))

      // Process document
      const processResponse = await authenticatedFetch(
        `${apiBaseUrl}/api/documents/${documentId}/process`,
        { method: 'POST' }
      )

      if (!processResponse.ok) {
        throw new Error(`Processing failed: ${processResponse.statusText}`)
      }

      const processData = await processResponse.json()

      // Update to complete
      setFileQueue(prev => prev.map((f, i) =>
        i === index ? {
          ...f,
          status: 'complete',
          message: `${processData.chunks_created} chunks created`,
          progress: 100,
          chunksCreated: processData.chunks_created
        } : f
      ))

      return true

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setFileQueue(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'error', message: errorMessage, progress: 0 } : f
      ))
      return false
    }
  }

  async function handleUploadAll() {
    const pendingFiles = fileQueue.filter(f => f.status === 'pending')
    if (pendingFiles.length === 0) return

    setIsUploading(true)

    // Upload files sequentially to avoid overwhelming the server
    for (let i = 0; i < fileQueue.length; i++) {
      if (fileQueue[i].status === 'pending') {
        await uploadSingleFile(fileQueue[i], i)
      }
    }

    setIsUploading(false)

    // Notify parent component
    if (onUploadComplete) {
      onUploadComplete()
    }
  }

  const pendingCount = fileQueue.filter(f => f.status === 'pending').length
  const completedCount = fileQueue.filter(f => f.status === 'complete').length
  const errorCount = fileQueue.filter(f => f.status === 'error').length

  return (
    <div>
      {/* Drag and Drop Zone */}
      <div
        ref={dropZoneRef}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-6 mb-4 transition-all duration-200 ${
          isDragOver
            ? 'border-brand bg-brand/10 scale-[1.02]'
            : 'border-default bg-tertiary hover:border-brand/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.docx,.doc,.csv,.json,.xml,.pdf"
          onChange={handleFileSelect}
          multiple
          disabled={isUploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <div className="text-center pointer-events-none">
          {/* Upload Icon */}
          <svg
            className={`mx-auto h-12 w-12 mb-3 transition-colors ${isDragOver ? 'text-brand' : 'text-muted'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>

          <p className={`text-sm font-medium mb-1 ${isDragOver ? 'text-brand' : 'text-primary'}`}>
            {isDragOver ? 'Drop files here' : 'Drag and drop files here'}
          </p>
          <p className="text-xs text-muted">
            or click to browse
          </p>
        </div>
      </div>

      {/* File Queue */}
      {fileQueue.length > 0 && (
        <div className="mb-4 border border-default rounded-lg overflow-hidden">
          <div className="bg-secondary px-3 py-2 border-b border-default flex items-center justify-between">
            <span className="text-sm font-medium text-primary">
              {fileQueue.length} file{fileQueue.length !== 1 ? 's' : ''} selected
            </span>
            <div className="flex items-center gap-2 text-xs">
              {completedCount > 0 && (
                <span className="text-green-600 dark:text-green-400">{completedCount} completed</span>
              )}
              {errorCount > 0 && (
                <span className="text-red-600 dark:text-red-400">{errorCount} failed</span>
              )}
              {(completedCount > 0 || errorCount > 0) && (
                <button
                  onClick={clearCompleted}
                  className="text-brand hover:underline"
                >
                  Clear done
                </button>
              )}
            </div>
          </div>

          <div className="max-h-48 overflow-y-auto">
            {fileQueue.map((fileStatus, index) => (
              <div
                key={`${fileStatus.file.name}-${index}`}
                className="px-3 py-2 border-b border-default last:border-b-0 flex items-center gap-3"
              >
                {/* Status Icon */}
                <div className="flex-shrink-0">
                  {fileStatus.status === 'pending' && (
                    <div className="w-5 h-5 rounded-full border-2 border-muted" />
                  )}
                  {fileStatus.status === 'uploading' && (
                    <div className="w-5 h-5 rounded-full border-2 border-brand border-t-transparent animate-spin" />
                  )}
                  {fileStatus.status === 'processing' && (
                    <div className="w-5 h-5 rounded-full border-2 border-amber-500 border-t-transparent animate-spin" />
                  )}
                  {fileStatus.status === 'complete' && (
                    <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {fileStatus.status === 'error' && (
                    <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                </div>

                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-primary truncate">{fileStatus.file.name}</p>
                  <p className={`text-xs ${
                    fileStatus.status === 'error' ? 'text-red-600 dark:text-red-400' :
                    fileStatus.status === 'complete' ? 'text-green-600 dark:text-green-400' :
                    'text-muted'
                  }`}>
                    {fileStatus.status === 'pending'
                      ? `${(fileStatus.file.size / 1024).toFixed(1)} KB`
                      : fileStatus.message
                    }
                  </p>

                  {/* Progress bar for uploading/processing */}
                  {(fileStatus.status === 'uploading' || fileStatus.status === 'processing') && (
                    <div className="mt-1 w-full bg-secondary rounded-full h-1">
                      <div
                        className={`h-1 rounded-full transition-all duration-300 ${
                          fileStatus.status === 'processing' ? 'bg-amber-500' : 'bg-brand'
                        }`}
                        style={{ width: `${fileStatus.progress}%` }}
                      />
                    </div>
                  )}
                </div>

                {/* Remove button (only for pending files) */}
                {fileStatus.status === 'pending' && (
                  <button
                    onClick={() => removeFromQueue(index)}
                    className="flex-shrink-0 p-1 text-muted hover:text-red-600 dark:hover:text-red-400 transition-colors"
                    title="Remove from queue"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Assignment Selector */}
      {showAgentSelector && fileQueue.length > 0 && pendingCount > 0 && (
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
              <p className="text-xs text-muted mb-2">Select which agents can access these documents:</p>
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

      {/* Original Date Picker (for transcripts/meeting notes) */}
      {fileQueue.length > 0 && pendingCount > 0 && (
        <div className="mb-4 p-4 bg-tertiary rounded-lg border border-default">
          <label className="block text-sm font-medium text-primary mb-2">
            Original Document Date (optional)
          </label>
          <p className="text-xs text-muted mb-3">
            For meeting transcripts or notes, enter the actual meeting date (not the upload date)
          </p>
          <input
            type="date"
            value={originalDate}
            onChange={(e) => setOriginalDate(e.target.value)}
            disabled={isUploading}
            className="w-full px-3 py-2 text-sm border border-default rounded-lg bg-primary text-primary focus:ring-2 focus:ring-brand focus:border-transparent"
          />
          {originalDate && (
            <button
              type="button"
              onClick={() => setOriginalDate('')}
              className="mt-2 text-xs text-muted hover:text-primary"
            >
              Clear date
            </button>
          )}
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUploadAll}
        disabled={pendingCount === 0 || isUploading}
        className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading
          ? `Uploading ${fileQueue.filter(f => f.status === 'uploading' || f.status === 'processing').length} of ${pendingCount + completedCount}...`
          : pendingCount === 0
            ? 'Select files to upload'
            : `Upload ${pendingCount} file${pendingCount !== 1 ? 's' : ''}`
        }
      </button>

      {/* Supported Formats */}
      <div className="mt-4 text-xs text-muted">
        <p className="font-semibold mb-1">Supported formats:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>PDF documents (.pdf)</li>
          <li>Plain text (.txt, .md)</li>
          <li>Word documents (.docx, .doc)</li>
          <li>Structured data (.csv, .json, .xml)</li>
        </ul>
      </div>
    </div>
  )
}
