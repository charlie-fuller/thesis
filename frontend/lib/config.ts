/**
 * Application configuration
 * Centralized configuration values for the frontend application
 */

/**
 * Backend API base URL
 * Uses NEXT_PUBLIC_API_URL from environment variables
 * Falls back to localhost for development if not set
 * Forces HTTPS for production URLs (railway.app, etc.)
 */
function getApiBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // Force HTTPS for production URLs
  if (url.includes('railway.app') || url.includes('vercel.app')) {
    return url.replace('http://', 'https://')
  }

  return url
}

export const API_BASE_URL = getApiBaseUrl()
