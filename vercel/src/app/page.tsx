'use client'

import { useEffect, useState } from 'react'
import { Activity, Battery, Sun, Zap } from 'lucide-react'

interface HealthStatus {
  status: string
  checks?: {
    api?: string
    database_connected?: boolean
  }
}

interface EnergyData {
  pv_power: number
  batt_power: number
  grid_power: number
  load_power: number
  soc: number
  pv_to_load: boolean
  pv_to_grid: boolean
  pv_to_bat: boolean
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [energy, setEnergy] = useState<EnergyData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'

        // Fetch health
        const healthRes = await fetch(`${API_URL}/health`)
        if (healthRes.ok) {
          setHealth(await healthRes.json())
        }

        // Fetch energy - note the data is nested in response
        const energyRes = await fetch(`${API_URL}/energy/latest`)
        if (energyRes.ok) {
          const response = await energyRes.json()
          setEnergy(response.data) // Extract the data object
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const isHealthy = health?.status === 'healthy'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">CommandCenter</h1>
          <p className="text-gray-600 mt-1">Solar Energy Management System</p>
        </div>
        <div className="flex items-center gap-2">
          <Activity className={`w-5 h-5 ${isHealthy ? 'text-green-500' : 'text-gray-400'}`} />
          <span className="text-sm text-gray-600">
            {isHealthy ? 'System Online' : 'Connecting...'}
          </span>
        </div>
      </div>

      {/* Energy Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Battery SOC */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <Battery className="w-8 h-8 text-green-600" />
            <span className="text-xs font-medium text-gray-500">BATTERY</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {loading ? '--' : `${energy?.soc?.toFixed(1) || '0'}%`}
          </div>
          <p className="text-sm text-gray-500 mt-1">State of Charge</p>
          {energy?.batt_power !== undefined && (
            <p className="text-xs text-gray-400 mt-2">
              {energy.batt_power > 0 ? '⬇️ Charging' : energy.batt_power < 0 ? '⬆️ Discharging' : '⏸️ Idle'}
              {' '}({Math.abs(energy.batt_power)}W)
            </p>
          )}
        </div>

        {/* Solar Power */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <Sun className="w-8 h-8 text-yellow-500" />
            <span className="text-xs font-medium text-gray-500">SOLAR</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {loading ? '--' : `${energy?.pv_power?.toLocaleString() || '0'}`}
          </div>
          <p className="text-sm text-gray-500 mt-1">Watts Production</p>
          {energy && (
            <p className="text-xs text-gray-400 mt-2">
              {energy.pv_to_load && '→ Load'} {energy.pv_to_bat && '→ Battery'} {energy.pv_to_grid && '→ Grid'}
            </p>
          )}
        </div>

        {/* Load Power */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <Zap className="w-8 h-8 text-blue-600" />
            <span className="text-xs font-medium text-gray-500">LOAD</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {loading ? '--' : `${energy?.load_power?.toLocaleString() || '0'}`}
          </div>
          <p className="text-sm text-gray-500 mt-1">Watts Consumption</p>
        </div>

        {/* Grid Power */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <Activity className="w-8 h-8 text-purple-600" />
            <span className="text-xs font-medium text-gray-500">GRID</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {loading ? '--' : `${energy?.grid_power?.toLocaleString() || '0'}`}
          </div>
          <p className="text-sm text-gray-500 mt-1">Watts {(energy?.grid_power || 0) > 0 ? 'Import' : 'Export'}</p>
        </div>
      </div>

      {/* System Status Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">System Status</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">API</p>
            <p className={`font-semibold ${isHealthy ? 'text-green-600' : 'text-gray-400'}`}>
              {health?.checks?.api || '--'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Database</p>
            <p className={`font-semibold ${health?.checks?.database_connected ? 'text-green-600' : 'text-gray-400'}`}>
              {health?.checks?.database_connected ? 'Connected' : 'Disconnected'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Solar → Load</p>
            <p className={`font-semibold ${energy?.pv_to_load ? 'text-green-600' : 'text-gray-400'}`}>
              {energy?.pv_to_load ? 'Active' : 'Inactive'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Solar → Battery</p>
            <p className={`font-semibold ${energy?.pv_to_bat ? 'text-green-600' : 'text-gray-400'}`}>
              {energy?.pv_to_bat ? 'Charging' : 'Idle'}
            </p>
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>API Connection:</strong> {process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'}
        </p>
        <p className="text-xs text-blue-600 mt-1">Data refreshes every 30 seconds</p>
      </div>
    </div>
  )
}
