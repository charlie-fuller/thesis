'use client';

import dynamic from 'next/dynamic';
import type { ComponentProps } from 'react';
import LoadingSpinner from './LoadingSpinner';

// Lazy load ChatInterface to reduce initial bundle
// Chat interface includes markdown rendering and syntax highlighting
const ChatInterface = dynamic(() => import('./ChatInterface'), {
  loading: () => (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-muted">Loading chat...</p>
      </div>
    </div>
  ),
  ssr: false,
});

type ChatInterfaceProps = ComponentProps<typeof ChatInterface>;

export default function LazyChatInterface(props: ChatInterfaceProps) {
  return <ChatInterface {...props} />;
}
