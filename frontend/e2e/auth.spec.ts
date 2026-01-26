import { test, expect } from '@playwright/test'

/**
 * Authentication E2E Tests
 * Tests the complete authentication flow including login, logout, and session management.
 */

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing session
    await page.context().clearCookies()
  })

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/auth/login')

    // Check for essential elements
    await expect(page.locator('[data-testid="email"]')).toBeVisible()
    await expect(page.locator('[data-testid="password"]')).toBeVisible()
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible()
  })

  test('login with valid credentials redirects to chat', async ({ page }) => {
    await page.goto('/auth/login')

    // Fill in credentials
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')

    // Submit the form
    await page.click('[data-testid="login-button"]')

    // Should redirect to chat page
    await expect(page).toHaveURL('/chat', { timeout: 10000 })
  })

  test('login with invalid credentials shows error message', async ({ page }) => {
    await page.goto('/auth/login')

    // Fill in invalid credentials
    await page.fill('[data-testid="email"]', 'invalid@example.com')
    await page.fill('[data-testid="password"]', 'wrongpassword')

    // Submit the form
    await page.click('[data-testid="login-button"]')

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/invalid|incorrect|failed/i)
  })

  test('login form validates email format', async ({ page }) => {
    await page.goto('/auth/login')

    // Fill in invalid email
    await page.fill('[data-testid="email"]', 'notanemail')
    await page.fill('[data-testid="password"]', 'password123')

    // Submit the form
    await page.click('[data-testid="login-button"]')

    // Should show validation error or browser validation
    const emailInput = page.locator('[data-testid="email"]')
    const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.validity.valid)
    expect(isValid).toBe(false)
  })

  test('login form requires password', async ({ page }) => {
    await page.goto('/auth/login')

    // Fill in only email
    await page.fill('[data-testid="email"]', 'test@example.com')

    // Try to submit
    await page.click('[data-testid="login-button"]')

    // Should stay on login page or show validation
    await expect(page).toHaveURL(/\/auth\/login/)
  })

  test('password reset link navigates to reset page', async ({ page }) => {
    await page.goto('/auth/login')

    // Click forgot password link
    await page.click('[data-testid="forgot-password-link"]')

    // Should navigate to password reset
    await expect(page).toHaveURL(/\/auth\/(forgot-password|reset)/)
  })

  test('logout clears session and redirects to login', async ({ page }) => {
    // First, log in
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/chat', { timeout: 10000 })

    // Now log out
    await page.click('[data-testid="user-menu"]')
    await page.click('[data-testid="logout-button"]')

    // Should redirect to login
    await expect(page).toHaveURL(/\/auth\/login/)
  })

  test('protected routes redirect to login when not authenticated', async ({ page }) => {
    // Try to access protected route
    await page.goto('/chat')

    // Should redirect to login
    await expect(page).toHaveURL(/\/auth\/login/)
  })

  test('session persists across page reload', async ({ page }) => {
    // Log in
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/chat', { timeout: 10000 })

    // Reload the page
    await page.reload()

    // Should still be on chat page (not redirected to login)
    await expect(page).toHaveURL('/chat')
  })
})
