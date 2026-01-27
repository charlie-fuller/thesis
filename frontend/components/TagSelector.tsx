'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Tag, X, ChevronDown, Loader2, Search, Building2, Check } from 'lucide-react'
import { apiGet } from '@/lib/api'

interface TagItem {
  tag: string
  count: number
  type?: 'regular' | 'initiative'
  initiative_id?: string
}

interface TagSelectorProps {
  selectedTags: Set<string>
  onTagsChange: (tags: Set<string>) => void
  placeholder?: string
  showInitiatives?: boolean
  disabled?: boolean
}

export default function TagSelector({
  selectedTags,
  onTagsChange,
  placeholder = 'Search tags...',
  showInitiatives = false,
  disabled = false
}: TagSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [tags, setTags] = useState<TagItem[]>([])
  const [initiativeTags, setInitiativeTags] = useState<TagItem[]>([])
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [offset, setOffset] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const LIMIT = 50

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setOffset(0) // Reset pagination on new search
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  // Fetch tags when search changes or dropdown opens
  useEffect(() => {
    if (!isOpen) return

    const fetchTags = async () => {
      setLoading(true)
      try {
        const params = new URLSearchParams({
          limit: LIMIT.toString(),
          offset: offset.toString()
        })
        if (debouncedSearch) {
          params.append('search', debouncedSearch)
        }

        const result = await apiGet<{
          success: boolean
          tags: Array<{ tag: string; count: number }>
          hasMore: boolean
        }>(`/api/documents/tags?${params}`)

        const formattedTags: TagItem[] = (result.tags || []).map(t => ({
          ...t,
          type: 'regular' as const
        }))

        if (offset === 0) {
          setTags(formattedTags)
        } else {
          setTags(prev => [...prev, ...formattedTags])
        }
        setHasMore(result.hasMore)
      } catch (err) {
        console.error('Failed to fetch tags:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchTags()
  }, [isOpen, debouncedSearch, offset])

  // Fetch initiative names when showInitiatives is true
  useEffect(() => {
    if (!showInitiatives || !isOpen) return

    const fetchInitiatives = async () => {
      try {
        const result = await apiGet<{
          success: boolean
          tags: Array<{
            tag: string
            count: number
            type: 'initiative'
            initiative_id: string
            status: string
          }>
        }>('/api/disco/initiatives/as-tags')

        setInitiativeTags(result.tags || [])
      } catch (err) {
        console.error('Failed to fetch initiatives as tags:', err)
      }
    }

    fetchInitiatives()
  }, [showInitiatives, isOpen])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggleTag = useCallback((tag: string) => {
    const newTags = new Set(selectedTags)
    if (newTags.has(tag)) {
      newTags.delete(tag)
    } else {
      newTags.add(tag)
    }
    onTagsChange(newTags)
  }, [selectedTags, onTagsChange])

  const removeTag = useCallback((tag: string) => {
    const newTags = new Set(selectedTags)
    newTags.delete(tag)
    onTagsChange(newTags)
  }, [selectedTags, onTagsChange])

  const loadMore = () => {
    setOffset(prev => prev + LIMIT)
  }

  // Filter initiative tags by search
  const filteredInitiativeTags = initiativeTags.filter(t =>
    !debouncedSearch || t.tag.toLowerCase().includes(debouncedSearch.toLowerCase())
  )

  return (
    <div ref={containerRef} className="relative">
      {/* Selected Tags Chips */}
      {selectedTags.size > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {Array.from(selectedTags).sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase())).map(tag => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2 py-1 text-sm bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-md"
            >
              <Tag className="w-3 h-3" />
              {tag}
              {!disabled && (
                <button
                  onClick={() => removeTag(tag)}
                  className="ml-1 hover:text-indigo-900 dark:hover:text-indigo-100"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      {/* Search Input */}
      <div
        className={`relative ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onClick={() => !disabled && setIsOpen(true)}
      >
        <div className="flex items-center gap-2 px-3 py-2 border border-default rounded-lg bg-card hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors">
          <Search className="w-4 h-4 text-muted" />
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => !disabled && setIsOpen(true)}
            placeholder={placeholder}
            disabled={disabled}
            className="flex-1 bg-transparent outline-none text-sm text-primary placeholder:text-muted"
          />
          <ChevronDown className={`w-4 h-4 text-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-1 bg-card border border-default rounded-lg shadow-lg max-h-72 overflow-auto">
          {loading && offset === 0 ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
            </div>
          ) : (
            <>
              {/* Initiative Tags Section */}
              {showInitiatives && filteredInitiativeTags.length > 0 && (
                <div>
                  <div className="px-3 py-2 text-xs font-semibold text-secondary uppercase tracking-wider bg-subtle flex items-center gap-2">
                    <Building2 className="w-3 h-3" />
                    Initiatives
                  </div>
                  {filteredInitiativeTags.map(item => (
                    <button
                      key={`initiative-${item.tag}`}
                      onClick={() => toggleTag(item.tag)}
                      className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-subtle transition-colors ${
                        selectedTags.has(item.tag) ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''
                      }`}
                    >
                      <div className={`w-4 h-4 rounded border flex items-center justify-center ${
                        selectedTags.has(item.tag)
                          ? 'bg-indigo-600 border-indigo-600'
                          : 'border-default'
                      }`}>
                        {selectedTags.has(item.tag) && <Check className="w-3 h-3 text-white" />}
                      </div>
                      <span className="flex-1 text-sm text-primary">{item.tag}</span>
                      <Building2 className="w-3 h-3 text-emerald-500" />
                    </button>
                  ))}
                </div>
              )}

              {/* Regular Tags Section */}
              {tags.length > 0 && (
                <div>
                  {showInitiatives && filteredInitiativeTags.length > 0 && (
                    <div className="px-3 py-2 text-xs font-semibold text-secondary uppercase tracking-wider bg-subtle flex items-center gap-2">
                      <Tag className="w-3 h-3" />
                      Tags
                    </div>
                  )}
                  {tags.map(item => (
                    <button
                      key={item.tag}
                      onClick={() => toggleTag(item.tag)}
                      className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-subtle transition-colors ${
                        selectedTags.has(item.tag) ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''
                      }`}
                    >
                      <div className={`w-4 h-4 rounded border flex items-center justify-center ${
                        selectedTags.has(item.tag)
                          ? 'bg-indigo-600 border-indigo-600'
                          : 'border-default'
                      }`}>
                        {selectedTags.has(item.tag) && <Check className="w-3 h-3 text-white" />}
                      </div>
                      <span className="flex-1 text-sm text-primary">{item.tag}</span>
                      <span className="text-xs text-muted">{item.count}</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Empty State */}
              {tags.length === 0 && filteredInitiativeTags.length === 0 && !loading && (
                <div className="px-3 py-4 text-center text-sm text-secondary">
                  {debouncedSearch ? `No tags matching "${debouncedSearch}"` : 'No tags found'}
                </div>
              )}

              {/* Load More */}
              {hasMore && (
                <button
                  onClick={loadMore}
                  disabled={loading}
                  className="w-full px-3 py-2 text-sm text-indigo-600 dark:text-indigo-400 hover:bg-subtle transition-colors flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    'Load more tags'
                  )}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
