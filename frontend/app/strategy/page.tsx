'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function StrategyPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to the Intelligence page with strategy tab
    router.replace('/intelligence?tab=strategy')
  }, [router])

  return null
}
