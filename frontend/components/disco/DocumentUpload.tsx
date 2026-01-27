'use client'

import { useState, useRef } from 'react'
import { Upload, FileText, X, Loader2, CheckCircle, Database } from 'lucide-react'
import { authenticatedFetch } from '@/lib/api'
import KBDocumentBrowser from './KBDocumentBrowser'

interface DocumentUploadProps {
  initiativeId: string
  initiativeName?: string
  onUploaded: (document: any) => void
}

interface UploadProgress {
  filename: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

type UploadMode = 'file' | 'paste' | 'kb'

export default function DocumentUpload({ initiativeId, initiativeName = 'Initiative', onUploaded }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([])
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<UploadMode>('file')
  const [pasteFilename, setPasteFilename] = useState('')
  const [pasteContent, setPasteContent] = useState('')
  const [kbBrowserOpen, setKbBrowserOpen] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      await uploadFiles(files)
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      await uploadFiles(Array.from(files))
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const uploadFiles = async (files: File[]) => {
    setUploading(true)
    setError(null)

    // Initialize progress for all files
    const progress: UploadProgress[] = files.map(f => ({
      filename: f.name,
      status: 'pending'
    }))
    setUploadProgress(progress)

    // Upload files sequentially to avoid overwhelming the server
    for (let i = 0; i < files.length; i++) {
      const file = files[i]

      // Update status to uploading
      setUploadProgress(prev => prev.map((p, idx) =>
        idx === i ? { ...p, status: 'uploading' } : p
      ))

      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await authenticatedFetch(
          `/api/disco/initiatives/${initiativeId}/documents`,
          {
            method: 'POST',
            body: formData,
          }
        )

        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.detail || 'Upload failed')
        }

        const result = await response.json()

        if (result.success && result.document) {
          onUploaded(result.document)
        }

        // Update status to success
        setUploadProgress(prev => prev.map((p, idx) =>
          idx === i ? { ...p, status: 'success' } : p
        ))
      } catch (err) {
        // Update status to error
        const errorMsg = err instanceof Error ? err.message : 'Upload failed'
        setUploadProgress(prev => prev.map((p, idx) =>
          idx === i ? { ...p, status: 'error', error: errorMsg } : p
        ))
      }
    }

    setUploading(false)

    // Clear progress after a delay if all succeeded
    const allSucceeded = uploadProgress.every(p => p.status === 'success')
    if (allSucceeded) {
      setTimeout(() => setUploadProgress([]), 2000)
    }
  }

  const uploadPastedContent = async () => {
    if (!pasteFilename.trim() || !pasteContent.trim()) {
      setError('Both filename and content are required')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const response = await authenticatedFetch(
        `/api/disco/initiatives/${initiativeId}/documents/text`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: pasteFilename.trim(),
            content: pasteContent.trim(),
            document_type: 'uploaded'
          }),
        }
      )

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Upload failed')
      }

      const result = await response.json()

      if (result.success && result.document) {
        onUploaded(result.document)
        setPasteFilename('')
        setPasteContent('')
        setMode('file')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Toggle buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => setMode('file')}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
            mode === 'file'
              ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
          }`}
        >
          Upload File
        </button>
        <button
          onClick={() => setMode('paste')}
          className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
            mode === 'paste'
              ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
          }`}
        >
          Paste Content
        </button>
        <button
          onClick={() => setKbBrowserOpen(true)}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors ${
            mode === 'kb'
              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          Add from KB
        </button>
      </div>

      {mode === 'file' ? (
        /* File Upload Zone */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
              : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            accept=".pdf,.docx,.txt,.md,.xlsx,.pptx"
            multiple
            className="hidden"
          />

          {uploading || uploadProgress.length > 0 ? (
            <div className="flex flex-col items-center gap-3 text-slate-500">
              {uploadProgress.length > 1 ? (
                // Multi-file progress
                <div className="w-full space-y-2">
                  {uploadProgress.map((p, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      {p.status === 'uploading' && <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />}
                      {p.status === 'success' && <CheckCircle className="w-4 h-4 text-green-500" />}
                      {p.status === 'error' && <X className="w-4 h-4 text-red-500" />}
                      {p.status === 'pending' && <div className="w-4 h-4 rounded-full border-2 border-slate-300" />}
                      <span className={p.status === 'error' ? 'text-red-500' : ''}>
                        {p.filename}
                      </span>
                      {p.error && <span className="text-xs text-red-400">({p.error})</span>}
                    </div>
                  ))}
                </div>
              ) : (
                // Single file progress
                <>
                  <Loader2 className="w-8 h-8 animate-spin" />
                  <p>Uploading {uploadProgress[0]?.filename || 'file'}...</p>
                </>
              )}
            </div>
          ) : (
            <>
              <Upload className="w-10 h-10 text-slate-400 mx-auto mb-3" />
              <p className="text-slate-600 dark:text-slate-400 mb-2">
                Drag and drop files here, or{' '}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  browse
                </button>
              </p>
              <p className="text-xs text-slate-400">
                Supported: PDF, DOCX, TXT, Markdown, Excel, PowerPoint (multiple files OK)
              </p>
            </>
          )}
        </div>
      ) : mode === 'paste' ? (
        /* Paste Content Form */
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Filename
            </label>
            <input
              type="text"
              value={pasteFilename}
              onChange={(e) => setPasteFilename(e.target.value)}
              placeholder="e.g., requirements.md"
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Content
            </label>
            <textarea
              value={pasteContent}
              onChange={(e) => setPasteContent(e.target.value)}
              placeholder="Paste your document content here..."
              rows={10}
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
            />
          </div>
          <button
            onClick={uploadPastedContent}
            disabled={uploading || !pasteFilename.trim() || !pasteContent.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading && <Loader2 className="w-4 h-4 animate-spin" />}
            Upload Content
          </button>
        </div>
      ) : null}

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
          <X className="w-4 h-4 flex-shrink-0" />
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-auto hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* KB Document Browser Modal */}
      <KBDocumentBrowser
        initiativeId={initiativeId}
        initiativeName={initiativeName}
        isOpen={kbBrowserOpen}
        onClose={() => setKbBrowserOpen(false)}
        onLinked={(docIds) => {
          // Notify parent of linked documents
          docIds.forEach(docId => {
            onUploaded({ id: docId, source: 'kb_linked' })
          })
        }}
      />
    </div>
  )
}
