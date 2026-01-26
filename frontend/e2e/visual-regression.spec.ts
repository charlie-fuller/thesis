/**
 * Visual Regression Testing
 *
 * Uses Playwright's built-in screenshot comparison to detect unintended visual changes.
 * Screenshots are stored in __snapshots__ directory and compared on each run.
 */

import { test, expect } from '@playwright/test'

// Configure visual comparison options
const screenshotOptions = {
  fullPage: true,
  animations: 'disabled' as const,
  mask: [] as any[], // Elements to mask (dynamic content)
}

test.describe('Visual Regression - Page Layouts', () => {
  test.describe('Light Mode', () => {
    test.beforeEach(async ({ page }) => {
      // Force light mode
      await page.emulateMedia({ colorScheme: 'light' })
    })

    test('Home page matches snapshot', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Wait for any animations to complete
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('home-light.png', screenshotOptions)
    })

    test('Chat page matches snapshot', async ({ page }) => {
      await page.goto('/chat')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('chat-light.png', {
        ...screenshotOptions,
        // Mask dynamic content like timestamps
        mask: [page.locator('[data-testid="timestamp"]')],
      })
    })

    test('Knowledge Base page matches snapshot', async ({ page }) => {
      await page.goto('/kb')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('kb-light.png', screenshotOptions)
    })

    test('Meeting Rooms page matches snapshot', async ({ page }) => {
      await page.goto('/meeting-room')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('meeting-room-light.png', screenshotOptions)
    })

    test('Tasks page matches snapshot', async ({ page }) => {
      await page.goto('/tasks')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('tasks-light.png', screenshotOptions)
    })

    test('Opportunities page matches snapshot', async ({ page }) => {
      await page.goto('/opportunities')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('opportunities-light.png', screenshotOptions)
    })

    test('Login page matches snapshot', async ({ page }) => {
      await page.goto('/auth/login')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('login-light.png', screenshotOptions)
    })
  })

  test.describe('Dark Mode', () => {
    test.beforeEach(async ({ page }) => {
      // Force dark mode
      await page.emulateMedia({ colorScheme: 'dark' })
    })

    test('Home page dark mode matches snapshot', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('home-dark.png', screenshotOptions)
    })

    test('Chat page dark mode matches snapshot', async ({ page }) => {
      await page.goto('/chat')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('chat-dark.png', {
        ...screenshotOptions,
        mask: [page.locator('[data-testid="timestamp"]')],
      })
    })

    test('Tasks page dark mode matches snapshot', async ({ page }) => {
      await page.goto('/tasks')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot('tasks-dark.png', screenshotOptions)
    })
  })
})

test.describe('Visual Regression - Components', () => {
  test('Agent selector component matches snapshot', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')

    // Open the agent selector
    const agentSelector = page.locator('[data-testid="agent-selector"]')
    if (await agentSelector.isVisible()) {
      await agentSelector.click()
      await page.waitForTimeout(300)

      // Screenshot just the dropdown
      const dropdown = page.locator('[data-testid="agent-dropdown"]')
      if (await dropdown.isVisible()) {
        await expect(dropdown).toHaveScreenshot('agent-selector-open.png')
      }
    }
  })

  test('Task card component matches snapshot', async ({ page }) => {
    await page.goto('/tasks')
    await page.waitForLoadState('networkidle')

    // Find first task card
    const taskCard = page.locator('[data-testid="task-card"]').first()
    if (await taskCard.isVisible()) {
      await expect(taskCard).toHaveScreenshot('task-card.png')
    }
  })

  test('Opportunity card component matches snapshot', async ({ page }) => {
    await page.goto('/opportunities')
    await page.waitForLoadState('networkidle')

    // Find first opportunity card
    const opportunityCard = page.locator('[data-testid="opportunity-card"]').first()
    if (await opportunityCard.isVisible()) {
      await expect(opportunityCard).toHaveScreenshot('opportunity-card.png')
    }
  })

  test('Meeting room card matches snapshot', async ({ page }) => {
    await page.goto('/meeting-room')
    await page.waitForLoadState('networkidle')

    const roomCard = page.locator('[data-testid="meeting-room-card"]').first()
    if (await roomCard.isVisible()) {
      await expect(roomCard).toHaveScreenshot('meeting-room-card.png')
    }
  })
})

test.describe('Visual Regression - Responsive Design', () => {
  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1440, height: 900 },
  ]

  for (const viewport of viewports) {
    test(`Chat page at ${viewport.name} viewport`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height })
      await page.goto('/chat')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot(`chat-${viewport.name}.png`, {
        ...screenshotOptions,
        fullPage: false, // Just viewport for responsive tests
      })
    })

    test(`Tasks page at ${viewport.name} viewport`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height })
      await page.goto('/tasks')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      await expect(page).toHaveScreenshot(`tasks-${viewport.name}.png`, {
        ...screenshotOptions,
        fullPage: false,
      })
    })
  }
})

