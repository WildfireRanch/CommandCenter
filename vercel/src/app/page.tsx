'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Activity, Battery, Sun, MessageSquare } from 'lucide-react'

interface HealthStatus {
  status: string
  timestamp?: string
}

interface EnergyData {
  battery_soc?: number
  solar_power?: number
  timestamp?: string
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [energy, setEnergy] = useState<EnergyData | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.wildfireranch.us'

        // Fetch health
        const healthRes = await fetch(`${API_URL}/health`)
        if (healthRes.ok) {
          setHealth(await healthRes.json())
        }

        // Fetch energy
        const energyRes = await fetch(`${API_URL}/energy/latest`)
        if (energyRes.ok) {
          setEnergy(await energyRes.json())
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sun className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">CommandCenter</h1>
                <p className="text-sm text-gray-500">Wildfire Ranch Energy Management</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Activity className={`w-5 h-5 ${health?.status === 'healthy' ? 'text-green-500' : 'text-gray-400'}`} />
              <span className="text-sm text-gray-600">
                {health?.status === 'healthy' ? 'System Online' : 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Welcome Section */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome to CommandCenter</h2>
          <p className="text-lg text-gray-600">
            Monitor and manage your solar energy system with AI-powered insights.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Battery SOC */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <Battery className="w-8 h-8 text-green-600" />
              <span className="text-sm font-medium text-gray-500">BATTERY</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {energy?.battery_soc?.toFixed(1) || '--'}%
            </div>
            <p className="text-sm text-gray-500 mt-1">State of Charge</p>
          </div>

          {/* Solar Power */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <Sun className="w-8 h-8 text-yellow-500" />
              <span className="text-sm font-medium text-gray-500">SOLAR</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {energy?.solar_power?.toFixed(0) || '--'} W
            </div>
            <p className="text-sm text-gray-500 mt-1">Current Production</p>
          </div>

          {/* System Status */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-blue-600" />
              <span className="text-sm font-medium text-gray-500">STATUS</span>
            </div>
            <div className="text-3xl font-bold text-green-600">
              {health?.status === 'healthy' ? 'Healthy' : 'Unknown'}
            </div>
            <p className="text-sm text-gray-500 mt-1">System Health</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Energy Dashboard */}
          <Link
            href="/dashboard"
            className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-8 text-white hover:shadow-xl transition-shadow group"
          >
            <div className="flex items-start justify-between mb-4">
              <Sun className="w-12 h-12" />
              <span className="text-blue-100">→</span>
            </div>
            <h3 className="text-2xl font-bold mb-2">Energy Dashboard</h3>
            <p className="text-blue-100">
              View real-time energy production, consumption, and battery status with interactive charts.
            </p>
          </Link>

          {/* Chat with Agent */}
          <Link
            href="/chat"
            className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg p-8 text-white hover:shadow-xl transition-shadow group"
          >
            <div className="flex items-start justify-between mb-4">
              <MessageSquare className="w-12 h-12" />
              <span className="text-green-100">→</span>
            </div>
            <h3 className="text-2xl font-bold mb-2">Solar Controller Agent</h3>
            <p className="text-green-100">
              Ask questions about your energy system and get AI-powered recommendations.
            </p>
          </Link>
        </div>

        {/* Info Banner */}
        <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <Activity className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-blue-900 mb-1">Connected to Railway API</h4>
              <p className="text-sm text-blue-800">
                This frontend is connected to your CommandCenter backend at <code className="bg-blue-100 px-2 py-0.5 rounded text-xs">{process.env.NEXT_PUBLIC_API_URL}</code>
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2025 Wildfire Ranch | CommandCenter Energy Management System
          </p>
        </div>
      </footer>
    </div>
  )
}
