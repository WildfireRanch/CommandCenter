'use client'

import { DollarSign, TrendingUp, TrendingDown, PiggyBank } from 'lucide-react'

interface CostData {
  period: {
    start: string
    end: string
    days: number
  }
  energy: {
    solar_produced_kwh: number
    load_consumed_kwh: number
    grid_import_kwh: number
    grid_export_kwh: number
    solar_self_consumed_kwh: number
  }
  costs: {
    grid_import_cost: number
    grid_export_revenue: number
    solar_savings: number
    net_savings: number
  }
  rates: {
    import_rate_per_kwh: number
    export_rate_per_kwh: number
  }
  metrics: {
    solar_self_consumption_pct: number
    grid_independence_pct: number
  }
}

interface CostTrackingProps {
  data: CostData | null
  loading: boolean
  onUpdateRates: (importRate: number, exportRate: number) => void
}

export function CostTracking({ data, loading, onUpdateRates }: CostTrackingProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">Loading cost data...</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">No cost data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Net Savings */}
        <div className="bg-gradient-to-br from-green-50 to-white rounded-lg shadow-sm border border-green-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <PiggyBank className="w-8 h-8 text-green-600" />
            <TrendingUp className="w-5 h-5 text-green-600" />
          </div>
          <div className="text-2xl font-bold text-green-600">
            ${data.costs.net_savings.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">Net Savings</div>
          <div className="text-xs text-gray-500 mt-1">
            ${(data.costs.net_savings / data.period.days).toFixed(2)}/day
          </div>
        </div>

        {/* Solar Savings */}
        <div className="bg-gradient-to-br from-yellow-50 to-white rounded-lg shadow-sm border border-yellow-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="w-8 h-8 text-yellow-600" />
            <span className="text-xs font-semibold text-yellow-700 bg-yellow-100 px-2 py-1 rounded">SAVED</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">
            ${data.costs.solar_savings.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">Solar Savings</div>
          <div className="text-xs text-gray-500 mt-1">
            From {data.energy.solar_self_consumed_kwh.toFixed(1)} kWh self-consumed
          </div>
        </div>

        {/* Grid Import Cost */}
        <div className="bg-gradient-to-br from-red-50 to-white rounded-lg shadow-sm border border-red-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <TrendingDown className="w-8 h-8 text-red-600" />
            <span className="text-xs font-semibold text-red-700 bg-red-100 px-2 py-1 rounded">COST</span>
          </div>
          <div className="text-2xl font-bold text-red-600">
            ${data.costs.grid_import_cost.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">Grid Import Cost</div>
          <div className="text-xs text-gray-500 mt-1">
            {data.energy.grid_import_kwh.toFixed(1)} kWh @ ${data.rates.import_rate_per_kwh}/kWh
          </div>
        </div>

        {/* Grid Export Revenue */}
        <div className="bg-gradient-to-br from-blue-50 to-white rounded-lg shadow-sm border border-blue-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="w-8 h-8 text-blue-600" />
            <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-1 rounded">REVENUE</span>
          </div>
          <div className="text-2xl font-bold text-blue-600">
            ${data.costs.grid_export_revenue.toFixed(2)}
          </div>
          <div className="text-sm text-gray-600">Grid Export Revenue</div>
          <div className="text-xs text-gray-500 mt-1">
            {data.energy.grid_export_kwh.toFixed(1)} kWh @ ${data.rates.export_rate_per_kwh}/kWh
          </div>
        </div>
      </div>

      {/* Energy Flow Breakdown */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Energy Flow Breakdown</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Production */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Production</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                <span className="text-sm text-gray-700">Solar Production</span>
                <span className="text-sm font-semibold text-gray-900">
                  {data.energy.solar_produced_kwh.toFixed(1)} kWh
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <span className="text-sm text-gray-700">Self-Consumed</span>
                <span className="text-sm font-semibold text-green-600">
                  {data.energy.solar_self_consumed_kwh.toFixed(1)} kWh ({data.metrics.solar_self_consumption_pct}%)
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                <span className="text-sm text-gray-700">Exported to Grid</span>
                <span className="text-sm font-semibold text-blue-600">
                  {data.energy.grid_export_kwh.toFixed(1)} kWh
                </span>
              </div>
            </div>
          </div>

          {/* Consumption */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Consumption</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-700">Total Load</span>
                <span className="text-sm font-semibold text-gray-900">
                  {data.energy.load_consumed_kwh.toFixed(1)} kWh
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <span className="text-sm text-gray-700">From Solar</span>
                <span className="text-sm font-semibold text-green-600">
                  {data.energy.solar_self_consumed_kwh.toFixed(1)} kWh ({data.metrics.grid_independence_pct}%)
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                <span className="text-sm text-gray-700">From Grid</span>
                <span className="text-sm font-semibold text-red-600">
                  {data.energy.grid_import_kwh.toFixed(1)} kWh
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Cost Calculation Details */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Cost Calculation</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Solar Savings (Self-consumed)</span>
            <span className="text-sm font-semibold text-green-600">
              +${data.costs.solar_savings.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Grid Export Revenue</span>
            <span className="text-sm font-semibold text-blue-600">
              +${data.costs.grid_export_revenue.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Grid Import Cost</span>
            <span className="text-sm font-semibold text-red-600">
              -${data.costs.grid_import_cost.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between items-center py-3 bg-green-50 rounded-lg px-3 mt-2">
            <span className="text-sm font-semibold text-gray-900">Net Savings</span>
            <span className="text-lg font-bold text-green-600">
              ${data.costs.net_savings.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Rates Configuration */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Electricity Rates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Grid Import Rate ($/kWh)
            </label>
            <input
              type="number"
              step="0.01"
              defaultValue={data.rates.import_rate_per_kwh}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => {
                const newImport = parseFloat(e.target.value) || data.rates.import_rate_per_kwh
                onUpdateRates(newImport, data.rates.export_rate_per_kwh)
              }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Grid Export Rate ($/kWh)
            </label>
            <input
              type="number"
              step="0.01"
              defaultValue={data.rates.export_rate_per_kwh}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => {
                const newExport = parseFloat(e.target.value) || data.rates.export_rate_per_kwh
                onUpdateRates(data.rates.import_rate_per_kwh, newExport)
              }}
            />
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          Period: {data.period.start} to {data.period.end} ({data.period.days} days)
        </p>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">Cost Insights</h4>
        <ul className="space-y-2 text-sm text-blue-800">
          <li>
            • Your solar system is providing <strong>{data.metrics.solar_self_consumption_pct}%</strong> self-consumption
          </li>
          <li>
            • You're <strong>{data.metrics.grid_independence_pct}%</strong> independent from the grid
          </li>
          <li>
            • Daily savings: <strong>${(data.costs.net_savings / data.period.days).toFixed(2)}</strong>
          </li>
          <li>
            • Projected annual savings: <strong>${((data.costs.net_savings / data.period.days) * 365).toFixed(2)}</strong>
          </li>
        </ul>
      </div>
    </div>
  )
}
