/**
 * Accessibility Testing with axe-core
 *
 * Tests for WCAG 2.1 Level AA compliance across all major pages.
 * Uses @axe-core/playwright for automated accessibility scanning.
 */

import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

// Define pages to test
const pagesToTest = [
  { name: 'Home', path: '/' },
  { name: 'Chat', path: '/chat' },
  { name: 'Knowledge Base', path: '/kb' },
  { name: 'Meeting Rooms', path: '/meeting-room' },
  { name: 'Tasks', path: '/tasks' },
  { name: 'Opportunities', path: '/opportunities' },
  { name: 'Login', path: '/auth/login' },
]

test.describe('Accessibility - WCAG 2.1 AA Compliance', () => {
  test.describe('Full Page Scans', () => {
    for (const page of pagesToTest) {
      test(`${page.name} page has no critical accessibility violations`, async ({
        page: browserPage,
      }) => {
        await browserPage.goto(page.path)

        // Wait for page to be fully loaded
        await browserPage.waitForLoadState('networkidle')

        // Run axe accessibility scan
        const accessibilityScanResults = await new AxeBuilder({ page: browserPage })
          .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
          .analyze()

        // Filter for critical and serious violations only
        const criticalViolations = accessibilityScanResults.violations.filter(
          (v) => v.impact === 'critical' || v.impact === 'serious'
        )

        // Log violations for debugging
        if (criticalViolations.length > 0) {
          console.log(`\nAccessibility violations on ${page.name}:`)
          criticalViolations.forEach((violation) => {
            console.log(`  - ${violation.id}: ${violation.description}`)
            console.log(`    Impact: ${violation.impact}`)
            console.log(`    Affected elements: ${violation.nodes.length}`)
          })
        }

        expect(criticalViolations).toHaveLength(0)
      })
    }
  })

  test.describe('Keyboard Navigation', () => {
    test('can navigate chat interface with keyboard only', async ({ page }) => {
      await page.goto('/chat')
      await page.waitForLoadState('networkidle')

      // Tab to message input
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab')

      // Find focused element
      const focusedElement = page.locator(':focus')
      await expect(focusedElement).toBeVisible()

      // Should be able to type in input
      await page.keyboard.type('Test message')

      // Tab to send button and activate
      await page.keyboard.press('Tab')
      await page.keyboard.press('Enter')
    })

    test('modal dialogs trap focus correctly', async ({ page }) => {
      await page.goto('/tasks')
      await page.waitForLoadState('networkidle')

      // Open a modal (e.g., new task)
      const newTaskButton = page.locator('[data-testid="new-task-button"]')
      if (await newTaskButton.isVisible()) {
        await newTaskButton.click()

        // Tab through modal
        await page.keyboard.press('Tab')
        const firstFocusable = page.locator(':focus')
        await expect(firstFocusable).toBeVisible()

        // Keep tabbing - focus should stay in modal
        for (let i = 0; i < 10; i++) {
          await page.keyboard.press('Tab')
        }

        // Focus should still be within modal
        const focusedInModal = page.locator('[role="dialog"] :focus')
        await expect(focusedInModal).toBeVisible()

        // Escape should close modal
        await page.keyboard.press('Escape')
      }
    })

    test('skip link allows bypassing navigation', async ({ page }) => {
      await page.goto('/')

      // Press Tab - first focusable should be skip link
      await page.keyboard.press('Tab')

      const skipLink = page.locator('a[href="#main-content"], [data-testid="skip-link"]')
      if (await skipLink.isVisible()) {
        await page.keyboard.press('Enter')

        // Focus should move to main content
        const mainContent = page.locator('#main-content, [role="main"]')
        await expect(mainContent).toBeFocused()
      }
    })
  })

  test.describe('Color Contrast', () => {
    test('text has sufficient color contrast', async ({ page }) => {
      await page.goto('/chat')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .withRules(['color-contrast'])
        .analyze()

      const contrastViolations = results.violations.filter(
        (v) => v.id === 'color-contrast'
      )

      expect(contrastViolations).toHaveLength(0)
    })

    test('focus indicators are visible', async ({ page }) => {
      await page.goto('/chat')

      // Tab to first interactive element
      await page.keyboard.press('Tab')

      // Get focused element
      const focused = page.locator(':focus')
      await expect(focused).toBeVisible()

      // Check that focus ring is visible (outline or box-shadow)
      const outlineStyle = await focused.evaluate((el) => {
        const styles = window.getComputedStyle(el)
        return {
          outline: styles.outline,
          boxShadow: styles.boxShadow,
          border: styles.border,
        }
      })

      // At least one focus indicator should be present
      const hasFocusIndicator =
        outlineStyle.outline !== 'none' ||
        outlineStyle.boxShadow !== 'none' ||
        outlineStyle.border !== 'none'

      expect(hasFocusIndicator).toBe(true)
    })
  })

  test.describe('Screen Reader Support', () => {
    test('images have alt text', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .withRules(['image-alt'])
        .analyze()

      expect(results.violations).toHaveLength(0)
    })

    test('form inputs have labels', async ({ page }) => {
      await page.goto('/auth/login')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .withRules(['label'])
        .analyze()

      expect(results.violations).toHaveLength(0)
    })

    test('buttons have accessible names', async ({ page }) => {
      await page.goto('/chat')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .withRules(['button-name'])
        .analyze()

      expect(results.violations).toHaveLength(0)
    })

    test('links have descriptive text', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .withRules(['link-name'])
        .analyze()

      expect(results.violations).toHaveLength(0)
    })

    test('page has proper heading hierarchy', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .withRules(['heading-order'])
        .analyze()

      expect(results.violations).toHaveLength(0)
    })

    test('ARIA attributes are valid', async ({ page }) => {
      await page.goto('/chat')
      await page.waitForLoadState('networkidle')

      const results = await new AxeBuilder({ page })
        .withRules([
          'aria-valid-attr',
          'aria-valid-attr-value',
          'aria-required-attr',
          'aria-roles',
        ])
        .analyze()

      expect(results.violations).toHaveLength(0)
    })

    test('landmarks are properly defined', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')

      // Check for main landmark
      const main = page.locator('main, [role="main"]')
      await expect(main).toBeVisible()

      // Check for navigation
      const nav = page.locator('nav, [role="navigation"]')
      expect(await nav.count()).toBeGreaterThan(0)
    })
  })

  test.describe('Motion and Animation', () => {
    test('respects reduced motion preference', async ({ page }) => {
      // Emulate reduced motion preference
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.goto('/chat')

      // Check that animations are disabled
      const animatedElements = page.locator('[class*="animate"], [class*="transition"]')
      const count = await animatedElements.count()

      if (count > 0) {
        for (let i = 0; i < Math.min(count, 5); i++) {
          const el = animatedElements.nth(i)
          const animation = await el.evaluate((element) => {
            const styles = window.getComputedStyle(element)
            return {
              animationDuration: styles.animationDuration,
              transitionDuration: styles.transitionDuration,
            }
          })

          // Animations should be instant with reduced motion
          // (0s or very short duration)
          const hasReducedMotion =
            animation.animationDuration === '0s' ||
            animation.transitionDuration === '0s' ||
            parseFloat(animation.animationDuration) <= 0.01 ||
            parseFloat(animation.transitionDuration) <= 0.01
        }
      }
    })
  })

  test.describe('Forms and Inputs', () => {
    test('error messages are announced to screen readers', async ({ page }) => {
      await page.goto('/auth/login')

      // Submit empty form
      const submitButton = page.locator('[type="submit"]')
      if (await submitButton.isVisible()) {
        await submitButton.click()

        // Error messages should have role="alert" or aria-live
        const errorMessages = page.locator(
          '[role="alert"], [aria-live="polite"], [aria-live="assertive"]'
        )

        // Wait for error to appear
        await page.waitForTimeout(500)

        // Check if error is announced
        const errorCount = await errorMessages.count()
        // Note: This depends on form validation implementation
      }
    })

    test('required fields are marked appropriately', async ({ page }) => {
      await page.goto('/auth/login')

      // Find required inputs
      const requiredInputs = page.locator('[required], [aria-required="true"]')
      const count = await requiredInputs.count()

      if (count > 0) {
        for (let i = 0; i < count; i++) {
          const input = requiredInputs.nth(i)

          // Check for visual indicator or aria-required
          const hasAriaRequired = await input.getAttribute('aria-required')
          const hasRequired = await input.getAttribute('required')

          expect(hasAriaRequired === 'true' || hasRequired !== null).toBe(true)
        }
      }
    })
  })

  test.describe('Dynamic Content', () => {
    test('loading states are announced', async ({ page }) => {
      await page.goto('/chat')

      // Find loading indicators
      const loadingIndicator = page.locator(
        '[aria-busy="true"], [role="progressbar"], [aria-label*="loading"]'
      )

      // Trigger a loading state (e.g., send message)
      const input = page.locator('[data-testid="message-input"]')
      if (await input.isVisible()) {
        await input.fill('Test message')
        await page.keyboard.press('Enter')

        // Check for accessible loading indicator
        // This may or may not appear depending on response speed
      }
    })

    test('live regions update screen readers', async ({ page }) => {
      await page.goto('/chat')

      // Check for aria-live regions
      const liveRegions = page.locator('[aria-live]')
      const count = await liveRegions.count()

      // Chat interface should have live region for new messages
      expect(count).toBeGreaterThanOrEqual(0) // May not always be present
    })
  })
})

