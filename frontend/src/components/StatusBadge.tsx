import clsx from 'clsx'
import type { ProcessStatus } from '../types'

const STATUS_CONFIG: Record<ProcessStatus, { label: string; classes: string }> = {
  pending: { label: 'Pending', classes: 'bg-amber-50 text-amber-700 ring-amber-600/20' },
  processing: { label: 'Processing', classes: 'bg-blue-50 text-blue-700 ring-blue-600/20 animate-pulse' },
  completed: { label: 'Completed', classes: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20' },
  failed: { label: 'Failed', classes: 'bg-red-50 text-red-700 ring-red-600/20' },
  awaiting_approval: { label: 'Awaiting Approval', classes: 'bg-orange-50 text-orange-700 ring-orange-600/20' },
  approved: { label: 'Approved', classes: 'bg-emerald-50 text-emerald-800 ring-emerald-600/20' },
  rejected: { label: 'Rejected', classes: 'bg-red-50 text-red-800 ring-red-600/20' },
  escalated: { label: 'Escalated', classes: 'bg-purple-50 text-purple-700 ring-purple-600/20' },
}

interface Props {
  status: ProcessStatus
  size?: 'sm' | 'md'
}

export default function StatusBadge({ status, size = 'md' }: Props) {
  const config = STATUS_CONFIG[status] ?? { label: status, classes: 'bg-gray-50 text-gray-600 ring-gray-500/20' }
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-medium ring-1 ring-inset',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs',
        config.classes
      )}
    >
      {config.label}
    </span>
  )
}
