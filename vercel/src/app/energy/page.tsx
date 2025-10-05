'use client'

import { useEffect, useState } from 'react'
import { Battery, Sun, Zap, Activity, ArrowDown, ArrowUp, Minus } from 'lucide-react'

interface EnergyData {
  pv_power: number
  batt_power: number
  grid_power: number
  load_power: number
  soc: number
  pv_to_load: boolean
  pv_to_grid: boolean
  pv_to_bat: boolean
  battery_voltage?: number
  battery_current?: number
  battery_temp?: number
  grid_voltage?: number
}

export default function EnergyPage() {
  const [energy, setEnergy] = useState<EnergyData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'
        const res = await fetch(`${API_URL}/energy/latest`)

        if (res.ok) {
          const response = await res.json()
          setEnergy(response.data)
        }
      } catch (error) {
        console.error('Failed to fetch energy data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 10000) // Refresh every 10s
    return () => clearInterval(interval)
  }, [])

  const getBatteryDirection = () => {
    if (!energy) return { icon: Minus, text: 'Idle', color: 'text-gray-500' }
    if (energy.batt_power > 0) return { icon: ArrowDown, text: 'Charging', color: 'text-green-600' }
    if (energy.batt_power < 0) return { icon: ArrowUp, text: 'Discharging', color: 'text-orange-600' }
    return { icon: Minus, text: 'Idle', color: 'text-gray-500' }
  }

  const batteryDirection = getBatteryDirection()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Energy Details</h1>
        <p className="text-gray-600 mt-1">Real-time power flow and system metrics</p>
      </div>

      {/* Power Flow Diagram */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h2 className="text-xl font-semibold mb-6">Power Flow</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Solar */}
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 rounded-full bg-yellow-100 flex items-center justify-center mb-4">
              <Sun className="w-12 h-12 text-yellow-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Solar</h3>
            <p className="text-3xl font-bold text-yellow-600 mt-2">
              {loading ? '--' : `${energy?.pv_power.toLocaleString()}`}
            </p>
            <p className="text-sm text-gray-500">Watts</p>
            <div className="mt-3 flex flex-col gap-1 text-xs">
              {energy?.pv_to_load && <span className="text-blue-600">→ Load</span>}
              {energy?.pv_to_bat && <span className="text-green-600">→ Battery</span>}
              {energy?.pv_to_grid && <span className="text-purple-600">→ Grid</span>}
            </div>
          </div>

          {/* Battery */}
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center mb-4">
              <Battery className="w-12 h-12 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Battery</h3>
            <p className="text-3xl font-bold text-green-600 mt-2">
              {loading ? '--' : `${energy?.soc.toFixed(1)}%`}
            </p>
            <p className="text-sm text-gray-500">State of Charge</p>
            <div className="mt-3 flex items-center gap-2">
              <batteryDirection.icon className={`w-5 h-5 ${batteryDirection.color}`} />
              <span className={`text-sm font-medium ${batteryDirection.color}`}>
                {batteryDirection.text}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {Math.abs(energy?.batt_power || 0)}W
            </p>
          </div>

          {/* Load */}
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center mb-4">
              <Zap className="w-12 h-12 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Load</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">
              {loading ? '--' : `${energy?.load_power.toLocaleString()}`}
            </p>
            <p className="text-sm text-gray-500">Watts</p>
          </div>
        </div>

        {/* Grid at bottom */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="flex flex-col items-center">
            <div className="w-20 h-20 rounded-full bg-purple-100 flex items-center justify-center mb-3">
              <Activity className="w-10 h-10 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Grid</h3>
            <p className="text-2xl font-bold text-purple-600 mt-2">
              {loading ? '--' : `${Math.abs(energy?.grid_power || 0).toLocaleString()}`}
            </p>
            <p className="text-sm text-gray-500">
              Watts {(energy?.grid_power || 0) > 0 ? 'Importing' : (energy?.grid_power || 0) < 0 ? 'Exporting' : ''}
            </p>
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Battery Details */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Battery className="w-6 h-6 text-green-600" />
            Battery Details
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">State of Charge</span>
              <span className="font-semibold text-gray-900">{energy?.soc.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Power</span>
              <span className="font-semibold text-gray-900">{energy?.batt_power.toFixed(0)}W</span>
            </div>
            {energy?.battery_voltage !== undefined && (
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-gray-600">Voltage</span>
                <span className="font-semibold text-gray-900">{energy.battery_voltage.toFixed(1)}V</span>
              </div>
            )}
            {energy?.battery_current !== undefined && (
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-gray-600">Current</span>
                <span className="font-semibold text-gray-900">{energy.battery_current.toFixed(1)}A</span>
              </div>
            )}
            {energy?.battery_temp !== undefined && (
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-gray-600">Temperature</span>
                <span className="font-semibold text-gray-900">{energy.battery_temp.toFixed(1)}°C</span>
              </div>
            )}
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Direction</span>
              <span className={`font-semibold ${batteryDirection.color}`}>
                {batteryDirection.text}
              </span>
            </div>
          </div>
        </div>

        {/* Solar Details */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Sun className="w-6 h-6 text-yellow-600" />
            Solar Production
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Current Power</span>
              <span className="font-semibold text-gray-900">{energy?.pv_power.toLocaleString()}W</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">To Load</span>
              <span className={`font-semibold ${energy?.pv_to_load ? 'text-green-600' : 'text-gray-400'}`}>
                {energy?.pv_to_load ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">To Battery</span>
              <span className={`font-semibold ${energy?.pv_to_bat ? 'text-green-600' : 'text-gray-400'}`}>
                {energy?.pv_to_bat ? 'Charging' : 'Not Charging'}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">To Grid</span>
              <span className={`font-semibold ${energy?.pv_to_grid ? 'text-green-600' : 'text-gray-400'}`}>
                {energy?.pv_to_grid ? 'Exporting' : 'Not Exporting'}
              </span>
            </div>
          </div>
        </div>

        {/* Load Details */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-6 h-6 text-blue-600" />
            Load Consumption
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Current Load</span>
              <span className="font-semibold text-gray-900">{energy?.load_power.toLocaleString()}W</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Load in kW</span>
              <span className="font-semibold text-gray-900">{((energy?.load_power || 0) / 1000).toFixed(2)}kW</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Status</span>
              <span className="font-semibold text-blue-600">Active</span>
            </div>
          </div>
        </div>

        {/* Grid Details */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-6 h-6 text-purple-600" />
            Grid Connection
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Grid Power</span>
              <span className="font-semibold text-gray-900">{Math.abs(energy?.grid_power || 0).toLocaleString()}W</span>
            </div>
            {energy?.grid_voltage !== undefined && (
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-gray-600">Grid Voltage</span>
                <span className="font-semibold text-gray-900">{energy.grid_voltage.toFixed(1)}V</span>
              </div>
            )}
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">Direction</span>
              <span className={`font-semibold ${(energy?.grid_power || 0) > 0 ? 'text-orange-600' : (energy?.grid_power || 0) < 0 ? 'text-green-600' : 'text-gray-400'}`}>
                {(energy?.grid_power || 0) > 0 ? 'Importing' : (energy?.grid_power || 0) < 0 ? 'Exporting' : 'Balanced'}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Status</span>
              <span className="font-semibold text-green-600">Connected</span>
            </div>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">System Insights</h2>
        <div className="space-y-3">
          {energy && (
            <>
              {energy.soc > 80 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-green-800">
                  ✅ Battery is well charged ({energy.soc.toFixed(1)}%)
                </div>
              )}
              {energy.soc <= 80 && energy.soc > 50 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-yellow-800">
                  🟡 Battery is at moderate level ({energy.soc.toFixed(1)}%)
                </div>
              )}
              {energy.soc <= 50 && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-orange-800">
                  ⚠️ Battery is low ({energy.soc.toFixed(1)}%) - consider charging
                </div>
              )}
              {energy.pv_power > energy.load_power && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-blue-800">
                  ☀️ Solar surplus: {(energy.pv_power - energy.load_power).toFixed(0)}W available for battery charging or export
                </div>
              )}
              {energy.pv_power > 0 && energy.pv_power <= energy.load_power && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-blue-800">
                  ⚡ Solar is active but not covering full load
                </div>
              )}
              {energy.pv_power === 0 && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-700">
                  🌙 No solar production (nighttime or cloudy)
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          Data refreshes every 10 seconds. Last updated: {new Date().toLocaleTimeString()}
        </p>
      </div>
    </div>
  )
}
