'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import PageLayout from '@/components/PageLayout';
import HelpChatFullPage from '@/components/HelpChatFullPage';
import LoadingSpinner from '@/components/LoadingSpinner';
import { API_BASE_URL } from '@/lib/config';
import { supabase } from '@/lib/supabase';

type TabId = 'get-started' | 'ask' | 'features' | 'process-maps' | 'architecture';

const TABS: { id: TabId; label: string }[] = [
  { id: 'get-started', label: 'Get Started' },
  { id: 'ask', label: 'Ask' },
  { id: 'features', label: 'Features' },
  { id: 'process-maps', label: 'Process Maps' },
  { id: 'architecture', label: 'Architecture' },
];

interface HelpDoc {
  slug: string;
  title: string;
  content: string;
}

interface GuideCard {
  id: string;
  title: string;
  description: string;
  htmlFile: string;
}

const PROCESS_MAP_CARDS: GuideCard[] = [
  { id: 'disco', title: 'DISCO Process Map', description: 'Discovery-Insights-Synthesis-Convergence workflow', htmlFile: '/disco-process-map.html' },
  { id: 'kraken', title: 'Kraken Process Map', description: 'Multi-agent orchestration pipeline', htmlFile: '/kraken-process-map.html' },
  { id: 'scoring', title: 'Project Scoring', description: 'How projects are evaluated and scored', htmlFile: '/project-scoring-map.html' },
  { id: 'data-flow', title: 'Data Flow', description: 'How data moves through the platform', htmlFile: '/data-flow-map.html' },
  { id: 'doc-lifecycle', title: 'Document Lifecycle', description: 'Upload, classification, and indexing', htmlFile: '/document-lifecycle.html' },
];

const ARCHITECTURE_CARDS: GuideCard[] = [
  { id: 'platform', title: 'Platform Overview', description: 'System architecture and components', htmlFile: '/platform-overview.html' },
  { id: 'agents', title: 'Agent Patterns', description: 'Agent design patterns and capabilities', htmlFile: '/agent-patterns.html' },
];

export default function HelpPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams.get('tab') as TabId | null;
  const [activeTab, setActiveTab] = useState<TabId>(tabParam && TABS.some(t => t.id === tabParam) ? tabParam : 'get-started');

  // Features tab state
  const [helpDocs, setHelpDocs] = useState<HelpDoc[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  // Card → iframe state for Process Maps and Architecture
  const [selectedGuide, setSelectedGuide] = useState<string | null>(null);

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
    setSelectedGuide(null);
    router.replace(`/help?tab=${tab}`, { scroll: false });
  };

  // Sync tab from URL on param change
  useEffect(() => {
    if (tabParam && TABS.some(t => t.id === tabParam) && tabParam !== activeTab) {
      setActiveTab(tabParam);
    }
  }, [tabParam, activeTab]);

  // Load help docs when Features tab is active
  const loadHelpDocs = useCallback(async () => {
    if (helpDocs.length > 0) return;
    setDocsLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
      }
      const res = await fetch(`${API_BASE_URL}/api/help/docs`, { headers });
      if (res.ok) {
        const data = await res.json();
        setHelpDocs(data);
        if (data.length > 0) setExpandedDoc(data[0].slug);
      }
    } catch {
      // silently handle
    } finally {
      setDocsLoading(false);
    }
  }, [helpDocs.length]);

  useEffect(() => {
    if (activeTab === 'features') loadHelpDocs();
  }, [activeTab, loadHelpDocs]);

  const renderGuideCards = (cards: GuideCard[]) => {
    const activeCard = cards.find(c => c.id === selectedGuide);
    return (
      <div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {cards.map((card) => (
            <button
              key={card.id}
              onClick={() => setSelectedGuide(selectedGuide === card.id ? null : card.id)}
              className={`text-left p-4 rounded-lg border transition-all ${
                selectedGuide === card.id
                  ? 'border-primary bg-subtle ring-2 ring-primary/20'
                  : 'border-default hover:border-primary/50 hover:bg-subtle'
              }`}
            >
              <h3 className="font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>{card.title}</h3>
              <p className="text-sm text-muted">{card.description}</p>
            </button>
          ))}
        </div>
        {activeCard && (
          <div className="border border-default rounded-lg overflow-hidden" style={{ height: 'calc(100vh - 320px)', minHeight: '500px' }}>
            <iframe
              src={activeCard.htmlFile}
              className="w-full h-full border-0"
              title={activeCard.title}
            />
          </div>
        )}
      </div>
    );
  };

  return (
    <PageLayout showHelpSidebar={false}>
      <div className="flex flex-col h-full">
        {/* Tab bar */}
        <div className="border-b border-default px-6 flex-shrink-0">
          <div className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary'
                    : 'border-transparent text-muted hover:text-base hover:border-default'
                }`}
                style={activeTab === tab.id ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)' } : undefined}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-hidden">
          {/* Get Started */}
          {activeTab === 'get-started' && (
            <iframe
              src="/quick-start.html"
              className="w-full h-full border-0"
              title="Quick Start Guide"
            />
          )}

          {/* Ask */}
          {activeTab === 'ask' && (
            <HelpChatFullPage />
          )}

          {/* Features */}
          {activeTab === 'features' && (
            <div className="overflow-y-auto h-full p-6">
              <div className="max-w-4xl mx-auto">
                <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Features</h2>
                {docsLoading ? (
                  <div className="flex justify-center py-12"><LoadingSpinner /></div>
                ) : helpDocs.length === 0 ? (
                  <p className="text-muted">No documentation available.</p>
                ) : (
                  <div className="space-y-2">
                    {helpDocs.map((doc) => (
                      <div key={doc.slug} className="border border-default rounded-lg overflow-hidden">
                        <button
                          onClick={() => setExpandedDoc(expandedDoc === doc.slug ? null : doc.slug)}
                          className="w-full flex items-center justify-between p-4 hover:bg-subtle transition-colors text-left"
                        >
                          <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{doc.title}</span>
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className={`h-5 w-5 text-muted transition-transform ${expandedDoc === doc.slug ? 'rotate-180' : ''}`}
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </button>
                        {expandedDoc === doc.slug && (
                          <div className="px-6 pb-6 prose prose-sm max-w-none" style={{ color: 'var(--color-text-primary)' }}>
                            <ReactMarkdown>{doc.content}</ReactMarkdown>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Process Maps */}
          {activeTab === 'process-maps' && (
            <div className="overflow-y-auto h-full p-6">
              <div className="max-w-6xl mx-auto">
                <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Process Maps</h2>
                {renderGuideCards(PROCESS_MAP_CARDS)}
              </div>
            </div>
          )}

          {/* Architecture */}
          {activeTab === 'architecture' && (
            <div className="overflow-y-auto h-full p-6">
              <div className="max-w-6xl mx-auto">
                <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Architecture</h2>
                {renderGuideCards(ARCHITECTURE_CARDS)}
              </div>
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  );
}
