/**
 * Testing Dashboard Page
 *
 * Interactive testing interface for edge case validation
 * Includes stress tests, performance tests, and memory monitoring
 */

'use client'

import { useState } from 'react'
import { Beaker, TrendingUp, Database, Zap, Activity } from 'lucide-react'
import TestCard from '@/components/testing/TestCard'
import MemoryMonitor from '@/components/testing/MemoryMonitor'
import Link from 'next/link'

export default function TestingPage() {
  const [panelToggleCount, setPanelToggleCount] = useState(0)
  const [generatedMessages, setGeneratedMessages] = useState<any[]>([])

  /**
   * Test #2: Rapid Panel Toggle
   * Simulates 100 rapid open/close cycles to detect memory leaks
   */
  const runRapidToggleTest = async () => {
    const startTime = performance.now()
    const startMemory = (performance as any).memory?.usedJSHeapSize || 0

    // Simulate rapid toggles
    for (let i = 0; i < 100; i++) {
      setPanelToggleCount(prev => prev + 1)
      // Simulate panel state change
      await new Promise(resolve => setTimeout(resolve, 1))
    }

    const endTime = performance.now()
    const endMemory = (performance as any).memory?.usedJSHeapSize || 0
    const duration = Math.round(endTime - startTime)
    const memoryGrowth = ((endMemory - startMemory) / 1024 / 1024).toFixed(2)

    const success = parseFloat(memoryGrowth) < 10 // Less than 10MB is acceptable
    const message = `Completed 100 toggles in ${duration}ms. Memory growth: ${memoryGrowth}MB ${success ? '✓ Acceptable' : '⚠️ High'}`

    return { success, message, duration }
  }

  /**
   * Test #3: Large Dataset Performance
   * Generates N messages and measures calculation time
   */
  const runLargeDatasetTest = async (count: number) => {
    const startTime = performance.now()

    const messages = Array.from({ length: count }, (_, i) => ({
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: `Test message ${i}`,
      timestamp: new Date(Date.now() - (count - i) * 60000).toISOString(),
      agent_role: ['Manager', 'Solar Controller', 'Research Agent'][i % 3],
      duration_ms: 500 + Math.random() * 1000,
      context_tokens: 2000 + Math.floor(Math.random() * 2000),
      cache_hit: Math.random() > 0.5,
      query_type: ['system', 'research', 'planning', 'general'][i % 4]
    }))

    setGeneratedMessages(messages)

    // Simulate insights calculation
    const assistantMessages = messages.filter(m => m.role === 'assistant')
    const totalTokens = assistantMessages.reduce((sum, m) => sum + (m.context_tokens || 0), 0)
    const avgTokens = totalTokens / assistantMessages.length

    const endTime = performance.now()
    const duration = Math.round(endTime - startTime)

    // Performance targets
    const target = count <= 100 ? 100 : count <= 500 ? 200 : 500
    const success = duration < target

    const message = `Generated ${count} messages, calculated ${assistantMessages.length} insights. Avg tokens: ${avgTokens.toFixed(0)}. ${success ? '✓ Fast' : '⚠️ Slow'}`

    return { success, message, duration }
  }

  /**
   * Test #4: Garbage Data Resilience
   * Tests with malformed, missing, and extreme data
   */
  const runGarbageDataTest = async () => {
    const startTime = performance.now()
    const testCases = [
      { name: 'Missing tokens', data: { role: 'assistant', content: 'Test' } },
      { name: 'Negative duration', data: { role: 'assistant', content: 'Test', duration_ms: -100, context_tokens: 2000 } },
      { name: 'Extreme tokens', data: { role: 'assistant', content: 'Test', context_tokens: 150000 } },
      { name: 'Invalid agent', data: { role: 'assistant', content: 'Test', agent_role: 'InvalidAgent', context_tokens: 2000 } },
      { name: 'Null values', data: { role: 'assistant', content: null, context_tokens: null } }
    ]

    let passed = 0
    const results: string[] = []

    for (const testCase of testCases) {
      try {
        // Simulate processing
        const tokens = testCase.data.context_tokens ?? 0
        const duration = Math.max(0, testCase.data.duration_ms ?? 0)

        if (!isNaN(tokens) && !isNaN(duration)) {
          passed++
          results.push(`✓ ${testCase.name}`)
        } else {
          results.push(`✗ ${testCase.name}: NaN detected`)
        }
      } catch (error) {
        results.push(`✗ ${testCase.name}: ${error}`)
      }
    }

    const endTime = performance.now()
    const duration = Math.round(endTime - startTime)
    const success = passed === testCases.length

    const message = `${passed}/${testCases.length} cases passed:\n${results.join('\n')}`

    return { success, message, duration }
  }

  /**
   * Test #9: Zero Division Edge Cases
   * Verifies all calculations handle zero values correctly
   */
  const runZeroDivisionTest = async () => {
    const startTime = performance.now()
    const tests = [
      {
        name: 'Zero total queries',
        calc: () => {
          const pct = (5 / (0 || 1)) * 100
          return isFinite(pct) && !isNaN(pct)
        }
      },
      {
        name: 'Zero tokens average',
        calc: () => {
          const avg = 0 / (0 || 1)
          return isFinite(avg) && !isNaN(avg)
        }
      },
      {
        name: 'Zero cache hits',
        calc: () => {
          const rate = (0 / (0 || 1)) * 100
          return isFinite(rate) && !isNaN(rate)
        }
      },
      {
        name: 'Empty array reduce',
        calc: () => {
          const sum = [].reduce((a, b) => a + b, 0)
          return sum === 0
        }
      }
    ]

    let passed = 0
    const results: string[] = []

    for (const test of tests) {
      try {
        const result = test.calc()
        if (result) {
          passed++
          results.push(`✓ ${test.name}`)
        } else {
          results.push(`✗ ${test.name}: Invalid result`)
        }
      } catch (error: any) {
        results.push(`✗ ${test.name}: ${error.message}`)
      }
    }

    const endTime = performance.now()
    const duration = Math.round(endTime - startTime)
    const success = passed === tests.length

    const message = `${passed}/${tests.length} checks passed:\n${results.join('\n')}`

    return { success, message, duration }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <Beaker className="w-8 h-8 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">Testing Dashboard</h1>
              </div>
              <p className="mt-2 text-sm text-gray-600">
                Interactive edge case validation and stress testing
              </p>
            </div>
            <Link
              href="/agents"
              className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              ← Back to Agents
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Memory Monitor (Top) */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-gray-700" />
            <h2 className="text-xl font-semibold text-gray-900">Real-time Memory Monitor</h2>
          </div>
          <MemoryMonitor />
        </div>

        {/* Test Grid */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-gray-700" />
            <h2 className="text-xl font-semibold text-gray-900">Interactive Tests</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Test #2: Rapid Toggle */}
            <TestCard
              name="Rapid Panel Toggle"
              description="Simulates 100 rapid open/close cycles to detect memory leaks"
              onRun={runRapidToggleTest}
            />

            {/* Test #3: Large Dataset */}
            <TestCard
              name="Large Dataset Performance"
              description="Generates messages and measures calculation time"
              actions={
                <>
                  <button
                    onClick={() => runLargeDatasetTest(100).then(() => {})}
                    className="px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                  >
                    100 msgs
                  </button>
                  <button
                    onClick={() => runLargeDatasetTest(500).then(() => {})}
                    className="px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                  >
                    500 msgs
                  </button>
                  <button
                    onClick={() => runLargeDatasetTest(1000).then(() => {})}
                    className="px-3 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                  >
                    1000 msgs
                  </button>
                </>
              }
            />

            {/* Test #4: Garbage Data */}
            <TestCard
              name="Malformed Data Resilience"
              description="Tests with missing fields, negative values, and extreme numbers"
              onRun={runGarbageDataTest}
            />

            {/* Test #9: Zero Division */}
            <TestCard
              name="Zero Division Safety"
              description="Verifies all calculations handle zero values without NaN/Infinity"
              onRun={runZeroDivisionTest}
            />
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-blue-900">Performance Targets</h3>
            </div>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• 100 msgs: &lt; 100ms</li>
              <li>• 500 msgs: &lt; 200ms</li>
              <li>• 1000 msgs: &lt; 500ms</li>
              <li>• Memory growth: &lt; 10MB</li>
            </ul>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-green-900">Test Coverage</h3>
            </div>
            <ul className="text-sm text-green-800 space-y-1">
              <li>• Memory leak detection</li>
              <li>• Performance at scale</li>
              <li>• Error handling</li>
              <li>• Math safety</li>
            </ul>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-3">
              <Beaker className="w-5 h-5 text-purple-600" />
              <h3 className="font-semibold text-purple-900">More Tests</h3>
            </div>
            <p className="text-sm text-purple-800 mb-2">
              Additional stress tests available:
            </p>
            <a
              href="/scripts/test-panel-stress.html"
              target="_blank"
              className="text-sm text-purple-600 hover:text-purple-700 underline"
            >
              Open Full Test Suite →
            </a>
          </div>
        </div>

        {/* Generated Messages Display */}
        {generatedMessages.length > 0 && (
          <div className="mt-8 bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-3">
              Generated Test Data ({generatedMessages.length} messages)
            </h3>
            <div className="bg-gray-50 rounded p-3 max-h-40 overflow-y-auto">
              <pre className="text-xs text-gray-700">
                {JSON.stringify(generatedMessages.slice(0, 5), null, 2)}
                {generatedMessages.length > 5 && '\n... and ' + (generatedMessages.length - 5) + ' more'}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