test.describe('Visual Regression - Interactive States', () => {
  test('Button hover states', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')

    // Find primary button
    const button = page.locator('button[class*="primary"]').first()
    if (await button.isVisible()) {
      // Hover state
      await button.hover()
      await page.waitForTimeout(100)
      await expect(button).toHaveScreenshot('button-hover.png')
    }
  })

  test('Input focus states', async ({ page }) => {
    await page.goto('/auth/login')
    await page.waitForLoadState('networkidle')

    const emailInput = page.locator('input[type="email"]')
    if (await emailInput.isVisible()) {
      // Focus state
      await emailInput.focus()
      await page.waitForTimeout(100)
      await expect(emailInput).toHaveScreenshot('input-focus.png')
    }
  })

  test('Modal dialog appearance', async ({ page }) => {
    await page.goto('/tasks')
    await page.waitForLoadState('networkidle')

    // Open new task modal
    const newTaskButton = page.locator('[data-testid="new-task-button"]')
    if (await newTaskButton.isVisible()) {
      await newTaskButton.click()
      await page.waitForTimeout(300)

      const modal = page.locator('[role="dialog"]')
      if (await modal.isVisible()) {
        await expect(modal).toHaveScreenshot('task-modal.png')
      }
    }
  })

  test('Dropdown menu appearance', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')

    // Find and open a dropdown
    const dropdown = page.locator('[data-testid="user-menu"]')
    if (await dropdown.isVisible()) {
      await dropdown.click()
      await page.waitForTimeout(200)

      const menu = page.locator('[role="menu"]')
      if (await menu.isVisible()) {
        await expect(menu).toHaveScreenshot('dropdown-menu.png')
      }
    }
  })

  test('Toast notification appearance', async ({ page }) => {
    await page.goto('/tasks')
    await page.waitForLoadState('networkidle')

    // Trigger a toast (e.g., by deleting something)
    // This depends on having test data and actions available

    // If toast container exists, screenshot it
    const toastContainer = page.locator('[data-testid="toast-container"]')
    if (await toastContainer.isVisible()) {
      await expect(toastContainer).toHaveScreenshot('toast-notification.png')
    }
  })
})

test.describe('Visual Regression - Loading States', () => {
  test('Skeleton loading state matches snapshot', async ({ page }) => {
    // Intercept API to delay response
    await page.route('**/api/**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000))
      await route.continue()
    })

    await page.goto('/chat')

    // Capture loading state quickly
    const skeleton = page.locator('[data-testid="skeleton"]')
    if (await skeleton.isVisible({ timeout: 1000 })) {
      await expect(skeleton).toHaveScreenshot('skeleton-loading.png')
    }
  })

  test('Empty state matches snapshot', async ({ page }) => {
    await page.goto('/chat/new')
    await page.waitForLoadState('networkidle')

    // Look for empty state
    const emptyState = page.locator('[data-testid="empty-state"]')
    if (await emptyState.isVisible()) {
      await expect(emptyState).toHaveScreenshot('empty-state.png')
    }
  })
})

test.describe('Visual Regression - Error States', () => {
  test('404 page matches snapshot', async ({ page }) => {
    await page.goto('/non-existent-page')
    await page.waitForLoadState('networkidle')

    await expect(page).toHaveScreenshot('404-page.png', screenshotOptions)
  })

  test('Form validation errors match snapshot', async ({ page }) => {
    await page.goto('/auth/login')
    await page.waitForLoadState('networkidle')

    // Submit empty form to trigger validation
    const submitButton = page.locator('[type="submit"]')
    if (await submitButton.isVisible()) {
      await submitButton.click()
      await page.waitForTimeout(300)

      await expect(page).toHaveScreenshot('form-errors.png', screenshotOptions)
    }
  })
})

test.describe('Visual Regression - Typography', () => {
  test('Heading styles are consistent', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Find all headings
    const h1 = page.locator('h1').first()
    const h2 = page.locator('h2').first()
    const h3 = page.locator('h3').first()

    if (await h1.isVisible()) {
      await expect(h1).toHaveScreenshot('heading-h1.png')
    }
    if (await h2.isVisible()) {
      await expect(h2).toHaveScreenshot('heading-h2.png')
    }
    if (await h3.isVisible()) {
      await expect(h3).toHaveScreenshot('heading-h3.png')
    }
  })
})

test.describe('Visual Regression - Agent Specific', () => {
  const agents = ['atlas', 'capital', 'guardian', 'counselor', 'sage']

  for (const agent of agents) {
    test(`${agent} agent icon matches snapshot`, async ({ page }) => {
      await page.goto('/chat')
      await page.waitForLoadState('networkidle')

      const agentIcon = page.locator(`[data-testid="agent-icon-${agent}"]`)
      if (await agentIcon.isVisible()) {
        await expect(agentIcon).toHaveScreenshot(`agent-icon-${agent}.png`)
      }
    })
  }
})

// Helper to update baselines
// Run with: npx playwright test --update-snapshots
test.describe('Baseline Update Helper', () => {
  test.skip('Generate all baselines', async ({ page }) => {
    // This test is skipped by default
    // Run with --update-snapshots flag to regenerate all baselines
    const pages = ['/', '/chat', '/kb', '/tasks', '/opportunities', '/meeting-room']

    for (const path of pages) {
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)

      const name = path === '/' ? 'home' : path.replace('/', '')
      await expect(page).toHaveScreenshot(`${name}-baseline.png`, screenshotOptions)
    }
  })
})
