'use client'

import { useState } from 'react'
import OnboardingStep from './OnboardingStep'
import {
  Sparkles,
  MessageSquare,
  FileText,
  Image as ImageIcon,
  Settings,
  ArrowRight,
  Check,
  Target,
  Compass,
  Layers,
  PlayCircle,
  BarChart2
} from 'lucide-react'

interface OnboardingWizardProps {
  onComplete: (preferences?: UserPreferences) => void
  onSkip: () => void
  userName?: string
}

interface UserPreferences {
  notificationsEnabled: boolean
  emailDigest: boolean
}

export default function OnboardingWizard({
  onComplete,
  onSkip,
  userName = 'there'
}: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [preferences, setPreferences] = useState<UserPreferences>({
    notificationsEnabled: true,
    emailDigest: false
  })

  const totalSteps = 6

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      onComplete(preferences)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <OnboardingStep
            title={`Welcome to Thesis, ${userName}!`}
            description="I'm your AI-powered Learning & Development assistant, designed to help you create high-impact training experiences using the Bradbury Architecture Method."
            icon={<Sparkles className="w-8 h-8 text-primary" />}
          >
            <div className="card p-6 text-left space-y-4">
              <h3 className="font-semibold text-primary mb-3">What is the Bradbury Method?</h3>
              <p className="text-secondary text-sm">
                The Bradbury Architecture Method is a proven framework for designing learning experiences
                that deliver measurable ROI. It focuses on:
              </p>
              <ul className="space-y-2 text-sm text-secondary">
                <li className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>Business outcomes first - aligning learning to strategic goals</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>Evidence-based design - using research-backed methodologies</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>Measurable impact - tracking and demonstrating real results</span>
                </li>
              </ul>
            </div>
          </OnboardingStep>
        )

      case 1:
        return (
          <OnboardingStep
            title="Quick Tour: Key Features"
            description="Let me show you around so you can get started quickly."
            icon={<MessageSquare className="w-8 h-8 text-primary" />}
          >
            <div className="space-y-4">
              <div className="card p-5 text-left hover:shadow-card-hover transition-shadow">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-primary mb-1">AI Chat Interface</h4>
                    <p className="text-sm text-secondary">
                      Have natural conversations about your learning design challenges.
                      I&apos;ll help you apply the Bradbury Method to create impactful solutions.
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-5 text-left hover:shadow-card-hover transition-shadow">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-primary mb-1">Document Knowledge Base</h4>
                    <p className="text-sm text-secondary">
                      Upload your training materials, research, and resources. I&apos;ll reference them
                      in our conversations for context-aware recommendations.
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-5 text-left hover:shadow-card-hover transition-shadow">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <ImageIcon className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-primary mb-1">Image Generation</h4>
                    <p className="text-sm text-secondary">
                      Create custom visuals for your training materials right within our conversations.
                      Perfect for slide decks, infographics, and more.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </OnboardingStep>
        )

      case 2:
        return (
          <OnboardingStep
            title="The ADDIE Framework"
            description="Thesis guides you through the proven ADDIE instructional design framework - used by leading L&D teams worldwide."
            icon={<Compass className="w-8 h-8 text-primary" />}
          >
            <div className="space-y-3">
              {/* Analysis */}
              <div className="card p-4 text-left border-l-4 border-green-500">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <Target className="w-4 h-4 text-green-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-primary">Analysis</h4>
                    <p className="text-sm text-secondary">
                      Identify learning gaps, audience needs, and business objectives
                    </p>
                  </div>
                </div>
              </div>

              {/* Design */}
              <div className="card p-4 text-left border-l-4 border-blue-500">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <Layers className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-primary">Design</h4>
                    <p className="text-sm text-secondary">
                      Create learning objectives, assessments, and course structure
                    </p>
                  </div>
                </div>
              </div>

              {/* Development */}
              <div className="card p-4 text-left border-l-4 border-purple-500">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-purple-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-primary">Development</h4>
                    <p className="text-sm text-secondary">
                      Build content, activities, visuals, and learning materials
                    </p>
                  </div>
                </div>
              </div>

              {/* Implementation */}
              <div className="card p-4 text-left border-l-4 border-orange-500">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center">
                    <PlayCircle className="w-4 h-4 text-orange-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-primary">Implementation</h4>
                    <p className="text-sm text-secondary">
                      Deploy training, prepare facilitators, and launch programs
                    </p>
                  </div>
                </div>
              </div>

              {/* Evaluation */}
              <div className="card p-4 text-left border-l-4 border-pink-500">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-pink-100 flex items-center justify-center">
                    <BarChart2 className="w-4 h-4 text-pink-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-primary">Evaluation</h4>
                    <p className="text-sm text-secondary">
                      Measure effectiveness, gather feedback, and demonstrate ROI
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </OnboardingStep>
        )

      case 3:
        return (
          <OnboardingStep
            title="See ADDIE in Action"
            description="Let's walk through a quick example of how Thesis helps at each phase."
            icon={<Sparkles className="w-8 h-8 text-primary" />}
          >
            <div className="card p-6 text-left space-y-5">
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center justify-center">1</span>
                  <div>
                    <p className="font-medium text-primary">You describe your training need:</p>
                    <div className="mt-2 p-3 bg-hover rounded-lg text-sm italic text-secondary">
                      &quot;We need to train 200 sales reps on our new product line. They&apos;re spread across 5 regions and have varying experience levels.&quot;
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center">2</span>
                  <div>
                    <p className="font-medium text-primary">Thesis helps you analyze:</p>
                    <div className="mt-2 p-3 bg-hover rounded-lg text-sm text-secondary">
                      <ul className="space-y-1">
                        <li className="flex items-start gap-2">
                          <Check className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                          <span>Identifies skill gaps and knowledge requirements</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <Check className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                          <span>Suggests audience segmentation strategies</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <Check className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                          <span>Recommends delivery methods for distributed teams</span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center">3</span>
                  <div>
                    <p className="font-medium text-primary">Together, you design & develop:</p>
                    <div className="mt-2 p-3 bg-hover rounded-lg text-sm text-secondary">
                      Learning objectives, assessments, content outlines, and even visuals for your materials.
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-default">
                <p className="text-sm text-muted text-center">
                  Thesis tracks your progress through each phase and suggests what to tackle next.
                </p>
              </div>
            </div>
          </OnboardingStep>
        )

      case 4:
        return (
          <OnboardingStep
            title="Set Your Preferences"
            description="Customize your Thesis experience (you can change these later)."
            icon={<Settings className="w-8 h-8 text-primary" />}
          >
            <div className="card p-6 space-y-6">
              <div className="flex items-start justify-between">
                <div className="flex-1 text-left">
                  <label className="label mb-1">Browser Notifications</label>
                  <p className="text-sm text-muted">
                    Get notified when I complete long-running tasks
                  </p>
                </div>
                <button
                  onClick={() => setPreferences(prev => ({
                    ...prev,
                    notificationsEnabled: !prev.notificationsEnabled
                  }))}
                  className={`ml-4 relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    preferences.notificationsEnabled ? 'bg-primary' : 'bg-border-default'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      preferences.notificationsEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="divider" />

              <div className="flex items-start justify-between">
                <div className="flex-1 text-left">
                  <label className="label mb-1">Weekly Email Digest</label>
                  <p className="text-sm text-muted">
                    Receive a summary of your conversations and insights
                  </p>
                </div>
                <button
                  onClick={() => setPreferences(prev => ({
                    ...prev,
                    emailDigest: !prev.emailDigest
                  }))}
                  className={`ml-4 relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    preferences.emailDigest ? 'bg-primary' : 'bg-border-default'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      preferences.emailDigest ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </OnboardingStep>
        )

      case 5:
        return (
          <OnboardingStep
            title="You're All Set!"
            description="Ready to start creating impactful learning experiences? Here are some suggestions to get you started."
            icon={<Sparkles className="w-8 h-8 text-primary" />}
          >
            <div className="space-y-3 mb-6">
              <button
                onClick={() => onComplete(preferences)}
                className="w-full card p-4 text-left hover:bg-hover transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-primary group-hover:text-primary-hover transition-colors">
                      &quot;Help me design a leadership development program&quot;
                    </h4>
                    <p className="text-sm text-muted mt-1">
                      Start with a guided Analysis phase conversation
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-muted group-hover:text-primary transition-colors" />
                </div>
              </button>

              <button
                onClick={() => onComplete(preferences)}
                className="w-full card p-4 text-left hover:bg-hover transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-primary group-hover:text-primary-hover transition-colors">
                      &quot;Create learning objectives for customer service training&quot;
                    </h4>
                    <p className="text-sm text-muted mt-1">
                      Jump into the Design phase with measurable objectives
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-muted group-hover:text-primary transition-colors" />
                </div>
              </button>

              <button
                onClick={() => onComplete(preferences)}
                className="w-full card p-4 text-left hover:bg-hover transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-primary group-hover:text-primary-hover transition-colors">
                      &quot;Show me how to measure training ROI&quot;
                    </h4>
                    <p className="text-sm text-muted mt-1">
                      Explore the Evaluation phase and demonstrate impact
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-muted group-hover:text-primary transition-colors" />
                </div>
              </button>
            </div>

            <p className="text-sm text-muted">
              Or just start with your own question - I&apos;m here to help!
            </p>
          </OnboardingStep>
        )

      default:
        return null
    }
  }

  return (
    <div className="w-full min-h-[500px] flex flex-col">
      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-center gap-2">
          {Array.from({ length: totalSteps }).map((_, index) => (
            <div
              key={index}
              className={`h-1.5 rounded-full transition-all ${
                index === currentStep
                  ? 'w-8 bg-primary'
                  : index < currentStep
                  ? 'w-6 bg-primary/50'
                  : 'w-6 bg-border-default'
              }`}
            />
          ))}
        </div>
        <p className="text-center text-sm text-muted mt-3">
          Step {currentStep + 1} of {totalSteps}
        </p>
      </div>

      {/* Step Content */}
      <div className="flex-1">
        {renderStep()}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-8 pt-6 border-t border-default">
        <button
          onClick={onSkip}
          className="text-sm text-muted hover:text-secondary transition-colors"
        >
          Skip for now
        </button>

        <div className="flex gap-3">
          {currentStep > 0 && (
            <button
              onClick={handleBack}
              className="btn-secondary px-6 py-2"
            >
              Back
            </button>
          )}
          <button
            onClick={handleNext}
            className="btn-primary px-6 py-2 flex items-center gap-2"
          >
            {currentStep === totalSteps - 1 ? 'Get Started' : 'Next'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
