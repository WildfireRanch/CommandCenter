'use client'

import { Activity, CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'

interface AgentHealthCardProps {
  agentName: string
  status: 'online' | 'offline' | 'error' | 'degraded'
  lastSeen?: string | number
  responseTimeMs?: number
  successRate?: number
  errorMessage?: string
}

export default function AgentHealthCard({
  agentName,
  status,
  lastSeen,
  responseTimeMs,
  successRate,
  errorMessage
}: AgentHealthCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'online':
        return 'text-green-600 bg-green-100'
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100'
      case 'offline':
        return 'text-gray-600 bg-gray-100'
      case 'error':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'online':
        return <CheckCircle className="w-6 h-6 text-green-600" />
      case 'degraded':
        return <AlertCircle className="w-6 h-6 text-yellow-600" />
      case 'offline':
        return <XCircle className="w-6 h-6 text-gray-600" />
      case 'error':
        return <XCircle className="w-6 h-6 text-red-600" />
      default:
        return <Activity className="w-6 h-6 text-gray-600" />
    }
  }

  const formatLastSeen = () => {
    if (!lastSeen) return 'Never'

    const date = typeof lastSeen === 'number'
      ? new Date(lastSeen * 1000)
      : new Date(lastSeen)

    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{agentName}</h3>
        {getStatusIcon()}
      </div>

      {/* Status Badge */}
      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium mb-4 ${getStatusColor()}`}>
        {status === 'online' && <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />}
        <span className="capitalize">{status}</span>
      </div>

      {/* Metrics */}
      <div className="space-y-3">
        {/* Last Seen */}
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600 flex items-center gap-1">
            <Clock className="w-4 h-4" />
            Last Seen
          </span>
          <span className="font-medium text-gray-900">{formatLastSeen()}</span>
        </div>

        {/* Response Time */}
        {responseTimeMs !== undefined && (
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Response Time</span>
            <span className="font-medium text-gray-900">{responseTimeMs}ms</span>
          </div>
        )}

        {/* Success Rate */}
        {successRate !== undefined && (
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Success Rate</span>
            <span className="font-medium text-gray-900">{successRate.toFixed(1)}%</span>
          </div>
        )}

        {/* Error Message */}
        {errorMessage && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-red-600">{errorMessage}</p>
          </div>
        )}
      </div>
    </div>
  )
}
