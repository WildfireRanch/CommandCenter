'use client'

import { useState } from 'react'
import { ExternalLink, Maximize2, Minimize2 } from 'lucide-react'

export default function StudioPage() {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const studioUrl = process.env.NEXT_PUBLIC_STUDIO_URL || 'http://localhost:8501'

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  const openInNewTab = () => {
    window.open(studioUrl, '_blank')
  }

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-white">
        <div className="absolute top-4 right-4 z-10 flex gap-2">
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
            <Minimize2 className="w-4 h-4" />
            Exit Fullscreen
          </button>
        </div>
        <iframe
          src={studioUrl}
          className="w-full h-full border-0"
          title="CrewAI Studio"
        />
      </div>
    )
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Operator Studio</h1>
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

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">About CrewAI Studio</h3>
        <p className="text-sm text-blue-800 mb-3">
          CrewAI Studio provides a no-code interface for creating and managing AI agents and crews.
          Build complex multi-agent workflows without writing any code.
        </p>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>✨ Create AI agents with different roles and capabilities</li>
          <li>🔧 Configure tasks and workflows</li>
          <li>🤖 Build crews (teams of agents working together)</li>
          <li>🚀 Run crews with various LLM providers (OpenAI, Anthropic, Ollama, etc.)</li>
          <li>📚 Add knowledge sources for your agents</li>
          <li>🛠️ Use built-in and custom tools</li>
        </ul>
      </div>

      {/* Embedded Studio */}
      <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <iframe
          src={studioUrl}
          className="w-full h-full border-0"
          title="CrewAI Studio"
        />
      </div>

      {/* Footer Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          <strong>Studio URL:</strong> {studioUrl}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          If the studio doesn't load, make sure it's running on port 8501
        </p>
      </div>
    </div>
  )
}
