'use client'

import { AlertTriangle, Zap, Clock, TrendingUp, Lightbulb, AlertCircle } from 'lucide-react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format, parseISO } from 'date-fns'

interface ExcessTimeSeriesPoint {
  timestamp: string
  excess_power: number
  soc: number
}

interface LoadOpportunity {
  type: string
  load: string
  action: string
  power_available?: number
  scheduled_time?: string
  reason: string
  priority: string
  duration_estimate: string
}

interface ExcessData {
  period: {
    hours: number
    start: string
    end: string
  }
  summary: {
    total_excess_kwh: number
    avg_excess_power_w: number
    peak_excess_power_w: number
    potential_value_usd: number
    data_points: number
  }
  time_series: ExcessTimeSeriesPoint[]
  peak_excess_times: Array<{
    timestamp: string
    excess_power: number
    soc: number
  }>
  hourly_patterns: Record<string, number>
  recommendations: {
    best_load_hours: Array<{
      hour: string
      avg_excess_w: number
      potential_kwh_daily: number
    }>
    suggested_actions: Array<{
      priority: string
      action: string
      details: string
      potential_revenue?: string
      potential_savings?: string
    }>
  }
}

interface ExcessEnergyDashboardProps {
  excessData: ExcessData | null
  loadOpportunities: {
    current_status: {
      solar_power_w: number
      load_power_w: number
      battery_soc_pct: number
      excess_power_w: number
      grid_power_w: number
    }
    solar_forecast_6h: Array<{
      hour: number
      predicted_solar_w: number
    }>
    opportunities: LoadOpportunity[]
    summary: {
      total_opportunities: number
      immediate_actions: number
      scheduled_actions: number
      warnings: number
    }
  } | null
  loading: boolean
}

