/**
 * AuthContext Tests
 *
 * Tests for the stubbed auth context (API-key auth mode).
 */

import { render, screen } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

// Test component to access auth context
function TestAuthConsumer() {
  const { user, loading, isAuthenticated, isAdmin } = useAuth()

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      <div data-testid="is-admin">
        {isAdmin ? 'yes' : 'no'}
      </div>
      {user && <div data-testid="user-id">{user.id}</div>}
    </div>
  )
}

describe('AuthContext (API key mode)', () => {
  describe('With API key set', () => {
    it('shows authenticated when API key is present', () => {
      // NEXT_PUBLIC_API_KEY is set in jest.setup.js
      render(
        <AuthProvider>
          <TestAuthConsumer />
        </AuthProvider>
      )

      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
    })

    it('provides admin access by default', () => {
      render(
        <AuthProvider>
          <TestAuthConsumer />
        </AuthProvider>
      )

      expect(screen.getByTestId('is-admin')).toHaveTextContent('yes')
    })

    it('provides stub user', () => {
      render(
        <AuthProvider>
          <TestAuthConsumer />
        </AuthProvider>
      )

      expect(screen.getByTestId('user-id')).toHaveTextContent('api-key-user')
    })
  })

  describe('Auth methods', () => {
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
})
