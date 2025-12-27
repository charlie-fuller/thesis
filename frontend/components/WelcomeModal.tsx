'use client'

interface WelcomeModalProps {
  open: boolean
  userName?: string
  onComplete: (preferences?: { notificationsEnabled?: boolean; emailDigest?: boolean }) => void
  onClose: () => void
  allowSkip?: boolean
}

export default function WelcomeModal({
  open,
  userName,
  onComplete,
  onClose,
  allowSkip = true
}: WelcomeModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Welcome to Thesis{userName ? `, ${userName.split(' ')[0]}` : ''}!
        </h2>

        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Your AI-powered platform for enterprise GenAI strategy. Get insights from specialized agents
          covering research, finance, governance, legal, and stakeholder analysis.
        </p>

        <div className="space-y-3 mb-6">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
              <span className="text-blue-600 dark:text-blue-300 text-sm font-semibold">1</span>
            </div>
            <div>
              <p className="font-medium text-gray-900 dark:text-white">Ask anything about GenAI strategy</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Research, ROI, governance, legal considerations</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
              <span className="text-blue-600 dark:text-blue-300 text-sm font-semibold">2</span>
            </div>
            <div>
              <p className="font-medium text-gray-900 dark:text-white">Upload meeting transcripts</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Extract stakeholder insights automatically</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
              <span className="text-blue-600 dark:text-blue-300 text-sm font-semibold">3</span>
            </div>
            <div>
              <p className="font-medium text-gray-900 dark:text-white">Track stakeholder sentiment</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Monitor engagement and alignment over time</p>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => onComplete()}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Get Started
          </button>
          {allowSkip && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Skip
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
