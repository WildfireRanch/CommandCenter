'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Trash2, Download, BarChart3 } from 'lucide-react'
import ChatAgentPanel from '@/components/chat/ChatAgentPanel'
import { useSessionInsights } from '@/hooks/useSessionInsights'
import ErrorBoundary from '@/components/ErrorBoundary'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  agent_role?: string  // Which agent handled this (Solar Controller, Research Agent, etc.)
  duration_ms?: number // How long the agent took to respond
  // V1.8: Smart Context metadata
  context_tokens?: number  // Tokens used for context
  cache_hit?: boolean      // Was context loaded from cache?
  query_type?: string      // Query classification (system/research/planning/general)
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState('')
  const [panelOpen, setPanelOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // V2.0: Session insights hook
  const { insights, liveMetrics } = useSessionInsights({
    sessionId,
    messages,
    enabled: true,
    refreshInterval: 5000
  })

  useEffect(() => {
    // Generate session ID on mount
    setSessionId(crypto.randomUUID())
  }, [])

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'
      const res = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: sessionId
        })
      })

      if (res.ok) {
        const data = await res.json()
        console.log('Agent response:', data) // Debug logging
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.response || 'No response received',
          timestamp: new Date().toISOString(),
          agent_role: data.agent_role || 'Unknown Agent',
          duration_ms: data.duration_ms || 0,
          // V1.8: Smart Context metadata
          context_tokens: data.context_tokens,
          cache_hit: data.cache_hit,
          query_type: data.query_type
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        console.error('API error:', res.status, res.statusText)
        const errorText = await res.text().catch(() => 'Unknown error')
        console.error('Error details:', errorText)
        const errorMessage: Message = {
          role: 'assistant',
          content: `Sorry, I encountered an error (${res.status}). Please try again.`,
          timestamp: new Date().toISOString(),
          agent_role: 'System'
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `Connection error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your network.`,
        timestamp: new Date().toISOString(),
        agent_role: 'System'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = () => {
    setMessages([])
    setSessionId(crypto.randomUUID())
  }

  const exportChat = () => {
    let exportText = `# Solar Controller Conversation\n\n`
    exportText += `**Session ID:** ${sessionId}\n\n`
    exportText += `**Date:** ${new Date().toLocaleString()}\n\n`
    exportText += `---\n\n`

    messages.forEach(msg => {
      const emoji = msg.role === 'user' ? '🧑' : '🤖'
      exportText += `### ${emoji} ${msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}\n\n`
      exportText += `${msg.content}\n\n`
      exportText += `---\n\n`
    })

    const blob = new Blob([exportText], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `conversation_${sessionId.slice(0, 8)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Energy Assistant</h1>
            <p className="text-sm text-gray-500 mt-1">
              Multi-Agent System • Session: {sessionId.slice(0, 8)}...
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPanelOpen(!panelOpen)}
              className={`px-4 py-2 text-sm font-medium border rounded-lg flex items-center gap-2 transition-colors ${
                panelOpen
                  ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
              title="Toggle insights panel"
            >
              <BarChart3 className="w-4 h-4" />
              <span className="hidden sm:inline">Insights</span>
            </button>
            <button
              onClick={exportChat}
              disabled={messages.length === 0}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">Export</span>
            </button>
            <button
              onClick={clearChat}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              <span className="hidden sm:inline">Clear</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area: Chat + Panel Split */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat Section: Full width on mobile, 2/3 on desktop when panel open */}
        <div className={`flex flex-col transition-all duration-300 ${
          panelOpen ? 'w-full lg:w-2/3' : 'w-full'
        }`}>
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
        {messages.length === 0 ? (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-blue-900 mb-3">Welcome! I'm your AI Energy Assistant.</h2>
            <p className="text-blue-800 mb-4">I have access to multiple specialized agents:</p>
            <ul className="space-y-2 text-blue-700">
              <li>🤖 <strong>Solar Controller</strong> - Battery status, solar production, real-time system data</li>
              <li>🔬 <strong>Research Agent</strong> - Industry trends, technology comparisons, best practices</li>
              <li>⚡ <strong>Energy Orchestrator</strong> - Planning, optimization strategies, multi-day forecasts</li>
              <li>🎯 <strong>Manager</strong> - Routes your questions to the right specialist</li>
            </ul>
            <p className="text-blue-800 mt-4 font-medium">Ask me anything! I'll automatically route to the best agent for your question.</p>
            <div className="mt-4 p-3 bg-white rounded border border-blue-300">
              <p className="text-xs text-blue-600 font-medium mb-1">Try asking:</p>
              <p className="text-xs text-blue-600">"What's my current battery level?" or "What are the latest trends in solar storage?"</p>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl rounded-lg p-4 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-900 border border-gray-200'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="text-2xl">{msg.role === 'user' ? '🧑' : '🤖'}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <div className="text-sm font-medium">
                        {msg.role === 'user' ? 'You' : msg.agent_role || 'Agent'}
                      </div>
                      {msg.duration_ms && msg.duration_ms > 0 && (
                        <div className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                          {(msg.duration_ms / 1000).toFixed(1)}s
                        </div>
                      )}
                      {/* V1.8: Smart Context metadata badges */}
                      {msg.query_type && (
                        <div className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                          {msg.query_type}
                        </div>
                      )}
                      {msg.context_tokens !== undefined && (
                        <div className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded border border-green-200">
                          {msg.context_tokens.toLocaleString()} tokens
                        </div>
                      )}
                      {msg.cache_hit !== undefined && (
                        <div className={`text-xs px-2 py-0.5 rounded border ${
                          msg.cache_hit
                            ? 'text-purple-600 bg-purple-50 border-purple-200'
                            : 'text-gray-500 bg-gray-50 border-gray-200'
                        }`}>
                          {msg.cache_hit ? '⚡ cached' : 'fresh'}
                        </div>
                      )}
                    </div>
                    <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    <div className={`text-xs mt-2 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'}`}>
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-900 border border-gray-200 rounded-lg p-4 max-w-2xl">
              <div className="flex items-center gap-3">
                <div className="text-2xl">🤖</div>
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="bg-white border-t border-gray-200 p-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about your solar system..."
                disabled={loading}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
              >
                <Send className="w-4 h-4" />
                Send
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">Press Enter to send, Shift+Enter for new line</p>
          </div>
        </div>

        {/* Agent Insights Panel: 1/3 width on desktop when open */}
        {panelOpen && (
          <div className={`
            fixed lg:relative
            inset-0 lg:inset-auto
            w-full lg:w-1/3
            z-50 lg:z-auto
            transition-all duration-300
          `}>
            <ErrorBoundary>
              <ChatAgentPanel
                isOpen={panelOpen}
                onClose={() => setPanelOpen(false)}
                sessionId={sessionId}
                insights={insights}
                liveMetrics={liveMetrics}
              />
            </ErrorBoundary>
          </div>
        )}
      </div>
    </div>
  )
}
