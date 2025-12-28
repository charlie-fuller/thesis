'use client'

import { useState } from 'react'
import LoadingSpinner from '@/components/LoadingSpinner'

interface AutonomousDiscussionPanelProps {
  meetingId: string
  isActive: boolean
  isPaused: boolean
  currentRound: number
  totalRounds: number
  topic: string | null
  onStart: (topic: string, rounds: number) => void
  onStop: () => void
  disabled?: boolean
}

export default function AutonomousDiscussionPanel({
  meetingId,
  isActive,
  isPaused,
  currentRound,
  totalRounds,
  topic,
  onStart,
  onStop,
  disabled = false,
}: AutonomousDiscussionPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [topicInput, setTopicInput] = useState('')
  const [roundsInput, setRoundsInput] = useState(3)
  const [isStarting, setIsStarting] = useState(false)

  const handleStart = async () => {
    if (!topicInput.trim()) return
    setIsStarting(true)
    try {
      await onStart(topicInput.trim(), roundsInput)
      setTopicInput('')
      setIsExpanded(false)
    } finally {
      setIsStarting(false)
    }
  }

  // Active discussion view
  if (isActive) {
    const progressPercent = totalRounds > 0 ? (currentRound / totalRounds) * 100 : 0

    return (
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Autonomous Discussion
            </span>
            <span className="text-sm text-blue-600 dark:text-blue-400">
              Round {currentRound} of {totalRounds}
            </span>
          </div>
          <button
            onClick={onStop}
            className="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 font-medium"
          >
            Stop Discussion
          </button>
        </div>

        {topic && (
          <p className="text-sm text-blue-600 dark:text-blue-400 mb-3 line-clamp-2">
            Topic: {topic}
          </p>
        )}

        {/* Progress bar */}
        <div className="h-2 bg-blue-200 dark:bg-blue-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>
    )
  }

  // Paused/resumable view
  if (isPaused && topic) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-yellow-500 rounded-full" />
              <span className="text-sm font-medium text-yellow-700 dark:text-yellow-300">
                Discussion Paused
              </span>
            </div>
            <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-1 line-clamp-1">
              {topic}
            </p>
          </div>
          <div className="text-xs text-yellow-600 dark:text-yellow-400">
            Round {currentRound}/{totalRounds}
          </div>
        </div>
      </div>
    )
  }

  // Collapsed state - just show trigger button
  if (!isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        disabled={disabled}
        className="w-full mb-4 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-blue-400 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <div className="flex items-center justify-center gap-2 text-gray-500 dark:text-gray-400">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"
            />
          </svg>
          <span className="text-sm font-medium">Start Autonomous Discussion</span>
        </div>
      </button>
    )
  }

  // Expanded state - show topic input form
  return (
    <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
          Start Autonomous Discussion
        </h4>
        <button
          onClick={() => setIsExpanded(false)}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            Discussion Topic
          </label>
          <textarea
            value={topicInput}
            onChange={(e) => setTopicInput(e.target.value)}
            placeholder="What should the agents discuss? Be specific about what perspectives you want explored..."
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            rows={3}
            disabled={isStarting}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-gray-600 dark:text-gray-400">
              Rounds:
            </label>
            <select
              value={roundsInput}
              onChange={(e) => setRoundsInput(parseInt(e.target.value))}
              className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
              disabled={isStarting}
            >
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n} {n === 1 ? 'round' : 'rounds'}
                </option>
              ))}
            </select>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              (each agent speaks once per round)
            </span>
          </div>

          <button
            onClick={handleStart}
            disabled={!topicInput.trim() || isStarting}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2"
          >
            {isStarting ? (
              <>
                <LoadingSpinner size="sm" />
                Starting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Start Discussion
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
