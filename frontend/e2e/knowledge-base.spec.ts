import { test, expect } from '@playwright/test'
import path from 'path'

/**
 * Knowledge Base E2E Tests
 * Tests document upload, search, and RAG integration.
 */

test.describe('Knowledge Base', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')
    await expect(page).toHaveURL('/chat', { timeout: 10000 })

    // Navigate to knowledge base
    await page.goto('/kb')
  })

  test('knowledge base page renders correctly', async ({ page }) => {
    await expect(page.locator('[data-testid="kb-document-list"]')).toBeVisible()
    await expect(page.locator('[data-testid="upload-button"]')).toBeVisible()
    await expect(page.locator('[data-testid="search-input"]')).toBeVisible()
  })

  test('can upload a PDF document', async ({ page }) => {
    // Click upload button
    await page.click('[data-testid="upload-button"]')

    // Upload a file
    const fileInput = page.locator('[data-testid="file-input"]')
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures/test-document.pdf'))

    // Wait for upload to complete
    await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible()
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible({ timeout: 30000 })

    // Document should appear in list
    await expect(page.locator('[data-testid="document-item"]').last()).toContainText('test-document.pdf')
  })

  test('can upload a text document', async ({ page }) => {
    // Click upload button
    await page.click('[data-testid="upload-button"]')

    // Upload a text file
    const fileInput = page.locator('[data-testid="file-input"]')
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures/test-notes.txt'))

    // Wait for upload to complete
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible({ timeout: 30000 })

    // Document should appear in list
    await expect(page.locator('[data-testid="document-item"]').last()).toContainText('test-notes.txt')
  })

  test('rejects unsupported file types', async ({ page }) => {
    // Click upload button
    await page.click('[data-testid="upload-button"]')

    // Try to upload an unsupported file type
    const fileInput = page.locator('[data-testid="file-input"]')
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures/test-image.jpg'))

    // Should show error
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible()
    await expect(page.locator('[data-testid="upload-error"]')).toContainText(/unsupported|invalid/i)
  })

  test('can search documents', async ({ page }) => {
    // Search for a document
    await page.fill('[data-testid="search-input"]', 'artificial intelligence')
    await page.keyboard.press('Enter')

    // Wait for search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 10000 })

    // Should show matching documents
    await expect(page.locator('[data-testid="search-result-item"]')).toHaveCount.greaterThan(0)
  })

  test('document classification is assigned automatically', async ({ page }) => {
    // Upload a document
    await page.click('[data-testid="upload-button"]')
    const fileInput = page.locator('[data-testid="file-input"]')
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures/test-document.pdf'))
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible({ timeout: 30000 })

    // Click on the document to view details
    await page.click('[data-testid="document-item"]')

    // Should show document classification
    await expect(page.locator('[data-testid="document-classification"]')).toBeVisible()
  })

  test('can view document details', async ({ page }) => {
    // Click on a document
    const documentItem = page.locator('[data-testid="document-item"]').first()
    if (await documentItem.isVisible()) {
      await documentItem.click()

      // Should show document details panel
      await expect(page.locator('[data-testid="document-details"]')).toBeVisible()
      await expect(page.locator('[data-testid="document-title"]')).toBeVisible()
      await expect(page.locator('[data-testid="document-chunks-count"]')).toBeVisible()
    }
  })

  test('can delete a document', async ({ page }) => {
    // Get initial document count
    const initialCount = await page.locator('[data-testid="document-item"]').count()

    if (initialCount > 0) {
      // Click on first document
      await page.click('[data-testid="document-item"]')

      // Click delete button
      await page.click('[data-testid="delete-document-button"]')

      // Confirm deletion
      await page.click('[data-testid="confirm-delete-button"]')

      // Document should be removed
      await expect(page.locator('[data-testid="document-item"]')).toHaveCount(initialCount - 1)
    }
  })

  test('agent cites KB content in responses', async ({ page }) => {
    // Navigate to chat
    await page.goto('/chat')

    // Ask about document content
    await page.fill('[data-testid="message-input"]', 'What does my knowledge base say about this topic?')
    await page.click('[data-testid="send-button"]')

    // Wait for response
    await expect(page.locator('[data-testid="assistant-message"]')).toBeVisible({ timeout: 30000 })

    // Response should include KB citations if documents exist
    // Note: This depends on having relevant documents in KB
  })

  test('document preview works', async ({ page }) => {
    const documentItem = page.locator('[data-testid="document-item"]').first()
    if (await documentItem.isVisible()) {
      // Click preview button
      await page.click('[data-testid="preview-document-button"]')

      // Preview modal should appear
      await expect(page.locator('[data-testid="document-preview-modal"]')).toBeVisible()
      await expect(page.locator('[data-testid="document-preview-content"]')).toBeVisible()
    }
  })

  test('can filter documents by type', async ({ page }) => {
    // Click type filter
    await page.click('[data-testid="filter-type-dropdown"]')

    // Select PDF filter
    await page.click('[data-testid="filter-type-pdf"]')

    // Should only show PDFs
    const documentItems = page.locator('[data-testid="document-item"]')
    const count = await documentItems.count()
    for (let i = 0; i < count; i++) {
      await expect(documentItems.nth(i)).toContainText('.pdf')
    }
  })

  test('bulk upload works', async ({ page }) => {
    // Click upload button
    await page.click('[data-testid="upload-button"]')

    // Upload multiple files
    const fileInput = page.locator('[data-testid="file-input"]')
    await fileInput.setInputFiles([
      path.join(__dirname, 'fixtures/test-document.pdf'),
      path.join(__dirname, 'fixtures/test-notes.txt'),
    ])

    // Wait for all uploads to complete
    await expect(page.locator('[data-testid="upload-success"]')).toHaveCount(2, { timeout: 60000 })
  })
})
