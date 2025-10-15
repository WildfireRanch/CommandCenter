/**
 * DatabaseHealthTab Component
 *
 * PURPOSE: Display comprehensive database and poller health monitoring
 *
 * WHAT IT DOES:
 *   - Shows overall system health status
 *   - Displays active alerts and warnings
 *   - Charts 24-hour collection health trends
 *   - Shows detailed poller statistics
 *   - Displays database metrics and table sizes
 *   - Auto-refreshes every 60 seconds
 *
 * USAGE:
 *   <DatabaseHealthTab />
 */

'use client'

import { useState } from 'react'
import { Activity, AlertCircle, CheckCircle, XCircle, RefreshCw, Database, Server, HardDrive, TrendingUp, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useHealthMonitoring } from '@/hooks/useHealthMonitoring'
import type { Alert } from '@/hooks/useHealthMonitoring'

// ─────────────────────────────────────────────────────────────────────────────
// Helper Functions
// ─────────────────────────────────────────────────────────────────────────────

function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'text-green-600'
    case 'degraded':
      return 'text-yellow-600'
    case 'critical':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

function getStatusBgColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-50 border-green-200'
    case 'degraded':
      return 'bg-yellow-50 border-yellow-200'
    case 'critical':
      return 'bg-red-50 border-red-200'
    default:
      return 'bg-gray-50 border-gray-200'
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="w-8 h-8 text-green-600" />
    case 'degraded':
      return <AlertCircle className="w-8 h-8 text-yellow-600" />
    case 'critical':
      return <XCircle className="w-8 h-8 text-red-600" />
    default:
      return <Activity className="w-8 h-8 text-gray-600" />
  }
}

function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return 'Never'

  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} min ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-Components
// ─────────────────────────────────────────────────────────────────────────────

interface StatusCardProps {
  title: string
  status: string
  subtitle?: string
}

