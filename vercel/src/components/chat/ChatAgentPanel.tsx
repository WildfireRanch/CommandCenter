'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X, BarChart3, Users, Layers, Zap, TrendingDown, Clock, CheckCircle } from 'lucide-react'
import { useState, useMemo, useEffect } from 'react'
import type { SessionInsights, LiveMetrics } from '@/types/insights'
import AgentBadge from './AgentBadge'
import TokenUsageBar from './TokenUsageBar'
import { AGENT_COLORS } from '@/types/insights'

interface ChatAgentPanelProps {
  isOpen: boolean
  onClose: () => void
  sessionId: string
  insights: SessionInsights | null
  liveMetrics: LiveMetrics | null
}

type TabType = 'overview' | 'agents' | 'context' | 'performance'

const TAB_STORAGE_KEY = 'agent-panel-active-tab'

export default function ChatAgentPanel({
  isOpen,
  onClose,
  sessionId,
  insights,
  liveMetrics
}: ChatAgentPanelProps) {
  // Load persisted tab from localStorage
  const [activeTab, setActiveTab] = useState<TabType>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(TAB_STORAGE_KEY)
      return (saved as TabType) || 'overview'
    }
    return 'overview'
  })

  // Persist tab selection to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TAB_STORAGE_KEY, activeTab)
    }
  }, [activeTab])

  // Check for reduced motion preference (accessibility)
  const prefersReducedMotion = typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={prefersReducedMotion ? { duration: 0 } : undefined}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
          />

          {/* Panel */}
          <motion.aside
            role="complementary"
            aria-label="Session insights panel"
            initial={{ x: prefersReducedMotion ? 0 : '100%' }}
            animate={{ x: 0 }}
            exit={{ x: prefersReducedMotion ? 0 : '100%' }}
            transition={prefersReducedMotion
              ? { duration: 0 }
              : { type: 'spring', damping: 30, stiffness: 300 }
            }
            className="fixed right-0 top-0 h-full w-full sm:w-96 lg:w-80 bg-white border-l border-gray-200 shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-bold text-lg text-gray-900 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  Session Insights
                </h2>
                <button
                  onClick={onClose}
                  className="p-1.5 hover:bg-white/50 rounded-lg transition-colors"
                  aria-label="Close panel"
                >
                  <X className="w-5 h-5 text-gray-600" />
                </button>
              </div>

              {/* Session ID */}
              <p className="text-xs text-gray-600 font-mono">
                {sessionId.slice(0, 13)}...
              </p>

              {/* Live Indicator */}
              {liveMetrics && (
                <div className="mt-2 flex items-center gap-2 text-xs text-green-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Live updates
                </div>
              )}
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200 bg-gray-50" role="tablist" aria-label="Insights sections">
              <div className="flex">
                {[
                  { id: 'overview', label: 'Overview', icon: BarChart3 },
                  { id: 'agents', label: 'Agents', icon: Users },
                  { id: 'context', label: 'Context', icon: Layers },
                  { id: 'performance', label: 'Stats', icon: Zap }
                ].map(tab => (
                  <button
                    key={tab.id}
                    role="tab"
                    aria-selected={activeTab === tab.id}
                    aria-controls={`${tab.id}-panel`}
                    onClick={() => setActiveTab(tab.id as TabType)}
                    className={`flex-1 px-3 py-3 text-xs font-medium transition-all relative ${
                      activeTab === tab.id
                        ? 'text-blue-600 bg-white'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center justify-center gap-1.5">
                      <tab.icon className="w-4 h-4" />
                      <span className="hidden sm:inline">{tab.label}</span>
                    </div>
                    {activeTab === tab.id && (
                      <motion.div
                        layoutId="activeTab"
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
                        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                      />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {!insights ? (
                <div className="space-y-4 animate-pulse" role="status" aria-label="Loading insights">
                  {/* Skeleton: Quick Stats */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-gray-200 rounded-lg h-20"></div>
                    <div className="bg-gray-200 rounded-lg h-20"></div>
                    <div className="bg-gray-200 rounded-lg h-20"></div>
                    <div className="bg-gray-200 rounded-lg h-20"></div>
                  </div>
                  {/* Skeleton: Chart */}
                  <div className="bg-gray-200 rounded-lg h-32"></div>
                  {/* Skeleton: List */}
                  <div className="space-y-2">
                    <div className="bg-gray-200 rounded h-12"></div>
                    <div className="bg-gray-200 rounded h-12"></div>
                    <div className="bg-gray-200 rounded h-12"></div>
                  </div>
                  <span className="sr-only">Loading insights...</span>
                </div>
              ) : (
                <>
                  <div role="tabpanel" id="overview-panel" aria-labelledby="overview-tab" hidden={activeTab !== 'overview'}>
                    {activeTab === 'overview' && <OverviewTab insights={insights} liveMetrics={liveMetrics} />}
                  </div>
                  <div role="tabpanel" id="agents-panel" aria-labelledby="agents-tab" hidden={activeTab !== 'agents'}>
                    {activeTab === 'agents' && <AgentsTab insights={insights} />}
                  </div>
                  <div role="tabpanel" id="context-panel" aria-labelledby="context-tab" hidden={activeTab !== 'context'}>
                    {activeTab === 'context' && <ContextTab insights={insights} />}
                  </div>
                  <div role="tabpanel" id="performance-panel" aria-labelledby="performance-tab" hidden={activeTab !== 'performance'}>
                    {activeTab === 'performance' && <PerformanceTab insights={insights} />}
                  </div>
                </>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}

// Overview Tab
function OverviewTab({ insights, liveMetrics }: { insights: SessionInsights; liveMetrics: LiveMetrics | null }) {
  return (
    <div className="space-y-4">
      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label="Total Queries"
          value={insights.total_queries}
          icon={<BarChart3 className="w-4 h-4" />}
          color="blue"
        />
        <StatCard
          label="Tokens Used"
          value={insights.token_metrics.total_tokens_used.toLocaleString()}
          icon={<Layers className="w-4 h-4" />}
          color="green"
        />
        <StatCard
          label="Cache Hits"
          value={`${insights.cache_metrics.hit_rate.toFixed(0)}%`}
          icon={<Zap className="w-4 h-4" />}
          color="purple"
        />
        <StatCard
          label="Saved"
          value={`$${insights.cost_metrics.savings_usd.toFixed(2)}`}
          icon={<TrendingDown className="w-4 h-4" />}
          color="orange"
        />
      </div>

      {/* Token Usage */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Token Usage</h3>
        <TokenUsageBar
          totalTokens={insights.token_metrics.total_tokens_used}
          breakdown={insights.token_metrics.breakdown}
          maxTokens={8000}
          showBreakdown={true}
          showComparison={true}
          comparisonValue={insights.token_metrics.baseline_tokens}
        />
      </div>

      {/* Agent Contributions */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Agent Activity</h3>
        <div className="space-y-2">
          {insights.agent_contributions.map(agentContrib => (
            <div key={agentContrib.agent} className="flex items-center justify-between">
              <AgentBadge agent={agentContrib.agent} size="sm" />
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-600">{agentContrib.query_count} queries</span>
                <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(agentContrib.query_count / insights.total_queries) * 100}%` }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    className={`h-full ${AGENT_COLORS[agentContrib.agent].bg}`}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Query Types */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Query Types</h3>
        <div className="space-y-2">
          {Object.entries(insights.query_types).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between text-xs">
              <span className="capitalize text-gray-700">{type}</span>
              <span className="font-medium text-gray-900">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Agents Tab
function AgentsTab({ insights }: { insights: SessionInsights }) {
  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800">
          Agent-by-agent breakdown showing contribution and performance metrics
        </p>
      </div>

      {insights.agent_contributions.map(agentContrib => (
        <motion.div
          key={agentContrib.agent}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white border border-gray-200 rounded-lg p-4"
        >
          <div className="flex items-center justify-between mb-3">
            <AgentBadge agent={agentContrib.agent} size="md" />
            <span className="text-xs text-gray-500">{agentContrib.query_count} queries</span>
          </div>

          <div className="space-y-2">
            <MetricRow label="Avg Response" value={`${agentContrib.avg_duration_ms.toFixed(0)}ms`} />
            <MetricRow label="Tokens Used" value={agentContrib.total_tokens.toLocaleString()} />
            <MetricRow label="Cache Hits" value={`${agentContrib.cache_hits}/${agentContrib.query_count}`} />
            <MetricRow label="Success Rate" value={`${agentContrib.success_rate.toFixed(0)}%`} />
          </div>

          {/* Performance Bar */}
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-gray-600">Contribution</span>
              <span className="font-medium">{((agentContrib.query_count / insights.total_queries) * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(agentContrib.query_count / insights.total_queries) * 100}%` }}
                transition={{ duration: 0.6 }}
                className={`h-full ${AGENT_COLORS[agentContrib.agent].bg}`}
              />
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  )
}

// Context Tab
function ContextTab({ insights }: { insights: SessionInsights }) {
  const breakdown = insights.token_metrics.breakdown

  return (
    <div className="space-y-4">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
        <p className="text-xs text-purple-800">
          V1.8 Smart Context Loading - showing token distribution across context types
        </p>
      </div>

      {/* Token Breakdown */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Context Breakdown</h3>
        <TokenUsageBar
          totalTokens={insights.token_metrics.total_tokens_used}
          breakdown={breakdown}
          maxTokens={insights.token_metrics.baseline_tokens}
          showBreakdown={true}
          showComparison={false}
        />
      </div>

      {/* Context Details */}
      <div className="space-y-2">
        <ContextCard
          label="System Context"
          tokens={breakdown.system_context}
          percentage={(breakdown.system_context / insights.token_metrics.total_tokens_used) * 100}
          color="blue"
          description="Current system status and real-time data"
        />
        <ContextCard
          label="Knowledge Base"
          tokens={breakdown.kb_context}
          percentage={(breakdown.kb_context / insights.token_metrics.total_tokens_used) * 100}
          color="green"
          description="Relevant documentation and guides"
        />
        <ContextCard
          label="Conversation"
          tokens={breakdown.conversation_context}
          percentage={(breakdown.conversation_context / insights.token_metrics.total_tokens_used) * 100}
          color="purple"
          description="Recent conversation history"
        />
        <ContextCard
          label="User Context"
          tokens={breakdown.user_context}
          percentage={(breakdown.user_context / insights.token_metrics.total_tokens_used) * 100}
          color="amber"
          description="User preferences and settings"
        />
      </div>

      {/* Comparison */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <TrendingDown className="w-4 h-4 text-green-600" />
          <h3 className="text-sm font-semibold text-green-900">Token Savings</h3>
        </div>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-green-700">Baseline (no smart loading):</span>
            <span className="font-medium text-green-900">{insights.token_metrics.baseline_tokens.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-green-700">Actual (V1.8):</span>
            <span className="font-medium text-green-900">{insights.token_metrics.total_tokens_used.toLocaleString()}</span>
          </div>
          <div className="flex justify-between pt-1 border-t border-green-300">
            <span className="text-green-800 font-medium">Saved:</span>
            <span className="font-bold text-green-900">
              {(insights.token_metrics.baseline_tokens - insights.token_metrics.total_tokens_used).toLocaleString()}
              ({(((insights.token_metrics.baseline_tokens - insights.token_metrics.total_tokens_used) / insights.token_metrics.baseline_tokens) * 100).toFixed(0)}%)
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Performance Tab
function PerformanceTab({ insights }: { insights: SessionInsights }) {
  return (
    <div className="space-y-4">
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
        <p className="text-xs text-orange-800">
          Cache performance and cost metrics
        </p>
      </div>

      {/* Cache Performance */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="w-4 h-4 text-purple-600" />
          <h3 className="text-sm font-semibold text-gray-900">Cache Performance</h3>
        </div>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-600">Hit Rate</span>
              <span className="font-medium text-gray-900">{insights.cache_metrics.hit_rate.toFixed(1)}%</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${insights.cache_metrics.hit_rate}%` }}
                transition={{ duration: 0.6 }}
                className="h-full bg-purple-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{insights.cache_metrics.cache_hits}</div>
              <div className="text-xs text-gray-600">Cache Hits</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-400">{insights.cache_metrics.cache_misses}</div>
              <div className="text-xs text-gray-600">Misses</div>
            </div>
          </div>
        </div>
      </div>

      {/* Cost Metrics */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <TrendingDown className="w-4 h-4 text-green-600" />
          <h3 className="text-sm font-semibold text-gray-900">Cost Analysis</h3>
        </div>
        <div className="space-y-2">
          <MetricRow label="Total Cost" value={`$${insights.cost_metrics.total_cost_usd.toFixed(3)}`} />
          <MetricRow label="Baseline Cost" value={`$${insights.cost_metrics.baseline_cost_usd.toFixed(3)}`} />
          <div className="pt-2 border-t border-gray-200">
            <MetricRow
              label="Cost Saved"
              value={`$${insights.cost_metrics.savings_usd.toFixed(3)}`}
              highlight="green"
            />
            <MetricRow
              label="Savings Rate"
              value={`${insights.cost_metrics.savings_percentage.toFixed(0)}%`}
              highlight="green"
            />
          </div>
        </div>
      </div>

      {/* Response Times */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Clock className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-gray-900">Response Times</h3>
        </div>
        <div className="space-y-2">
          {insights.agent_contributions.map(agentContrib => (
            <div key={agentContrib.agent} className="flex items-center justify-between text-xs">
              <AgentBadge agent={agentContrib.agent} size="sm" showIcon={false} />
              <span className="font-medium text-gray-900">{agentContrib.avg_duration_ms.toFixed(0)}ms</span>
            </div>
          ))}
        </div>
      </div>

      {/* Success Rates */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle className="w-4 h-4 text-green-600" />
          <h3 className="text-sm font-semibold text-gray-900">Success Rates</h3>
        </div>
        <div className="space-y-2">
          {insights.agent_contributions.map(agentContrib => (
            <div key={agentContrib.agent}>
              <div className="flex items-center justify-between text-xs mb-1">
                <AgentBadge agent={agentContrib.agent} size="sm" showIcon={false} />
                <span className="font-medium text-gray-900">{agentContrib.success_rate.toFixed(0)}%</span>
              </div>
              <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${agentContrib.success_rate}%` }}
                  transition={{ duration: 0.5 }}
                  className={agentContrib.success_rate >= 95 ? 'bg-green-500' : agentContrib.success_rate >= 80 ? 'bg-yellow-500' : 'bg-red-500'}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Helper Components
function StatCard({
  label,
  value,
  icon,
  color
}: {
  label: string
  value: string | number
  icon: React.ReactNode
  color: 'blue' | 'green' | 'purple' | 'orange'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-600',
    green: 'bg-green-50 border-green-200 text-green-600',
    purple: 'bg-purple-50 border-purple-200 text-purple-600',
    orange: 'bg-orange-50 border-orange-200 text-orange-600'
  }

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={`${colorClasses[color]} border rounded-lg p-3`}
    >
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-xs font-medium text-gray-600">{label}</span>
      </div>
      <div className="text-xl font-bold text-gray-900">{value}</div>
    </motion.div>
  )
}

function MetricRow({
  label,
  value,
  highlight
}: {
  label: string
  value: string
  highlight?: 'green' | 'red'
}) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-600">{label}</span>
      <span className={`font-medium ${
        highlight === 'green' ? 'text-green-600' :
        highlight === 'red' ? 'text-red-600' :
        'text-gray-900'
      }`}>
        {value}
      </span>
    </div>
  )
}

function ContextCard({
  label,
  tokens,
  percentage,
  color,
  description
}: {
  label: string
  tokens: number
  percentage: number
  color: 'blue' | 'green' | 'purple' | 'amber'
  description: string
}) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    amber: 'bg-amber-500'
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded ${colorClasses[color]}`} />
          <span className="text-sm font-medium text-gray-900">{label}</span>
        </div>
        <span className="text-xs text-gray-600">{tokens.toLocaleString()} tokens</span>
      </div>
      <p className="text-xs text-gray-500 mb-2">{description}</p>
      <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5 }}
          className={`h-full ${colorClasses[color]}`}
        />
      </div>
      <div className="text-right text-xs text-gray-600 mt-1">{percentage.toFixed(1)}%</div>
    </div>
  )
}
