'use client'

import { useState } from 'react'
import { Folder, X, Link2, Loader2 } from 'lucide-react'
import { apiDelete } from '@/lib/api'

interface LinkedFolder {
  id: string
  folder_path: string
  recursive: boolean
  linked_at: string
}

interface LinkedFoldersSectionProps {
  initiativeId: string
  folders: LinkedFolder[]
  canEdit: boolean
  onUnlinked: () => void
}

export default function LinkedFoldersSection({
  initiativeId,
  folders,
  canEdit,
  onUnlinked,
}: LinkedFoldersSectionProps) {
  const [unlinking, setUnlinking] = useState<string | null>(null)

  if (folders.length === 0) return null

  const handleUnlink = async (folderPath: string) => {
    setUnlinking(folderPath)
    try {
      await apiDelete(`/api/disco/initiatives/${initiativeId}/linked-folders/${folderPath}`)
      onUnlinked()
    } catch (err) {
      console.error('Failed to unlink folder:', err)
    } finally {
      setUnlinking(null)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1">
        <Link2 className="w-3 h-3" />
        Auto-linked folders:
      </span>
      {folders.map((f) => (
        <span
          key={f.id}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 rounded-full"
        >
          <Folder className="w-3 h-3" />
          {f.folder_path}
          {f.recursive && (
            <span className="text-emerald-500 dark:text-emerald-500 opacity-60">{'/*'}</span>
          )}
          {canEdit && (
            <button
              onClick={() => handleUnlink(f.folder_path)}
              disabled={unlinking === f.folder_path}
              className="ml-0.5 p-0.5 rounded-full hover:bg-emerald-200 dark:hover:bg-emerald-800 transition-colors"
              title="Stop auto-linking this folder"
            >
              {unlinking === f.folder_path ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <X className="w-3 h-3" />
              )}
            </button>
          )}
        </span>
      ))}
    </div>
  )
}
