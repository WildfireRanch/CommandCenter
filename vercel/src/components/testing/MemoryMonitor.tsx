/**
 * MemoryMonitor Component
 *
 * Real-time memory usage monitoring for detecting memory leaks
 * Displays heap usage over time with live graph
 */

'use client'

import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react'

interface MemoryDataPoint {
  time: number
  memory: number
}

export default function MemoryMonitor() {
  const [memory, setMemory] = useState<MemoryDataPoint[]>([])
  const [isRunning, setIsRunning] = useState(true)
  const [startTime] = useState(Date.now())
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!isRunning) return

    intervalRef.current = setInterval(() => {
      // Check if performance.memory is available (Chromium browsers)
      const heap = (performance as any).memory?.usedJSHeapSize
      if (heap) {
        const memoryMB = heap / 1024 / 1024
        const elapsed = Math.floor((Date.now() - startTime) / 1000)

        setMemory(prev => {
          const newData = [...prev, { time: elapsed, memory: memoryMB }]
          // Keep last 60 data points (1 minute at 1s intervals)
          return newData.slice(-60)
        })
      }
    }, 1000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      // Clear memory data to prevent chart memory leaks
      setMemory([])
    }
  }, [isRunning, startTime])

  // Calculate metrics
  const currentMemory = memory[memory.length - 1]?.memory || 0
  const startMemory = memory[0]?.memory || currentMemory
  const memoryGrowth = currentMemory - startMemory
  const growthRate = memory.length > 1
    ? (memoryGrowth / memory.length * 60).toFixed(1) // KB per minute
    : '0'

  // Determine status
  const growthRateNum = parseFloat(growthRate)
  const status = growthRateNum < 100 ? 'healthy' :
                 growthRateNum < 500 ? 'warning' :
                 'critical'

  const statusColors = {
    healthy: { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-200', icon: 'text-green-600' },
    warning: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-200', icon: 'text-yellow-600' },
    critical: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-200', icon: 'text-red-600' }
  }

  const colors = statusColors[status]

  // Check if memory API is available
  const isMemoryAPIAvailable = typeof performance !== 'undefined' && (performance as any).memory

  if (!isMemoryAPIAvailable) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-4 h-4 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Memory Monitor</h3>
        </div>
        <p className="text-sm text-gray-600">
          Memory monitoring is only available in Chromium-based browsers (Chrome, Edge).
        </p>
      </div>
    )
  }

  return (
    <div className={`border rounded-lg p-4 ${colors.bg} ${colors.border}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className={`w-4 h-4 ${colors.icon}`} />
          <h3 className={`font-semibold ${colors.text}`}>Memory Monitor</h3>
        </div>
        <button
          onClick={() => setIsRunning(!isRunning)}
          className={`text-sm px-3 py-1 rounded ${
            isRunning
              ? 'bg-white/50 hover:bg-white/80'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          } transition-colors`}
          aria-label={isRunning ? 'Pause monitoring' : 'Resume monitoring'}
        >
          {isRunning ? '⏸ Pause' : '▶ Resume'}
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-xs text-gray-600 mb-1">Current</div>
          <div className={`text-lg font-bold ${colors.text}`}>
            {currentMemory.toFixed(1)}MB
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-600 mb-1">Growth Rate</div>
          <div className={`text-lg font-bold ${colors.text} flex items-center justify-center gap-1`}>
            {growthRateNum > 10 && <TrendingUp className="w-4 h-4" />}
            {growthRateNum < -10 && <TrendingDown className="w-4 h-4" />}
            {Math.abs(growthRateNum) <= 10 && <Minus className="w-4 h-4" />}
            {Math.abs(growthRateNum).toFixed(0)}KB/min
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-600 mb-1">Status</div>
          <div className={`text-lg font-bold ${colors.text}`}>
            {status === 'healthy' && '✅ Good'}
            {status === 'warning' && '⚠️ Monitor'}
            {status === 'critical' && '🔴 Leak'}
          </div>
        </div>
      </div>

      {/* Chart */}
      {memory.length > 1 && (
        <div className="bg-white rounded-lg p-2 mb-3">
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={memory}>
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10 }}
                label={{ value: 'Seconds', position: 'insideBottom', offset: -5, fontSize: 10 }}
              />
              <YAxis
                tick={{ fontSize: 10 }}
                domain={['dataMin - 5', 'dataMax + 5']}
                label={{ value: 'MB', angle: -90, position: 'insideLeft', fontSize: 10 }}
              />
              <Tooltip
                formatter={(value: number) => `${value.toFixed(2)} MB`}
                labelFormatter={(label) => `${label}s`}
              />
              <Line
                type="monotone"
                dataKey="memory"
                stroke={status === 'healthy' ? '#10b981' : status === 'warning' ? '#f59e0b' : '#ef4444'}
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Info */}
      <div className="text-xs space-y-1">
        <p className={colors.text}>
          <strong>Growth:</strong> {memoryGrowth > 0 ? '+' : ''}{memoryGrowth.toFixed(1)}MB
          {' '}in {memory.length}s
        </p>
        <p className="text-gray-600">
          Monitoring {memory.length < 60 ? memory.length : '60'}s of data
        </p>
      </div>

      {/* Status Messages */}
      {status === 'critical' && (
        <div className="mt-3 p-2 bg-red-100 border border-red-300 rounded text-xs text-red-800">
          <strong>⚠️ Possible Memory Leak Detected</strong>
          <p>Memory growth &gt; 500KB/min. Check for:</p>
          <ul className="list-disc ml-4 mt-1">
            <li>Uncleaned intervals/timeouts</li>
            <li>Event listeners not removed</li>
            <li>Large objects in closures</li>
          </ul>
        </div>
      )}

      {status === 'healthy' && memory.length > 20 && (
        <div className="mt-3 p-2 bg-green-100 border border-green-300 rounded text-xs text-green-800">
          ✅ Memory usage is stable. No leaks detected.
        </div>
      )}
    </div>
  )
}
