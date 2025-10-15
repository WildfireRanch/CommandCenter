/**
 * useHealthMonitoring Hook
 *
 * PURPOSE: Fetch and auto-refresh health monitoring data from the backend
 *
 * WHAT IT DOES:
 *   - Fetches current health status from /health/monitoring/status
 *   - Fetches historical data from /health/monitoring/history
 *   - Auto-refreshes every 60 seconds
 *   - Handles loading and error states
 *   - Provides manual refresh capability
 *
 * USAGE:
 *   const { healthData, historyData, loading, error, refresh } = useHealthMonitoring()
 */

import { useState, useEffect, useCallback } from 'react'

// ─────────────────────────────────────────────────────────────────────────────
// Type Definitions
// ─────────────────────────────────────────────────────────────────────────────

export interface ConnectionPoolInfo {
  active_connections: number
  idle_connections: number
  max_connections: number
}

export interface DatabaseHealth {
  connected: boolean
  connection_pool: ConnectionPoolInfo
  response_time_ms: number
}

export interface PollerHealth {
  is_running: boolean
  is_healthy: boolean
  last_poll_attempt: string | null
  last_successful_poll: string | null
  consecutive_failures: number
  poll_interval_seconds: number
  total_polls_24h: number
  total_records_saved_24h: number
}

export interface VictronPollerHealth extends PollerHealth {
  api_requests_this_hour: number
  rate_limit_max: number
}

export interface DataQualityMetrics {
  total_records: number
  oldest_record: string | null
  newest_record: string | null
  records_last_hour: number
  records_last_24h: number
  records_last_7d: number
  null_percentage: number
  expected_records_24h: number
  collection_health_pct: number
}

export interface VictronDataQuality extends Omit<DataQualityMetrics, 'records_last_7d'> {
  records_last_72h: number
}

export interface TableMetrics {
  total_size_mb: number
  total_rows: number
  index_size_mb: number
  avg_row_size_bytes: number
}

export interface DatabaseMetrics {
  solark_table: TableMetrics
  victron_table: TableMetrics
}

export interface Alert {
  severity: 'critical' | 'warning' | 'info'
  component: 'database' | 'solark_poller' | 'victron_poller' | 'data_quality'
  message: string
  timestamp: string
}

export interface HealthMonitoringData {
  timestamp: string
  overall_status: 'healthy' | 'degraded' | 'critical'
  database: DatabaseHealth
  solark_poller: PollerHealth
  victron_poller: VictronPollerHealth
  data_quality: {
    solark: DataQualityMetrics
    victron: VictronDataQuality
  }
  database_metrics: DatabaseMetrics
  alerts: Alert[]
}

export interface HistoryDataPoint {
  timestamp: string
  overall_status: string
  solark_collection_health_pct: number
  victron_collection_health_pct: number
  db_response_time_ms: number
  solark_records_24h: number
  victron_records_24h: number
  critical_alerts: number
  warning_alerts: number
}

export interface HistoryData {
  status: string
  hours: number
  data: HistoryDataPoint[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook Implementation
// ─────────────────────────────────────────────────────────────────────────────

export function useHealthMonitoring(refreshInterval = 60000) {
  const [healthData, setHealthData] = useState<HealthMonitoringData | null>(null)
  const [historyData, setHistoryData] = useState<HistoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'

  // Fetch current health status
  const fetchHealthStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/health/monitoring/status`)

      if (!response.ok) {
        throw new Error(`Failed to fetch health status: ${response.statusText}`)
      }

      const data = await response.json()
      setHealthData(data)
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      console.error('Error fetching health status:', err)
    }
  }, [API_URL])

  // Fetch historical data
  const fetchHistory = useCallback(async (hours = 24) => {
    try {
      const response = await fetch(`${API_URL}/health/monitoring/history?hours=${hours}`)

      if (!response.ok) {
        throw new Error(`Failed to fetch history: ${response.statusText}`)
      }

      const data = await response.json()
      setHistoryData(data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      console.error('Error fetching history:', err)
      // Don't set error state for history failures - it's non-critical
    }
  }, [API_URL])

  // Combined fetch
  const fetchAll = useCallback(async () => {
    setLoading(true)
    await Promise.all([
      fetchHealthStatus(),
      fetchHistory(24)
    ])
    setLoading(false)
  }, [fetchHealthStatus, fetchHistory])

  // Manual refresh
  const refresh = useCallback(async () => {
    await fetchAll()
  }, [fetchAll])

  // Initial fetch
  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  // Auto-refresh interval
  useEffect(() => {
    if (refreshInterval <= 0) return

    const interval = setInterval(() => {
      fetchHealthStatus()
      // Fetch history less frequently (every 5 minutes)
      if (Date.now() % 300000 < refreshInterval) {
        fetchHistory(24)
      }
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval, fetchHealthStatus, fetchHistory])

  return {
    healthData,
    historyData,
    loading,
    error,
    lastUpdate,
    refresh
  }
}
