'use client'

import { useRouter } from 'next/navigation'
import { ReactNode, useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import {
  FileText,
  Home,
  LogOut,
  Settings,
  User,
  Menu,
  X,
  Folder
} from 'lucide-react'

interface PurdyLayoutProps {
  children: ReactNode
}

export default function PurdyLayout({ children }: PurdyLayoutProps) {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const getUser = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.user) {
        setUser(session.user)
      }
    }
    getUser()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null)
        if (event === 'SIGNED_OUT') {
          router.push('/auth/login')
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [router])

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push('/auth/login')
  }

  const navItems = [
    { href: '/purdy', label: 'Initiatives', icon: Folder },
  ]

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <header className="bg-indigo-600 dark:bg-indigo-700 text-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.push('/purdy')}
                className="flex items-center gap-2 hover:opacity-90 transition-opacity"
              >
                <FileText className="w-8 h-8" />
                <div>
                  <span className="text-xl font-bold">PuRDy</span>
                  <span className="hidden sm:inline text-sm ml-2 opacity-80">
                    Product Requirements Discovery
                  </span>
                </div>
              </button>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              {navItems.map((item) => (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500 transition-colors"
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </button>
              ))}
            </nav>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              {user && (
                <div className="hidden md:flex items-center gap-3">
                  <span className="text-sm opacity-80">{user.email}</span>
                  <button
                    onClick={handleSignOut}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md hover:bg-indigo-500 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-md hover:bg-indigo-500"
              >
                {mobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-indigo-500">
            <div className="px-4 py-3 space-y-2">
              {navItems.map((item) => (
                <button
                  key={item.href}
                  onClick={() => {
                    router.push(item.href)
                    setMobileMenuOpen(false)
                  }}
                  className="flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500"
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </button>
              ))}
              {user && (
                <div className="pt-2 border-t border-indigo-500">
                  <div className="px-3 py-2 text-sm opacity-80">{user.email}</div>
                  <button
                    onClick={handleSignOut}
                    className="flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm font-medium hover:bg-indigo-500"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main>{children}</main>
    </div>
  )
}
