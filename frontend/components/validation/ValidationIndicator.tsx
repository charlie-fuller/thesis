/**
 * ValidationIndicator Component
 *
 * Visual indicator for entity validation status.
 * Shows whether extracted names/organizations match registry entries.
 *
 * Version: 1.0.0
 * Created: 2026-01-23
 */

'use client';

import { Check, AlertTriangle, Plus, HelpCircle } from 'lucide-react';

export type ValidationStatus =
  | 'validated'
  | 'suggested_correction'
  | 'new'
  | 'potential_error'
  | null
  | undefined;

interface ValidationIndicatorProps {
  status: ValidationStatus;
  suggestedValue?: string | null;
  confidence?: number | null;
  size?: 'sm' | 'md';
  showLabel?: boolean;
  className?: string;
}

const STATUS_CONFIG = {
  validated: {
    icon: Check,
    label: 'Validated',
    bgColor: 'bg-green-50',
    textColor: 'text-green-700',
    borderColor: 'border-green-200',
    iconColor: 'text-green-500',
  },
  suggested_correction: {
    icon: AlertTriangle,
    label: 'Correction Suggested',
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-700',
    borderColor: 'border-amber-200',
    iconColor: 'text-amber-500',
  },
  new: {
    icon: Plus,
    label: 'New Entity',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
    borderColor: 'border-blue-200',
    iconColor: 'text-blue-500',
  },
  potential_error: {
    icon: HelpCircle,
    label: 'Potential Error',
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    borderColor: 'border-red-200',
    iconColor: 'text-red-500',
  },
};

export function ValidationIndicator({
  status,
  suggestedValue,
  confidence,
  size = 'sm',
  showLabel = false,
  className = '',
}: ValidationIndicatorProps) {
  if (!status) return null;

  const config = STATUS_CONFIG[status];
  if (!config) return null;

  const Icon = config.icon;
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border ${config.bgColor} ${config.borderColor} ${config.textColor} ${textSize} ${className}`}
      title={getTooltip(status, suggestedValue, confidence)}
    >
      <Icon className={`${iconSize} ${config.iconColor}`} />
      {showLabel && <span>{config.label}</span>}
      {confidence !== null && confidence !== undefined && (
        <span className="opacity-75">({Math.round(confidence * 100)}%)</span>
      )}
    </span>
  );
}

function getTooltip(
  status: ValidationStatus,
  suggestedValue?: string | null,
  confidence?: number | null
): string {
  if (!status) return '';

  switch (status) {
    case 'validated':
      return 'This entity matches a known entry in the registry';
    case 'suggested_correction':
      return suggestedValue
        ? `Did you mean "${suggestedValue}"? (${Math.round((confidence || 0) * 100)}% match)`
        : 'A similar entity exists in the registry';
    case 'new':
      return 'This is a new entity not yet in the registry';
    case 'potential_error':
      return suggestedValue
        ? `Possible transcription error. Did you mean "${suggestedValue}"?`
        : 'This may be a transcription error';
    default:
      return '';
  }
}

interface ValidationBadgeProps {
  status: ValidationStatus;
  entityType: 'name' | 'organization';
  suggestedValue?: string | null;
  confidence?: number | null;
  onAcceptSuggestion?: () => void;
  onKeepOriginal?: () => void;
  className?: string;
}

export function ValidationBadge({
  status,
  entityType,
  suggestedValue,
  confidence,
  onAcceptSuggestion,
  onKeepOriginal,
  className = '',
}: ValidationBadgeProps) {
  if (!status || status === 'validated' || status === 'new') {
    // Don't show correction UI for validated or new entities
    return <ValidationIndicator status={status} className={className} />;
  }

  const config = STATUS_CONFIG[status];
  if (!config) return null;

  return (
    <div
      className={`${config.bgColor} border ${config.borderColor} rounded-lg p-3 ${className}`}
    >
      <div className="flex items-start gap-2">
        <ValidationIndicator status={status} confidence={confidence} />
        <div className="flex-1 min-w-0">
          {suggestedValue && (
            <p className={`${config.textColor} text-sm`}>
              Did you mean:{' '}
              <strong className="font-semibold">{suggestedValue}</strong>?
            </p>
          )}
          {confidence !== null && confidence !== undefined && (
            <p className="text-xs text-muted-foreground mt-0.5">
              {Math.round(confidence * 100)}% match confidence
            </p>
          )}
        </div>
      </div>

      {(onAcceptSuggestion || onKeepOriginal) && suggestedValue && (
        <div className="flex gap-2 mt-2">
          {onAcceptSuggestion && (
            <button
              onClick={onAcceptSuggestion}
              className="px-2.5 py-1 text-xs font-medium rounded bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              Use suggestion
            </button>
          )}
          {onKeepOriginal && (
            <button
              onClick={onKeepOriginal}
              className="px-2.5 py-1 text-xs font-medium rounded bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              Keep original
            </button>
          )}
        </div>
      )}
    </div>
  );
}
