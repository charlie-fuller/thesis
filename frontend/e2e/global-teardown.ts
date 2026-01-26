/**
 * Playwright Global Teardown
 *
 * Runs once after all tests to:
 * - Clean up test database state
 * - Remove test user accounts
 * - Clear any temporary files
 */

import { FullConfig } from '@playwright/test'
import { cleanupTestData } from './fixtures/seed'

async function globalTeardown(config: FullConfig) {
  console.log('Running global E2E teardown...')

  // Clean up test data
  try {
    await cleanupTestData()
    console.log('Test data cleaned up successfully')
  } catch (error) {
    console.error('Error cleaning up test data:', error)
  }

  console.log('Global E2E teardown complete')
}

export default globalTeardown
