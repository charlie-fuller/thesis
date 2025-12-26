/**
 * AuthContext Tests
 *
 * Tests for authentication context provider and hooks.
 */

import { render, screen, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

// Mock Supabase
jest.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: jest.fn().mockResolvedValue({
        data: { session: null },
        error: null
      }),
      onAuthStateChange: jest.fn(() => {
        return {
          data: {
            subscription: {
              unsubscribe: jest.fn()
            }
          }
        }
      }),
      signInWithPassword: jest.fn(),
      signOut: jest.fn(),
      resetPasswordForEmail: jest.fn(),
      updateUser: jest.fn()
    }
  }
}))

// Test component to access auth context
function TestAuthConsumer() {
  const { user, loading, isAuthenticated } = useAuth()

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      {user && <div data-testid="user-email">{user.email}</div>}
    </div>
  )
}

describe('AuthContext', () => {
  describe('Initial State', () => {
    it('shows loading state initially', () => {
      render(
        <AuthProvider>
          <TestAuthConsumer />
        </AuthProvider>
      )

      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('shows not authenticated when no session', async () => {
      render(
        <AuthProvider>
          <TestAuthConsumer />
        </AuthProvider>
      )

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated')
      })
    })
  })

  describe('Authentication Flow', () => {
    it('provides auth methods to consumers', () => {
      const TestMethodsConsumer = () => {
        const { signIn, signOut, resetPassword, updatePassword } = useAuth()

        return (
          <div>
            <div data-testid="has-signin">{typeof signIn === 'function' ? 'yes' : 'no'}</div>
            <div data-testid="has-signout">{typeof signOut === 'function' ? 'yes' : 'no'}</div>
            <div data-testid="has-reset">{typeof resetPassword === 'function' ? 'yes' : 'no'}</div>
            <div data-testid="has-update">{typeof updatePassword === 'function' ? 'yes' : 'no'}</div>
          </div>
        )
      }

      render(
        <AuthProvider>
          <TestMethodsConsumer />
        </AuthProvider>
      )

      expect(screen.getByTestId('has-signin')).toHaveTextContent('yes')
      expect(screen.getByTestId('has-signout')).toHaveTextContent('yes')
      expect(screen.getByTestId('has-reset')).toHaveTextContent('yes')
      expect(screen.getByTestId('has-update')).toHaveTextContent('yes')
    })
  })

  describe('Error Handling', () => {
    it('component renders without crashing', async () => {
      // Simply verify the component can render and handle the loading state
      render(
        <AuthProvider>
          <TestAuthConsumer />
        </AuthProvider>
      )

      // Should render either loading or auth status
      await waitFor(() => {
        const authStatus = screen.queryByTestId('auth-status')
        const loading = screen.queryByText('Loading...')
        expect(authStatus || loading).toBeInTheDocument()
      })
    })
  })
})
