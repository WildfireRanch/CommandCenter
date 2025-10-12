// ═══════════════════════════════════════════════════════════════════════════
// FILE: vercel/src/hooks/useSessionInsights.ts
// PURPOSE: Custom hook for fetching and managing session insights data
// ═══════════════════════════════════════════════════════════════════════════

import { useState, useEffect, useCallback, useRef } from 'react'
import type { SessionInsights, MessageInsight, LiveMetrics } from '@/types/insights'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  agent_role?: string
  duration_ms?: number
  context_tokens?: number
  cache_hit?: boolean
  query_type?: string
}

interface UseSessionInsightsOptions {
  sessionId: string
  messages: Message[]
  enabled?: boolean
  refreshInterval?: number // Auto-refresh interval in ms (0 = disabled)
}

interface UseSessionInsightsReturn {
  insights: SessionInsights | null
  liveMetrics: LiveMetrics | null
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
  lastUpdated: Date | null
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'

/**
 * Hook to fetch and manage session insights with real-time updates
 */
export function useSessionInsights({
  sessionId,
  messages,
  enabled = true,
  refreshInterval = 0
}: UseSessionInsightsOptions): UseSessionInsightsReturn {
  const [insights, setInsights] = useState<SessionInsights | null>(null)
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  /**
   * Calculate insights from messages (fallback if API not available)
   */
  const calculateInsightsFromMessages = useCallback((messages: Message[]): SessionInsights | null => {
    if (messages.length === 0) return null

    const assistantMessages = messages.filter(m => m.role === 'assistant')
    if (assistantMessages.length === 0) return null

    // Calculate agent contributions
    const agentMap = new Map<string, {
      count: number
      duration: number
      tokens: number
      successes: number
      cacheHits: number
    }>()

    let totalTokens = 0
    let systemTokens = 0
    let kbTokens = 0
    let conversationTokens = 0
    let userTokens = 0
    let cacheHits = 0
    let cacheMisses = 0
    const queryTypeCount: Record<string, number> = {}

    assistantMessages.forEach((msg) => {
      const agent = msg.agent_role || 'Unknown'
      const existing = agentMap.get(agent) || { count: 0, duration: 0, tokens: 0, successes: 0, cacheHits: 0 }

      agentMap.set(agent, {
        count: existing.count + 1,
        duration: existing.duration + (msg.duration_ms || 0),
        tokens: existing.tokens + (msg.context_tokens || 0),
        successes: existing.successes + 1, // Assume success if we got a response
        cacheHits: existing.cacheHits + (msg.cache_hit ? 1 : 0)
      })

      // Track tokens
      if (msg.context_tokens) {
        totalTokens += msg.context_tokens
        // Estimate breakdown (rough approximation if not provided)
        systemTokens += Math.floor(msg.context_tokens * 0.75)
        kbTokens += Math.floor(msg.context_tokens * 0.17)
        conversationTokens += Math.floor(msg.context_tokens * 0.08)
      }

      // Track cache
      if (msg.cache_hit !== undefined) {
        if (msg.cache_hit) cacheHits++
        else cacheMisses++
      }

      // Track query types
      if (msg.query_type) {
        queryTypeCount[msg.query_type] = (queryTypeCount[msg.query_type] || 0) + 1
      }
    })

    // Build agent contributions array
    const agentContributions = Array.from(agentMap.entries()).map(([agent, data]) => ({
      agent: agent as any,
      query_count: data.count,
      total_duration_ms: data.duration,
      avg_duration_ms: data.duration / data.count,
      total_tokens: data.tokens,
      cache_hits: data.cacheHits || 0,
      success_rate: (data.successes / data.count) * 100,
      avg_response_time: data.duration / data.count,
      percentage: (data.count / assistantMessages.length) * 100
    }))

    // Sort by query count desc
    agentContributions.sort((a, b) => b.query_count - a.query_count)

    const totalQueries = messages.filter(m => m.role === 'user').length
    const totalCacheQueries = cacheHits + cacheMisses
    const avgTokens = totalTokens / assistantMessages.length || 0

    // Calculate costs (rough estimate: $0.005 per 1k tokens)
    const actualCost = (totalTokens / 1000) * 0.005
    const baselineCost = (totalTokens / 1000) * 0.008 // 60% more without V1.8
    const savings = baselineCost - actualCost

    const now = new Date().toISOString()

    return {
      session_id: sessionId,
      started_at: messages[0]?.timestamp || now,
      last_activity: messages[messages.length - 1]?.timestamp || now,
      total_queries: totalQueries,
      total_responses: assistantMessages.length,
      total_duration_ms: assistantMessages.reduce((sum, m) => sum + (m.duration_ms || 0), 0),
      avg_response_time_ms: assistantMessages.reduce((sum, m) => sum + (m.duration_ms || 0), 0) / assistantMessages.length || 0,
      success_rate: 100, // Assume all successful for now

      agent_contributions: agentContributions,
      primary_agent: agentContributions[0]?.agent || 'Manager',

      token_metrics: {
        total_tokens_used: totalTokens,
        avg_tokens_per_query: avgTokens,
        baseline_tokens: Math.floor(totalTokens * 1.6), // Estimate 60% more without V1.8
        token_timeline: assistantMessages.map(m => ({
          timestamp: m.timestamp,
          tokens: m.context_tokens || 0,
          query_type: (m.query_type || 'system') as any
        })),
        breakdown: {
          system_context: systemTokens,
          kb_context: kbTokens,
          conversation_context: conversationTokens,
          user_context: userTokens
        }
      },

      cache_metrics: {
        total_queries: totalCacheQueries,
        cache_hits: cacheHits,
        cache_misses: cacheMisses,
        hit_rate: totalCacheQueries > 0 ? (cacheHits / totalCacheQueries) * 100 : 0,
        avg_cache_response_time: 0, // Not available from messages
        avg_fresh_response_time: 0,
        time_saved_ms: 0
      },

      cost_metrics: {
        total_cost_usd: actualCost,
        cost_per_query_usd: actualCost / totalQueries || 0,
        baseline_cost_usd: baselineCost,
        savings_usd: savings,
        savings_percentage: (savings / baselineCost) * 100 || 0
      },

      query_types: queryTypeCount as any,

      messages: [] // Not needed for basic insights
    }
  }, [sessionId])

  /**
   * Fetch insights from API (when available)
   */
  const fetchInsights = useCallback(async (signal?: AbortSignal) => {
    if (!enabled || !sessionId) return

    try {
      setLoading(true)
      setError(null)

      // Try to fetch from API
      try {
        const response = await fetch(`${API_URL}/chat/sessions/${sessionId}/insights`, {
          signal // Pass AbortSignal to fetch
        })

        if (response.ok) {
          const data = await response.json()
          setInsights(data)
          setLastUpdated(new Date())
          return
        }
      } catch (apiError: any) {
        // If request was aborted, don't fallback or log
        if (apiError.name === 'AbortError') {
          return
        }
        // API not available yet, fallback to client-side calculation
        console.log('API insights not available, calculating from messages')
      }

      // Fallback: Calculate from messages
      const calculatedInsights = calculateInsightsFromMessages(messages)
      setInsights(calculatedInsights)
      setLastUpdated(new Date())

    } catch (err) {
      console.error('Error fetching insights:', err)
      setError(err instanceof Error ? err : new Error('Failed to fetch insights'))
    } finally {
      setLoading(false)
    }
  }, [enabled, sessionId, messages, calculateInsightsFromMessages])

  /**
   * Update live metrics
   */
  const updateLiveMetrics = useCallback(() => {
    if (!insights) return

    const lastMessage = messages[messages.length - 1]
    const liveData: LiveMetrics = {
      current_query_count: insights.total_queries,
      active_agent: lastMessage?.role === 'assistant' ? (lastMessage.agent_role as any) : null,
      current_tokens_used: insights.token_metrics.total_tokens_used,
      current_cache_hit_rate: insights.cache_metrics.hit_rate,
      last_update: new Date().toISOString()
    }

    setLiveMetrics(liveData)
  }, [insights, messages])

  /**
   * Effect: Initial load and refresh on messages change
   */
  useEffect(() => {
    const controller = new AbortController()
    fetchInsights(controller.signal)

    return () => {
      controller.abort() // Cancel pending request on unmount
    }
  }, [fetchInsights])

  /**
   * Effect: Update live metrics when insights change
   */
  useEffect(() => {
    updateLiveMetrics()
  }, [updateLiveMetrics])

  /**
   * Effect: Auto-refresh interval
   */
  useEffect(() => {
    const controller = new AbortController()

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        fetchInsights(controller.signal)
      }, refreshInterval)

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
        controller.abort() // Cancel any pending requests
      }
    }

    return () => {
      controller.abort()
    }
  }, [refreshInterval, fetchInsights])

  /**
   * Manual refresh function
   */
  const refresh = useCallback(async () => {
    await fetchInsights()
  }, [fetchInsights])

  return {
    insights,
    liveMetrics,
    loading,
    error,
    refresh,
    lastUpdated
  }
}

export default useSessionInsights
