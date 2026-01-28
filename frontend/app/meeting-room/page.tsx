'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function MeetingRoomListPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to the combined chat page with meetings tab
    router.replace('/chat?tab=meetings')
  }, [router])

  return null
}
