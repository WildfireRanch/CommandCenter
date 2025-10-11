// ═══════════════════════════════════════════════════════════════════════════
// FILE: vercel/src/components/chat/AgentBadge.tsx
// PURPOSE: Reusable agent indicator badge with color coding and animations
// ═══════════════════════════════════════════════════════════════════════════

'use client'

import { motion } from 'framer-motion'
import { Bot, Cpu, Lightbulb, Zap, Settings } from 'lucide-react'
import { AGENT_COLORS, type AgentRole } from '@/types/insights'

interface AgentBadgeProps {
  agent: AgentRole
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  showLabel?: boolean
  animated?: boolean
  pulse?: boolean
  className?: string
}

const AGENT_ICONS: Record<AgentRole, React.ReactNode> = {
  'Manager': <Settings className="w-full h-full" />,
  'Solar Controller': <Zap className="w-full h-full" />,
  'Energy Systems Monitor': <Zap className="w-full h-full" />,
  'Energy Orchestrator': <Cpu className="w-full h-full" />,
  'Energy Operations Manager': <Cpu className="w-full h-full" />,
  'Research Agent': <Lightbulb className="w-full h-full" />,
  'Energy Systems Research Consultant': <Lightbulb className="w-full h-full" />,
  'System': <Bot className="w-full h-full" />
}

const AGENT_SHORT_NAMES: Record<AgentRole, string> = {
  'Manager': 'Manager',
  'Solar Controller': 'Solar',
  'Energy Systems Monitor': 'Solar',
  'Energy Orchestrator': 'Orchestrator',
  'Energy Operations Manager': 'Orchestrator',
  'Research Agent': 'Research',
  'Energy Systems Research Consultant': 'Research',
  'System': 'System'
}

const SIZE_CLASSES = {
  sm: {
    badge: 'px-2 py-0.5 text-xs gap-1',
    icon: 'w-3 h-3'
  },
  md: {
    badge: 'px-2.5 py-1 text-sm gap-1.5',
    icon: 'w-4 h-4'
  },
  lg: {
    badge: 'px-3 py-1.5 text-base gap-2',
    icon: 'w-5 h-5'
  }
}

export default function AgentBadge({
  agent,
  size = 'md',
  showIcon = true,
  showLabel = true,
  animated = true,
  pulse = false,
  className = ''
}: AgentBadgeProps) {
  const colors = AGENT_COLORS[agent]
  const icon = AGENT_ICONS[agent]
  const shortName = AGENT_SHORT_NAMES[agent]
  const sizeClasses = SIZE_CLASSES[size]

  const badgeContent = (
    <div
      className={`
        inline-flex items-center rounded-full font-medium
        ${sizeClasses.badge}
        ${colors.light} ${colors.text}
        border border-current border-opacity-20
        ${pulse ? 'animate-pulse' : ''}
        ${className}
      `}
    >
      {showIcon && (
        <span className={sizeClasses.icon}>
          {icon}
        </span>
      )}
      {showLabel && (
        <span>{shortName}</span>
      )}
    </div>
  )

  if (!animated) {
    return badgeContent
  }

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{
        type: "spring",
        stiffness: 500,
        damping: 30
      }}
      whileHover={{ scale: 1.05 }}
    >
      {badgeContent}
    </motion.div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Specialized Variants
// ─────────────────────────────────────────────────────────────────────────────

interface AgentDotProps {
  agent: AgentRole
  size?: number
  pulse?: boolean
}

export function AgentDot({ agent, size = 8, pulse = false }: AgentDotProps) {
  const colors = AGENT_COLORS[agent]

  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      className={`
        rounded-full ${colors.bg}
        ${pulse ? 'animate-pulse' : ''}
      `}
      style={{ width: size, height: size }}
    />
  )
}

interface AgentAvatarProps {
  agent: AgentRole
  size?: 'sm' | 'md' | 'lg'
  showTooltip?: boolean
}

export function AgentAvatar({ agent, size = 'md', showTooltip = true }: AgentAvatarProps) {
  const colors = AGENT_COLORS[agent]
  const icon = AGENT_ICONS[agent]

  const sizeMap = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10'
  }

  const iconSizeMap = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  }

  return (
    <motion.div
      initial={{ scale: 0, rotate: -180 }}
      animate={{ scale: 1, rotate: 0 }}
      transition={{
        type: "spring",
        stiffness: 400,
        damping: 20
      }}
      whileHover={{ scale: 1.1 }}
      className={`
        ${sizeMap[size]}
        ${colors.bg}
        rounded-full
        flex items-center justify-center
        text-white
        shadow-md
        cursor-pointer
        relative
        group
      `}
      title={showTooltip ? agent : undefined}
    >
      <div className={iconSizeMap[size]}>
        {icon}
      </div>

      {showTooltip && (
        <div className="
          absolute bottom-full left-1/2 -translate-x-1/2 mb-2
          opacity-0 group-hover:opacity-100
          transition-opacity duration-200
          pointer-events-none
          bg-gray-900 text-white text-xs rounded px-2 py-1
          whitespace-nowrap
        ">
          {agent}
        </div>
      )}
    </motion.div>
  )
}
