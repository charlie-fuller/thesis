'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiGet } from '@/lib/api'

declare global {
  interface Window {
    gapi: {
      load: (api: string, callback: () => void) => void
      client: {
        init: (config: object) => Promise<void>
      }
    }
    google: {
      picker: {
        PickerBuilder: new () => PickerBuilder
        ViewId: {
          DOCS: string
          FOLDERS: string
        }
        Feature: {
          MULTISELECT_ENABLED: string
          NAV_HIDDEN: string
        }
        Action: {
          PICKED: string
          CANCEL: string
        }
        DocsView: new (viewId?: string) => DocsView
      }
    }
  }
}

interface PickerBuilder {
  setOAuthToken: (token: string) => PickerBuilder
  setDeveloperKey: (key: string) => PickerBuilder
  setAppId: (appId: string) => PickerBuilder
  addView: (view: DocsView) => PickerBuilder
  enableFeature: (feature: string) => PickerBuilder
  setCallback: (callback: (data: PickerResponse) => void) => PickerBuilder
  setTitle: (title: string) => PickerBuilder
  setSize: (width: number, height: number) => PickerBuilder
  build: () => { setVisible: (visible: boolean) => void }
}

interface DocsView {
  setIncludeFolders: (include: boolean) => DocsView
  setSelectFolderEnabled: (enabled: boolean) => DocsView
  setMimeTypes: (mimeTypes: string) => DocsView
  setMode: (mode: string) => DocsView
}

interface PickerDocument {
  id: string
  name: string
  mimeType: string
  url?: string
  sizeBytes?: number
  iconUrl?: string
}

interface PickerResponse {
  action: string
  docs?: PickerDocument[]
}

interface GoogleDrivePickerProps {
  onFilesPicked: (files: PickerDocument[]) => void
  disabled?: boolean
  buttonText?: string
  buttonClassName?: string
}

export default function GoogleDrivePicker({
  onFilesPicked,
  disabled = false,
  buttonText = 'Browse Google Drive',
  buttonClassName = 'btn-secondary'
}: GoogleDrivePickerProps) {
  const [pickerLoaded, setPickerLoaded] = useState(false)
  const [loading, setLoading] = useState(false)

  // Load Google Picker API script
  useEffect(() => {
    // Check if already loaded
    if (window.google?.picker) {
      setPickerLoaded(true)
      return
    }

    const script = document.createElement('script')
    script.src = 'https://apis.google.com/js/api.js'
    script.async = true
    script.defer = true
    script.onload = () => {
      window.gapi.load('picker', () => {
        setPickerLoaded(true)
      })
    }
    document.body.appendChild(script)

    return () => {
      // Cleanup if needed
    }
  }, [])

  const openPicker = useCallback(async () => {
    if (!pickerLoaded || loading) return

    setLoading(true)

    try {
      // Get picker credentials from backend
      const { access_token, app_id } = await apiGet<{
        access_token: string
        client_id: string
        app_id: string
      }>('/api/google-drive/picker-token')

      // Supported file types for Thesis
      const supportedMimeTypes = [
        'application/pdf',
        'application/vnd.google-apps.document', // Google Docs
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
        'text/plain',
        'text/markdown',
        'application/rtf'
      ].join(',')

      // Create the picker
      const view = new window.google.picker.DocsView()
        .setIncludeFolders(true)
        .setSelectFolderEnabled(false)
        .setMimeTypes(supportedMimeTypes)

      const picker = new window.google.picker.PickerBuilder()
        .setOAuthToken(access_token)
        .setAppId(app_id)
        .addView(view)
        .enableFeature(window.google.picker.Feature.MULTISELECT_ENABLED)
        .setTitle('Select files to import')
        .setCallback((data: PickerResponse) => {
          if (data.action === window.google.picker.Action.PICKED && data.docs) {
            onFilesPicked(data.docs)
          }
        })
        .build()

      picker.setVisible(true)
    } catch {
      // Silently handle picker errors - user will see the button is not loading
    } finally {
      setLoading(false)
    }
  }, [pickerLoaded, loading, onFilesPicked])

  return (
    <button
      onClick={openPicker}
      disabled={disabled || !pickerLoaded || loading}
      className={buttonClassName}
    >
      {loading ? 'Opening...' : buttonText}
    </button>
  )
}
