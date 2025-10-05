'use client'

import { useEffect, useState } from 'react'
import { MessageSquare, Download, RefreshCw, Database, Activity } from 'lucide-react'

interface Conversation {
  session_id: string
  created_at: string
  message_count: number
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

interface EnergyLog {
  timestamp: string
  battery_soc: number
  battery_voltage: number
  battery_power: number
  solar_power: number
  load_power: number
  grid_power: number
}

export default function LogsPage() {
  const [viewMode, setViewMode] = useState<'conversations' | 'energy'>('conversations')
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedSession, setSelectedSession] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [energyLogs, setEnergyLogs] = useState<EnergyLog[]>([])
  const [loading, setLoading] = useState(true)
  const [limit, setLimit] = useState(20)

  useEffect(() => {
    fetchData()
  }, [viewMode, limit])

  const fetchData = async () => {
    setLoading(true)
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'

      if (viewMode === 'conversations') {
        const res = await fetch(`${API_URL}/conversations/recent?limit=${limit}`)
        if (res.ok) {
          const data = await res.json()
          setConversations(data.conversations || [])
        }
      } else {
        const res = await fetch(`${API_URL}/energy/stats?hours=24`)
        if (res.ok) {
          const data = await res.json()
          setEnergyLogs((data.data || []).slice(0, limit))
        }
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadConversation = async (sessionId: string) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'
      const res = await fetch(`${API_URL}/conversations/${sessionId}`)
      if (res.ok) {
        const data = await res.json()
        setMessages(data.messages || [])
        setSelectedSession(sessionId)
      }
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }

  const exportConversation = () => {
    if (!messages.length) return

    let exportText = `# Conversation Export\n\n`
    exportText += `**Session ID:** ${selectedSession}\n\n`
    exportText += `---\n\n`

    messages.forEach(msg => {
      const emoji = msg.role === 'user' ? '🧑' : '🤖'
      exportText += `### ${emoji} ${msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}\n`
      exportText += `*${msg.created_at}*\n\n`
      exportText += `${msg.content}\n\n`
      exportText += `---\n\n`
    })

    const blob = new Blob([exportText], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `conversation_${selectedSession.slice(0, 8)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportEnergyLogs = () => {
    if (!energyLogs.length) return

    const headers = ['Timestamp', 'Battery SOC (%)', 'Battery Voltage (V)', 'Battery Power (W)', 'Solar Power (W)', 'Load Power (W)', 'Grid Power (W)']
    const csvContent = [
      headers.join(','),
      ...energyLogs.map(log => [
        log.timestamp,
        log.battery_soc.toFixed(1),
        log.battery_voltage.toFixed(1),
        log.battery_power.toFixed(0),
        log.solar_power.toFixed(0),
        log.load_power.toFixed(0),
        log.grid_power.toFixed(0)
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `energy_logs_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Logs & Activity</h1>
          <p className="text-gray-600 mt-1">View system logs and conversation history</p>
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('conversations')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === 'conversations'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Conversations
            </button>
            <button
              onClick={() => setViewMode('energy')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === 'energy'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Database className="w-4 h-4 inline mr-2" />
              Energy Logs
            </button>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Records:</label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <button
            onClick={viewMode === 'conversations' ? exportConversation : exportEnergyLogs}
            disabled={viewMode === 'conversations' ? !messages.length : !energyLogs.length}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 ml-auto"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600">Loading {viewMode}...</p>
        </div>
      ) : viewMode === 'conversations' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversations List */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Conversations</h2>
            {conversations.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No conversations found</p>
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <button
                    key={conv.session_id}
                    onClick={() => loadConversation(conv.session_id)}
                    className={`w-full text-left p-4 rounded-lg border transition-colors ${
                      selectedSession === conv.session_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-mono text-sm text-gray-600">
                          {conv.session_id.slice(0, 8)}...
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(conv.created_at).toLocaleString()}
                        </p>
                      </div>
                      <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                        {conv.message_count} msgs
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Conversation Messages */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">
              {selectedSession ? `Conversation ${selectedSession.slice(0, 8)}...` : 'Select a Conversation'}
            </h2>
            {messages.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                {selectedSession ? 'No messages in this conversation' : 'Select a conversation to view messages'}
              </p>
            ) : (
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-lg">{msg.role === 'user' ? '🧑' : '🤖'}</span>
                        <div>
                          <p className="text-sm">{msg.content}</p>
                          <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
                            {new Date(msg.created_at).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Battery SOC
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Voltage
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Battery
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Solar
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Load
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Grid
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {energyLogs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                      No energy logs available
                    </td>
                  </tr>
                ) : (
                  energyLogs.map((log, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.battery_soc.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.battery_voltage.toFixed(1)}V
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.battery_power.toFixed(0)}W
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.solar_power.toFixed(0)}W
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.load_power.toFixed(0)}W
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.grid_power.toFixed(0)}W
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {energyLogs.length > 0 && (
            <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Showing {energyLogs.length} of last 24 hours of energy data
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
