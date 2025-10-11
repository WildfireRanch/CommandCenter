'use client'

import { useEffect, useState } from 'react'
import { Activity, Database, Server, Wifi, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface HealthStatus {
  status: string
  checks?: {
    api?: string
    database_connected?: boolean
    database_type?: string
  }
}

interface SystemStats {
  total_energy_snapshots: number
  total_conversations: number
  conversations_today: number
  latest_energy?: {
    timestamp: string
    battery_soc: number
    solar_power: number
  }
}

interface AgentHealth {
  agent_name: string
  status: string
  response_time_ms?: number
  checked_at: string
}

export default function StatusPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [agentsHealth, setAgentsHealth] = useState<AgentHealth[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    const fetchData = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'

        // Fetch health status
        const healthRes = await fetch(`${API_URL}/health`)
        if (healthRes.ok) {
          setHealth(await healthRes.json())
        }

        // Fetch system stats
        const statsRes = await fetch(`${API_URL}/system/stats`)
        if (statsRes.ok) {
          const statsData = await statsRes.json()
          setStats(statsData.data)
        }

        // Fetch agent health
        const agentsRes = await fetch(`${API_URL}/agents/health`)
        if (agentsRes.ok) {
          const agentsData = await agentsRes.json()
          setAgentsHealth(agentsData.data?.agents || [])
        }

        setLastUpdate(new Date())
      } catch (error) {
        console.error('Failed to fetch status:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const isHealthy = health?.status === 'healthy'
  const isDatabaseConnected = health?.checks?.database_connected === true

  const getStatusIcon = (status: boolean) => {
    return status ? (
      <CheckCircle className="w-6 h-6 text-green-600" />
    ) : (
      <XCircle className="w-6 h-6 text-red-600" />
    )
  }

  const getStatusColor = (status: boolean) => {
    return status ? 'text-green-600' : 'text-red-600'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Status</h1>
          <p className="text-gray-600 mt-1">Monitor system health and performance</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-gray-200">
          <Activity className={`w-5 h-5 ${isHealthy ? 'text-green-500 animate-pulse' : 'text-gray-400'}`} />
          <span className={`font-medium ${getStatusColor(isHealthy)}`}>
            {isHealthy ? 'All Systems Operational' : 'System Issues Detected'}
          </span>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* API Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <Server className="w-8 h-8 text-blue-600" />
            {getStatusIcon(isHealthy)}
          </div>
          <h3 className="text-lg font-semibold text-gray-900">API Server</h3>
          <p className={`text-sm font-medium mt-2 ${getStatusColor(isHealthy)}`}>
            {health?.checks?.api || (isHealthy ? 'Online' : 'Offline')}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'}
          </p>
        </div>

        {/* Database Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <Database className="w-8 h-8 text-purple-600" />
            {getStatusIcon(isDatabaseConnected)}
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Database</h3>
          <p className={`text-sm font-medium mt-2 ${getStatusColor(isDatabaseConnected)}`}>
            {isDatabaseConnected ? 'Connected' : 'Disconnected'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {health?.checks?.database_type || 'PostgreSQL'}
          </p>
        </div>

        {/* Frontend Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <Wifi className="w-8 h-8 text-green-600" />
            <CheckCircle className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Frontend</h3>
          <p className="text-sm font-medium text-green-600 mt-2">Active</p>
          <p className="text-xs text-gray-500 mt-1">Next.js 14</p>
        </div>

        {/* Data Collection */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <Activity className="w-8 h-8 text-yellow-600" />
            {getStatusIcon(!!stats?.latest_energy)}
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Data Collection</h3>
          <p className={`text-sm font-medium mt-2 ${getStatusColor(!!stats?.latest_energy)}`}>
            {stats?.latest_energy ? 'Active' : 'Inactive'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {stats?.latest_energy ? 'Real-time updates' : 'No recent data'}
          </p>
        </div>
      </div>

      {/* Agent Services Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Agent Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {agentsHealth.length === 0 ? (
            <div className="col-span-3 text-center py-6 text-gray-500">
              {loading ? 'Loading agent status...' : 'No agent health data available'}
            </div>
          ) : (
            agentsHealth.map((agent) => {
              const isOnline = agent.status === 'online'
              const isDegraded = agent.status === 'degraded'
              const statusColor = isOnline ? 'text-green-600' : isDegraded ? 'text-yellow-600' : 'text-red-600'

              return (
                <div key={agent.agent_name} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium text-gray-900">{agent.agent_name}</p>
                    {isOnline ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : isDegraded ? (
                      <AlertCircle className="w-5 h-5 text-yellow-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600" />
                    )}
                  </div>
                  <p className={`text-sm font-medium ${statusColor} capitalize`}>
                    {agent.status}
                  </p>
                  {agent.response_time_ms !== undefined && (
                    <p className="text-xs text-gray-500 mt-1">
                      Response: {agent.response_time_ms}ms
                    </p>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* System Statistics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">System Statistics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-500">Total Energy Snapshots</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {loading ? '--' : (stats?.total_energy_snapshots.toLocaleString() || '0')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Conversations</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {loading ? '--' : (stats?.total_conversations.toLocaleString() || '0')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Conversations Today</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {loading ? '--' : (stats?.conversations_today || '0')}
            </p>
          </div>
        </div>
      </div>

      {/* Latest Data */}
      {stats?.latest_energy && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Latest Energy Data</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Timestamp</p>
              <p className="text-lg font-semibold text-gray-900 mt-1">
                {new Date(stats.latest_energy.timestamp).toLocaleString()}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Battery SOC</p>
              <p className="text-lg font-semibold text-gray-900 mt-1">
                {stats.latest_energy.battery_soc.toFixed(1)}%
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Solar Power</p>
              <p className="text-lg font-semibold text-gray-900 mt-1">
                {stats.latest_energy.solar_power.toLocaleString()}W
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Service Endpoints */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Service Endpoints</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">API Server</p>
              <p className="text-sm text-gray-600">{process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'}</p>
            </div>
            {getStatusIcon(isHealthy)}
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Database</p>
              <p className="text-sm text-gray-600">PostgreSQL (TimescaleDB)</p>
            </div>
            {getStatusIcon(isDatabaseConnected)}
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Streamlit Ops Dashboard</p>
              <p className="text-sm text-gray-600">Port 8502</p>
            </div>
            <AlertCircle className="w-6 h-6 text-gray-400" />
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">CrewAI Studio</p>
              <p className="text-sm text-gray-600">Port 8501</p>
            </div>
            <AlertCircle className="w-6 h-6 text-gray-400" />
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">MCP Server</p>
              <p className="text-sm text-gray-600">Port 8080</p>
            </div>
            <AlertCircle className="w-6 h-6 text-gray-400" />
          </div>
        </div>
      </div>

      {/* System Health Details */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Health Check Details</h2>
        {health ? (
          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="text-sm text-gray-800 overflow-x-auto">
              {JSON.stringify(health, null, 2)}
            </pre>
          </div>
        ) : (
          <p className="text-gray-500">No health data available</p>
        )}
      </div>

      {/* Last Update */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Last Updated:</strong> {lastUpdate.toLocaleTimeString()} • Auto-refreshes every 30 seconds
        </p>
      </div>
    </div>
  )
}
