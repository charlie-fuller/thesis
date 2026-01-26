import { test, expect } from '@playwright/test'

/**
 * Chat E2E Tests
 * Tests the complete chat flow including message sending, streaming, and agent routing.
 */

test.describe('Agent Chat', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/chat', { timeout: 10000 })
  })

  test('chat page renders with message input', async ({ page }) => {
    await expect(page.locator('[data-testid="message-input"]')).toBeVisible()
    await expect(page.locator('[data-testid="send-button"]')).toBeVisible()
  })

  test('send message and receive streaming response', async ({ page }) => {
    // Type a message
    await page.fill('[data-testid="message-input"]', 'What are AI trends?')

    // Send the message
    await page.click('[data-testid="send-button"]')

    // User message should appear
    await expect(page.locator('[data-testid="user-message"]').last()).toContainText('What are AI trends?')

    // Wait for assistant response to start streaming
    await expect(page.locator('[data-testid="assistant-message"]')).toBeVisible({ timeout: 30000 })

    // Wait for streaming to complete (loading indicator disappears)
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeHidden({ timeout: 60000 })

    // Assistant message should have content
    const assistantMessage = page.locator('[data-testid="assistant-message"]').last()
    await expect(assistantMessage).not.toBeEmpty()
  })

  test('@mention routes to specific agent', async ({ page }) => {
    // Send message with @mention
    await page.fill('[data-testid="message-input"]', '@atlas What are the latest AI research trends?')
    await page.click('[data-testid="send-button"]')

    // Wait for response
    await expect(page.locator('[data-testid="assistant-message"]')).toBeVisible({ timeout: 30000 })

    // Check that Atlas agent responded (look for agent badge or attribution)
    await expect(page.locator('[data-testid="agent-badge"]').last()).toContainText(/atlas/i)
  })

  test('conversation persists on refresh', async ({ page }) => {
    // Send a message
    const testMessage = 'Test message for persistence ' + Date.now()
    await page.fill('[data-testid="message-input"]', testMessage)
    await page.click('[data-testid="send-button"]')

    // Wait for message to appear
    await expect(page.locator('[data-testid="user-message"]').last()).toContainText(testMessage)

    // Reload the page
    await page.reload()

    // Message should still be visible
    await expect(page.locator('[data-testid="user-message"]')).toContainText(testMessage)
  })

  test('keyboard submit works with Enter key', async ({ page }) => {
    // Type a message
    await page.fill('[data-testid="message-input"]', 'Hello from keyboard')

    // Press Enter to send
    await page.keyboard.press('Enter')

    // Message should appear
    await expect(page.locator('[data-testid="user-message"]').last()).toContainText('Hello from keyboard')
  })

  test('Shift+Enter creates new line instead of sending', async ({ page }) => {
    const messageInput = page.locator('[data-testid="message-input"]')

    // Type first line
    await messageInput.fill('Line 1')

    // Shift+Enter for new line
    await page.keyboard.press('Shift+Enter')
    await page.keyboard.type('Line 2')

    // Check that input has both lines (not sent)
    await expect(messageInput).toContainText('Line 1')
    await expect(messageInput).toContainText('Line 2')
  })

  test('empty message cannot be sent', async ({ page }) => {
    // Try to click send with empty input
    await page.click('[data-testid="send-button"]')

    // No message should appear
    await expect(page.locator('[data-testid="user-message"]')).toHaveCount(0)
  })

  test('message input is disabled during streaming', async ({ page }) => {
    // Send a message
    await page.fill('[data-testid="message-input"]', 'Test loading state')
    await page.click('[data-testid="send-button"]')

    // Input should be disabled while streaming
    await expect(page.locator('[data-testid="message-input"]')).toBeDisabled()

    // Wait for streaming to complete
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeHidden({ timeout: 60000 })

    // Input should be enabled again
    await expect(page.locator('[data-testid="message-input"]')).toBeEnabled()
  })

  test('can switch between conversations', async ({ page }) => {
    // Click new conversation button
    await page.click('[data-testid="new-conversation-button"]')

    // Send a message in new conversation
    await page.fill('[data-testid="message-input"]', 'New conversation message')
    await page.click('[data-testid="send-button"]')

    // Wait for response
    await expect(page.locator('[data-testid="assistant-message"]')).toBeVisible({ timeout: 30000 })

    // Click on a previous conversation in sidebar
    await page.click('[data-testid="conversation-item"]')

    // Should show previous conversation's messages
    await expect(page.locator('[data-testid="message-container"]')).toBeVisible()
  })

  test('dig deeper button expands response', async ({ page }) => {
    // Send a message
    await page.fill('[data-testid="message-input"]', 'Explain AI briefly')
    await page.click('[data-testid="send-button"]')

    // Wait for response
    await expect(page.locator('[data-testid="assistant-message"]')).toBeVisible({ timeout: 30000 })
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeHidden({ timeout: 60000 })

    // Click dig deeper button if available
    const digDeeperButton = page.locator('[data-testid="dig-deeper-button"]')
    if (await digDeeperButton.isVisible()) {
      await digDeeperButton.click()

      // Should trigger a new response
      await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible()
    }
  })

  test('error handling shows user-friendly message', async ({ page }) => {
    // Intercept API calls to simulate failure
    await page.route('**/api/chat/**', (route) => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal server error' }),
      })
    })

    // Send a message
    await page.fill('[data-testid="message-input"]', 'This will fail')
    await page.click('[data-testid="send-button"]')

    // Error message should appear
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 10000 })
  })
})
