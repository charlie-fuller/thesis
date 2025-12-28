'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AdminPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to home page where the dashboard now lives
    router.replace('/');
  }, [router]);

  return null;
}