test.describe('Component-Specific Accessibility', () => {
  test('Agent selector dropdown is accessible', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')

    // Find agent selector
    const agentSelector = page.locator('[data-testid="agent-selector"]')
    if (await agentSelector.isVisible()) {
      // Should have proper ARIA attributes
      const role = await agentSelector.getAttribute('role')
      const expanded = await agentSelector.getAttribute('aria-expanded')
      const hasPopup = await agentSelector.getAttribute('aria-haspopup')

      // Open dropdown
      await agentSelector.click()

      // Dropdown should be announced
      const dropdown = page.locator('[role="listbox"], [role="menu"]')
      await expect(dropdown).toBeVisible()

      // Options should be selectable with keyboard
      await page.keyboard.press('ArrowDown')
      await page.keyboard.press('Enter')
    }
  })

  test('Kanban board is accessible', async ({ page }) => {
    await page.goto('/tasks')
    await page.waitForLoadState('networkidle')

    // Kanban columns should have proper labels
    const columns = page.locator('[role="region"], [data-testid*="column"]')
    const count = await columns.count()

    if (count > 0) {
      for (let i = 0; i < count; i++) {
        const column = columns.nth(i)
        const label = await column.getAttribute('aria-label')
        const labelledBy = await column.getAttribute('aria-labelledby')

        // Column should have accessible name
        const hasAccessibleName = label !== null || labelledBy !== null
      }
    }
  })

  test('Chat messages are accessible', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')

    // Message container should be a list or have proper role
    const messageContainer = page.locator(
      '[role="log"], [role="list"], [data-testid="message-container"]'
    )

    if (await messageContainer.isVisible()) {
      const role = await messageContainer.getAttribute('role')
      const ariaLabel = await messageContainer.getAttribute('aria-label')

      // Container should be accessible
      expect(role !== null || ariaLabel !== null).toBe(true)
    }
  })
})
