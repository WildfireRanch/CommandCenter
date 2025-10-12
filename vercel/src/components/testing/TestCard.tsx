/**
 * TestCard Component
 *
 * Reusable card for displaying and running individual tests
 * Shows test status, results, and action buttons
 */

'use client'

import { useState } from 'react'
import { Play, CheckCircle, XCircle, Loader2, Clock } from 'lucide-react'

interface TestCardProps {
  name: string
  description: string
  status?: 'idle' | 'running' | 'success' | 'failed'
  result?: string
  duration?: number
  onRun?: () => Promise<{ success: boolean; message: string; duration: number }>
  actions?: React.ReactNode
  autoRun?: boolean
}

export default function TestCard({
  name,
  description,
  status: initialStatus = 'idle',
  result: initialResult,
  duration: initialDuration,
  onRun,
  actions,
  autoRun = false
}: TestCardProps) {
  const [testStatus, setTestStatus] = useState(initialStatus)
  const [testResult, setTestResult] = useState(initialResult)
  const [testDuration, setTestDuration] = useState(initialDuration)

  const handleRun = async () => {
    if (!onRun || testStatus === 'running') return

    setTestStatus('running')
    setTestResult(undefined)
    setTestDuration(undefined)

    try {
      const result = await onRun()
      setTestStatus(result.success ? 'success' : 'failed')
      setTestResult(result.message)
      setTestDuration(result.duration)
    } catch (error: any) {
      setTestStatus('failed')
      setTestResult(error.message || 'Test failed with unknown error')
    }
  }

  // Status colors and icons
  const statusConfig = {
    idle: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      text: 'text-gray-600',
      icon: <Clock className="w-6 h-6 text-gray-400" />
    },
    running: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-600',
      icon: <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
    },
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-600',
      icon: <CheckCircle className="w-6 h-6 text-green-600" />
    },
    failed: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-600',
      icon: <XCircle className="w-6 h-6 text-red-600" />
    }
  }

  const config = statusConfig[testStatus]

  return (
    <div className={`border rounded-lg p-4 ${config.bg} ${config.border} transition-colors`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">{name}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
        <div className="ml-4" aria-label={`Test status: ${testStatus}`}>
          {config.icon}
        </div>
      </div>

      {/* Result */}
      {testResult && (
        <div className={`text-sm p-3 rounded mb-3 ${
          testStatus === 'success'
            ? 'bg-green-100 border border-green-300 text-green-800'
            : 'bg-red-100 border border-red-300 text-red-800'
        }`}>
          {testResult}
          {testDuration !== undefined && (
            <span className="block mt-1 text-xs opacity-75">
              Duration: {testDuration}ms
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 flex-wrap">
        {onRun && (
          <button
            onClick={handleRun}
            disabled={testStatus === 'running'}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            aria-label={testStatus === 'running' ? 'Test is running' : 'Run test'}
          >
            {testStatus === 'running' ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Test
              </>
            )}
          </button>
        )}
        {actions}
      </div>

      {/* Status badge */}
      <div className={`mt-3 text-xs font-medium ${config.text}`}>
        {testStatus === 'idle' && 'Ready to run'}
        {testStatus === 'running' && 'Running...'}
        {testStatus === 'success' && '✓ Passed'}
        {testStatus === 'failed' && '✗ Failed'}
      </div>
    </div>
  )
}
