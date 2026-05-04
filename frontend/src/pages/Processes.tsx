import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { Search, Filter, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react'
import { processApi } from '../api/processes'
import StatusBadge from '../components/StatusBadge'
import PriorityBadge from '../components/PriorityBadge'
import ConfidenceBar from '../components/ConfidenceBar'
import ProcessTypeIcon from '../components/ProcessTypeIcon'
import type { ProcessStatus, ProcessType } from '../types'

const STATUSES = ['', 'pending', 'processing', 'completed', 'failed', 'awaiting_approval', 'approved', 'rejected', 'escalated']
const TYPES = ['', 'invoice', 'customer_request', 'claim', 'lead', 'support_ticket', 'admin_case', 'payment_request', 'other']
const PRIORITIES = ['', 'low', 'medium', 'high', 'critical']

export default function Processes() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [processType, setProcessType] = useState('')
  const [priority, setPriority] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['processes', page, search, status, processType, priority],
    queryFn: () => processApi.list({ page, per_page: 15, search, status, process_type: processType, priority }),
    refetchInterval: 6_000,
  })

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); setPage(1) }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Processes</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {data ? `${data.total} total` : '—'} · Auto-refreshes every 6s
          </p>
        </div>
        <Link to="/new" className="btn-primary">
          + New Process
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              className="input pl-8"
              placeholder="Search title or content..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
            />
          </div>
          <select className="select w-40" value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}>
            {STATUSES.map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
          </select>
          <select className="select w-44" value={processType} onChange={e => { setProcessType(e.target.value); setPage(1) }}>
            {TYPES.map(t => <option key={t} value={t}>{t ? t.replace('_', ' ') : 'All Types'}</option>)}
          </select>
          <select className="select w-36" value={priority} onChange={e => { setPriority(e.target.value); setPage(1) }}>
            {PRIORITIES.map(p => <option key={p} value={p}>{p || 'All Priorities'}</option>)}
          </select>
        </form>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-8">#</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Process</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">Type</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-36">Status</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-24">Priority</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-28">Confidence</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-32">Created</th>
                <th className="w-12" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {isLoading && (
                <tr><td colSpan={8} className="text-center py-12 text-gray-400">Loading…</td></tr>
              )}
              {!isLoading && !data?.items.length && (
                <tr><td colSpan={8} className="text-center py-12 text-gray-400">No processes found</td></tr>
              )}
              {data?.items.map(p => (
                <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs">{p.id}</td>
                  <td className="px-4 py-3 max-w-xs">
                    <div className="flex items-center gap-2">
                      <ProcessTypeIcon type={p.process_type as ProcessType} size={13} />
                      <span className="font-medium text-gray-800 truncate">
                        {p.title ?? p.raw_input.slice(0, 55) + '…'}
                      </span>
                    </div>
                    {p.extracted_data?.email && (
                      <p className="text-xs text-gray-400 ml-8 mt-0.5">{p.extracted_data.email}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-600 capitalize">{p.process_type.replace('_', ' ')}</span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={p.status as ProcessStatus} size="sm" />
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={p.priority as any} />
                  </td>
                  <td className="px-4 py-3 w-28">
                    <ConfidenceBar value={p.confidence_score} />
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {format(new Date(p.created_at), 'MMM d, HH:mm')}
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/processes/${p.id}`} className="text-blue-500 hover:text-blue-700">
                      <ExternalLink size={14} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <p className="text-xs text-gray-500">
              Page {data.page} of {data.pages} · {data.total} total
            </p>
            <div className="flex items-center gap-1">
              <button
                className="btn-secondary px-2 py-1"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                <ChevronLeft size={14} />
              </button>
              <button
                className="btn-secondary px-2 py-1"
                disabled={page >= data.pages}
                onClick={() => setPage(p => p + 1)}
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
