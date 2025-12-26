'use client'

import React, { useState } from 'react'

interface AspectRatioOption {
  ratio: string
  width: number
  height: number
  description: string
}

interface ModelOption {
  key: string
  name: string
  display_name: string
  description: string
  speed: string
}

interface AspectRatioSelectorProps {
  onSelect: (aspectRatio: string, model: string) => void
  onCancel?: () => void
  defaultRatio?: string
  defaultModel?: string
  aspectRatios?: AspectRatioOption[]
  models?: ModelOption[]
}

const DEFAULT_ASPECT_RATIOS: AspectRatioOption[] = [
  { ratio: '1:1', width: 1024, height: 1024, description: 'Square' },
  { ratio: '16:9', width: 1536, height: 864, description: 'Landscape (presentation)' },
  { ratio: '9:16', width: 864, height: 1536, description: 'Portrait (mobile)' },
  { ratio: '4:3', width: 1280, height: 960, description: 'Standard' }
]

const DEFAULT_MODELS: ModelOption[] = [
  {
    key: 'fast',
    name: 'gemini-2.5-flash-image',
    display_name: 'Fast',
    description: 'Quick generation, good quality',
    speed: 'fast'
  },
  {
    key: 'quality',
    name: 'gemini-3-pro-image-preview',
    display_name: 'Quality',
    description: 'Higher quality, slower generation',
    speed: 'slow'
  }
]

export default function AspectRatioSelector({
  onSelect,
  onCancel,
  defaultRatio = '16:9',
  defaultModel = 'fast',
  aspectRatios = DEFAULT_ASPECT_RATIOS,
  models = DEFAULT_MODELS
}: AspectRatioSelectorProps) {
  const [selectedRatio, setSelectedRatio] = useState(defaultRatio)
  const [selectedModel, setSelectedModel] = useState(defaultModel)

  const handleGenerate = () => {
    onSelect(selectedRatio, selectedModel)
  }

  return (
    <div className="w-full max-w-2xl bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg p-6 space-y-6">
      {/* Aspect Ratio Section */}
      <div>
        <h3 className="text-[var(--color-text-primary)] font-semibold mb-3">
          Choose Aspect Ratio
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {aspectRatios.map((option) => (
            <button
              key={option.ratio}
              onClick={() => setSelectedRatio(option.ratio)}
              className={`
                relative p-4 rounded-lg border-2 transition-all
                ${
                  selectedRatio === option.ratio
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/10'
                    : 'border-[var(--color-border)] hover:border-[var(--color-border-focus)] bg-[var(--color-bg-hover)]'
                }
              `}
            >
              {/* Visual representation of ratio */}
              <div className="flex items-center justify-center mb-3">
                <div
                  className={`
                    bg-[var(--color-primary)]/20 border border-[var(--color-primary)]
                    ${selectedRatio === option.ratio ? 'opacity-100' : 'opacity-50'}
                  `}
                  style={{
                    width: option.ratio === '1:1' ? '40px' : option.ratio === '16:9' ? '50px' : option.ratio === '9:16' ? '25px' : '45px',
                    height: option.ratio === '1:1' ? '40px' : option.ratio === '16:9' ? '28px' : option.ratio === '9:16' ? '44px' : '34px'
                  }}
                />
              </div>

              {/* Ratio label */}
              <div className="text-[var(--color-text-primary)] font-semibold text-sm mb-1">
                {option.ratio}
              </div>
              <div className="text-[var(--color-text-muted)] text-xs">
                {option.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Model Selection Section */}
      <div>
        <h3 className="text-[var(--color-text-primary)] font-semibold mb-3">
          Choose Quality
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {models.map((model) => (
            <button
              key={model.key}
              onClick={() => setSelectedModel(model.key)}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${
                  selectedModel === model.key
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/10'
                    : 'border-[var(--color-border)] hover:border-[var(--color-border-focus)] bg-[var(--color-bg-hover)]'
                }
              `}
            >
              <div className="text-[var(--color-text-primary)] font-semibold mb-1">
                {model.display_name}
              </div>
              <div className="text-[var(--color-text-secondary)] text-sm">
                {model.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end pt-4 border-t border-[var(--color-border)]">
        {onCancel && (
          <button
            onClick={onCancel}
            className="px-6 py-2 rounded-lg bg-[var(--color-bg-hover)] text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-card)] border border-[var(--color-border)] transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          onClick={handleGenerate}
          className="px-6 py-2 rounded-lg bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] transition-colors font-medium"
        >
          Generate Image
        </button>
      </div>
    </div>
  )
}
