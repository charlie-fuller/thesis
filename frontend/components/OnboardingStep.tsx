'use client'

import { ReactNode } from 'react'

interface OnboardingStepProps {
  title: string
  description: string
  icon?: ReactNode
  children?: ReactNode
}

export default function OnboardingStep({
  title,
  description,
  icon,
  children
}: OnboardingStepProps) {
  return (
    <div className="flex flex-col items-center text-center px-6 py-8 max-w-2xl mx-auto">
      {icon && (
        <div className="mb-6 flex items-center justify-center w-16 h-16 rounded-full bg-primary/10">
          {icon}
        </div>
      )}

      <h2 className="heading-2 mb-4">
        {title}
      </h2>

      <p className="text-secondary text-lg mb-8 max-w-xl">
        {description}
      </p>

      {children && (
        <div className="w-full">
          {children}
        </div>
      )}
    </div>
  )
}
