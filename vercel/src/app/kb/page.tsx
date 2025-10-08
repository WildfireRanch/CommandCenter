'use client';

import { useSession, signIn } from 'next-auth/react';
import { useState, useEffect } from 'react';

interface Document {
  id: number;
  title: string;
  folder: string | null;
  folder_path: string | null;
  is_context_file: boolean;
  token_count: number;
  last_synced: string;
}

interface PreviewData {
  total_folders: number;
  total_files: number;
  google_docs_count: number;
  folders: Array<{
    name: string;
    path: string;
    file_count: number;
    files: Array<{
      name: string;
      type: string;
      size?: number;
    }>;
  }>;
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

interface SyncHistory {
  id: number;
  sync_type: string;
  triggered_by: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  files_processed: number | null;
  files_succeeded: number | null;
  files_failed: number | null;
}

type Tab = 'overview' | 'files' | 'settings';

export default function KnowledgeBasePage() {
  const { data: session, status } = useSession();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [syncHistory, setSyncHistory] = useState<SyncHistory[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [showSyncModal, setShowSyncModal] = useState(false);

  useEffect(() => {
    if (status === 'authenticated' && session) {
      fetchDocuments();
      fetchPreview();
      fetchSyncHistory();
    }
  }, [status, session]);

  const fetchDocuments = async () => {
    try {
      const res = await fetch('https://api.wildfireranch.us/kb/documents');
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  };

  const fetchPreview = async () => {
    try {
      const res = await fetch('https://api.wildfireranch.us/kb/preview', {
        method: 'POST'
      });
      const data = await res.json();
      setPreview(data);
    } catch (error) {
      console.error('Failed to fetch preview:', error);
    }
  };

  const fetchSyncHistory = async () => {
    try {
      const res = await fetch('https://api.wildfireranch.us/kb/sync-history');
      if (res.ok) {
        const data = await res.json();
        setSyncHistory(data.history || []);
      } else {
        // Endpoint doesn't exist yet, use empty array
        setSyncHistory([]);
      }
    } catch (error) {
      console.error('Failed to fetch sync history:', error);
      setSyncHistory([]);
    }
  };

  const triggerSync = async (syncType: 'full' | 'smart' = 'smart') => {
    if (!session?.accessToken) {
      alert('No access token available');
      return;
    }

    setSyncing(true);
    setShowSyncModal(true);
    setProgress({ status: 'starting' });

    try {
      const response = await fetch(
        `https://api.wildfireranch.us/kb/sync?force=${syncType === 'full'}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.accessToken}`
          }
        }
      );

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
                fetchSyncHistory();
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
      <div className="flex items-center justify-center h-screen">
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

  // Group documents by folder
  const groupedDocs = documents.reduce((acc, doc) => {
    const folder = doc.folder || 'Root';
    if (!acc[folder]) {
      acc[folder] = [];
    }
    acc[folder].push(doc);
    return acc;
  }, {} as Record<string, Document[]>);

  const totalTokens = documents.reduce((sum, doc) => sum + (doc.token_count || 0), 0);
  const contextFiles = documents.filter(d => d.is_context_file).length;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">📚 Knowledge Base</h1>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📊 Overview
          </button>
          <button
            onClick={() => setActiveTab('files')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'files'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📁 Files
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'settings'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            ⚙️ Settings
          </button>
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Sync Status Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Sync Status</h2>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div>
                <p className="text-sm text-gray-600">Last Sync</p>
                <p className="text-lg font-semibold">
                  {syncHistory[0]?.completed_at
                    ? new Date(syncHistory[0].completed_at).toLocaleString()
                    : 'Never'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Documents</p>
                <p className="text-lg font-semibold">
                  {documents.length} synced, {contextFiles} context files
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Tokens</p>
                <p className="text-lg font-semibold">
                  {totalTokens.toLocaleString()} (~${(totalTokens / 1000000 * 0.1).toFixed(2)})
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => triggerSync('full')}
                disabled={syncing}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                🔄 Full Sync
              </button>
              <button
                onClick={() => triggerSync('smart')}
                disabled={syncing}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                ⚡ Smart Sync
              </button>
            </div>
          </div>

          {/* Preview Card */}
          {preview && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">Preview (What Will Be Synced)</h2>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-blue-50 p-4 rounded">
                  <p className="text-sm text-gray-600">Folders</p>
                  <p className="text-2xl font-bold text-blue-600">{preview.total_folders}</p>
                </div>
                <div className="bg-green-50 p-4 rounded">
                  <p className="text-sm text-gray-600">Total Files</p>
                  <p className="text-2xl font-bold text-green-600">{preview.total_files}</p>
                </div>
                <div className="bg-purple-50 p-4 rounded">
                  <p className="text-sm text-gray-600">Google Docs</p>
                  <p className="text-2xl font-bold text-purple-600">{preview.google_docs_count}</p>
                </div>
              </div>
              <div className="space-y-2">
                {preview.folders.map((folder) => (
                  <div key={folder.path} className="border-l-4 border-blue-500 pl-4 py-2">
                    <p className="font-medium">📂 {folder.name} ({folder.file_count} files)</p>
                    <p className="text-sm text-gray-500">{folder.path}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sync History */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Sync History (Last 5)</h2>
            <div className="space-y-2">
              {(syncHistory || []).slice(0, 5).map((sync) => (
                <div key={sync.id} className="flex justify-between items-center border-b pb-2">
                  <div>
                    <p className="font-medium">
                      {new Date(sync.started_at).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500">
                      {sync.sync_type} | {sync.triggered_by}
                    </p>
                  </div>
                  <div className="text-right">
                    <span
                      className={`px-3 py-1 rounded-full text-sm ${
                        sync.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : sync.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {sync.status === 'completed' && '✅ Success'}
                      {sync.status === 'failed' && '❌ Failed'}
                      {sync.status === 'partial' && '⚠️ Partial'}
                    </span>
                    {sync.files_succeeded !== null && (
                      <p className="text-sm text-gray-500 mt-1">
                        {sync.files_succeeded} files
                      </p>
                    )}
                  </div>
                </div>
              ))}
              {(!syncHistory || syncHistory.length === 0) && (
                <p className="text-gray-500 text-center py-4">No sync history yet</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Files Tab */}
      {activeTab === 'files' && (
        <div className="space-y-4">
          {Object.keys(groupedDocs).length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              No documents synced yet. Click "Full Sync" in the Overview tab to get started.
            </div>
          ) : (
            Object.entries(groupedDocs).map(([folder, docs]) => (
              <div key={folder} className="bg-white rounded-lg shadow">
                <div className="p-4 bg-gray-50 border-b">
                  <h3 className="font-semibold">
                    📂 {folder} {folder === 'CONTEXT' && '(Tier 1: Context Files)'} - {docs.length} files
                  </h3>
                </div>
                <div className="divide-y">
                  {docs.map((doc) => (
                    <div key={doc.id} className="p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-medium">{doc.title}</h4>
                          {doc.folder_path && (
                            <p className="text-sm text-gray-500 mt-1">{doc.folder_path}</p>
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
              </div>
            ))
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">🔄 Automatic Sync</h2>
            <div className="space-y-4">
              <div className="flex items-center">
                <input type="checkbox" id="auto-sync" className="mr-3" />
                <label htmlFor="auto-sync" className="text-sm">Enable nightly auto-sync</label>
              </div>
              <div>
                <label className="text-sm text-gray-600">Time</label>
                <input type="time" defaultValue="03:00" className="ml-3 border rounded px-2 py-1" />
              </div>
              <div>
                <label className="text-sm text-gray-600">Sync type</label>
                <select className="ml-3 border rounded px-2 py-1">
                  <option>Smart Sync (changed only)</option>
                  <option>Full Sync</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">📁 Folder Configuration</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-600">Root folder</label>
                <input
                  type="text"
                  defaultValue="COMMAND_CENTER"
                  className="w-full mt-1 border rounded px-3 py-2"
                  disabled
                />
              </div>
              <div>
                <label className="text-sm text-gray-600">Context folder</label>
                <input
                  type="text"
                  defaultValue="COMMAND_CENTER/CONTEXT"
                  className="w-full mt-1 border rounded px-3 py-2"
                  disabled
                />
              </div>
              <div>
                <label className="text-sm text-gray-600">Ignore patterns</label>
                <input
                  type="text"
                  defaultValue="old.*, archive/*, temp/*"
                  className="w-full mt-1 border rounded px-3 py-2"
                  disabled
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">🎛️ Advanced Options</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-600">Chunk size (tokens)</label>
                <input type="number" defaultValue="512" className="w-full mt-1 border rounded px-3 py-2" disabled />
              </div>
              <div>
                <label className="text-sm text-gray-600">Embedding model</label>
                <input
                  type="text"
                  defaultValue="text-embedding-3-small"
                  className="w-full mt-1 border rounded px-3 py-2"
                  disabled
                />
              </div>
              <div>
                <label className="text-sm text-gray-600">Max file size (tokens)</label>
                <input type="number" defaultValue="50000" className="w-full mt-1 border rounded px-3 py-2" disabled />
              </div>
              <div>
                <label className="text-sm text-gray-600">Concurrent uploads</label>
                <input type="number" defaultValue="5" className="w-full mt-1 border rounded px-3 py-2" disabled />
              </div>
            </div>
          </div>

          <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            💾 Save Settings
          </button>
        </div>
      )}

      {/* Sync Progress Modal */}
      {showSyncModal && progress && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <h2 className="text-2xl font-bold mb-4">
              {progress.status === 'completed' ? '✅ Sync Complete!' : '🔄 Syncing Knowledge Base...'}
            </h2>

            {progress.status !== 'completed' && progress.status !== 'failed' && (
              <>
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Progress: {progress.current || 0} / {progress.total || 0} documents</span>
                    <span>{Math.round(((progress.current || 0) / (progress.total || 1)) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                      className="bg-blue-600 h-4 rounded-full transition-all"
                      style={{ width: `${((progress.current || 0) / (progress.total || 1)) * 100}%` }}
                    />
                  </div>
                </div>

                {progress.current_file && (
                  <div className="mb-4 p-4 bg-blue-50 rounded">
                    <p className="font-medium">Currently processing:</p>
                    <p className="text-sm text-gray-600">📄 {progress.current_file}</p>
                  </div>
                )}
              </>
            )}

            {progress.status === 'completed' && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-green-50 rounded">
                    <p className="text-2xl font-bold text-green-600">{progress.processed || 0}</p>
                    <p className="text-sm text-gray-600">Processed</p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded">
                    <p className="text-2xl font-bold text-blue-600">{progress.updated || 0}</p>
                    <p className="text-sm text-gray-600">Updated</p>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded">
                    <p className="text-2xl font-bold text-red-600">{progress.failed || 0}</p>
                    <p className="text-sm text-gray-600">Failed</p>
                  </div>
                </div>
              </div>
            )}

            {progress.error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
                <p className="text-red-800 font-medium">❌ Error:</p>
                <p className="text-sm text-red-600">{progress.error}</p>
              </div>
            )}

            {progress.message && (
              <div className="mt-4 p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-600">{progress.message}</p>
              </div>
            )}

            <div className="mt-6 flex justify-end gap-3">
              {(progress.status === 'completed' || progress.status === 'failed') && (
                <button
                  onClick={() => {
                    setShowSyncModal(false);
                    setProgress(null);
                  }}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  ✅ Close
                </button>
              )}
              {progress.status !== 'completed' && progress.status !== 'failed' && (
                <button
                  onClick={() => {
                    setSyncing(false);
                    setShowSyncModal(false);
                  }}
                  className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  ❌ Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
