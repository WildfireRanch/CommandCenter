'use client'

import { useEffect, useState } from 'react'
import { Battery, Sun, Zap, Activity, ArrowDown, ArrowUp, Minus, ThermometerSun, Gauge, TrendingUp, AlertCircle, BarChart3, DollarSign, Lightbulb, Clock } from 'lucide-react'
import { PowerFlowChart, SOCComparisonChart, BatteryVoltageChart, BatteryCurrentChart, BatteryTemperatureChart } from '@/components/energy/HistoricalCharts'
import { TimeRangeSelector } from '@/components/energy/TimeRangeSelector'
import { AnalyticsSection } from '@/components/energy/AnalyticsSection'
import { CostTracking } from '@/components/energy/CostTracking'
import { PredictiveAnalytics } from '@/components/energy/PredictiveAnalytics'
import { ExcessEnergyDashboard } from '@/components/energy/ExcessEnergyDashboard'

interface SolArkData {
  pv_power: number
  batt_power: number
  grid_power: number
  load_power: number
  soc: number
  pv_to_load: boolean
  pv_to_grid: boolean
  pv_to_bat: boolean
}

interface VictronData {
  timestamp: string
  installation_id: string
  soc: number
  voltage: number
  current: number
  power: number
  state: 'charging' | 'discharging' | 'idle'
  temperature: number
}

interface VictronHealth {
  poller_running: boolean
  last_poll_attempt: string
  last_successful_poll: string
  consecutive_failures: number
  is_healthy: boolean
  readings_count_24h: number
  api_requests_this_hour: number
  rate_limit_max: number
}

