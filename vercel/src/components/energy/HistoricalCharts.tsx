'use client'

import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

interface HistoricalDataPoint {
  timestamp: string
  pv_power?: number
  battery_power?: number
  load_power?: number
  grid_power?: number
  soc?: number
  victron_soc?: number
  voltage?: number
  current?: number
  temperature?: number
}

export function PowerFlowChart({ data }: { data: HistoricalDataPoint[] }) {
  const chartData = data.map(d => ({
    time: format(new Date(d.timestamp), 'HH:mm'),
    solar: d.pv_power || 0,
    load: d.load_power || 0,
    battery: Math.abs(d.battery_power || 0),
    grid: Math.abs(d.grid_power || 0)
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 12 }}
          interval="preserveStartEnd"
        />
        <YAxis
          label={{ value: 'Power (W)', angle: -90, position: 'insideLeft' }}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          formatter={(value: number) => `${value.toLocaleString()}W`}
        />
        <Legend />
        <Area
          type="monotone"
          dataKey="solar"
          stackId="1"
          stroke="#f59e0b"
          fill="#fef3c7"
          name="Solar"
        />
        <Area
          type="monotone"
          dataKey="battery"
          stackId="2"
          stroke="#10b981"
          fill="#d1fae5"
          name="Battery"
        />
        <Area
          type="monotone"
          dataKey="load"
          stackId="3"
          stroke="#3b82f6"
          fill="#dbeafe"
          name="Load"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function SOCComparisonChart({ data }: { data: HistoricalDataPoint[] }) {
  const chartData = data
    .filter(d => d.victron_soc !== undefined && d.victron_soc !== null)
    .map(d => ({
      time: format(new Date(d.timestamp), 'HH:mm'),
      victron: d.victron_soc,
      solark: d.soc,
      difference: Math.abs((d.victron_soc || 0) - (d.soc || 0))
    }))

  return (
    <ResponsiveContainer width="100%" height={300}>
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
        <Line
          type="monotone"
          dataKey="victron"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          name="Victron (Accurate)"
        />
        <Line
          type="monotone"
          dataKey="solark"
          stroke="#94a3b8"
          strokeWidth={2}
          dot={false}
          strokeDasharray="5 5"
          name="SolArk (Estimated)"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function BatteryVoltageChart({ data }: { data: HistoricalDataPoint[] }) {
  const chartData = data
    .filter(d => d.voltage !== undefined && d.voltage !== null)
    .map(d => ({
      time: format(new Date(d.timestamp), 'HH:mm'),
      voltage: d.voltage
    }))

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 12 }}
          interval="preserveStartEnd"
        />
        <YAxis
          label={{ value: 'Voltage (V)', angle: -90, position: 'insideLeft' }}
          tick={{ fontSize: 12 }}
          domain={[48, 58]}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          formatter={(value: number) => `${value.toFixed(2)}V`}
        />
        <Area
          type="monotone"
          dataKey="voltage"
          stroke="#3b82f6"
          fill="#dbeafe"
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function BatteryCurrentChart({ data }: { data: HistoricalDataPoint[] }) {
  const chartData = data
    .filter(d => d.current !== undefined && d.current !== null)
    .map(d => ({
      time: format(new Date(d.timestamp), 'HH:mm'),
      current: d.current,
      charging: d.current && d.current > 0 ? d.current : 0,
      discharging: d.current && d.current < 0 ? Math.abs(d.current) : 0
    }))

  return (
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 12 }}
          interval="preserveStartEnd"
        />
        <YAxis
          label={{ value: 'Current (A)', angle: -90, position: 'insideLeft' }}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          formatter={(value: number) => `${value.toFixed(1)}A`}
        />
        <Legend />
        <Area
          type="monotone"
          dataKey="charging"
          stackId="1"
          stroke="#10b981"
          fill="#d1fae5"
          name="Charging"
        />
        <Area
          type="monotone"
          dataKey="discharging"
          stackId="2"
          stroke="#f59e0b"
          fill="#fef3c7"
          name="Discharging"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function BatteryTemperatureChart({ data }: { data: HistoricalDataPoint[] }) {
  const chartData = data
    .filter(d => d.temperature !== undefined && d.temperature !== null)
    .map(d => ({
      time: format(new Date(d.timestamp), 'HH:mm'),
      temperature: d.temperature
    }))

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 12 }}
          interval="preserveStartEnd"
        />
        <YAxis
          label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb' }}
          formatter={(value: number) => `${value.toFixed(1)}°C (${((value * 9/5) + 32).toFixed(1)}°F)`}
        />
        <Line
          type="monotone"
          dataKey="temperature"
          stroke="#f59e0b"
          strokeWidth={2}
          dot={false}
          name="Temperature"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
