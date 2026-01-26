/**
 * Playwright Global Setup
 *
 * Runs once before all tests to:
 * - Set up test database state
 * - Create test user accounts
 * - Seed necessary test data
 */

import { chromium, FullConfig } from '@playwright/test'
import { seedTestData, cleanupTestData } from './fixtures/seed'

async function globalSetup(config: FullConfig) {
  console.log('Running global E2E setup...')

  // Clean up any leftover test data from previous runs
  try {
    await cleanupTestData()
  } catch (error) {
    console.log('No existing test data to clean up')
  }

  // Seed fresh test data
  await seedTestData()

  // Optionally: Create authenticated state for reuse
  // This speeds up tests by not having to login for each test
  const browser = await chromium.launch()
  const page = await browser.newPage()

  try {
    // Login to create authenticated state
    await page.goto(`${process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000'}/auth/login`)

    // Fill login form
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')

    // Wait for successful login
    await page.waitForURL('**/chat', { timeout: 10000 })

    // Save authentication state
    await page.context().storageState({ path: 'e2e/.auth/user.json' })

    console.log('Saved authenticated state')
  } catch (error) {
    console.log('Could not save authenticated state (login may have failed)')
  } finally {
    await browser.close()
  }

  console.log('Global E2E setup complete')
}

export default globalSetup
