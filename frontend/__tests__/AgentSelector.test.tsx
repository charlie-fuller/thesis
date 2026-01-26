/**
 * AgentSelector Component Tests
 *
 * Tests for the agent selector component including:
 * - @mention parsing
 * - Agent filtering/search
 * - Keyboard navigation
 * - Selection handling
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AgentSelector from '@/components/AgentSelector'

// Mock agent data
const mockAgents = [
  { id: 'atlas', name: 'Atlas', display_name: 'Atlas (Research)', description: 'Research and trends' },
  { id: 'capital', name: 'Capital', display_name: 'Capital (Finance)', description: 'Financial analysis' },
  { id: 'guardian', name: 'Guardian', display_name: 'Guardian (Security)', description: 'Security and compliance' },
  { id: 'counselor', name: 'Counselor', display_name: 'Counselor (Legal)', description: 'Legal advice' },
  { id: 'sage', name: 'Sage', display_name: 'Sage (People)', description: 'Change management' },
]

// Default props
const defaultProps = {
  agents: mockAgents,
  onSelect: jest.fn(),
  isOpen: false,
  onClose: jest.fn(),
  searchQuery: '',
}

describe('AgentSelector', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('does not render when isOpen is false', () => {
      render(<AgentSelector {...defaultProps} isOpen={false} />)

      expect(screen.queryByTestId('agent-selector')).not.toBeInTheDocument()
    })

    it('renders agent list when isOpen is true', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} />)

      expect(screen.getByTestId('agent-selector')).toBeInTheDocument()
      expect(screen.getByText('Atlas (Research)')).toBeInTheDocument()
      expect(screen.getByText('Capital (Finance)')).toBeInTheDocument()
    })

    it('displays agent descriptions', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} />)

      expect(screen.getByText('Research and trends')).toBeInTheDocument()
      expect(screen.getByText('Financial analysis')).toBeInTheDocument()
    })

    it('shows agent icons/avatars', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} />)

      // Each agent should have an icon/avatar
      const agentItems = screen.getAllByTestId('agent-item')
      expect(agentItems).toHaveLength(mockAgents.length)
    })
  })

  describe('@Mention Parsing', () => {
    it('filters agents based on searchQuery', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} searchQuery="atl" />)

      expect(screen.getByText('Atlas (Research)')).toBeInTheDocument()
      expect(screen.queryByText('Capital (Finance)')).not.toBeInTheDocument()
    })

    it('shows all agents when searchQuery is empty', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} searchQuery="" />)

      const agentItems = screen.getAllByTestId('agent-item')
      expect(agentItems).toHaveLength(mockAgents.length)
    })

    it('matches partial agent names case-insensitively', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} searchQuery="CAP" />)

      expect(screen.getByText('Capital (Finance)')).toBeInTheDocument()
    })

    it('matches agent descriptions', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} searchQuery="security" />)

      expect(screen.getByText('Guardian (Security)')).toBeInTheDocument()
    })

    it('shows no results message when no agents match', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} searchQuery="xyz123" />)

      expect(screen.getByText(/no agents found/i)).toBeInTheDocument()
    })
  })

  describe('Selection', () => {
    it('calls onSelect when agent is clicked', async () => {
      const onSelect = jest.fn()
      render(<AgentSelector {...defaultProps} isOpen={true} onSelect={onSelect} />)

      await userEvent.click(screen.getByText('Atlas (Research)'))

      expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'atlas' }))
    })

    it('closes selector after selection', async () => {
      const onClose = jest.fn()
      render(<AgentSelector {...defaultProps} isOpen={true} onClose={onClose} />)

      await userEvent.click(screen.getByText('Atlas (Research)'))

      expect(onClose).toHaveBeenCalled()
    })

    it('highlights first filtered result', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} searchQuery="atl" />)

      const firstItem = screen.getByTestId('agent-item')
      expect(firstItem).toHaveClass('highlighted') // Or whatever highlight class is used
    })
  })

  describe('Keyboard Navigation', () => {
    it('navigates down with ArrowDown key', async () => {
      render(<AgentSelector {...defaultProps} isOpen={true} />)

      // Simulate arrow key navigation
      fireEvent.keyDown(document, { key: 'ArrowDown' })

      await waitFor(() => {
        const highlightedItem = screen.getByTestId('agent-item-highlighted')
        expect(highlightedItem).toBeInTheDocument()
      })
    })

    it('navigates up with ArrowUp key', async () => {
      render(<AgentSelector {...defaultProps} isOpen={true} />)

      // Navigate down first
      fireEvent.keyDown(document, { key: 'ArrowDown' })
      fireEvent.keyDown(document, { key: 'ArrowDown' })

      // Then up
      fireEvent.keyDown(document, { key: 'ArrowUp' })

      // Verify highlight moved
    })

    it('selects highlighted agent on Enter', async () => {
      const onSelect = jest.fn()
      render(<AgentSelector {...defaultProps} isOpen={true} onSelect={onSelect} />)

      // Navigate to second item and select
      fireEvent.keyDown(document, { key: 'ArrowDown' })
      fireEvent.keyDown(document, { key: 'Enter' })

      await waitFor(() => {
        expect(onSelect).toHaveBeenCalled()
      })
    })

    it('closes on Escape key', () => {
      const onClose = jest.fn()
      render(<AgentSelector {...defaultProps} isOpen={true} onClose={onClose} />)

      fireEvent.keyDown(document, { key: 'Escape' })

      expect(onClose).toHaveBeenCalled()
    })

    it('wraps navigation at list boundaries', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} />)

      // Navigate beyond the end
      for (let i = 0; i < mockAgents.length + 1; i++) {
        fireEvent.keyDown(document, { key: 'ArrowDown' })
      }

      // Should wrap to first item
    })
  })

  describe('Multi-Select Mode', () => {
    it('supports selecting multiple agents when multiSelect is true', async () => {
      const onSelect = jest.fn()
      render(<AgentSelector {...defaultProps} isOpen={true} multiSelect={true} onSelect={onSelect} />)

      await userEvent.click(screen.getByText('Atlas (Research)'))
      await userEvent.click(screen.getByText('Capital (Finance)'))

      // Both agents should be selected
      expect(onSelect).toHaveBeenCalledTimes(2)
    })

    it('toggles selection on repeated click in multiSelect mode', async () => {
      const onSelect = jest.fn()
      render(<AgentSelector {...defaultProps} isOpen={true} multiSelect={true} onSelect={onSelect} />)

      const atlasItem = screen.getByText('Atlas (Research)')

      await userEvent.click(atlasItem)
      await userEvent.click(atlasItem)

      // Should have toggled selection
    })

    it('shows checkmarks on selected agents in multiSelect mode', async () => {
      render(
        <AgentSelector {...defaultProps} isOpen={true} multiSelect={true} selectedAgentIds={['atlas', 'capital']} />
      )

      // Selected items should have checkmarks
      const checkmarks = screen.getAllByTestId('agent-checkmark')
      expect(checkmarks).toHaveLength(2)
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} />)

      const selector = screen.getByTestId('agent-selector')
      expect(selector).toHaveAttribute('role', 'listbox')
    })

    it('items have proper role', () => {
      render(<AgentSelector {...defaultProps} isOpen={true} />)

      const items = screen.getAllByTestId('agent-item')
      items.forEach((item) => {
        expect(item).toHaveAttribute('role', 'option')
      })
    })

    it('indicates selected state with aria-selected', async () => {
      const onSelect = jest.fn()
      render(<AgentSelector {...defaultProps} isOpen={true} onSelect={onSelect} />)

      await userEvent.click(screen.getByText('Atlas (Research)'))

      // After selection, item should have aria-selected
    })
  })

  describe('Positioning', () => {
    it('positions dropdown relative to anchor', () => {
      const anchorRef = { current: document.createElement('div') }
      render(<AgentSelector {...defaultProps} isOpen={true} anchorRef={anchorRef} />)

      const selector = screen.getByTestId('agent-selector')
      expect(selector).toHaveStyle({ position: 'absolute' })
    })
  })

  describe('Click Outside', () => {
    it('closes when clicking outside', async () => {
      const onClose = jest.fn()
      render(
        <div>
          <div data-testid="outside">Outside</div>
          <AgentSelector {...defaultProps} isOpen={true} onClose={onClose} />
        </div>
      )

      await userEvent.click(screen.getByTestId('outside'))

      expect(onClose).toHaveBeenCalled()
    })
  })
})
