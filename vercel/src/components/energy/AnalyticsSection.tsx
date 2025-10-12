'use client'

import { Sun, Battery, Zap, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

interface DailyStats {
  date: string
  total_solar_kwh: number
  total_load_kwh: number
  battery_charging_kwh: number
  grid_import_kwh: number
  grid_export_kwh: number
  excess_energy_kwh: number
  excess_energy_pct: number
  excess_value_usd: number
  solar_self_consumption_pct: number
  grid_independence_pct: number
  avg_soc: number
  min_soc: number
  max_soc: number
  peak_solar: number
  avg_solar: number
}

interface AnalyticsSectionProps {
  data: DailyStats[]
  period: 'daily' | 'weekly' | 'monthly'
}

export function AnalyticsSection({ data, period }: AnalyticsSectionProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">No analytics data available</p>
      </div>
    )
  }

  // Calculate summary from all data
  const summary = {
    totalSolar: data.reduce((sum, d) => sum + d.total_solar_kwh, 0),
    totalLoad: data.reduce((sum, d) => sum + d.total_load_kwh, 0),
    totalExcess: data.reduce((sum, d) => sum + d.excess_energy_kwh, 0),
    totalGridImport: data.reduce((sum, d) => sum + d.grid_import_kwh, 0),
    totalGridExport: data.reduce((sum, d) => sum + d.grid_export_kwh, 0),
    avgSelfConsumption: data.reduce((sum, d) => sum + d.solar_self_consumption_pct, 0) / data.length,
    avgGridIndependence: data.reduce((sum, d) => sum + d.grid_independence_pct, 0) / data.length,
    totalExcessValue: data.reduce((sum, d) => sum + d.excess_value_usd, 0),
  }

  // Prepare chart data (reverse for chronological order)
  const chartData = [...data].reverse().map(d => ({
    date: format(new Date(d.date), 'MMM d'),
    solar: d.total_solar_kwh,
    load: d.total_load_kwh,
    excess: d.excess_energy_kwh,
    import: d.grid_import_kwh,
    export: d.grid_export_kwh,
  }))

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Solar Production */}
        <div className="bg-gradient-to-br from-yellow-50 to-white rounded-lg shadow-sm border border-yellow-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <Sun className="w-8 h-8 text-yellow-600" />
            <TrendingUp className="w-5 h-5 text-green-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{summary.totalSolar.toFixed(1)} kWh</div>
          <div className="text-sm text-gray-600">Total Solar Production</div>
          <div className="text-xs text-gray-500 mt-1">
            {(summary.totalSolar / data.length).toFixed(1)} kWh/day avg
          </div>
        </div>

        {/* Total Load Consumption */}
        <div className="bg-gradient-to-br from-blue-50 to-white rounded-lg shadow-sm border border-blue-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <Zap className="w-8 h-8 text-blue-600" />
            <TrendingDown className="w-5 h-5 text-orange-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{summary.totalLoad.toFixed(1)} kWh</div>
          <div className="text-sm text-gray-600">Total Load Consumption</div>
          <div className="text-xs text-gray-500 mt-1">
            {(summary.totalLoad / data.length).toFixed(1)} kWh/day avg
          </div>
        </div>

        {/* Excess Energy */}
        <div className="bg-gradient-to-br from-red-50 to-white rounded-lg shadow-sm border border-red-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <span className="text-xs font-semibold text-red-600 bg-red-100 px-2 py-1 rounded">WASTED</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{summary.totalExcess.toFixed(1)} kWh</div>
          <div className="text-sm text-gray-600">Excess Energy (Wasted)</div>
          <div className="text-xs text-red-600 mt-1">
            Potential value: ${summary.totalExcessValue.toFixed(2)}
          </div>
        </div>

        {/* Battery Stats */}
        <div className="bg-gradient-to-br from-green-50 to-white rounded-lg shadow-sm border border-green-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <Battery className="w-8 h-8 text-green-600" />
            <span className="text-xs font-semibold text-green-600 bg-green-100 px-2 py-1 rounded">
              {summary.avgGridIndependence.toFixed(0)}%
            </span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            {summary.avgSelfConsumption.toFixed(0)}%
          </div>
          <div className="text-sm text-gray-600">Solar Self-Consumption</div>
          <div className="text-xs text-gray-500 mt-1">
            Grid Independence: {summary.avgGridIndependence.toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Energy Production & Consumption Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Energy Production & Consumption</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
            />
            <YAxis
              label={{ value: 'Energy (kWh)', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
              formatter={(value: number) => `${value.toFixed(2)} kWh`}
            />
            <Legend />
            <Bar dataKey="solar" fill="#fbbf24" name="Solar Production" />
            <Bar dataKey="load" fill="#3b82f6" name="Load Consumption" />
            <Bar dataKey="excess" fill="#ef4444" name="Excess (Wasted)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Grid Activity Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Grid Import/Export</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
            />
            <YAxis
              label={{ value: 'Energy (kWh)', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
              formatter={(value: number) => `${value.toFixed(2)} kWh`}
            />
            <Legend />
            <Bar dataKey="import" fill="#f59e0b" name="Grid Import" />
            <Bar dataKey="export" fill="#10b981" name="Grid Export" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Daily Details Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Daily Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Solar</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Load</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Excess</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Self-Cons %</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg SOC</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((day, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {format(new Date(day.date), 'MMM d, yyyy')}
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {day.total_solar_kwh.toFixed(1)} kWh
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {day.total_load_kwh.toFixed(1)} kWh
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-medium text-red-600">
                    {day.excess_energy_kwh.toFixed(1)} kWh
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-green-600 font-medium">
                    {day.solar_self_consumption_pct.toFixed(0)}%
                  </td>
                  <td className="px-4 py-3 text-sm text-right text-gray-900">
                    {day.avg_soc.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
