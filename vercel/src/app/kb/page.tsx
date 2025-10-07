'use client';

import { useSession, signIn } from 'next-auth/react';
import { useState, useEffect } from 'react';

interface Document {
  id: number;
  title: string;
  folder: string | null;
  is_context_file: boolean;
  token_count: number;
  last_synced: string;
}

interface ProgressUpdate {
  status: string;
  current?: number;
  total?: number;
  current_file?: string;
  processed?: number;
  updated?: number;
  failed?: number;
  error?: string;
  message?: string;
}

export default function KnowledgeBasePage() {
  const { data: session, status } = useSession();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (session) {
      fetchDocuments();
    }
  }, [session]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await fetch('https://api.wildfireranch.us/kb/documents');
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerSync = async () => {
    if (!session?.accessToken) {
      alert('No access token available');
      return;
    }

    setSyncing(true);
    setProgress({ status: 'starting' });

    try {
      const response = await fetch('https://api.wildfireranch.us/kb/sync?force=false', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6);
            try {
              const update = JSON.parse(data);
              setProgress(update);

              if (update.status === 'completed' || update.status === 'failed') {
                setSyncing(false);
                fetchDocuments();
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Sync error:', error);
      setProgress({ status: 'failed', error: String(error) });
      setSyncing(false);
    }
  };

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (status === 'unauthenticated') {
    return (
      <div className="max-w-md mx-auto mt-20 text-center">
        <h1 className="text-2xl font-bold mb-4">Knowledge Base</h1>
        <p className="mb-6 text-gray-600">
          Sign in with Google to manage your knowledge base
        </p>
        <button
          onClick={() => signIn('google')}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Sign in with Google
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Base</h1>
          <p className="text-gray-600 mt-1">
            Sync and manage your Google Docs knowledge base
          </p>
        </div>
        <button
          onClick={triggerSync}
          disabled={syncing}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {syncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>

      {progress && (
        <div className={`rounded-lg p-4 mb-6 ${
          progress.status === 'completed' ? 'bg-green-50 border border-green-200' :
          progress.status === 'failed' ? 'bg-red-50 border border-red-200' :
          'bg-blue-50 border border-blue-200'
        }`}>
          <p className="font-semibold">
            {progress.status === 'completed' ? '✅ Sync Complete' :
             progress.status === 'failed' ? '❌ Sync Failed' :
             progress.status === 'started' ? '🔄 Starting sync...' :
             `🔄 Syncing: ${progress.current || 0} / ${progress.total || 0}`}
          </p>
          {progress.current_file && (
            <p className="text-sm text-gray-600 mt-1">
              Current: {progress.current_file}
            </p>
          )}
          {progress.message && (
            <p className="text-sm text-gray-600 mt-1">{progress.message}</p>
          )}
          {progress.status === 'completed' && (
            <p className="text-sm text-gray-600 mt-1">
              Processed: {progress.processed} | Updated: {progress.updated} | Failed: {progress.failed}
            </p>
          )}
          {progress.error && (
            <p className="text-sm text-red-600 mt-1">Error: {progress.error}</p>
          )}
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">
            Synced Documents ({documents.length})
          </h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">
            Loading documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No documents synced yet. Click "Sync Now" to get started.
          </div>
        ) : (
          <div className="divide-y">
            {documents.map((doc) => (
              <div key={doc.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-medium">{doc.title}</h3>
                    {doc.folder && (
                      <p className="text-sm text-gray-500 mt-1">📁 {doc.folder}</p>
                    )}
                    {doc.is_context_file && (
                      <span className="inline-block mt-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                        Context File (Always Loaded)
                      </span>
                    )}
                  </div>
                  <div className="text-right text-sm text-gray-500 ml-4">
                    <p>{doc.token_count?.toLocaleString() || 0} tokens</p>
                    <p className="mt-1">
                      {doc.last_synced
                        ? new Date(doc.last_synced).toLocaleDateString()
                        : 'Never'}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
