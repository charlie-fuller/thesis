import { render, screen } from '@testing-library/react'
import ChatMessage from '@/components/ChatMessage'

describe('ChatMessage', () => {
  it('renders user message content', () => {
    render(
      <ChatMessage
        content="Hello from user"
        role="user"
        timestamp="2025-10-31T12:00:00.000Z"
      />
    )

    const messageElement = screen.getByText('Hello from user')
    expect(messageElement).toBeInTheDocument()
  })

  it('renders assistant message content', () => {
    render(
      <ChatMessage
        content="Hello from assistant"
        role="assistant"
        timestamp="2025-10-31T12:00:00.000Z"
      />
    )

    const messageElement = screen.getByText('Hello from assistant')
    expect(messageElement).toBeInTheDocument()
  })

  it('displays timestamp', () => {
    const timestamp = '2025-10-31T15:30:00.000Z'
    render(
      <ChatMessage
        content="Test message"
        role="user"
        timestamp={timestamp}
      />
    )

    // Timestamp should be formatted and displayed
    const timestampElement = screen.getByTitle(timestamp)
    expect(timestampElement).toBeInTheDocument()
  })

  it('aligns user messages to the right', () => {
    const { container } = render(
      <ChatMessage
        content="User message"
        role="user"
        timestamp="2025-10-31T12:00:00.000Z"
      />
    )

    const outerDiv = container.firstChild as HTMLElement
    expect(outerDiv).toHaveClass('justify-end')
  })

  it('aligns assistant messages to the left', () => {
    const { container } = render(
      <ChatMessage
        content="Assistant message"
        role="assistant"
        timestamp="2025-10-31T12:00:00.000Z"
      />
    )

    const outerDiv = container.firstChild as HTMLElement
    expect(outerDiv).toHaveClass('justify-start')
  })

  it('applies correct message class for user role', () => {
    const { container } = render(
      <ChatMessage
        content="User message"
        role="user"
        timestamp="2025-10-31T12:00:00.000Z"
      />
    )

    const messageDiv = container.querySelector('.message-user')
    expect(messageDiv).toBeInTheDocument()
  })

  it('applies correct message class for assistant role', () => {
    const { container } = render(
      <ChatMessage
        content="Assistant message"
        role="assistant"
        timestamp="2025-10-31T12:00:00.000Z"
      />
    )

    const messageDiv = container.querySelector('.message-assistant')
    expect(messageDiv).toBeInTheDocument()
  })
})
