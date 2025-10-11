'use client'

import { useEffect, useState } from 'react'
import { Activity, CheckCircle, XCircle, Wrench, MessageSquare, Clock } from 'lucide-react'

interface ActivityEvent {
  id: number
  agent_name: string
  event_type: string
  event_status: string
  query?: string
  tool_name?: string
  duration_ms?: number
  error_message?: string
  created_at: string
}

interface AgentActivityFeedProps {
  limit?: number
  agentName?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export default function AgentActivityFeed({
  limit = 50,
  agentName,
  autoRefresh = true,
  refreshInterval = 5000
}: AgentActivityFeedProps) {
  const [activity, setActivity] = useState<ActivityEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchActivity = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'
        const endpoint = agentName
          ? `${API_URL}/agents/${encodeURIComponent(agentName)}/activity?limit=${limit}`
          : `${API_URL}/agents/activity?limit=${limit}`

        const res = await fetch(endpoint)

        if (res.ok) {
          const response = await res.json()
          setActivity(response.data || [])
        }
      } catch (error) {
        console.error('Failed to fetch agent activity:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchActivity()

    if (autoRefresh) {
      const interval = setInterval(fetchActivity, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [limit, agentName, autoRefresh, refreshInterval])

  const getEventIcon = (eventType: string, eventStatus: string) => {
    if (eventStatus === 'failure') {
      return <XCircle className="w-5 h-5 text-red-600" />
    }

    switch (eventType) {
      case 'start':
      case 'stop':
        return <Activity className="w-5 h-5 text-blue-600" />
      case 'tool_call':
        return <Wrench className="w-5 h-5 text-purple-600" />
      case 'query':
        return <MessageSquare className="w-5 h-5 text-green-600" />
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Activity className="w-5 h-5 text-gray-600" />
    }
  }

  const getEventColor = (eventStatus: string) => {
    switch (eventStatus) {
      case 'success':
        return 'bg-green-50 border-green-200'
      case 'failure':
        return 'bg-red-50 border-red-200'
      case 'in_progress':
        return 'bg-blue-50 border-blue-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getEventDescription = (event: ActivityEvent) => {
    if (event.query) {
      return event.query.substring(0, 80) + (event.query.length > 80 ? '...' : '')
    }
    if (event.tool_name) {
      return `Called tool: ${event.tool_name}`
    }
    if (event.error_message) {
      return `Error: ${event.error_message.substring(0, 80)}`
    }
    return `${event.event_type} event`
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">Loading activity...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Activity className="w-6 h-6 text-blue-600" />
          {agentName ? `${agentName} Activity` : 'Agent Activity'}
        </h2>
        {autoRefresh && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Clock className="w-4 h-4 animate-pulse" />
            Live
          </div>
        )}
      </div>

      {activity.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No recent activity
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {activity.map((event) => (
            <div
              key={event.id}
              className={`p-3 rounded-lg border ${getEventColor(event.event_status)} transition-colors`}
            >
              <div className="flex items-start gap-3">
                {getEventIcon(event.event_type, event.event_status)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-gray-900 text-sm">
                      {event.agent_name}
                    </span>
                    <span className="text-xs text-gray-500 whitespace-nowrap">
                      {formatTimestamp(event.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mt-1 break-words">
                    {getEventDescription(event)}
                  </p>
                  {event.duration_ms && (
                    <p className="text-xs text-gray-500 mt-1">
                      Duration: {event.duration_ms}ms
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
