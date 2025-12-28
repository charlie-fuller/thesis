'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function StakeholdersPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to the unified Intelligence page
    router.replace('/intelligence')
  }, [router])

  return null
}
