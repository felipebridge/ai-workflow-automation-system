import { format } from 'date-fns'
import type { AuditLog } from '../types'
import clsx from 'clsx'

const EVENT_COLORS: Record<string, string> = {
  'process.received': 'bg-gray-400',
  'pipeline.started': 'bg-blue-400',
  'classification.completed': 'bg-violet-500',
  'extraction.completed': 'bg-blue-500',
  'validation.completed': 'bg-cyan-500',
  'decision.made': 'bg-amber-500',
  'approval.queued': 'bg-orange-500',
  'approval.approved': 'bg-emerald-500',
  'approval.rejected': 'bg-red-500',
  'action.executed': 'bg-emerald-600',
  'pipeline.completed': 'bg-emerald-500',
  'pipeline.failed': 'bg-red-600',
}

const EVENT_LABELS: Record<string, string> = {
  'process.received': 'Input received',
  'pipeline.started': 'Pipeline started',
  'classification.completed': 'Classified',
  'extraction.completed': 'Data extracted',
  'validation.completed': 'Validation complete',
  'decision.made': 'Decision made',
  'approval.queued': 'Queued for approval',
  'approval.approved': 'Approved',
  'approval.rejected': 'Rejected',
  'action.executed': 'Action executed',
  'pipeline.completed': 'Pipeline completed',
  'pipeline.failed': 'Pipeline failed',
}

interface Props {
  logs: AuditLog[]
}

export default function Timeline({ logs }: Props) {
  if (!logs.length) {
    return <p className="text-sm text-gray-400 italic">No audit events yet.</p>
  }

  return (
    <ol className="relative border-l border-gray-200 ml-2 space-y-4">
      {logs.map((log, idx) => {
        const color = EVENT_COLORS[log.event_type] ?? 'bg-gray-400'
        const label = EVENT_LABELS[log.event_type] ?? log.event_type
        const isLast = idx === logs.length - 1

        return (
          <li key={log.id} className="ml-4">
            <div
              className={clsx(
                'absolute -left-1.5 mt-1.5 w-3 h-3 rounded-full border-2 border-white',
                color
              )}
            />
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className={clsx('text-sm font-medium', isLast ? 'text-gray-900' : 'text-gray-700')}>
                  {label}
                </p>
                {Object.keys(log.event_data).length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {Object.entries(log.event_data).slice(0, 4).map(([k, v]) => (
                      <span key={k} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">
                        {k}: {String(v).slice(0, 40)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <time className="text-xs text-gray-400 whitespace-nowrap flex-shrink-0">
                {format(new Date(log.created_at), 'MMM d, HH:mm:ss')}
              </time>
            </div>
          </li>
        )
      })}
    </ol>
  )
}
