'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Battery, Sun, Zap, TrendingUp } from 'lucide-react'

interface EnergyStats {
  timestamp: string
  battery_soc: number
  solar_power: number
  load_power: number
  battery_power: number
  grid_power: number
}

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState(24)
  const [data, setData] = useState<EnergyStats[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    avgSoc: 0,
    maxSolar: 0,
    avgLoad: 0,
    totalEnergy: 0
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'
        const res = await fetch(`${API_URL}/energy/stats?hours=${timeRange}`)

        if (res.ok) {
          const response = await res.json()
          const energyData = response.data || []

          setData(energyData)

          // Calculate statistics
          if (energyData.length > 0) {
            const avgSoc = energyData.reduce((sum: number, d: EnergyStats) => sum + d.battery_soc, 0) / energyData.length
            const maxSolar = Math.max(...energyData.map((d: EnergyStats) => d.solar_power))
            const avgLoad = energyData.reduce((sum: number, d: EnergyStats) => sum + d.load_power, 0) / energyData.length
            const totalEnergy = energyData.reduce((sum: number, d: EnergyStats) => sum + d.solar_power, 0) / 1000

            setStats({ avgSoc, maxSolar, avgLoad, totalEnergy })
          }
        }
      } catch (error) {
        console.error('Failed to fetch energy stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [timeRange])

  // Format data for charts
  const chartData = data.map(d => ({
    time: new Date(d.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }),
    soc: d.battery_soc,
    solar: d.solar_power,
    load: d.load_power,
    battery: d.battery_power,
    grid: d.grid_power
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Energy Dashboard</h1>
          <p className="text-gray-600 mt-1">Historical trends and analysis</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value={1}>Last 1 hour</option>
          <option value={6}>Last 6 hours</option>
          <option value={12}>Last 12 hours</option>
          <option value={24}>Last 24 hours</option>
          <option value={48}>Last 48 hours</option>
          <option value={72}>Last 72 hours</option>
        </select>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <Battery className="w-6 h-6 text-green-600" />
            <span className="text-sm font-medium text-gray-500">Avg Battery SOC</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {loading ? '--' : `${stats.avgSoc.toFixed(1)}%`}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <Sun className="w-6 h-6 text-yellow-500" />
            <span className="text-sm font-medium text-gray-500">Peak Solar</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {loading ? '--' : `${stats.maxSolar.toLocaleString()}W`}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <Zap className="w-6 h-6 text-blue-600" />
            <span className="text-sm font-medium text-gray-500">Avg Load</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {loading ? '--' : `${stats.avgLoad.toFixed(0)}W`}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-6 h-6 text-purple-600" />
            <span className="text-sm font-medium text-gray-500">Est. Solar Energy</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {loading ? '--' : `${stats.totalEnergy.toFixed(1)}kWh`}
          </div>
        </div>
      </div>

      {/* Battery SOC Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Battery State of Charge</h2>
        {loading ? (
          <div className="h-64 flex items-center justify-center text-gray-400">
            Loading chart data...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis label={{ value: 'SOC (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="soc"
                stroke="#10b981"
                strokeWidth={2}
                name="Battery SOC"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Power Flow Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold mb-4">Power Flow</h2>
        {loading ? (
          <div className="h-96 flex items-center justify-center text-gray-400">
            Loading chart data...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis label={{ value: 'Power (W)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="solar"
                stroke="#f59e0b"
                strokeWidth={2}
                name="Solar Production"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="load"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Load Consumption"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="battery"
                stroke="#10b981"
                strokeWidth={2}
                name="Battery Power"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="grid"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Grid Power"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          Showing {chartData.length} data points from the last {timeRange} hours
        </p>
      </div>
    </div>
  )
}
