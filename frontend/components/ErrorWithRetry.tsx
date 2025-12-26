'use client';

import { ReactNode } from 'react';

interface ErrorWithRetryProps {
  /** Title to display in the error header */
  title: string;
  /** Subtitle/description for the card */
  subtitle?: string;
  /** Error message to display */
  message?: string;
  /** Callback when retry button is clicked */
  onRetry: () => void;
  /** Optional icon to display (defaults to lightning bolt) */
  icon?: ReactNode;
  /** Custom class name for the card container */
  className?: string;
}

/**
 * Reusable error state component with retry functionality.
 * Eliminates duplicate error UI across dashboard card components.
 */
export function ErrorWithRetry({
  title,
  subtitle,
  message = 'Unable to load data.',
  onRetry,
  icon,
  className = ''
}: ErrorWithRetryProps) {
  const defaultIcon = (
    <svg
      className="w-5 h-5 icon-primary"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M13 10V3L4 14h7v7l9-11h-7z"
      />
    </svg>
  );

  return (
    <div className={`bg-card rounded-lg shadow-sm border border-default p-6 ${className}`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            {icon || defaultIcon}
            <h3
              className="text-sm font-semibold"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {title}
            </h3>
          </div>
          {subtitle && (
            <p
              className="text-xs"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div
        className="text-sm mb-3"
        style={{ color: 'var(--color-text-secondary)' }}
      >
        {message}
      </div>
      <button
        onClick={onRetry}
        className="text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
      >
        Try Again
      </button>
    </div>
  );
}

export default ErrorWithRetry;
