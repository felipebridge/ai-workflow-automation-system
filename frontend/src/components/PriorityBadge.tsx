import clsx from 'clsx'
import type { Priority } from '../types'

const PRIORITY_CONFIG: Record<Priority, { label: string; dot: string; text: string }> = {
  low: { label: 'Low', dot: 'bg-gray-400', text: 'text-gray-600' },
  medium: { label: 'Medium', dot: 'bg-blue-400', text: 'text-blue-700' },
  high: { label: 'High', dot: 'bg-orange-400', text: 'text-orange-700' },
  critical: { label: 'Critical', dot: 'bg-red-500', text: 'text-red-700' },
}

interface Props {
  priority: Priority
}

export default function PriorityBadge({ priority }: Props) {
  const cfg = PRIORITY_CONFIG[priority] ?? PRIORITY_CONFIG.medium
  return (
    <span className={clsx('inline-flex items-center gap-1.5 text-xs font-medium', cfg.text)}>
      <span className={clsx('w-1.5 h-1.5 rounded-full', cfg.dot)} />
      {cfg.label}
    </span>
  )
}
