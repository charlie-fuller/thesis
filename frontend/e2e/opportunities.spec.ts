import { test, expect } from '@playwright/test'

/**
 * Opportunities Pipeline E2E Tests
 * Tests the complete opportunities management flow.
 */

test.describe('Opportunities Pipeline', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/chat', { timeout: 10000 })

    // Navigate to opportunities
    await page.goto('/opportunities')
  })

  test('opportunities page renders correctly', async ({ page }) => {
    await expect(page.locator('[data-testid="opportunities-pipeline"]')).toBeVisible()
    await expect(page.locator('[data-testid="create-opportunity-button"]')).toBeVisible()
  })

  test('can create a new opportunity', async ({ page }) => {
    // Click create button
    await page.click('[data-testid="create-opportunity-button"]')

    // Fill in opportunity details
    await page.fill('[data-testid="opportunity-name"]', 'Test AI Implementation')
    await page.fill('[data-testid="opportunity-description"]', 'Testing opportunity creation')
    await page.fill('[data-testid="opportunity-value"]', '100000')

    // Set scores
    await page.fill('[data-testid="score-impact"]', '8')
    await page.fill('[data-testid="score-feasibility"]', '7')
    await page.fill('[data-testid="score-alignment"]', '9')

    // Submit
    await page.click('[data-testid="save-opportunity-button"]')

    // Should appear in pipeline
    await expect(page.locator('[data-testid="opportunity-card"]').last()).toContainText('Test AI Implementation')
  })

  test('tier is calculated correctly based on scores', async ({ page }) => {
    // Create high-scoring opportunity
    await page.click('[data-testid="create-opportunity-button"]')
    await page.fill('[data-testid="opportunity-name"]', 'High Score Test')
    await page.fill('[data-testid="score-impact"]', '10')
    await page.fill('[data-testid="score-feasibility"]', '10')
    await page.fill('[data-testid="score-alignment"]', '10')
    await page.click('[data-testid="save-opportunity-button"]')

    // Should be Tier 1
    const opportunityCard = page.locator('[data-testid="opportunity-card"]').filter({ hasText: 'High Score Test' })
    await expect(opportunityCard.locator('[data-testid="tier-badge"]')).toContainText('Tier 1')
  })

  test('can change opportunity status', async ({ page }) => {
    // Find an opportunity card
    const opportunityCard = page.locator('[data-testid="opportunity-card"]').first()
    if (await opportunityCard.isVisible()) {
      // Click on it to open details
      await opportunityCard.click()

      // Change status
      await page.click('[data-testid="status-dropdown"]')
      await page.click('[data-testid="status-in-progress"]')

      // Status should update
      await expect(page.locator('[data-testid="current-status"]')).toContainText('In Progress')
    }
  })

  test('can drag opportunity between pipeline stages', async ({ page }) => {
    // Get an opportunity card in Discovery stage
    const sourceCard = page.locator('[data-testid="pipeline-column-discovery"] [data-testid="opportunity-card"]').first()

    if (await sourceCard.isVisible()) {
      // Get target column
      const targetColumn = page.locator('[data-testid="pipeline-column-validation"]')

      // Drag and drop
      await sourceCard.dragTo(targetColumn)

      // Card should now be in Validation column
      await expect(
        page.locator('[data-testid="pipeline-column-validation"] [data-testid="opportunity-card"]')
      ).toHaveCount(1)
    }
  })

  test('can link stakeholders to opportunity', async ({ page }) => {
    // Open an opportunity
    const opportunityCard = page.locator('[data-testid="opportunity-card"]').first()
    if (await opportunityCard.isVisible()) {
      await opportunityCard.click()

      // Click add stakeholder
      await page.click('[data-testid="add-stakeholder-button"]')

      // Search for stakeholder
      await page.fill('[data-testid="stakeholder-search"]', 'John')

      // Select from results
      await page.click('[data-testid="stakeholder-result"]')

      // Should appear in linked stakeholders
      await expect(page.locator('[data-testid="linked-stakeholders"]')).toContainText('John')
    }
  })

  test('can filter opportunities by tier', async ({ page }) => {
    // Click tier filter
    await page.click('[data-testid="filter-tier-dropdown"]')

    // Select Tier 1
    await page.click('[data-testid="filter-tier-1"]')

    // All visible cards should be Tier 1
    const opportunityCards = page.locator('[data-testid="opportunity-card"]')
    const count = await opportunityCards.count()
    for (let i = 0; i < count; i++) {
      await expect(opportunityCards.nth(i).locator('[data-testid="tier-badge"]')).toContainText('Tier 1')
    }
  })

  test('can search opportunities', async ({ page }) => {
    // Search for specific opportunity
    await page.fill('[data-testid="search-opportunities"]', 'AI Implementation')
    await page.keyboard.press('Enter')

    // Results should be filtered
    const opportunityCards = page.locator('[data-testid="opportunity-card"]')
    const count = await opportunityCards.count()

    for (let i = 0; i < count; i++) {
      await expect(opportunityCards.nth(i)).toContainText('AI Implementation')
    }
  })

  test('can edit opportunity details', async ({ page }) => {
    // Open an opportunity
    const opportunityCard = page.locator('[data-testid="opportunity-card"]').first()
    if (await opportunityCard.isVisible()) {
      await opportunityCard.click()

      // Click edit button
      await page.click('[data-testid="edit-opportunity-button"]')

      // Update name
      await page.fill('[data-testid="opportunity-name"]', 'Updated Name')

      // Save changes
      await page.click('[data-testid="save-opportunity-button"]')

      // Should show updated name
      await expect(page.locator('[data-testid="opportunity-title"]')).toContainText('Updated Name')
    }
  })

  test('can delete an opportunity', async ({ page }) => {
    // Get initial count
    const initialCount = await page.locator('[data-testid="opportunity-card"]').count()

    if (initialCount > 0) {
      // Open first opportunity
      await page.click('[data-testid="opportunity-card"]')

      // Click delete
      await page.click('[data-testid="delete-opportunity-button"]')

      // Confirm deletion
      await page.click('[data-testid="confirm-delete-button"]')

      // Count should decrease
      await expect(page.locator('[data-testid="opportunity-card"]')).toHaveCount(initialCount - 1)
    }
  })

  test('opportunity details show engagement metrics', async ({ page }) => {
    const opportunityCard = page.locator('[data-testid="opportunity-card"]').first()
    if (await opportunityCard.isVisible()) {
      await opportunityCard.click()

      // Should show engagement metrics
      await expect(page.locator('[data-testid="engagement-score"]')).toBeVisible()
      await expect(page.locator('[data-testid="meeting-count"]')).toBeVisible()
    }
  })
})