export default function EnergyPage() {
  const [activeTab, setActiveTab] = useState('realtime')
  const [solark, setSolark] = useState<SolArkData | null>(null)
  const [victron, setVictron] = useState<VictronData | null>(null)
  const [victronHealth, setVictronHealth] = useState<VictronHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  // Analytics state
  const [timeRange, setTimeRange] = useState('24')
  const [historicalData, setHistoricalData] = useState<any>(null)
  const [dailyAnalytics, setDailyAnalytics] = useState<any>(null)
  const [costData, setCostData] = useState<any>(null)
  const [predictions, setPredictions] = useState<any>(null)
  const [excessData, setExcessData] = useState<any>(null)
  const [loadOpportunities, setLoadOpportunities] = useState<any>(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)

  // Cost tracking state
  const [importRate, setImportRate] = useState(0.12)
  const [exportRate, setExportRate] = useState(0.08)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'

  useEffect(() => {
    const fetchRealtimeData = async () => {
      try {
        // Fetch SolArk data
        const solarkRes = await fetch(`${API_URL}/energy/latest`)
        if (solarkRes.ok) {
          const response = await solarkRes.json()
          setSolark(response.data)
        }

        // Fetch Victron data
        const victronRes = await fetch(`${API_URL}/victron/battery/current`)
        if (victronRes.ok) {
          const response = await victronRes.json()
          setVictron(response.data)
        }

        // Fetch Victron health
        const healthRes = await fetch(`${API_URL}/victron/health`)
        if (healthRes.ok) {
          const response = await healthRes.json()
          setVictronHealth(response.data)
        }

        setLastUpdate(new Date())
      } catch (error) {
        console.error('Failed to fetch energy data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchRealtimeData()
    const interval = setInterval(fetchRealtimeData, 10000) // Refresh every 10s
    return () => clearInterval(interval)
  }, [API_URL])

  // Fetch analytics data when tab changes
  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistoricalData()
    } else if (activeTab === 'analytics') {
      fetchDailyAnalytics()
    } else if (activeTab === 'cost') {
      fetchCostData()
    } else if (activeTab === 'predictions') {
      fetchPredictions()
    } else if (activeTab === 'excess') {
      fetchExcessData()
      fetchLoadOpportunities()
    }
  }, [activeTab, timeRange, importRate, exportRate])

  const fetchHistoricalData = async () => {
    setAnalyticsLoading(true)
    try {
      const res = await fetch(`${API_URL}/energy/history?hours=${timeRange}&limit=1000`)
      if (res.ok) {
        const data = await res.json()
        setHistoricalData(data)
      }
    } catch (error) {
      console.error('Failed to fetch historical data:', error)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const fetchDailyAnalytics = async () => {
    setAnalyticsLoading(true)
    try {
      const days = parseInt(timeRange) <= 168 ? 7 : 30
      const res = await fetch(`${API_URL}/energy/analytics/daily?days=${days}`)
      if (res.ok) {
        const data = await res.json()
        setDailyAnalytics(data)
      }
    } catch (error) {
      console.error('Failed to fetch daily analytics:', error)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const fetchCostData = async () => {
    setAnalyticsLoading(true)
    try {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - 30)

      const res = await fetch(
        `${API_URL}/energy/analytics/cost?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}&import_rate=${importRate}&export_rate=${exportRate}`
      )
      if (res.ok) {
        const data = await res.json()
        setCostData(data)
      }
    } catch (error) {
      console.error('Failed to fetch cost data:', error)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const fetchPredictions = async () => {
    setAnalyticsLoading(true)
    try {
      const res = await fetch(`${API_URL}/energy/predictions/soc?hours=24`)
      if (res.ok) {
        const data = await res.json()
        setPredictions(data)
      }
    } catch (error) {
      console.error('Failed to fetch predictions:', error)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const fetchExcessData = async () => {
    setAnalyticsLoading(true)
    try {
      const res = await fetch(`${API_URL}/energy/analytics/excess?hours=${timeRange}`)
      if (res.ok) {
        const data = await res.json()
        setExcessData(data)
      }
    } catch (error) {
      console.error('Failed to fetch excess data:', error)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const fetchLoadOpportunities = async () => {
    try {
      const res = await fetch(`${API_URL}/energy/analytics/load-opportunities`)
      if (res.ok) {
        const data = await res.json()
        setLoadOpportunities(data)
      }
    } catch (error) {
      console.error('Failed to fetch load opportunities:', error)
    }
  }

  const getBatteryDirection = (power: number) => {
    if (power > 0) return { icon: ArrowDown, text: 'Charging', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' }
    if (power < 0) return { icon: ArrowUp, text: 'Discharging', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' }
    return { icon: Minus, text: 'Idle', color: 'text-gray-500', bg: 'bg-gray-50', border: 'border-gray-200' }
  }

  const getVictronState = () => {
    if (!victron) return getBatteryDirection(0)
    return getBatteryDirection(victron.power)
  }

  const getSolArkState = () => {
    if (!solark) return getBatteryDirection(0)
    return getBatteryDirection(solark.batt_power)
  }

  const getBatteryHealthColor = (soc: number) => {
    if (soc > 80) return 'text-green-600'
    if (soc > 50) return 'text-yellow-600'
    if (soc > 20) return 'text-orange-600'
    return 'text-red-600'
  }

  const getTemperatureColor = (temp: number) => {
    if (temp >= 15 && temp <= 30) return 'text-green-600'
    if (temp > 30 && temp <= 40) return 'text-yellow-600'
    return 'text-orange-600'
  }

  const victronState = getVictronState()
  const solarkState = getSolArkState()

  const tabs = [
    { id: 'realtime', label: 'Real-time', icon: Activity },
    { id: 'history', label: 'Historical Trends', icon: TrendingUp },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'cost', label: 'Cost Tracking', icon: DollarSign },
    { id: 'predictions', label: 'Predictions', icon: Clock },
    { id: 'excess', label: 'Excess Energy', icon: Lightbulb },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Energy Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor and optimize your solar energy system</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Last updated</p>
          <p className="text-sm font-medium text-gray-900">{lastUpdate.toLocaleTimeString()}</p>
        </div>
      </div>

      {/* System Health Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-gray-600" />
            <span className="font-semibold text-gray-900">Integration Status</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${solark ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">SolArk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${victronHealth?.is_healthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">Victron</span>
              {victronHealth && (
                <span className="text-xs text-gray-500">
                  ({victronHealth.readings_count_24h} readings/24h)
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-2">
        <div className="flex items-center gap-2 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'realtime' && (
        <div className="space-y-6">
          {/* Main Power Flow */}
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
                  {loading ? '--' : `${solark?.pv_power.toLocaleString()}`}
                </p>
                <p className="text-sm text-gray-500">Watts</p>
                <div className="mt-3 flex flex-col gap-1 text-xs">
                  {solark?.pv_to_load && <span className="text-blue-600">→ Load</span>}
                  {solark?.pv_to_bat && <span className="text-green-600">→ Battery</span>}
                  {solark?.pv_to_grid && <span className="text-purple-600">→ Grid</span>}
                </div>
              </div>

              {/* Battery - Combined View */}
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center mb-4">
                  <Battery className="w-12 h-12 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Battery</h3>
                {victron ? (
                  <>
                    <p className={`text-3xl font-bold mt-2 ${getBatteryHealthColor(victron.soc)}`}>
                      {victron.soc.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500">Victron (Accurate)</p>
                    {solark && Math.abs(victron.soc - solark.soc) > 2 && (
                      <p className="text-xs text-orange-600 mt-1">
                        SolArk: {solark.soc.toFixed(1)}% (±{Math.abs(victron.soc - solark.soc).toFixed(1)}%)
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <p className={`text-3xl font-bold mt-2 ${solark ? getBatteryHealthColor(solark.soc) : 'text-gray-400'}`}>
                      {loading ? '--' : `${solark?.soc.toFixed(1)}%`}
                    </p>
                    <p className="text-xs text-gray-500">SolArk (Estimated)</p>
                  </>
                )}
                <div className="mt-3 flex items-center gap-2">
                  <victronState.icon className={`w-5 h-5 ${victronState.color}`} />
                  <span className={`text-sm font-medium ${victronState.color}`}>
                    {victronState.text}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {victron ? `${Math.abs(victron.power)}W` : `${Math.abs(solark?.batt_power || 0)}W`}
                </p>
              </div>

              {/* Load */}
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center mb-4">
                  <Zap className="w-12 h-12 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Load</h3>
                <p className="text-3xl font-bold text-blue-600 mt-2">
                  {loading ? '--' : `${solark?.load_power.toLocaleString()}`}
                </p>
                <p className="text-sm text-gray-500">Watts</p>
                <p className="text-xs text-gray-600 mt-2">
                  {((solark?.load_power || 0) / 1000).toFixed(2)} kW
                </p>
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
                  {loading ? '--' : `${Math.abs(solark?.grid_power || 0).toLocaleString()}`}
                </p>
                <p className="text-sm text-gray-500">
                  Watts {(solark?.grid_power || 0) > 0 ? 'Importing' : (solark?.grid_power || 0) < 0 ? 'Exporting' : ''}
                </p>
              </div>
            </div>
          </div>

          {/* Detailed Battery Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Victron Battery (Accurate) */}
            {victron && (
              <div className="bg-gradient-to-br from-blue-50 to-white rounded-lg shadow-sm border border-blue-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <Battery className="w-6 h-6 text-blue-600" />
                    Victron Battery
                  </h2>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                    ACCURATE
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b border-blue-100">
                    <span className="text-gray-600 flex items-center gap-2">
                      <Gauge className="w-4 h-4" />
                      State of Charge
                    </span>
                    <span className={`font-semibold text-lg ${getBatteryHealthColor(victron.soc)}`}>
                      {victron.soc.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-blue-100">
                    <span className="text-gray-600 flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      Voltage
                    </span>
                    <span className="font-semibold text-gray-900">{victron.voltage.toFixed(2)}V</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-blue-100">
                    <span className="text-gray-600 flex items-center gap-2">
                      <Activity className="w-4 h-4" />
                      Current
                    </span>
                    <span className="font-semibold text-gray-900">{victron.current.toFixed(1)}A</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-blue-100">
                    <span className="text-gray-600 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Power
                    </span>
                    <span className="font-semibold text-gray-900">{victron.power.toFixed(0)}W</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-blue-100">
                    <span className="text-gray-600 flex items-center gap-2">
                      <ThermometerSun className="w-4 h-4" />
                      Temperature
                    </span>
                    <span className={`font-semibold ${getTemperatureColor(victron.temperature)}`}>
                      {victron.temperature.toFixed(1)}°C ({((victron.temperature * 9/5) + 32).toFixed(1)}°F)
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600">State</span>
                    <span className={`font-semibold px-3 py-1 rounded-full text-sm ${victronState.bg} ${victronState.color} ${victronState.border} border`}>
                      {victron.state.charAt(0).toUpperCase() + victron.state.slice(1)}
                    </span>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-blue-100">
                  <p className="text-xs text-gray-500">
                    Data Source: Victron Cerbo GX (Direct Shunt Measurement)
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Last Reading: {new Date(victron.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            )}

            {/* SolArk Battery (Estimated) */}
            {solark && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <Battery className="w-6 h-6 text-green-600" />
                    SolArk Battery
                  </h2>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full font-medium">
                    ESTIMATED
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600 flex items-center gap-2">
                      <Gauge className="w-4 h-4" />
                      State of Charge
                    </span>
                    <span className={`font-semibold text-lg ${getBatteryHealthColor(solark.soc)}`}>
                      {solark.soc.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-gray-100">
                    <span className="text-gray-600 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Power
                    </span>
                    <span className="font-semibold text-gray-900">{solark.batt_power.toFixed(0)}W</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600">State</span>
                    <span className={`font-semibold px-3 py-1 rounded-full text-sm ${solarkState.bg} ${solarkState.color} ${solarkState.border} border`}>
                      {solarkState.text}
                    </span>
                  </div>

                  {/* Comparison Alert */}
                  {victron && Math.abs(victron.soc - solark.soc) > 2 && (
                    <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5" />
                        <div>
                          <p className="text-xs font-medium text-yellow-800">SOC Difference Detected</p>
                          <p className="text-xs text-yellow-700 mt-1">
                            {Math.abs(victron.soc - solark.soc).toFixed(1)}% difference from Victron reading.
                            Victron provides more accurate data via direct shunt measurement.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <p className="text-xs text-gray-500">
                    Data Source: SolArk Inverter (Calculated Estimate)
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* System Insights */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">System Insights</h2>
            <div className="space-y-3">
              {solark && victron && (
                <>
                  {victron.soc > 80 && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-green-800">
                      ✅ Battery is well charged ({victron.soc.toFixed(1)}%)
                    </div>
                  )}
                  {victron.soc <= 80 && victron.soc > 50 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-yellow-800">
                      🟡 Battery is at moderate level ({victron.soc.toFixed(1)}%)
                    </div>
                  )}
                  {victron.soc <= 50 && victron.soc > 20 && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-orange-800">
                      ⚠️ Battery is low ({victron.soc.toFixed(1)}%) - consider charging
                    </div>
                  )}
                  {victron.soc <= 20 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-800">
                      🚨 Battery critically low ({victron.soc.toFixed(1)}%) - charging recommended
                    </div>
                  )}
                  {victron.temperature > 35 && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-orange-800">
                      🌡️ Battery temperature elevated ({victron.temperature.toFixed(1)}°C) - monitor closely
                    </div>
                  )}
                  {solark.pv_power > solark.load_power && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-blue-800">
                      ☀️ Solar surplus: {(solark.pv_power - solark.load_power).toFixed(0)}W available for battery charging or export
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Historical Trends</h2>
            <TimeRangeSelector selected={timeRange} onChange={setTimeRange} />
          </div>

          {analyticsLoading ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <p className="text-gray-500">Loading historical data...</p>
            </div>
          ) : historicalData && historicalData.data && historicalData.data.length > 0 ? (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4">Power Flow Over Time</h3>
                <PowerFlowChart data={historicalData.data} />
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4">Battery SOC Comparison</h3>
                <SOCComparisonChart data={historicalData.data} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold mb-4">Battery Voltage</h3>
                  <BatteryVoltageChart data={historicalData.data} />
                </div>

                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold mb-4">Battery Current</h3>
                  <BatteryCurrentChart data={historicalData.data} />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-4">Battery Temperature</h3>
                <BatteryTemperatureChart data={historicalData.data} />
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <p className="text-gray-500">No historical data available</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Energy Analytics</h2>
          </div>
          {dailyAnalytics && dailyAnalytics.data ? (
            <AnalyticsSection data={dailyAnalytics.data} period="daily" />
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <p className="text-gray-500">Loading analytics...</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'cost' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Cost Tracking</h2>
          </div>
          <CostTracking
            data={costData}
            loading={analyticsLoading}
            onUpdateRates={(newImport, newExport) => {
              setImportRate(newImport)
              setExportRate(newExport)
            }}
          />
        </div>
      )}

      {activeTab === 'predictions' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Predictive Analytics</h2>
          </div>
          <PredictiveAnalytics data={predictions} loading={analyticsLoading} />
        </div>
      )}

      {activeTab === 'excess' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">⚡ Excess Energy & Load Opportunities</h2>
            <TimeRangeSelector selected={timeRange} onChange={setTimeRange} />
          </div>
          <ExcessEnergyDashboard
            excessData={excessData}
            loadOpportunities={loadOpportunities}
            loading={analyticsLoading}
          />
        </div>
      )}
    </div>
  )
}
