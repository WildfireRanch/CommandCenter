'use client'

import { useState, useEffect } from 'react'
import { ExternalLink, Maximize2, Minimize2, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'

export default function StudioPage() {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [studioStatus, setStudioStatus] = useState<'loading' | 'available' | 'unavailable'>('loading')
  const [studioUrl, setStudioUrl] = useState('')

  useEffect(() => {
    // Check for production studio URL first, fallback to local
    const checkStudioAvailability = async () => {
      const productionUrl = process.env.NEXT_PUBLIC_STUDIO_URL
      const localUrl = 'http://localhost:8501'

      if (productionUrl) {
        try {
          const res = await fetch(productionUrl, { method: 'HEAD', mode: 'no-cors' })
          setStudioUrl(productionUrl)
          setStudioStatus('available')
          return
        } catch (error) {
          console.warn('Production studio not available, trying local...')
        }
      }

      // Try local if production not available
      try {
        const res = await fetch(localUrl, { method: 'HEAD' })
        if (res.ok || res.status === 0) {
          setStudioUrl(localUrl)
          setStudioStatus('available')
          return
        }
      } catch (error) {
        console.warn('Local studio not available')
      }

      setStudioStatus('unavailable')
    }

    checkStudioAvailability()
  }, [])

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  const openInNewTab = () => {
    if (studioUrl) {
      window.open(studioUrl, '_blank')
    }
  }

  // Loading state
  if (studioStatus === 'loading') {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Connecting to Operator Studio...</h2>
          <p className="text-gray-600 mt-2">Please wait while we establish the connection</p>
        </div>
      </div>
    )
  }

  // Unavailable state
  if (studioStatus === 'unavailable') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Operator Studio</h1>
            <p className="text-gray-600 mt-1">CrewAI agent management and crew configuration</p>
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-yellow-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-2">Studio Not Available</h3>
              <p className="text-sm text-yellow-800 mb-4">
                CrewAI Studio is not currently accessible. This could be because:
              </p>
              <ul className="text-sm text-yellow-700 space-y-2 mb-4">
                <li>• The studio service is not deployed to production yet</li>
                <li>• The local studio server (port 8501) is not running</li>
                <li>• Network connectivity issues</li>
              </ul>
              <div className="bg-yellow-100 rounded-lg p-4 mt-4">
                <p className="text-sm font-medium text-yellow-900 mb-2">To run locally:</p>
                <pre className="text-xs bg-yellow-50 p-3 rounded border border-yellow-200 overflow-x-auto">
cd /workspaces/CommandCenter/crewai-studio
streamlit run app/app.py --server.port 8501
                </pre>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-3">About Operator Studio</h3>
          <p className="text-sm text-blue-800 mb-3">
            CrewAI Studio provides a no-code interface for creating and managing AI agents and crews.
            Build complex multi-agent workflows without writing any code.
          </p>
          <ul className="text-sm text-blue-700 space-y-2">
            <li>✨ Create AI agents with different roles and capabilities</li>
            <li>🔧 Configure tasks and workflows</li>
            <li>🤖 Build crews (teams of agents working together)</li>
            <li>🚀 Run crews with various LLM providers (OpenAI, Anthropic, Ollama, etc.)</li>
            <li>📚 Add knowledge sources for your agents</li>
            <li>🛠️ Use built-in and custom tools</li>
          </ul>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Deployment Configuration</h3>
          <p className="text-sm text-gray-600 mb-4">
            To deploy CrewAI Studio to production, add the following environment variable to your Vercel project:
          </p>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs font-mono text-gray-700 mb-2">NEXT_PUBLIC_STUDIO_URL</p>
            <p className="text-xs text-gray-600">
              Value: Your deployed CrewAI Studio URL (e.g., https://studio.wildfireranch.us)
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Available state - show iframe
  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-white">
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <button
            onClick={openInNewTab}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 shadow-lg"
          >
            <ExternalLink className="w-4 h-4" />
            Open in New Tab
          </button>
          <button
            onClick={toggleFullscreen}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2 shadow-lg"
          >
            <Minimize2 className="w-4 h-4" />
            Exit Fullscreen
          </button>
        </div>
        <iframe
          src={`${studioUrl}?embed=true&embed_options=show_toolbar,show_padding,show_colored_line`}
          className="w-full h-full border-0"
          title="CrewAI Studio"
          allow="clipboard-read; clipboard-write"
        />
      </div>
    )
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            Operator Studio
            <CheckCircle className="w-6 h-6 text-green-600" />
          </h1>
          <p className="text-gray-600 mt-1">CrewAI agent management and crew configuration</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={openInNewTab}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <ExternalLink className="w-4 h-4" />
            Open in New Tab
          </button>
          <button
            onClick={toggleFullscreen}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2"
          >
            <Maximize2 className="w-4 h-4" />
            Fullscreen
          </button>
        </div>
      </div>

      {/* Status Info */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <p className="text-sm text-green-800">
            <strong>Studio Connected:</strong> {studioUrl}
          </p>
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Quick Guide</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>✨ Create AI agents with different roles and capabilities</li>
          <li>🔧 Configure tasks and workflows</li>
          <li>🤖 Build crews (teams of agents working together)</li>
          <li>🚀 Run crews with various LLM providers</li>
          <li>📚 Add knowledge sources for your agents</li>
          <li>🛠️ Use built-in and custom tools</li>
        </ul>
      </div>

      {/* Embedded Studio */}
      <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <iframe
          src={`${studioUrl}?embed=true&embed_options=show_toolbar,show_padding,show_colored_line`}
          className="w-full h-full border-0"
          title="CrewAI Studio"
          allow="clipboard-read; clipboard-write"
        />
      </div>
    </div>
  )
}
