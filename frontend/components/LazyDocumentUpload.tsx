'use client';

import dynamic from 'next/dynamic';
import type { ComponentProps } from 'react';
import LoadingSpinner from './LoadingSpinner';

// Lazy load DocumentUpload to reduce initial bundle
const DocumentUpload = dynamic(() => import('./DocumentUpload'), {
  loading: () => (
    <div className="flex items-center justify-center p-8">
      <LoadingSpinner size="lg" />
    </div>
  ),
  ssr: false,
});

type DocumentUploadProps = ComponentProps<typeof DocumentUpload>;

export default function LazyDocumentUpload(props: DocumentUploadProps) {
  return <DocumentUpload {...props} />;
}