export function ExcessEnergyDashboard({ excessData, loadOpportunities, loading }: ExcessEnergyDashboardProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">Loading excess energy data...</p>
      </div>
    )
  }

  if (!excessData) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">No excess energy data available</p>
      </div>
    )
  }

  // Prepare chart data
  const timeSeriesChart = excessData.time_series.map(point => ({
    time: format(parseISO(point.timestamp), 'HH:mm'),
    excess: point.excess_power,
    soc: point.soc
  }))

  const hourlyPatternsChart = Object.entries(excessData.hourly_patterns).map(([hour, excess]) => ({
    hour,
    excess: excess
  }))

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-100 border-red-200'
      case 'medium': return 'text-yellow-600 bg-yellow-100 border-yellow-200'
      case 'low': return 'text-blue-600 bg-blue-100 border-blue-200'
      default: return 'text-gray-600 bg-gray-100 border-gray-200'
    }
  }

  const getActionIcon = (action: string) => {
    if (action.includes('Bitcoin') || action.includes('Miner')) return '₿'
    if (action.includes('Irrigation')) return '💧'
    if (action.includes('Water')) return '🔥'
    if (action.includes('EV') || action.includes('Charging')) return '🔌'
    return '⚡'
  }

  return (
    <div className="space-y-6">
      {/* Critical Alert Banner */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-600 rounded-lg p-6">
        <div className="flex items-start gap-4">
          <AlertTriangle className="w-8 h-8 text-red-600 flex-shrink-0 mt-1" />
          <div>
            <h2 className="text-xl font-bold text-red-900 mb-2">
              ⚡ EXCESS ENERGY DETECTED: {excessData.summary.total_excess_kwh} kWh WASTED
            </h2>
            <p className="text-red-800 text-sm mb-3">
              You're wasting <strong>{excessData.summary.total_excess_kwh} kWh</strong> of solar energy that could be harnessed for additional loads.
              This represents <strong>${excessData.summary.potential_value_usd}</strong> in lost opportunity value.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
              <div className="bg-white rounded-lg p-3">
                <div className="text-gray-600 text-xs">Peak Excess Power</div>
                <div className="text-red-700 font-bold text-lg">{excessData.summary.peak_excess_power_w.toLocaleString()} W</div>
              </div>
              <div className="bg-white rounded-lg p-3">
                <div className="text-gray-600 text-xs">Average Excess Power</div>
                <div className="text-red-700 font-bold text-lg">{excessData.summary.avg_excess_power_w.toLocaleString()} W</div>
              </div>
              <div className="bg-white rounded-lg p-3">
                <div className="text-gray-600 text-xs">Potential Value</div>
                <div className="text-red-700 font-bold text-lg">${excessData.summary.potential_value_usd}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Current Status & Load Opportunities */}
      {loadOpportunities && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-6 h-6 text-blue-600" />
            Current Status & Opportunities
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
              <div className="text-xs text-gray-600">Solar Power</div>
              <div className="text-lg font-bold text-yellow-700">
                {loadOpportunities.current_status.solar_power_w.toLocaleString()} W
              </div>
            </div>
            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <div className="text-xs text-gray-600">Load Power</div>
              <div className="text-lg font-bold text-blue-700">
                {loadOpportunities.current_status.load_power_w.toLocaleString()} W
              </div>
            </div>
            <div className="bg-green-50 rounded-lg p-3 border border-green-200">
              <div className="text-xs text-gray-600">Battery SOC</div>
              <div className="text-lg font-bold text-green-700">
                {loadOpportunities.current_status.battery_soc_pct.toFixed(1)}%
              </div>
            </div>
            <div className="bg-red-50 rounded-lg p-3 border border-red-200">
              <div className="text-xs text-gray-600">Excess Power</div>
              <div className="text-lg font-bold text-red-700">
                {loadOpportunities.current_status.excess_power_w.toLocaleString()} W
              </div>
            </div>
            <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
              <div className="text-xs text-gray-600">Grid Power</div>
              <div className="text-lg font-bold text-purple-700">
                {loadOpportunities.current_status.grid_power_w.toLocaleString()} W
              </div>
            </div>
          </div>

          {/* Load Opportunities */}
          <div className="space-y-3">
            {loadOpportunities.opportunities.length === 0 ? (
              <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
                No immediate load opportunities detected
              </div>
            ) : (
              loadOpportunities.opportunities.map((opp, idx) => (
                <div
                  key={idx}
                  className={`border-2 rounded-lg p-4 ${
                    opp.type === 'warning' ? 'bg-red-50 border-red-300' :
                    opp.type === 'immediate' ? 'bg-green-50 border-green-300' :
                    'bg-blue-50 border-blue-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="text-3xl">{getActionIcon(opp.load)}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-gray-900">{opp.load}</h4>
                          <span className={`text-xs font-medium px-2 py-1 rounded-full ${getPriorityColor(opp.priority)}`}>
                            {opp.priority.toUpperCase()}
                          </span>
                          <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                            opp.type === 'immediate' ? 'bg-green-600 text-white' :
                            opp.type === 'scheduled' ? 'bg-blue-600 text-white' :
                            'bg-red-600 text-white'
                          }`}>
                            {opp.type.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mb-2">{opp.reason}</p>
                        <div className="flex items-center gap-4 text-xs text-gray-600">
                          {opp.power_available !== undefined && (
                            <span>⚡ {opp.power_available.toLocaleString()} W available</span>
                          )}
                          {opp.scheduled_time && (
                            <span>🕐 Schedule at {opp.scheduled_time}</span>
                          )}
                          <span>⏱️ {opp.duration_estimate}</span>
                        </div>
                      </div>
                    </div>
                    <div className={`text-2xl font-bold px-4 py-2 rounded-lg ${
                      opp.action === 'START' ? 'bg-green-600 text-white' :
                      opp.action === 'STOP' ? 'bg-red-600 text-white' :
                      'bg-blue-600 text-white'
                    }`}>
                      {opp.action}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Excess Energy Time Series */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Excess Energy Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={timeSeriesChart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              label={{ value: 'Excess Power (W)', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
              formatter={(value: number) => `${value.toLocaleString()} W`}
            />
            <Area
              type="monotone"
              dataKey="excess"
              stroke="#ef4444"
              fill="#fecaca"
              strokeWidth={2}
              name="Excess Power (Wasted)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Hourly Patterns */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Best Hours for Load Scheduling</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={hourlyPatternsChart}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="hour"
              tick={{ fontSize: 12 }}
            />
            <YAxis
              label={{ value: 'Avg Excess Power (W)', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
              formatter={(value: number) => `${value.toLocaleString()} W`}
            />
            <Bar
              dataKey="excess"
              fill="#f59e0b"
              name="Average Excess Power"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recommended Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Lightbulb className="w-6 h-6 text-yellow-600" />
          Recommended Actions to Capture Excess Energy
        </h3>
        <div className="space-y-3">
          {excessData.recommendations.suggested_actions.length === 0 ? (
            <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
              No recommendations available. Excess energy is minimal.
            </div>
          ) : (
            excessData.recommendations.suggested_actions.map((action, idx) => (
              <div
                key={idx}
                className={`border-l-4 rounded-lg p-4 ${
                  action.priority === 'high' ? 'bg-red-50 border-red-600' :
                  action.priority === 'medium' ? 'bg-yellow-50 border-yellow-600' :
                  'bg-blue-50 border-blue-600'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold text-gray-900">{action.action}</h4>
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${getPriorityColor(action.priority)}`}>
                        {action.priority.toUpperCase()} PRIORITY
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{action.details}</p>
                    <div className="flex items-center gap-4 text-sm">
                      {action.potential_revenue && (
                        <span className="text-green-700 font-medium">
                          💰 {action.potential_revenue}
                        </span>
                      )}
                      {action.potential_savings && (
                        <span className="text-blue-700 font-medium">
                          💵 {action.potential_savings}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Best Load Hours Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Clock className="w-6 h-6 text-blue-600" />
          Optimal Load Scheduling Hours
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hour</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg Excess Power</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Daily Potential</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {excessData.recommendations.best_load_hours.map((hour, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{hour.hour}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {hour.avg_excess_w.toLocaleString()} W
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-green-600 font-medium">
                    {hour.potential_kwh_daily} kWh
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-orange-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-orange-900 mb-1">About Excess Energy</h4>
            <p className="text-sm text-orange-800">
              Excess energy represents solar power that is <strong>not being used</strong> for loads or battery charging.
              This energy is typically curtailed by the inverter or exported to the grid at low rates. By running additional
              loads during these times, you can maximize your solar investment and reduce waste.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
