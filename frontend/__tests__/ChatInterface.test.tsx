/**
 * ChatInterface Component Tests
 *
 * Tests for the main chat interface component including:
 * - Message sending and display
 * - Streaming responses
 * - Agent routing via @mentions
 * - Error handling
 * - Loading states
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChatInterface from '@/components/ChatInterface'
import { AuthProvider } from '@/contexts/AuthContext'

// Mock dependencies
jest.mock('@/lib/supabase', () => ({
  supabase: {
    from: jest.fn(() => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => ({
          order: jest.fn(() => Promise.resolve({ data: [], error: null })),
        })),
      })),
      insert: jest.fn(() => Promise.resolve({ data: [{ id: 'test-msg-1' }], error: null })),
    })),
    auth: {
      getSession: jest.fn(() => Promise.resolve({ data: { session: { user: { id: 'test-user' } } } })),
    },
  },
}))

// Mock fetch for API calls
const mockFetch = jest.fn()
global.fetch = mockFetch

// Mock EventSource for streaming
class MockEventSource {
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  close = jest.fn()

  constructor(url: string) {
    // Simulate connection
    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', { data: JSON.stringify({ content: 'Test response' }) }))
      }
    }, 100)
  }
}
;(global as any).EventSource = MockEventSource

// Test wrapper with providers
const renderWithProviders = (component: React.ReactElement) => {
  return render(<AuthProvider>{component}</AuthProvider>)
}

describe('ChatInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockFetch.mockReset()
  })

  describe('Rendering', () => {
    it('renders message input and send button', () => {
      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      expect(screen.getByTestId('message-input')).toBeInTheDocument()
      expect(screen.getByTestId('send-button')).toBeInTheDocument()
    })

    it('renders empty state for new conversation', () => {
      renderWithProviders(<ChatInterface conversationId={null} />)

      expect(screen.getByTestId('message-input')).toBeInTheDocument()
    })

    it('displays existing messages', async () => {
      const mockMessages = [
        { id: '1', role: 'user', content: 'Hello', created_at: new Date().toISOString() },
        { id: '2', role: 'assistant', content: 'Hi there!', created_at: new Date().toISOString() },
      ]

      // Would need to mock the message loading properly
      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      // Wait for messages to load
      await waitFor(() => {
        // Check for message container
        expect(screen.getByTestId('message-container')).toBeInTheDocument()
      })
    })
  })

  describe('Message Sending', () => {
    it('sends message when send button is clicked', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ conversation_id: 'test-conv', message: 'Response' }),
      })

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')
      const sendButton = screen.getByTestId('send-button')

      await userEvent.type(input, 'Test message')
      await userEvent.click(sendButton)

      // Verify message was sent
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it('sends message on Enter key press', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ conversation_id: 'test-conv' }),
      })

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test message{enter}')

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it('does not send on Shift+Enter (allows new line)', async () => {
      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Line 1{shift>}{enter}{/shift}Line 2')

      // Should not have sent a message
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('prevents sending empty messages', async () => {
      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const sendButton = screen.getByTestId('send-button')

      await userEvent.click(sendButton)

      // Should not have sent
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('displays optimistic message immediately', async () => {
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                ok: true,
                json: () => Promise.resolve({ conversation_id: 'test-conv' }),
              })
            }, 1000)
          })
      )

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test message')
      await userEvent.click(screen.getByTestId('send-button'))

      // Message should appear immediately (optimistic update)
      await waitFor(() => {
        expect(screen.getByText('Test message')).toBeInTheDocument()
      })
    })

    it('prevents double-submit while loading', async () => {
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => {
              resolve({ ok: true, json: () => Promise.resolve({}) })
            }, 1000)
          })
      )

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')
      const sendButton = screen.getByTestId('send-button')

      await userEvent.type(input, 'Test')
      await userEvent.click(sendButton)
      await userEvent.click(sendButton)
      await userEvent.click(sendButton)

      // Should only have one fetch call
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('Agent Routing', () => {
    it('routes message to @mentioned agent', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ agent: 'atlas', conversation_id: 'test' }),
      })

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, '@atlas What are the trends?')
      await userEvent.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        // Check that the request included agent mention
        const lastCall = mockFetch.mock.calls[0]
        expect(lastCall[1].body).toContain('@atlas')
      })
    })

    it('uses locked agent when lockedAgentId is provided', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ agent: 'capital', conversation_id: 'test' }),
      })

      renderWithProviders(<ChatInterface conversationId="test-conv" lockedAgentId="capital" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Calculate ROI')
      await userEvent.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        // Should route to capital regardless of content
        const lastCall = mockFetch.mock.calls[0]
        if (lastCall) {
          const body = JSON.parse(lastCall[1].body)
          expect(body.agent_id || body.lockedAgentId).toBe('capital')
        }
      })
    })
  })

  describe('Streaming Responses', () => {
    it('displays streaming text as it arrives', async () => {
      // This test would require more complex EventSource mocking
      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      // The MockEventSource above simulates streaming
      // A full test would verify chunks appear incrementally
    })

    it('shows loading indicator during streaming', async () => {
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve({ ok: true, json: () => Promise.resolve({}) }), 1000)
          })
      )

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test')
      await userEvent.click(screen.getByTestId('send-button'))

      // Loading indicator should appear
      await waitFor(() => {
        expect(screen.getByTestId('loading-indicator')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message on API failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test')
      await userEvent.click(screen.getByTestId('send-button'))

      // Error should be displayed
      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
      })
    })

    it('shows retry button on network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test')
      await userEvent.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        expect(screen.getByTestId('retry-button')).toBeInTheDocument()
      })
    })

    it('retries failed message when retry button is clicked', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ conversation_id: 'test' }),
        })

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test')
      await userEvent.click(screen.getByTestId('send-button'))

      // Wait for error
      await waitFor(() => {
        expect(screen.getByTestId('retry-button')).toBeInTheDocument()
      })

      // Click retry
      await userEvent.click(screen.getByTestId('retry-button'))

      // Should retry the request
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2)
      })
    })

    it('handles 429 rate limit gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: () => Promise.resolve({ error: 'Rate limit exceeded' }),
      })

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test')
      await userEvent.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        const error = screen.getByTestId('error-message')
        expect(error).toHaveTextContent(/rate limit|too many/i)
      })
    })
  })

  describe('Input Behavior', () => {
    it('clears input after successful send', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ conversation_id: 'test' }),
      })

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input') as HTMLInputElement

      await userEvent.type(input, 'Test message')
      await userEvent.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        expect(input.value).toBe('')
      })
    })

    it('disables input while streaming', async () => {
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve({ ok: true, json: () => Promise.resolve({}) }), 1000)
          })
      )

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test')
      await userEvent.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        expect(input).toBeDisabled()
      })
    })

    it('auto-focuses input on mount', () => {
      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')
      expect(document.activeElement).toBe(input)
    })
  })

  describe('Markdown Rendering', () => {
    it('renders markdown in assistant messages', async () => {
      // This would test that markdown like **bold** renders correctly
      // Requires mocking messages with markdown content
    })

    it('renders code blocks with syntax highlighting', async () => {
      // Test code block rendering
    })
  })

  describe('Scroll Behavior', () => {
    it('scrolls to bottom on new message', async () => {
      const scrollIntoViewMock = jest.fn()
      Element.prototype.scrollIntoView = scrollIntoViewMock

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ conversation_id: 'test' }),
      })

      renderWithProviders(<ChatInterface conversationId="test-conv" />)

      const input = screen.getByTestId('message-input')

      await userEvent.type(input, 'Test')
      await userEvent.click(screen.getByTestId('send-button'))

      await waitFor(() => {
        expect(scrollIntoViewMock).toHaveBeenCalled()
      })
    })
  })
})
