'use client'

import { useState } from 'react'
import { Database, FileText } from 'lucide-react'
import KBDocumentBrowser from './KBDocumentBrowser'

interface UploadedDocument {
  id: string
  name: string
  [key: string]: unknown
}

interface DocumentUploadProps {
  initiativeId: string
  initiativeName?: string
  onUploaded: (document: UploadedDocument) => void
  onDocumentsLinked?: () => void
}

export default function DocumentUpload({ initiativeId, initiativeName = 'Initiative', onUploaded, onDocumentsLinked }: DocumentUploadProps) {
  const [kbBrowserOpen, setKbBrowserOpen] = useState(false)

  return (
    <div className="space-y-4">
      {/* Add from KB button */}
      <div className="border-2 border-dashed rounded-lg p-6 text-center border-slate-300 dark:border-slate-600">
        <Database className="w-8 h-8 text-slate-400 mx-auto mb-3" />
        <p className="text-slate-600 dark:text-slate-400 mb-3">
          Link documents from the Knowledge Base to this initiative
        </p>
        <button
          onClick={() => setKbBrowserOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition-colors"
        >
          <FileText className="w-4 h-4" />
          Browse Knowledge Base
        </button>
        <p className="text-xs text-slate-400 mt-3">
          Upload documents to the KB first, then link them here. Use tags to organize documents by initiative.
        </p>
      </div>

      {/* KB Document Browser Modal */}
      <KBDocumentBrowser
        initiativeId={initiativeId}
        initiativeName={initiativeName}
        isOpen={kbBrowserOpen}
        onClose={() => setKbBrowserOpen(false)}
        onLinked={() => {
          // Refresh the documents list after linking
          if (onDocumentsLinked) {
            onDocumentsLinked()
          }
        }}
      />
    </div>
  )
}
