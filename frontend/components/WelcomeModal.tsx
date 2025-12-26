'use client'

import { useEffect, useState, useRef } from 'react'
import OnboardingWizard from './OnboardingWizard'
import { X } from 'lucide-react'

interface WelcomeModalProps {
  open: boolean
  userName?: string
  onComplete: (preferences?: UserPreferences) => void
  onClose: () => void
  allowSkip?: boolean
}

interface UserPreferences {
  notificationsEnabled: boolean
  emailDigest: boolean
}

export default function WelcomeModal({
  open,
  userName,
  onComplete,
  onClose,
  allowSkip = true
}: WelcomeModalProps) {
  const [isVisible, setIsVisible] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  // Handle escape key and focus trapping
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open && allowSkip) {
        onClose()
        return
      }

      // Focus trapping
      if (e.key === 'Tab' && open && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        const firstElement = focusableElements[0]
        const lastElement = focusableElements[focusableElements.length - 1]

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault()
          lastElement?.focus()
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault()
          firstElement?.focus()
        }
      }
    }

    if (open) {
      document.addEventListener('keydown', handleKeyDown)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
      // Trigger animation - using requestAnimationFrame to avoid cascading render warning
      requestAnimationFrame(() => {
        setTimeout(() => setIsVisible(true), 10)
      })
    } else {
      // Defer state update to avoid cascading render warning
      requestAnimationFrame(() => {
        setIsVisible(false)
      })
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [open, allowSkip, onClose])

  if (!open) return null

  const handleComplete = (preferences?: UserPreferences) => {
    setIsVisible(false)
    setTimeout(() => {
      onComplete(preferences)
    }, 200) // Wait for fade-out animation
  }

  const handleSkip = () => {
    if (allowSkip) {
      setIsVisible(false)
      setTimeout(() => {
        onClose()
      }, 200)
    }
  }

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center transition-opacity duration-200 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-modal-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
        onClick={allowSkip ? handleSkip : undefined}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        ref={modalRef}
        className={`relative bg-card rounded-2xl shadow-2xl max-w-3xl w-full mx-4 p-8 transform transition-all duration-200 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        style={{ maxHeight: '90vh', overflowY: 'auto' }}
      >
        {/* Close button - only show if skippable */}
        {allowSkip && (
          <button
            onClick={handleSkip}
            className="absolute top-4 right-4 p-2 rounded-lg text-muted hover:text-primary hover:bg-hover transition-colors"
            aria-label="Close welcome modal"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        {/* Content */}
        <div id="welcome-modal-title" className="sr-only">
          Welcome to Thesis
        </div>

        <OnboardingWizard
          onComplete={handleComplete}
          onSkip={handleSkip}
          userName={userName}
        />
      </div>
    </div>
  )
}
