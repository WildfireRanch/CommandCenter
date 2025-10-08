'use client';

import { useSession, signIn } from 'next-auth/react';
import { useEffect, ReactNode } from 'react';

interface ProtectedPageProps {
  children: ReactNode;
  loadingMessage?: string;
}

/**
 * ProtectedPage Component
 *
 * Wraps any page content to require Google authentication.
 * - If user is not authenticated, automatically redirects to Google OAuth
 * - If user is authenticated, renders the children
 * - Shows loading state during auth check
 *
 * Usage:
 * ```tsx
 * export default function MyPage() {
 *   return (
 *     <ProtectedPage>
 *       <div>Your protected content here</div>
 *     </ProtectedPage>
 *   );
 * }
 * ```
 */
export default function ProtectedPage({
  children,
  loadingMessage = 'Checking authentication...'
}: ProtectedPageProps) {
  const { data: session, status } = useSession();

  useEffect(() => {
    // If not authenticated and not already loading, redirect to Google sign-in
    if (status === 'unauthenticated') {
      signIn('google', { callbackUrl: window.location.href });
    }
  }, [status]);

  // Show loading state while checking auth or redirecting
  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">{loadingMessage}</p>
        </div>
      </div>
    );
  }

  // While redirecting to Google OAuth
  if (status === 'unauthenticated') {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Redirecting to Google sign-in...</p>
        </div>
      </div>
    );
  }

  // User is authenticated, render the protected content
  return <>{children}</>;
}
