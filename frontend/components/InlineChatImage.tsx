'use client'

import React, { useState } from 'react'
import { Download, RotateCcw, Trash2, Image as ImageIcon } from 'lucide-react'
import toast from 'react-hot-toast'

interface ConversationImage {
  id: string
  storage_url: string
  prompt: string
  aspect_ratio: string
  model: string
  mime_type: string
  file_size: number
  generated_at: string
}

interface InlineChatImageProps {
  image: ConversationImage
  onRegenerate?: (prompt: string) => void
  onDelete?: (imageId: string) => void
  showActions?: boolean
}

export default function InlineChatImage({
  image,
  onRegenerate,
  onDelete,
  showActions = true
}: InlineChatImageProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [showFullImage, setShowFullImage] = useState(false)

  const handleDownload = async () => {
    try {
      // Fetch the image
      const response = await fetch(image.storage_url)
      const blob = await response.blob()

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url

      // Generate filename from prompt (sanitized)
      const sanitizedPrompt = image.prompt
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '_')
        .substring(0, 50)
      const extension = image.mime_type.split('/')[1] || 'png'
      link.download = `${sanitizedPrompt}.${extension}`

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // Cleanup
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Failed to download image. Please try again.')
    }
  }

  const handleRegenerate = () => {
    if (onRegenerate) {
      onRegenerate(image.prompt)
    }
  }

  const handleDelete = () => {
    if (onDelete && confirm('Delete this image? This cannot be undone.')) {
      onDelete(image.id)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    })
  }

  return (
    <div className="my-4 max-w-2xl">
      {/* Image Container */}
      <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg overflow-hidden">
        {/* Image */}
        <div className="relative bg-black/5">
          {!hasError ? (
            <>
              <img
                src={image.storage_url}
                alt={image.prompt}
                className={`
                  w-full h-auto cursor-pointer transition-opacity
                  ${isLoading ? 'opacity-0' : 'opacity-100'}
                `}
                onLoad={() => setIsLoading(false)}
                onError={() => {
                  setIsLoading(false)
                  setHasError(true)
                }}
                onClick={() => setShowFullImage(true)}
              />
              {isLoading && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]"></div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center py-12 text-[var(--color-text-muted)]">
              <div className="text-center">
                <ImageIcon className="mx-auto mb-2 w-12 h-12 opacity-50" />
                <p>Failed to load image</p>
              </div>
            </div>
          )}
        </div>

        {/* Metadata and Actions */}
        <div className="p-3 space-y-2">
          {/* Details - compact row */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--color-text-muted)]">
            <span>{image.aspect_ratio}</span>
            <span>•</span>
            <span>{image.model.includes('flash') ? 'Fast' : 'Quality'}</span>
            <span>•</span>
            <span>{formatFileSize(image.file_size)}</span>
            <span>•</span>
            <span>{formatDate(image.generated_at)}</span>
          </div>

          {/* Actions */}
          {showActions && !hasError && (
            <div className="flex gap-2 pt-2 border-t border-[var(--color-border)]">
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 px-3 py-1.5 rounded bg-[var(--color-bg-hover)] hover:bg-[var(--color-border)] text-[var(--color-text-primary)] text-sm transition-colors"
                title="Download image"
              >
                <Download className="w-4 h-4" />
                Download
              </button>

              {onRegenerate && (
                <button
                  onClick={handleRegenerate}
                  className="flex items-center gap-2 px-3 py-1.5 rounded bg-[var(--color-bg-hover)] hover:bg-[var(--color-border)] text-[var(--color-text-primary)] text-sm transition-colors"
                  title="Regenerate with different settings"
                >
                  <RotateCcw className="w-4 h-4" />
                  Regenerate
                </button>
              )}

              {onDelete && (
                <button
                  onClick={handleDelete}
                  className="flex items-center gap-2 px-3 py-1.5 rounded bg-red-500/10 hover:bg-red-500/20 text-red-500 text-sm transition-colors ml-auto"
                  title="Delete image"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Full Image Modal */}
      {showFullImage && !hasError && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setShowFullImage(false)}
        >
          <div className="relative max-w-[90vw] max-h-[90vh]">
            <img
              src={image.storage_url}
              alt={image.prompt}
              className="max-w-full max-h-[90vh] object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setShowFullImage(false)}
              className="absolute top-4 right-4 bg-white/10 hover:bg-white/20 text-white p-2 rounded-full backdrop-blur-sm transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
