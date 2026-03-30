'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import PageLayout from '@/components/PageLayout'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function DecisionTreePage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  if (loading) return <LoadingSpinner />
  if (!user) {
    router.push('/auth/login')
    return null
  }

  return (
    <PageLayout>
      <div className="w-full h-full">
        <iframe
          src="/platform-decision-tree.html"
          className="w-full h-full border-0"
          title="AI Platform Selection Decision Tree"
        />
      </div>
    </PageLayout>
  )
}
