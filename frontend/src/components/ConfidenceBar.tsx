import clsx from 'clsx'

interface Props {
  value: number
  showLabel?: boolean
}

export default function ConfidenceBar({ value, showLabel = true }: Props) {
  const color =
    value >= 78 ? 'bg-emerald-500' :
    value >= 50 ? 'bg-amber-400' :
    'bg-red-400'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-500', color)}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-mono text-gray-500 w-9 text-right">
          {value.toFixed(0)}%
        </span>
      )}
    </div>
  )
}
