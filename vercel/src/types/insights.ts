// ═══════════════════════════════════════════════════════════════════════════
// FILE: vercel/src/types/insights.ts
// PURPOSE: TypeScript types for agent insights and session analytics
// ═══════════════════════════════════════════════════════════════════════════

export type AgentRole =
  | 'Manager'
  | 'Solar Controller'
  | 'Energy Orchestrator'
  | 'Research Agent'
  | 'Energy Systems Monitor'
  | 'Energy Operations Manager'
  | 'Energy Systems Research Consultant'
  | 'System'

export type QueryType = 'system' | 'research' | 'planning' | 'general'

// ─────────────────────────────────────────────────────────────────────────────
// Message & Context Types
// ─────────────────────────────────────────────────────────────────────────────

export interface ContextBreakdown {
  system_context_tokens: number
  kb_context_tokens: number
  conversation_context_tokens: number
  user_context_tokens: number
}

export interface AgentFlowStep {
  agent: AgentRole
  duration_ms: number
  action: string
  tokens_used?: number
}

export interface ToolUsage {
  tool: string
  duration_ms: number
  tokens?: number
  status: 'success' | 'failure'
}

export interface MessageInsight {
  message_id: string
  query: string
  response: string
  timestamp: string

  // Agent info
  agent_role: AgentRole
  agent_flow: AgentFlowStep[]

  // Context info (V1.8)
  total_tokens: number
  context_tokens: number
  context_breakdown: ContextBreakdown
  cache_hit: boolean
  query_type: QueryType

  // Performance
  duration_ms: number
  tools_used: ToolUsage[]

  // Status
  status: 'success' | 'failure' | 'partial'
  error_message?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Session Insights
// ─────────────────────────────────────────────────────────────────────────────

export interface AgentContribution {
  agent: AgentRole
  query_count: number
  total_duration_ms: number
  total_tokens: number
  success_rate: number
  avg_response_time: number
  percentage: number // % of total queries handled
}

export interface TokenMetrics {
  total_tokens_used: number
  avg_tokens_per_query: number
  token_timeline: Array<{
    timestamp: string
    tokens: number
    query_type: QueryType
  }>
  breakdown: {
    system_context: number
    kb_context: number
    conversation_context: number
    user_context: number
  }
}

export interface CacheMetrics {
  total_queries: number
  cache_hits: number
  cache_misses: number
  hit_rate: number // percentage
  avg_cache_response_time: number
  avg_fresh_response_time: number
  time_saved_ms: number
}

export interface CostMetrics {
  total_cost_usd: number
  cost_per_query_usd: number
  baseline_cost_usd: number // What it would have cost without V1.8
  savings_usd: number
  savings_percentage: number
}

export interface SessionInsights {
  session_id: string
  started_at: string
  last_activity: string

  // Aggregate stats
  total_queries: number
  total_responses: number
  total_duration_ms: number
  avg_response_time_ms: number
  success_rate: number

  // Agent stats
  agent_contributions: AgentContribution[]
  primary_agent: AgentRole // Agent that handled most queries

  // Token & Context stats (V1.8)
  token_metrics: TokenMetrics
  cache_metrics: CacheMetrics
  cost_metrics: CostMetrics

  // Query distribution
  query_types: Record<QueryType, number>

  // Messages with full insights
  messages: MessageInsight[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Real-time Updates
// ─────────────────────────────────────────────────────────────────────────────

export interface LiveMetrics {
  current_query_count: number
  active_agent: AgentRole | null
  current_tokens_used: number
  current_cache_hit_rate: number
  last_update: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Chart Data Types
// ─────────────────────────────────────────────────────────────────────────────

export interface AgentContributionChartData {
  agent: string
  value: number
  color: string
  percentage: number
}

export interface TokenTimelineChartData {
  timestamp: string
  tokens: number
  queryType: QueryType
  cached: boolean
}

export interface ContextBreakdownChartData {
  category: 'System' | 'KB' | 'Conversation' | 'User'
  tokens: number
  percentage: number
  color: string
}

// ─────────────────────────────────────────────────────────────────────────────
// UI State Types
// ─────────────────────────────────────────────────────────────────────────────

export interface PanelState {
  isOpen: boolean
  selectedTab: 'overview' | 'agents' | 'context' | 'performance'
  expandedMessageId: string | null
}

export interface PanelPreferences {
  autoOpen: boolean
  defaultTab: 'overview' | 'agents' | 'context' | 'performance'
  showMiniStats: boolean
  updateInterval: number // milliseconds
}

// ─────────────────────────────────────────────────────────────────────────────
// Agent Colors (for consistency across components)
// ─────────────────────────────────────────────────────────────────────────────

export const AGENT_COLORS: Record<AgentRole, { bg: string; text: string; light: string; dark: string }> = {
  'Manager': {
    bg: 'bg-blue-500',
    text: 'text-blue-600',
    light: 'bg-blue-50',
    dark: 'bg-blue-900'
  },
  'Solar Controller': {
    bg: 'bg-orange-500',
    text: 'text-orange-600',
    light: 'bg-orange-50',
    dark: 'bg-orange-900'
  },
  'Energy Systems Monitor': {
    bg: 'bg-orange-500',
    text: 'text-orange-600',
    light: 'bg-orange-50',
    dark: 'bg-orange-900'
  },
  'Energy Orchestrator': {
    bg: 'bg-purple-500',
    text: 'text-purple-600',
    light: 'bg-purple-50',
    dark: 'bg-purple-900'
  },
  'Energy Operations Manager': {
    bg: 'bg-purple-500',
    text: 'text-purple-600',
    light: 'bg-purple-50',
    dark: 'bg-purple-900'
  },
  'Research Agent': {
    bg: 'bg-green-500',
    text: 'text-green-600',
    light: 'bg-green-50',
    dark: 'bg-green-900'
  },
  'Energy Systems Research Consultant': {
    bg: 'bg-green-500',
    text: 'text-green-600',
    light: 'bg-green-50',
    dark: 'bg-green-900'
  },
  'System': {
    bg: 'bg-gray-500',
    text: 'text-gray-600',
    light: 'bg-gray-50',
    dark: 'bg-gray-900'
  }
}

export const QUERY_TYPE_COLORS: Record<QueryType, string> = {
  system: '#3b82f6', // blue
  research: '#10b981', // green
  planning: '#8b5cf6', // purple
  general: '#6b7280' // gray
}

export const CONTEXT_COLORS = {
  system: '#3b82f6', // blue
  kb: '#10b981', // green
  conversation: '#8b5cf6', // purple
  user: '#f59e0b' // amber
}
