import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { CheckCircle, XCircle, ExternalLink, Users, Clock } from 'lucide-react'
import { approvalApi } from '../api/approvals'
import StatusBadge from '../components/StatusBadge'
import PriorityBadge from '../components/PriorityBadge'
import ProcessTypeIcon from '../components/ProcessTypeIcon'
import ConfidenceBar from '../components/ConfidenceBar'
import type { ProcessType } from '../types'

export default function Approvals() {
  const qc = useQueryClient()
  const [filter, setFilter] = useState<'pending' | 'approved' | 'rejected'>('pending')
  const [reviewers, setReviewers] = useState<Record<number, string>>({})
  const [notes, setNotes] = useState<Record<number, string>>({})

  const { data = [], isLoading } = useQuery({
    queryKey: ['approvals', filter],
    queryFn: () => approvalApi.list(filter),
    refetchInterval: filter === 'pending' ? 5_000 : false,
  })

  const approve = useMutation({
    mutationFn: (id: number) => approvalApi.approve(id, reviewers[id] || 'admin', notes[id]),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approvals'] }),
  })
  const reject = useMutation({
    mutationFn: (id: number) => approvalApi.reject(id, reviewers[id] || 'admin', notes[id]),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['approvals'] }),
  })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Approval Queue</h1>
          <p className="text-sm text-gray-500 mt-0.5">Review and authorize actions flagged by the agent</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        {(['pending', 'approved', 'rejected'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors capitalize ${
              filter === tab ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {isLoading && <div className="text-gray-400 text-sm">Loading…</div>}

      {!isLoading && data.length === 0 && (
        <div className="card text-center py-16">
          <Users size={40} className="mx-auto text-gray-200 mb-3" />
          <p className="text-gray-500 font-medium">No {filter} approvals</p>
          <p className="text-sm text-gray-400 mt-1">
            {filter === 'pending' ? 'All clear — no actions waiting for review' : `No ${filter} items yet`}
          </p>
        </div>
      )}

      <div className="space-y-4">
        {data.map(approval => {
          const p = approval.process
          const isPending = approval.status === 'pending'

          return (
            <div
              key={approval.id}
              className={`card border-l-4 ${
                approval.status === 'pending' ? 'border-l-orange-400' :
                approval.status === 'approved' ? 'border-l-emerald-400' :
                'border-l-red-400'
              }`}
            >
              <div className="flex items-start gap-4">
                {p && <ProcessTypeIcon type={p.process_type as ProcessType} size={15} />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <h3 className="font-semibold text-gray-900">
                      {p?.title ?? `Process #${approval.process_id}`}
                    </h3>
                    {p && <StatusBadge status={p.status} size="sm" />}
                    {p && <PriorityBadge priority={p.priority as any} />}
                    <Link to={`/processes/${approval.process_id}`} className="text-blue-400 hover:text-blue-600">
                      <ExternalLink size={13} />
                    </Link>
                  </div>

                  <div className="mt-2 bg-orange-50 rounded-lg px-3 py-2 text-sm text-orange-800">
                    <span className="font-medium">Reason: </span>{approval.reason}
                  </div>

                  {p && (
                    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                      <span>Type: <strong>{p.process_type.replace('_', ' ')}</strong></span>
                      {p.extracted_data?.amount && (
                        <span>Amount: <strong className="text-gray-800">${Number(p.extracted_data.amount).toLocaleString()}</strong></span>
                      )}
                      {p.extracted_data?.email && <span>Contact: {p.extracted_data.email}</span>}
                      <div className="w-28"><ConfidenceBar value={p.confidence_score} /></div>
                      <span className="flex items-center gap-1">
                        <Clock size={11} />{format(new Date(approval.created_at), 'MMM d, HH:mm')}
                      </span>
                    </div>
                  )}

                  {!isPending && approval.reviewer && (
                    <div className="mt-2 text-xs text-gray-500">
                      {approval.status === 'approved' ? '✓' : '✗'} {approval.status} by{' '}
                      <strong>{approval.reviewer}</strong>
                      {approval.reviewed_at && ` at ${format(new Date(approval.reviewed_at), 'MMM d, HH:mm')}`}
                      {approval.review_notes && ` — "${approval.review_notes}"`}
                    </div>
                  )}

                  {isPending && (
                    <div className="flex items-center gap-2 mt-3 flex-wrap">
                      <input
                        className="input w-36 text-xs"
                        placeholder="Reviewer"
                        value={reviewers[approval.id] ?? 'admin'}
                        onChange={e => setReviewers(prev => ({ ...prev, [approval.id]: e.target.value }))}
                      />
                      <input
                        className="input flex-1 min-w-40 text-xs"
                        placeholder="Notes (optional)"
                        value={notes[approval.id] ?? ''}
                        onChange={e => setNotes(prev => ({ ...prev, [approval.id]: e.target.value }))}
                      />
                      <button
                        className="btn-primary bg-emerald-600 hover:bg-emerald-700 text-xs py-1.5"
                        onClick={() => approve.mutate(approval.id)}
                        disabled={approve.isPending}
                      >
                        <CheckCircle size={13} /> Approve
                      </button>
                      <button
                        className="btn-danger text-xs py-1.5"
                        onClick={() => reject.mutate(approval.id)}
                        disabled={reject.isPending}
                      >
                        <XCircle size={13} /> Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
