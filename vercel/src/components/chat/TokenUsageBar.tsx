// ═══════════════════════════════════════════════════════════════════════════
// FILE: vercel/src/components/chat/TokenUsageBar.tsx
// PURPOSE: Visual token usage display with context breakdown
// ═══════════════════════════════════════════════════════════════════════════

'use client'

import { motion } from 'framer-motion'
import { TrendingDown, TrendingUp, Minus } from 'lucide-react'
import { CONTEXT_COLORS } from '@/types/insights'

interface TokenUsageBarProps {
  totalTokens: number
  breakdown?: {
    system_context?: number
    kb_context?: number
    conversation_context?: number
    user_context?: number
  }
  maxTokens?: number
  showBreakdown?: boolean
  showComparison?: boolean
  comparisonValue?: number // Previous average or baseline
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
  className?: string
}

export default function TokenUsageBar({
  totalTokens,
  breakdown,
  maxTokens = 8000, // Default max (pre-V1.8 average)
  showBreakdown = true,
  showComparison = false,
  comparisonValue,
  size = 'md',
  animated = true,
  className = ''
}: TokenUsageBarProps) {
  const percentage = Math.min((totalTokens / maxTokens) * 100, 100)

  // Calculate breakdown percentages
  const breakdownPercentages = breakdown ? {
    system: (breakdown.system_context || 0) / totalTokens * 100,
    kb: (breakdown.kb_context || 0) / totalTokens * 100,
    conversation: (breakdown.conversation_context || 0) / totalTokens * 100,
    user: (breakdown.user_context || 0) / totalTokens * 100
  } : null

  // Calculate comparison
  const comparisonDiff = comparisonValue ? totalTokens - comparisonValue : 0
  const comparisonPercentage = comparisonValue ? ((totalTokens - comparisonValue) / comparisonValue) * 100 : 0

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3'
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Token count and comparison */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900">
            {totalTokens.toLocaleString()} tokens
          </span>

          {showComparison && comparisonValue && (
            <div className={`
              flex items-center gap-1 text-xs font-medium
              ${comparisonDiff < 0 ? 'text-green-600' : comparisonDiff > 0 ? 'text-red-600' : 'text-gray-600'}
            `}>
              {comparisonDiff < 0 && <TrendingDown className="w-3 h-3" />}
              {comparisonDiff > 0 && <TrendingUp className="w-3 h-3" />}
              {comparisonDiff === 0 && <Minus className="w-3 h-3" />}
              <span>
                {Math.abs(comparisonPercentage).toFixed(0)}%
              </span>
            </div>
          )}
        </div>

        <span className="text-xs text-gray-500">
          {percentage.toFixed(0)}% of {maxTokens.toLocaleString()}
        </span>
      </div>

      {/* Progress bar */}
      <div className={`relative w-full ${sizeClasses[size]} bg-gray-200 rounded-full overflow-hidden`}>
        {showBreakdown && breakdownPercentages ? (
          // Segmented bar showing context breakdown
          <div className="flex h-full">
            {breakdownPercentages.system > 0 && (
              <motion.div
                initial={animated ? { width: 0 } : undefined}
                animate={{ width: `${breakdownPercentages.system}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="h-full"
                style={{ backgroundColor: CONTEXT_COLORS.system }}
                title={`System context: ${breakdown?.system_context?.toLocaleString()} tokens`}
              />
            )}
            {breakdownPercentages.kb > 0 && (
              <motion.div
                initial={animated ? { width: 0 } : undefined}
                animate={{ width: `${breakdownPercentages.kb}%` }}
                transition={{ duration: 0.5, ease: "easeOut", delay: 0.1 }}
                className="h-full"
                style={{ backgroundColor: CONTEXT_COLORS.kb }}
                title={`KB context: ${breakdown?.kb_context?.toLocaleString()} tokens`}
              />
            )}
            {breakdownPercentages.conversation > 0 && (
              <motion.div
                initial={animated ? { width: 0 } : undefined}
                animate={{ width: `${breakdownPercentages.conversation}%` }}
                transition={{ duration: 0.5, ease: "easeOut", delay: 0.2 }}
                className="h-full"
                style={{ backgroundColor: CONTEXT_COLORS.conversation }}
                title={`Conversation context: ${breakdown?.conversation_context?.toLocaleString()} tokens`}
              />
            )}
            {breakdownPercentages.user > 0 && (
              <motion.div
                initial={animated ? { width: 0 } : undefined}
                animate={{ width: `${breakdownPercentages.user}%` }}
                transition={{ duration: 0.5, ease: "easeOut", delay: 0.3 }}
                className="h-full"
                style={{ backgroundColor: CONTEXT_COLORS.user }}
                title={`User context: ${breakdown?.user_context?.toLocaleString()} tokens`}
              />
            )}
          </div>
        ) : (
          // Single bar
          <motion.div
            initial={animated ? { width: 0 } : undefined}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={`
              h-full rounded-full
              ${percentage < 40 ? 'bg-green-500' :
                percentage < 70 ? 'bg-yellow-500' :
                  'bg-red-500'}
            `}
          />
        )}
      </div>

      {/* Breakdown legend */}
      {showBreakdown && breakdownPercentages && breakdown && (
        <div className="grid grid-cols-2 gap-2 text-xs">
          {(breakdown.system_context ?? 0) > 0 && (
            <div className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CONTEXT_COLORS.system }}
              />
              <span className="text-gray-600">
                System: <span className="font-medium text-gray-900">
                  {(breakdown.system_context ?? 0).toLocaleString()}
                </span>
              </span>
            </div>
          )}
          {(breakdown.kb_context ?? 0) > 0 && (
            <div className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CONTEXT_COLORS.kb }}
              />
              <span className="text-gray-600">
                KB: <span className="font-medium text-gray-900">
                  {(breakdown.kb_context ?? 0).toLocaleString()}
                </span>
              </span>
            </div>
          )}
          {(breakdown.conversation_context ?? 0) > 0 && (
            <div className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CONTEXT_COLORS.conversation }}
              />
              <span className="text-gray-600">
                Conversation: <span className="font-medium text-gray-900">
                  {(breakdown.conversation_context ?? 0).toLocaleString()}
                </span>
              </span>
            </div>
          )}
          {(breakdown.user_context ?? 0) > 0 && (
            <div className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: CONTEXT_COLORS.user }}
              />
              <span className="text-gray-600">
                User: <span className="font-medium text-gray-900">
                  {(breakdown.user_context ?? 0).toLocaleString()}
                </span>
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Simplified Mini Version
// ─────────────────────────────────────────────────────────────────────────────

interface TokenUsageMiniProps {
  tokens: number
  maxTokens?: number
  showLabel?: boolean
}

export function TokenUsageMini({ tokens, maxTokens = 8000, showLabel = true }: TokenUsageMiniProps) {
  const percentage = Math.min((tokens / maxTokens) * 100, 100)

  return (
    <div className="flex items-center gap-2">
      {showLabel && (
        <span className="text-xs font-medium text-gray-600 whitespace-nowrap">
          {tokens.toLocaleString()} tk
        </span>
      )}
      <div className="relative w-full h-1 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          className={`
            h-full
            ${percentage < 40 ? 'bg-green-500' :
              percentage < 70 ? 'bg-yellow-500' :
                'bg-red-500'}
          `}
        />
      </div>
    </div>
  )
}
