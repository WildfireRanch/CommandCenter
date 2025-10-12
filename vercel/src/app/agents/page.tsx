'use client'

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import AgentHealthCard from '@/components/AgentHealthCard'
import AgentActivityFeed from '@/components/AgentActivityFeed'
import { TrendingUp, Activity, CheckCircle, AlertCircle } from 'lucide-react'

interface AgentHealth {
  agent_name: string
  status: 'online' | 'offline' | 'error' | 'degraded'
  response_time_ms?: number
  error_message?: string
  checked_at: string
}

interface AgentMetrics {
  agent_name?: string
  total_events: number
  successful_events: number
  failed_events: number
  avg_duration_ms: number
  total_tool_calls: number
}

export default function AgentsPage() {
  const [agentsHealth, setAgentsHealth] = useState<AgentHealth[]>([])
  const [metrics, setMetrics] = useState<Record<string, AgentMetrics>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'

        // Fetch agent health
        const healthRes = await fetch(`${API_URL}/agents/health`)
        if (healthRes.ok) {
          const healthData = await healthRes.json()
          setAgentsHealth(healthData.data?.agents || [])
        }

        // Fetch metrics for each agent
        const agents = ['Manager', 'Solar Controller', 'Energy Orchestrator']
        const metricsData: Record<string, AgentMetrics> = {}

        for (const agent of agents) {
          try {
            const metricsRes = await fetch(`${API_URL}/agents/${encodeURIComponent(agent)}/metrics?hours=24`)
            if (metricsRes.ok) {
              const data = await metricsRes.json()
              metricsData[agent] = data.data
            }
          } catch (err) {
            console.error(`Failed to fetch metrics for ${agent}:`, err)
          }
        }

        setMetrics(metricsData)
      } catch (error) {
        console.error('Failed to fetch agent data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  // Calculate success rate for each agent
  const getSuccessRate = (agentName: string): number | undefined => {
    const agentMetrics = metrics[agentName]
    if (!agentMetrics || agentMetrics.total_events === 0) return undefined
    return (agentMetrics.successful_events / agentMetrics.total_events) * 100
  }

  // Prepare tool usage chart data
  const toolUsageData = Object.entries(metrics).map(([agent, data]) => ({
    agent: agent.replace(' Controller', '').replace(' Orchestrator', ''),
    'Tool Calls': data.total_tool_calls || 0,
    'Total Events': data.total_events || 0
  }))

  // Prepare performance chart data
  const performanceData = Object.entries(metrics).map(([agent, data]) => ({
    agent: agent.replace(' Controller', '').replace(' Orchestrator', ''),
    'Avg Response (ms)': Math.round(data.avg_duration_ms || 0),
    'Success Rate': getSuccessRate(agent)?.toFixed(1) || 0
  }))

  const healthSummary = agentsHealth.reduce(
    (acc, agent) => {
      acc[agent.status] = (acc[agent.status] || 0) + 1
      return acc
    },
    {} as Record<string, number>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agent Monitor</h1>
          <p className="text-gray-600 mt-1">Real-time health and performance monitoring</p>
        </div>
        <a
          href="/testing"
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          🧪 Developer Tools
        </a>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <span className="text-sm font-medium text-gray-500">Online</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {healthSummary.online || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="w-6 h-6 text-yellow-600" />
            <span className="text-sm font-medium text-gray-500">Degraded</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {healthSummary.degraded || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-6 h-6 text-blue-600" />
            <span className="text-sm font-medium text-gray-500">Total Events (24h)</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {Object.values(metrics).reduce((sum, m) => sum + (m.total_events || 0), 0)}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-6 h-6 text-purple-600" />
            <span className="text-sm font-medium text-gray-500">Avg Success Rate</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {loading
              ? '--'
              : Object.keys(metrics).length > 0
              ? (
                  Object.keys(metrics).reduce((sum, agent) => sum + (getSuccessRate(agent) || 0), 0) /
                  Object.keys(metrics).length
                ).toFixed(1)
              : '0'}%
          </div>
        </div>
      </div>

      {/* Agent Health Cards */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Agent Health Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {loading ? (
            <div className="col-span-3 text-center py-12 text-gray-500">Loading agent health...</div>
          ) : agentsHealth.length === 0 ? (
            <div className="col-span-3 text-center py-12 text-gray-500">No agent health data available</div>
          ) : (
            agentsHealth.map((agent) => (
              <AgentHealthCard
                key={agent.agent_name}
                agentName={agent.agent_name}
                status={agent.status}
                lastSeen={agent.checked_at}
                responseTimeMs={agent.response_time_ms}
                successRate={getSuccessRate(agent.agent_name)}
                errorMessage={agent.error_message}
              />
            ))
          )}
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Tool Usage Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Tool Usage (24h)</h2>
          {loading || toolUsageData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-400">
              {loading ? 'Loading chart data...' : 'No data available'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={toolUsageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="agent" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Tool Calls" fill="#8b5cf6" />
                <Bar dataKey="Total Events" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Performance Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Performance Metrics (24h)</h2>
          {loading || performanceData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-400">
              {loading ? 'Loading chart data...' : 'No data available'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="agent" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="Avg Response (ms)"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="Success Rate"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Activity Feed */}
      <AgentActivityFeed limit={50} autoRefresh={true} refreshInterval={10000} />

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          Agent health and metrics update every 30 seconds. Activity feed updates every 10 seconds.
        </p>
      </div>
    </div>
  )
}
