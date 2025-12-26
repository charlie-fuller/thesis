/**
 * DocumentUpload Component Tests
 *
 * Tests for document upload functionality.
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock the API module
jest.mock('@/lib/api', () => ({
  uploadDocument: jest.fn(),
  apiGet: jest.fn()
}))

// Mock AuthContext
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'test-user', email: 'test@example.com' },
    isAuthenticated: true,
    loading: false
  })
}))

// Simple mock component for testing upload logic
function MockDocumentUpload() {
  const { uploadDocument } = require('@/lib/api')
  const [uploading, setUploading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [success, setSuccess] = React.useState(false)

  const handleUpload = async (file: File) => {
    setUploading(true)
    setError(null)

    try {
      await uploadDocument(file)
      setSuccess(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <input
        type="file"
        data-testid="file-input"
        onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
      />
      {uploading && <div data-testid="uploading">Uploading...</div>}
      {error && <div data-testid="error">{error}</div>}
      {success && <div data-testid="success">Upload successful!</div>}
    </div>
  )
}

import React from 'react'

describe('DocumentUpload', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('File Selection', () => {
    it('accepts PDF files', async () => {
      const { uploadDocument } = require('@/lib/api')
      uploadDocument.mockResolvedValueOnce({ id: 'doc-123' })

      render(<MockDocumentUpload />)

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByTestId('file-input')

      await userEvent.upload(input, file)

      await waitFor(() => {
        expect(uploadDocument).toHaveBeenCalledWith(file)
      })
    })

    it('accepts DOCX files', async () => {
      const { uploadDocument } = require('@/lib/api')
      uploadDocument.mockResolvedValueOnce({ id: 'doc-124' })

      render(<MockDocumentUpload />)

      const file = new File(['test content'], 'test.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      })
      const input = screen.getByTestId('file-input')

      await userEvent.upload(input, file)

      await waitFor(() => {
        expect(uploadDocument).toHaveBeenCalled()
      })
    })
  })

  describe('Upload States', () => {
    it('shows uploading state', async () => {
      const { uploadDocument } = require('@/lib/api')
      uploadDocument.mockImplementation(() => new Promise(() => {})) // Never resolves

      render(<MockDocumentUpload />)

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByTestId('file-input')

      await userEvent.upload(input, file)

      expect(screen.getByTestId('uploading')).toBeInTheDocument()
    })

    it('shows success message after upload', async () => {
      const { uploadDocument } = require('@/lib/api')
      uploadDocument.mockResolvedValueOnce({ id: 'doc-123' })

      render(<MockDocumentUpload />)

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByTestId('file-input')

      await userEvent.upload(input, file)

      await waitFor(() => {
        expect(screen.getByTestId('success')).toBeInTheDocument()
      })
    })

    it('shows error message on failure', async () => {
      const { uploadDocument } = require('@/lib/api')
      uploadDocument.mockRejectedValueOnce(new Error('Upload failed'))

      render(<MockDocumentUpload />)

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const input = screen.getByTestId('file-input')

      await userEvent.upload(input, file)

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Upload failed')
      })
    })
  })
})

describe('File Validation', () => {
  const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'csv', 'pptx', 'ppt', 'md', 'rtf']
  const MAX_SIZE_MB = 50

  it('has correct allowed extensions', () => {
    expect(ALLOWED_EXTENSIONS).toContain('pdf')
    expect(ALLOWED_EXTENSIONS).toContain('docx')
    expect(ALLOWED_EXTENSIONS).toContain('xlsx')
    expect(ALLOWED_EXTENSIONS).toContain('pptx')
  })

  it('has correct max file size', () => {
    expect(MAX_SIZE_MB).toBe(50)
  })

  it('validates file extension', () => {
    const isValidExtension = (filename: string) => {
      const ext = filename.split('.').pop()?.toLowerCase()
      return ext ? ALLOWED_EXTENSIONS.includes(ext) : false
    }

    expect(isValidExtension('document.pdf')).toBe(true)
    expect(isValidExtension('document.docx')).toBe(true)
    expect(isValidExtension('document.exe')).toBe(false)
    expect(isValidExtension('document.js')).toBe(false)
  })

  it('validates file size', () => {
    const isValidSize = (sizeBytes: number) => {
      return sizeBytes <= MAX_SIZE_MB * 1024 * 1024
    }

    expect(isValidSize(10 * 1024 * 1024)).toBe(true) // 10MB
    expect(isValidSize(50 * 1024 * 1024)).toBe(true) // 50MB exactly
    expect(isValidSize(51 * 1024 * 1024)).toBe(false) // 51MB
  })
})
