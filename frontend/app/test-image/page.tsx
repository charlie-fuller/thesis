'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AspectRatioSelector from '@/components/AspectRatioSelector'
import InlineChatImage from '@/components/InlineChatImage'
import ImageSuggestionPrompt from '@/components/ImageSuggestionPrompt'
import { generateConversationImage, type ConversationImage } from '@/lib/api'
import { supabase } from '@/lib/supabase'

// This page is only available in development mode
const IS_DEV = process.env.NODE_ENV === 'development'

export default function TestImagePage() {
  const router = useRouter()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(false)
  const [image, setImage] = useState<ConversationImage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showSelector, setShowSelector] = useState(false)
  const [testConversationId, setTestConversationId] = useState<string>('')

  // Redirect to home in production
  useEffect(() => {
    if (!IS_DEV) {
      router.replace('/')
    }
  }, [router])

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (session) {
        setIsAuthenticated(true)
        // Try to get or create a test conversation
        const { data: conversations } = await supabase
          .from('conversations')
          .select('id')
          .eq('user_id', session.user.id)
          .limit(1)

        if (conversations && conversations.length > 0) {
          setTestConversationId(conversations[0].id)
        } else {
          // Create a test conversation
          const { data: newConv } = await supabase
            .from('conversations')
            .insert({
              user_id: session.user.id,
              title: 'Image Generation Test',
              client_id: '00000000-0000-0000-0000-000000000001'
            })
            .select('id')
            .single()

          if (newConv) {
            setTestConversationId(newConv.id)
          }
        }
      } else {
        router.push('/login')
      }
    }
    checkAuth()
  }, [router])

  const handleGenerate = async (aspectRatio: string, model: string) => {
    if (!testConversationId) {
      setError('No test conversation available')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await generateConversationImage({
        conversation_id: testConversationId,
        prompt: 'A beautiful sunset over mountains with vibrant colors',
        aspect_ratio: aspectRatio,
        model: model
      })

      setImage(result)
      setShowSelector(false)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate image'
      console.error('Generation error:', err)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleRegenerate = () => {
    setImage(null)
    setShowSelector(true)
  }

  const handleDelete = async () => {
    // Would call deleteConversationImage(imageId) here
    setImage(null)
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Checking authentication...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[var(--color-bg-page)] p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-[var(--color-text-primary)] mb-2">
            Image Generation Test
          </h1>
          <p className="text-[var(--color-text-secondary)]">
            Test the new AI-powered image generation feature
          </p>
          {testConversationId && (
            <p className="text-sm text-[var(--color-text-muted)] mt-2">
              Test Conversation ID: {testConversationId}
            </p>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <p className="text-red-500">Error: {error}</p>
          </div>
        )}

        {/* Test Suggestion Component */}
        <div>
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
            1. Test Suggestion Prompt
          </h2>
          <ImageSuggestionPrompt
            suggestion={{
              suggested_prompt: 'sunset over mountains',
              reason: 'This would be clearer with a visual'
            }}
            onAccept={handleGenerate}
            onDecline={() => setShowSelector(false)}
            isGenerating={loading}
          />
        </div>

        {/* Test Manual Selector */}
        {showSelector && !loading && !image && (
          <div>
            <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
              2. Test Manual Selection
            </h2>
            <AspectRatioSelector
              onSelect={handleGenerate}
              onCancel={() => setShowSelector(false)}
            />
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 rounded-lg p-8">
            <div className="flex items-center justify-center gap-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]"></div>
              <span className="text-[var(--color-text-primary)]">
                Generating image... This may take 5-10 seconds
              </span>
            </div>
          </div>
        )}

        {/* Generated Image */}
        {image && !loading && (
          <div>
            <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
              3. Generated Image
            </h2>
            <InlineChatImage
              image={image}
              onRegenerate={handleRegenerate}
              onDelete={handleDelete}
            />
          </div>
        )}

        {/* Manual Trigger */}
        {!showSelector && !image && !loading && (
          <div>
            <button
              onClick={() => setShowSelector(true)}
              className="px-6 py-3 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors"
            >
              Or Generate Image Manually
            </button>
          </div>
        )}

        {/* Instructions */}
        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg p-6">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-3">
            Test Instructions
          </h3>
          <ol className="list-decimal list-inside space-y-2 text-[var(--color-text-secondary)]">
            <li>Click &quot;Yes, generate it&quot; on the suggestion to test the suggestion flow</li>
            <li>Or click &quot;Generate Image Manually&quot; to test the aspect ratio selector</li>
            <li>Select your preferred aspect ratio (1:1, 16:9, 9:16, or 4:3)</li>
            <li>Choose quality level (Fast or Quality)</li>
            <li>Click &quot;Generate Image&quot; and wait 5-10 seconds</li>
            <li>Test Download, Regenerate, and Delete buttons</li>
            <li>Check that images persist after page refresh</li>
          </ol>
        </div>

        {/* Back Button */}
        <div>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-2 bg-[var(--color-bg-hover)] text-[var(--color-text-primary)] rounded-lg hover:bg-[var(--color-border)] transition-colors"
          >
            ← Back to Chat
          </button>
        </div>
      </div>
    </div>
  )
}
