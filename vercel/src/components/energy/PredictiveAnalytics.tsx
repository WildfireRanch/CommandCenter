'use client'

import { Battery, Clock, TrendingUp, AlertCircle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { format, parseISO } from 'date-fns'

interface Prediction {
  timestamp: string
  hour: number
  predicted_soc: number
  confidence: string
}

interface PredictiveData {
  current_soc: number
  prediction_hours: number
  predictions: Prediction[]
  model: string
  note: string
}

interface PredictiveAnalyticsProps {
  data: PredictiveData | null
  loading: boolean
}

export function PredictiveAnalytics({ data, loading }: PredictiveAnalyticsProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">Loading predictions...</p>
      </div>
    )
  }

  if (!data || !data.predictions || data.predictions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">No prediction data available</p>
      </div>
    )
  }

  // Prepare chart data
  const chartData = data.predictions.map(p => ({
    time: format(parseISO(p.timestamp), 'MMM d HH:mm'),
    soc: p.predicted_soc,
    confidence: p.confidence
  }))

  // Find min/max predicted SOC
  const minSoc = Math.min(...data.predictions.map(p => p.predicted_soc))
  const maxSoc = Math.max(...data.predictions.map(p => p.predicted_soc))

  // Find critical predictions (< 20% or > 90%)
  const lowSocPredictions = data.predictions.filter(p => p.predicted_soc < 20)
  const highSocPredictions = data.predictions.filter(p => p.predicted_soc > 90)

  // Confidence distribution
  const confidenceCounts = data.predictions.reduce((acc, p) => {
    acc[p.confidence] = (acc[p.confidence] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const getSOCColor = (soc: number) => {
    if (soc < 20) return 'text-red-600'
    if (soc < 50) return 'text-orange-600'
    if (soc < 80) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getSOCBgColor = (soc: number) => {
    if (soc < 20) return 'bg-red-50'
    if (soc < 50) return 'bg-orange-50'
    if (soc < 80) return 'bg-yellow-50'
    return 'bg-green-50'
  }

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Current SOC */}
        <div className={`${getSOCBgColor(data.current_soc)} rounded-lg shadow-sm border border-gray-200 p-4`}>
          <div className="flex items-center justify-between mb-2">
            <Battery className={`w-8 h-8 ${getSOCColor(data.current_soc)}`} />
            <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded">NOW</span>
          </div>
          <div className={`text-3xl font-bold ${getSOCColor(data.current_soc)}`}>
            {data.current_soc.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Current Battery SOC</div>
        </div>

        {/* Predicted Min SOC */}
        <div className={`${getSOCBgColor(minSoc)} rounded-lg shadow-sm border border-gray-200 p-4`}>
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className={`w-8 h-8 ${getSOCColor(minSoc)}`} />
            <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded">MIN</span>
          </div>
          <div className={`text-3xl font-bold ${getSOCColor(minSoc)}`}>
            {minSoc.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Predicted Minimum</div>
        </div>

        {/* Predicted Max SOC */}
        <div className={`${getSOCBgColor(maxSoc)} rounded-lg shadow-sm border border-gray-200 p-4`}>
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className={`w-8 h-8 ${getSOCColor(maxSoc)}`} />
            <span className="text-xs font-semibold text-gray-600 bg-white px-2 py-1 rounded">MAX</span>
          </div>
          <div className={`text-3xl font-bold ${getSOCColor(maxSoc)}`}>
            {maxSoc.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Predicted Maximum</div>
        </div>

        {/* Prediction Horizon */}
        <div className="bg-gradient-to-br from-blue-50 to-white rounded-lg shadow-sm border border-blue-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-8 h-8 text-blue-600" />
            <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-1 rounded">
              {data.model.toUpperCase()}
            </span>
          </div>
          <div className="text-3xl font-bold text-blue-600">
            {data.prediction_hours}h
          </div>
          <div className="text-sm text-gray-600">Prediction Horizon</div>
        </div>
      </div>

      {/* SOC Prediction Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Battery SOC Forecast</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              label={{ value: 'SOC (%)', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
              domain={[0, 100]}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
              formatter={(value: number) => `${value.toFixed(1)}%`}
            />
            <Legend />
            <ReferenceLine y={20} stroke="#ef4444" strokeDasharray="3 3" label="Low (20%)" />
            <ReferenceLine y={80} stroke="#10b981" strokeDasharray="3 3" label="High (80%)" />
            <Line
              type="monotone"
              dataKey="soc"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', r: 4 }}
              name="Predicted SOC"
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-500 mt-3">
          {data.note}
        </p>
      </div>

      {/* Alerts & Warnings */}
      {(lowSocPredictions.length > 0 || highSocPredictions.length > 0) && (
        <div className="space-y-3">
          {lowSocPredictions.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-red-900 mb-1">Low SOC Warning</h4>
                  <p className="text-sm text-red-800">
                    Battery SOC is predicted to drop below 20% in the next {data.prediction_hours} hours.
                    First occurrence: {format(parseISO(lowSocPredictions[0].timestamp), 'MMM d HH:mm')} ({lowSocPredictions[0].predicted_soc.toFixed(1)}%)
                  </p>
                  <p className="text-xs text-red-700 mt-2">
                    Consider reducing load or ensuring solar production will increase during this period.
                  </p>
                </div>
              </div>
            </div>
          )}

          {highSocPredictions.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-green-900 mb-1">High SOC Opportunity</h4>
                  <p className="text-sm text-green-800">
                    Battery SOC is predicted to exceed 90% in the next {data.prediction_hours} hours.
                    First occurrence: {format(parseISO(highSocPredictions[0].timestamp), 'MMM d HH:mm')} ({highSocPredictions[0].predicted_soc.toFixed(1)}%)
                  </p>
                  <p className="text-xs text-green-700 mt-2">
                    Good opportunity to run discretionary loads like miners, pumps, or water heaters.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Prediction Details */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Prediction Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Model</div>
            <div className="text-sm font-semibold text-gray-900">{data.model}</div>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Total Predictions</div>
            <div className="text-sm font-semibold text-gray-900">{data.predictions.length} hours</div>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600 mb-1">Confidence Distribution</div>
            <div className="text-sm font-semibold text-gray-900">
              {Object.entries(confidenceCounts).map(([conf, count]) => (
                <span key={conf} className="mr-2">
                  {conf}: {count}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Hourly Predictions Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Hour</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Predicted SOC</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Change</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Confidence</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.predictions.map((pred, idx) => {
                const prevSoc = idx === 0 ? data.current_soc : data.predictions[idx - 1].predicted_soc
                const change = pred.predicted_soc - prevSoc
                return (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {format(parseISO(pred.timestamp), 'MMM d HH:mm')}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-600">
                      {pred.hour}:00
                    </td>
                    <td className={`px-4 py-3 text-sm text-right font-semibold ${getSOCColor(pred.predicted_soc)}`}>
                      {pred.predicted_soc.toFixed(1)}%
                    </td>
                    <td className={`px-4 py-3 text-sm text-right font-medium ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {change >= 0 ? '+' : ''}{change.toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        pred.confidence === 'high' ? 'bg-green-100 text-green-700' :
                        pred.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {pred.confidence}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">About These Predictions</h4>
        <ul className="space-y-1 text-sm text-blue-800">
          <li>• Predictions are based on 7-day historical patterns</li>
          <li>• Actual SOC may vary based on weather and usage changes</li>
          <li>• Higher confidence predictions use more reliable historical data</li>
          <li>• Use these predictions to plan energy-intensive activities</li>
        </ul>
      </div>
    </div>
  )
}
