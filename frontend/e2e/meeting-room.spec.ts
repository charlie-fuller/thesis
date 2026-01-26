import { test, expect } from '@playwright/test'

/**
 * Meeting Room E2E Tests
 * Tests multi-agent meeting room functionality including autonomous mode.
 */

test.describe('Meeting Room', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/chat', { timeout: 10000 })

    // Navigate to meeting rooms
    await page.goto('/meeting-room')
  })

  test('meeting room page renders correctly', async ({ page }) => {
    await expect(page.locator('[data-testid="meeting-room-list"]')).toBeVisible()
    await expect(page.locator('[data-testid="create-room-button"]')).toBeVisible()
  })

  test('can create a new meeting room', async ({ page }) => {
    // Click create room button
    await page.click('[data-testid="create-room-button"]')

    // Fill in room details
    await page.fill('[data-testid="room-name-input"]', 'Test Strategy Meeting')
    await page.fill('[data-testid="room-topic-input"]', 'AI implementation strategy')

    // Select agents
    await page.click('[data-testid="agent-select-atlas"]')
    await page.click('[data-testid="agent-select-capital"]')
    await page.click('[data-testid="agent-select-guardian"]')

    // Create the room
    await page.click('[data-testid="create-room-submit"]')

    // Should redirect to the new room
    await expect(page).toHaveURL(/\/meeting-room\/[\w-]+/)
  })

  test('can add agents to an existing room', async ({ page }) => {
    // Create a room first
    await page.click('[data-testid="create-room-button"]')
    await page.fill('[data-testid="room-name-input"]', 'Agent Addition Test')
    await page.click('[data-testid="agent-select-coordinator"]')
    await page.click('[data-testid="create-room-submit"]')

    // Wait for room to load
    await expect(page).toHaveURL(/\/meeting-room\/[\w-]+/)

    // Open agent management
    await page.click('[data-testid="manage-agents-button"]')

    // Add new agent
    await page.click('[data-testid="add-agent-sage"]')
    await page.click('[data-testid="save-agents-button"]')

    // Verify agent was added
    await expect(page.locator('[data-testid="participant-sage"]')).toBeVisible()
  })

  test('can send message and get multi-agent responses', async ({ page }) => {
    // Create room with multiple agents
    await page.click('[data-testid="create-room-button"]')
    await page.fill('[data-testid="room-name-input"]', 'Multi-Agent Test')
    await page.fill('[data-testid="room-topic-input"]', 'ROI analysis and compliance')
    await page.click('[data-testid="agent-select-capital"]')
    await page.click('[data-testid="agent-select-guardian"]')
    await page.click('[data-testid="create-room-submit"]')

    // Send a message
    await page.fill('[data-testid="meeting-message-input"]', 'What are the financial and compliance considerations?')
    await page.click('[data-testid="meeting-send-button"]')

    // Should get responses from multiple agents
    await expect(page.locator('[data-testid="agent-message"]')).toHaveCount(2, { timeout: 60000 })
  })

  test('autonomous mode starts discussion automatically', async ({ page }) => {
    // Create room
    await page.click('[data-testid="create-room-button"]')
    await page.fill('[data-testid="room-name-input"]', 'Autonomous Test')
    await page.fill('[data-testid="room-topic-input"]', 'Enterprise AI strategy')
    await page.click('[data-testid="agent-select-atlas"]')
    await page.click('[data-testid="agent-select-strategist"]')
    await page.click('[data-testid="create-room-submit"]')

    // Enable autonomous mode
    await page.click('[data-testid="autonomous-mode-toggle"]')

    // Start autonomous discussion
    await page.click('[data-testid="start-discussion-button"]')

    // Should see agents discussing automatically
    await expect(page.locator('[data-testid="agent-message"]')).toHaveCount(1, { timeout: 30000 })

    // Wait for more messages
    await expect(page.locator('[data-testid="agent-message"]').nth(1)).toBeVisible({ timeout: 30000 })
  })

  test('user interjection pauses autonomous mode', async ({ page }) => {
    // Create and start autonomous room
    await page.click('[data-testid="create-room-button"]')
    await page.fill('[data-testid="room-name-input"]', 'Interjection Test')
    await page.click('[data-testid="agent-select-coordinator"]')
    await page.click('[data-testid="agent-select-atlas"]')
    await page.click('[data-testid="create-room-submit"]')

    await page.click('[data-testid="autonomous-mode-toggle"]')
    await page.click('[data-testid="start-discussion-button"]')

    // Wait for discussion to start
    await expect(page.locator('[data-testid="agent-message"]')).toBeVisible({ timeout: 30000 })

    // User interjects
    await page.fill('[data-testid="meeting-message-input"]', 'I have a question about this')
    await page.click('[data-testid="meeting-send-button"]')

    // Autonomous mode should pause
    await expect(page.locator('[data-testid="autonomous-paused-indicator"]')).toBeVisible()
  })

  test('can generate synthesis report', async ({ page }) => {
    // Create room with discussion
    await page.click('[data-testid="create-room-button"]')
    await page.fill('[data-testid="room-name-input"]', 'Synthesis Test')
    await page.click('[data-testid="agent-select-coordinator"]')
    await page.click('[data-testid="agent-select-capital"]')
    await page.click('[data-testid="create-room-submit"]')

    // Have a discussion
    await page.fill('[data-testid="meeting-message-input"]', 'Discuss ROI considerations')
    await page.click('[data-testid="meeting-send-button"]')
    await expect(page.locator('[data-testid="agent-message"]')).toBeVisible({ timeout: 30000 })

    // Generate synthesis
    await page.click('[data-testid="generate-synthesis-button"]')

    // Should show synthesis report
    await expect(page.locator('[data-testid="synthesis-report"]')).toBeVisible({ timeout: 30000 })
  })

  test('meeting room preserves history on reload', async ({ page }) => {
    // Create room
    await page.click('[data-testid="create-room-button"]')
    await page.fill('[data-testid="room-name-input"]', 'Persistence Test')
    await page.click('[data-testid="agent-select-coordinator"]')
    await page.click('[data-testid="create-room-submit"]')

    // Send message
    const testMessage = 'Test persistence ' + Date.now()
    await page.fill('[data-testid="meeting-message-input"]', testMessage)
    await page.click('[data-testid="meeting-send-button"]')

    // Wait for response
    await expect(page.locator('[data-testid="agent-message"]')).toBeVisible({ timeout: 30000 })

    // Reload page
    await page.reload()

    // Message should still be visible
    await expect(page.locator('[data-testid="user-message"]')).toContainText(testMessage)
  })

  test('can delete a meeting room', async ({ page }) => {
    // Create room
    await page.click('[data-testid="create-room-button"]')
    await page.fill('[data-testid="room-name-input"]', 'Delete Test Room')
    await page.click('[data-testid="agent-select-coordinator"]')
    await page.click('[data-testid="create-room-submit"]')

    // Wait for room to load
    await expect(page).toHaveURL(/\/meeting-room\/[\w-]+/)

    // Get the room ID from URL
    const roomUrl = page.url()

    // Delete the room
    await page.click('[data-testid="room-settings-button"]')
    await page.click('[data-testid="delete-room-button"]')
    await page.click('[data-testid="confirm-delete-button"]')

    // Should redirect to meeting room list
    await expect(page).toHaveURL('/meeting-room')

    // Room should no longer be in list
    await expect(page.locator(`[data-testid="room-item"]:has-text("Delete Test Room")`)).toHaveCount(0)
  })
})
