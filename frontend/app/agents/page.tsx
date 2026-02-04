'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Redirect to Intelligence page with Agents tab
export default function AgentsPage() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/intelligence?tab=agents')
  }, [router])

  return null
}
