/**
 * AgentSelector Component Tests
 *
 * Tests for the agent selector component used in meeting rooms.
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AgentSelector from '@/components/AgentSelector'

// Mock the AgentIcon component
jest.mock('@/components/AgentIcon', () => ({
  AgentIcon: ({ agentId }: { agentId: string }) => <div data-testid={`agent-icon-${agentId}`}>{agentId}</div>,
  getAgentColor: () => 'blue',
}))

describe('AgentSelector', () => {
  const defaultProps = {
    selectedAgents: [] as string[],
    onAgentsChange: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders with empty selection', () => {
      render(<AgentSelector {...defaultProps} />)
      // Should show the selector button
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('renders selected agent chips', () => {
      render(<AgentSelector {...defaultProps} selectedAgents={['atlas', 'capital']} />)
      // Should display selected agents
      expect(screen.getByText(/Atlas/i)).toBeInTheDocument()
      expect(screen.getByText(/Capital/i)).toBeInTheDocument()
    })

    it('applies custom className', () => {
      const { container } = render(<AgentSelector {...defaultProps} className="custom-class" />)
      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('Dropdown Behavior', () => {
    it('opens dropdown on button click', async () => {
      render(<AgentSelector {...defaultProps} />)

      const buttons = screen.getAllByRole('button')
      await userEvent.click(buttons[0])

      // Dropdown should show agent options
      await waitFor(() => {
        expect(screen.getByText(/Atlas/i)).toBeInTheDocument()
      })
    })
  })

  describe('Agent Selection', () => {
    it('calls onAgentsChange when agent is toggled', async () => {
      const onAgentsChange = jest.fn()
      render(<AgentSelector {...defaultProps} onAgentsChange={onAgentsChange} />)

      // Open dropdown
      const buttons = screen.getAllByRole('button')
      await userEvent.click(buttons[0])

      // Wait for dropdown to appear and click on Atlas
      await waitFor(() => {
        expect(screen.getByText(/Atlas/i)).toBeInTheDocument()
      })

      const atlasButton = screen.getAllByRole('button').find(btn =>
        btn.textContent?.includes('Atlas')
      )
      if (atlasButton) {
        await userEvent.click(atlasButton)
        expect(onAgentsChange).toHaveBeenCalled()
      }
    })
  })

  describe('Agent Categories', () => {
    it('displays agent categories', async () => {
      render(<AgentSelector {...defaultProps} />)

      // Open dropdown
      const buttons = screen.getAllByRole('button')
      await userEvent.click(buttons[0])

      // Should show categories (use getAllByText since "Stakeholder" appears multiple times)
      await waitFor(() => {
        expect(screen.getAllByText(/Stakeholder/i).length).toBeGreaterThan(0)
      })
    })
  })

  describe('Agent Descriptions', () => {
    it('shows agent descriptions in dropdown', async () => {
      render(<AgentSelector {...defaultProps} />)

      // Open dropdown
      const buttons = screen.getAllByRole('button')
      await userEvent.click(buttons[0])

      // Should show descriptions
      await waitFor(() => {
        expect(screen.getByText(/research, case studies/i)).toBeInTheDocument()
      })
    })
  })
})