function StatusCard({ title, status, subtitle }: StatusCardProps) {
  return (
    <div className={`rounded-lg border-2 p-6 ${getStatusBgColor(status)}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-700">{title}</h3>
        {getStatusIcon(status)}
      </div>
      <p className={`text-2xl font-bold capitalize ${getStatusColor(status)}`}>
        {status}
      </p>
      {subtitle && (
        <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
      )}
    </div>
  )
}

interface AlertItemProps {
  alert: Alert
}

function AlertItem({ alert }: AlertItemProps) {
  const severityColors = {
    critical: 'bg-red-100 border-red-300 text-red-800',
    warning: 'bg-yellow-100 border-yellow-300 text-yellow-800',
    info: 'bg-blue-100 border-blue-300 text-blue-800'
  }

  const severityIcons = {
    critical: <XCircle className="w-5 h-5" />,
    warning: <AlertCircle className="w-5 h-5" />,
    info: <Activity className="w-5 h-5" />
  }

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${severityColors[alert.severity]}`}>
      {severityIcons[alert.severity]}
      <div className="flex-1">
        <p className="text-sm font-medium">{alert.message}</p>
        <p className="text-xs opacity-75 mt-1">
          {alert.component} • {formatTimestamp(alert.timestamp)}
        </p>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export function DatabaseHealthTab() {
  const { healthData, historyData, loading, error, lastUpdate, refresh } = useHealthMonitoring(60000)
  const [detailsExpanded, setDetailsExpanded] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = async () => {
    setRefreshing(true)
    await refresh()
    setRefreshing(false)
  }

  if (loading && !healthData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-gray-400 mx-auto mb-2" />
          <p className="text-gray-600">Loading health data...</p>
        </div>
      </div>
    )
  }

  if (error && !healthData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <XCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-600 font-medium">Failed to load health data</p>
          <p className="text-sm text-gray-600 mt-1">{error}</p>
          <button
            onClick={handleRefresh}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!healthData) return null

  // Prepare chart data
  const chartData = historyData?.data.slice().reverse().map(point => ({
    time: new Date(point.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    solark: point.solark_collection_health_pct,
    victron: point.victron_collection_health_pct,
    response_time: point.db_response_time_ms
  })) || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Database Health Monitoring</h2>
          <p className="text-sm text-gray-600 mt-1">
            Last updated: {formatTimestamp(lastUpdate.toISOString())}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusCard
          title="OVERALL STATUS"
          status={healthData.overall_status}
          subtitle={`${healthData.alerts.length} active alert${healthData.alerts.length !== 1 ? 's' : ''}`}
        />
        <StatusCard
          title="SOLARK POLLER"
          status={healthData.solark_poller.is_healthy ? 'healthy' : 'critical'}
          subtitle={`${healthData.data_quality.solark.records_last_24h}/${healthData.data_quality.solark.expected_records_24h} records`}
        />
        <StatusCard
          title="VICTRON POLLER"
          status={healthData.victron_poller.is_healthy ? 'healthy' : 'critical'}
          subtitle={`${healthData.data_quality.victron.records_last_24h}/${healthData.data_quality.victron.expected_records_24h} records`}
        />
      </div>

      {/* Alerts Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Active Alerts</h3>
          <span className="text-sm font-medium text-gray-600">
            {healthData.alerts.length} total
          </span>
        </div>
        {healthData.alerts.length === 0 ? (
          <div className="flex items-center gap-2 text-green-600 p-4 bg-green-50 rounded-lg">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">All systems operational</span>
          </div>
        ) : (
          <div className="space-y-3">
            {healthData.alerts.map((alert, index) => (
              <AlertItem key={index} alert={alert} />
            ))}
          </div>
        )}
      </div>

      {/* 24-Hour Collection Health Chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">24-Hour Collection Health</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} label={{ value: 'Health %', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="solark" stroke="#f59e0b" name="SolArk" strokeWidth={2} />
              <Line type="monotone" dataKey="victron" stroke="#3b82f6" name="Victron" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Poller Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Poller Stats */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Server className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Poller Stats</h3>
          </div>
          <div className="space-y-3 text-sm">
            <div>
              <p className="text-gray-600">Last Poll (SolArk)</p>
              <p className="font-medium">{formatTimestamp(healthData.solark_poller.last_successful_poll)}</p>
            </div>
            <div>
              <p className="text-gray-600">Last Poll (Victron)</p>
              <p className="font-medium">{formatTimestamp(healthData.victron_poller.last_successful_poll)}</p>
            </div>
            <div>
              <p className="text-gray-600">Poll Interval</p>
              <p className="font-medium">{healthData.solark_poller.poll_interval_seconds}s</p>
            </div>
            <div>
              <p className="text-gray-600">Consecutive Failures</p>
              <p className="font-medium">
                SolArk: {healthData.solark_poller.consecutive_failures} | Victron: {healthData.victron_poller.consecutive_failures}
              </p>
            </div>
          </div>
        </div>

        {/* Database Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Database</h3>
          </div>
          <div className="space-y-3 text-sm">
            <div>
              <p className="text-gray-600">Status</p>
              <p className="font-medium">{healthData.database.connected ? 'Connected' : 'Disconnected'}</p>
            </div>
            <div>
              <p className="text-gray-600">Response Time</p>
              <p className="font-medium">{healthData.database.response_time_ms.toFixed(2)}ms</p>
            </div>
            <div>
              <p className="text-gray-600">Active Connections</p>
              <p className="font-medium">
                {healthData.database.connection_pool.active_connections} / {healthData.database.connection_pool.max_connections}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Total Size</p>
              <p className="font-medium">
                {(healthData.database_metrics.solark_table.total_size_mb + healthData.database_metrics.victron_table.total_size_mb).toFixed(2)} MB
              </p>
            </div>
          </div>
        </div>

        {/* Data Quality */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Data Quality</h3>
          </div>
          <div className="space-y-3 text-sm">
            <div>
              <p className="text-gray-600">SolArk Collection</p>
              <p className="font-medium">{healthData.data_quality.solark.collection_health_pct.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-gray-600">Victron Collection</p>
              <p className="font-medium">{healthData.data_quality.victron.collection_health_pct.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-gray-600">NULL Values</p>
              <p className="font-medium">
                SolArk: {healthData.data_quality.solark.null_percentage.toFixed(2)}% | Victron: {healthData.data_quality.victron.null_percentage.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-gray-600">Victron API Usage</p>
              <p className="font-medium">
                {healthData.victron_poller.api_requests_this_hour}/{healthData.victron_poller.rate_limit_max} requests/hour
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Metrics (Expandable) */}
      <div className="bg-white rounded-lg shadow">
        <button
          onClick={() => setDetailsExpanded(!detailsExpanded)}
          className="w-full flex items-center justify-between p-6 hover:bg-gray-50"
        >
          <h3 className="text-lg font-semibold text-gray-900">Detailed Metrics</h3>
          {detailsExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-600" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-600" />
          )}
        </button>

        {detailsExpanded && (
          <div className="p-6 pt-0 space-y-6">
            {/* SolArk Table */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <HardDrive className="w-5 h-5 text-amber-600" />
                <h4 className="font-semibold text-gray-900">SolArk Table</h4>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Total Records</p>
                  <p className="font-medium">{healthData.data_quality.solark.total_records.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-600">Oldest Record</p>
                  <p className="font-medium">{formatTimestamp(healthData.data_quality.solark.oldest_record)}</p>
                </div>
                <div>
                  <p className="text-gray-600">Table Size</p>
                  <p className="font-medium">{healthData.database_metrics.solark_table.total_size_mb.toFixed(2)} MB</p>
                </div>
                <div>
                  <p className="text-gray-600">Index Size</p>
                  <p className="font-medium">{healthData.database_metrics.solark_table.index_size_mb.toFixed(2)} MB</p>
                </div>
                <div>
                  <p className="text-gray-600">Avg Row Size</p>
                  <p className="font-medium">{formatBytes(healthData.database_metrics.solark_table.avg_row_size_bytes)}</p>
                </div>
              </div>
            </div>

            {/* Victron Table */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <HardDrive className="w-5 h-5 text-blue-600" />
                <h4 className="font-semibold text-gray-900">Victron Table</h4>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Total Records</p>
                  <p className="font-medium">{healthData.data_quality.victron.total_records.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-600">Oldest Record</p>
                  <p className="font-medium">{formatTimestamp(healthData.data_quality.victron.oldest_record)}</p>
                </div>
                <div>
                  <p className="text-gray-600">Table Size</p>
                  <p className="font-medium">{healthData.database_metrics.victron_table.total_size_mb.toFixed(2)} MB</p>
                </div>
                <div>
                  <p className="text-gray-600">Index Size</p>
                  <p className="font-medium">{healthData.database_metrics.victron_table.index_size_mb.toFixed(2)} MB</p>
                </div>
                <div>
                  <p className="text-gray-600">Avg Row Size</p>
                  <p className="font-medium">{formatBytes(healthData.database_metrics.victron_table.avg_row_size_bytes)}</p>
                </div>
              </div>
            </div>

            {/* Connection Pool */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-5 h-5 text-green-600" />
                <h4 className="font-semibold text-gray-900">Connection Pool</h4>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Active Connections</p>
                  <p className="font-medium">{healthData.database.connection_pool.active_connections} / {healthData.database.connection_pool.max_connections}</p>
                </div>
                <div>
                  <p className="text-gray-600">Idle Connections</p>
                  <p className="font-medium">{healthData.database.connection_pool.idle_connections}</p>
                </div>
                <div>
                  <p className="text-gray-600">Waiting</p>
                  <p className="font-medium">0</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
