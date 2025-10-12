'use client'

interface TimeRangeSelectorProps {
  selected: string
  onChange: (range: string) => void
}

const timeRanges = [
  { value: '6', label: '6h' },
  { value: '12', label: '12h' },
  { value: '24', label: '24h' },
  { value: '48', label: '48h' },
  { value: '72', label: '72h' },
  { value: '168', label: '7d' },
  { value: '720', label: '30d' },
]

export function TimeRangeSelector({ selected, onChange }: TimeRangeSelectorProps) {
  return (
    <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
      {timeRanges.map((range) => (
        <button
          key={range.value}
          onClick={() => onChange(range.value)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            selected === range.value
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  )
}
