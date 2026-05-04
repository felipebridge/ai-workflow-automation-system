import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { format } from 'date-fns'
import {
  ArrowLeft, Bot, User, Zap, AlertCircle,
  CheckCircle, XCircle, Clock, Database, Mail,
} from 'lucide-react'
import { processApi } from '../api/processes'
import { approvalApi } from '../api/approvals'
import StatusBadge from '../components/StatusBadge'
import PriorityBadge from '../components/PriorityBadge'
import ConfidenceBar from '../components/ConfidenceBar'
import Timeline from '../components/Timeline'
import ProcessTypeIcon from '../components/ProcessTypeIcon'
import type { ProcessType } from '../types'

export default function ProcessDetail() {
  const { id } = useParams<{ id: string }>()
  const processId = Number(id)
  const qc = useQueryClient()
  const [reviewer, setReviewer] = useState('admin')
  const [notes, setNotes] = useState('')

  const { data: process, isLoading } = useQuery({
    queryKey: ['process', processId],
    queryFn: () => processApi.get(processId),
    refetchInterval: 5_000,
  })

  const approveMutation = useMutation({
    mutationFn: ({ apId }: { apId: number }) => approvalApi.approve(apId, reviewer, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['process', processId] })
      qc.invalidateQueries({ queryKey: ['approvals'] })
    },
  })
  const rejectMutation = useMutation({
    mutationFn: ({ apId }: { apId: number }) => approvalApi.reject(apId, reviewer, notes || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['process', processId] })
      qc.invalidateQueries({ queryKey: ['approvals'] })
    },
  })

  if (isLoading) return <div className="p-6 text-gray-400">Loading…</div>
  if (!process) return <div className="p-6 text-red-500">Process not found</div>

  const decision = process.decisions[0]
  const action = process.actions[0]
  const approval = process.approval
  const extracted = process.extracted_data

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/processes" className="mt-1 text-gray-400 hover:text-gray-600">
          <ArrowLeft size={18} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <ProcessTypeIcon type={process.process_type as ProcessType} size={16} />
            <h1 className="text-xl font-bold text-gray-900">{process.title ?? `Process #${process.id}`}</h1>
            <StatusBadge status={process.status} />
            <PriorityBadge priority={process.priority as any} />
          </div>
          <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
            <span>ID: #{process.id}</span>
            <span>Source: {process.source}</span>
            <span>Created: {format(new Date(process.created_at), 'MMM d, yyyy HH:mm')}</span>
            {process.processed_at && <span>Processed: {format(new Date(process.processed_at), 'HH:mm:ss')}</span>}
          </div>
        </div>
        <div className="flex-shrink-0 text-right">
          <p className="text-xs text-gray-400 mb-1">Confidence</p>
          <div className="w-32">
            <ConfidenceBar value={process.confidence_score} />
          </div>
        </div>
      </div>

      {/* Approval action (if pending) */}
      {approval?.status === 'pending' && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertCircle size={18} className="text-orange-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-orange-900">Human Review Required</h3>
              <p className="text-sm text-orange-700 mt-0.5">{approval.reason}</p>
              {action && (
                <p className="text-xs text-orange-600 mt-1">
                  Proposed action: <strong>{action.action_type.replace('_', ' ')}</strong>
                  {action.parameters?.amount != null && ` · $${Number(action.parameters.amount).toLocaleString()}`}
                  {action.parameters?.to != null && ` → ${String(action.parameters.to)}`}
                </p>
              )}
              <div className="flex items-center gap-3 mt-3 flex-wrap">
                <input
                  className="input w-40 text-xs"
                  placeholder="Reviewer name"
                  value={reviewer}
                  onChange={e => setReviewer(e.target.value)}
                />
                <input
                  className="input flex-1 min-w-40 text-xs"
                  placeholder="Notes (optional)"
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                />
                <button
                  className="btn-primary bg-emerald-600 hover:bg-emerald-700 text-xs"
                  onClick={() => approveMutation.mutate({ apId: approval.id })}
                  disabled={approveMutation.isPending}
                >
                  <CheckCircle size={13} /> Approve
                </button>
                <button
                  className="btn-danger text-xs"
                  onClick={() => rejectMutation.mutate({ apId: approval.id })}
                  disabled={rejectMutation.isPending}
                >
                  <XCircle size={13} /> Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3-column info grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Extracted Data */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5 mb-3">
            <Database size={14} className="text-blue-500" /> Extracted Data
          </h3>
          {extracted ? (
            <div className="space-y-2">
              {[
                { label: 'Name', value: extracted.name },
                { label: 'Email', value: extracted.email },
                { label: 'Phone', value: extracted.phone },
                { label: 'Amount', value: extracted.amount ? `$${Number(extracted.amount).toLocaleString()} ${extracted.currency ?? ''}` : null },
                { label: 'Date', value: extracted.date },
                { label: 'Ref#', value: extracted.order_number },
                { label: 'Summary', value: extracted.summary },
              ].map(({ label, value }) => value && (
                <div key={label} className="flex gap-2">
                  <span className="text-xs text-gray-400 w-14 flex-shrink-0">{label}</span>
                  <span className="text-xs text-gray-800 font-medium break-all">{value}</span>
                </div>
              ))}
              {extracted.urgency_indicators?.length > 0 && (
                <div className="flex gap-2">
                  <span className="text-xs text-gray-400 w-14 flex-shrink-0">Urgency</span>
                  <div className="flex flex-wrap gap-1">
                    {extracted.urgency_indicators.map(u => (
                      <span key={u} className="badge bg-red-50 text-red-700 ring-1 ring-red-200">{u}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-400">Not yet extracted</p>
          )}
        </div>

        {/* Decision */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5 mb-3">
            {decision?.auto_executable ? <Zap size={14} className="text-emerald-500" /> : <User size={14} className="text-orange-500" />}
            AI Decision
          </h3>
          {decision ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className={`badge text-xs ${decision.auto_executable ? 'bg-emerald-50 text-emerald-700' : 'bg-orange-50 text-orange-700'}`}>
                  {decision.auto_executable ? 'Auto Execute' : 'Human Review'}
                </span>
                <span className="badge bg-slate-50 text-slate-600 text-xs">{decision.ai_mode}</span>
              </div>
              <div>
                <p className="text-xs text-gray-400">Reasoning</p>
                <p className="text-xs text-gray-700 mt-0.5">{decision.reasoning}</p>
              </div>
              {decision.validation_errors?.length > 0 && (
                <div>
                  <p className="text-xs text-red-500 font-medium">Validation Errors</p>
                  {decision.validation_errors.map(e => (
                    <p key={e} className="text-xs text-red-600 mt-0.5">• {e}</p>
                  ))}
                </div>
              )}
              {decision.missing_fields?.length > 0 && (
                <div>
                  <p className="text-xs text-amber-500 font-medium">Missing Fields</p>
                  <p className="text-xs text-amber-600">{decision.missing_fields.join(', ')}</p>
                </div>
              )}
              <div>
                <p className="text-xs text-gray-400">Confidence</p>
                <ConfidenceBar value={decision.confidence} />
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-400">Decision pending…</p>
          )}
        </div>

        {/* Action */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5 mb-3">
            <Mail size={14} className="text-violet-500" /> Action
          </h3>
          {action ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="badge bg-violet-50 text-violet-700 text-xs">{action.action_type.replace('_', ' ')}</span>
                <span className={`badge text-xs ${
                  action.status === 'executed' ? 'bg-emerald-50 text-emerald-700' :
                  action.status === 'pending_approval' ? 'bg-orange-50 text-orange-700' :
                  action.status === 'failed' ? 'bg-red-50 text-red-700' :
                  action.status === 'cancelled' ? 'bg-gray-100 text-gray-600' :
                  'bg-amber-50 text-amber-700'
                }`}>{action.status.replace('_', ' ')}</span>
              </div>
              {action.parameters?.to != null && (
                <div className="flex gap-2">
                  <span className="text-xs text-gray-400 w-12">To</span>
                  <span className="text-xs text-gray-700">{String(action.parameters.to)}</span>
                </div>
              )}
              {action.result && (
                <div>
                  <p className="text-xs text-gray-400 mb-1">Result</p>
                  {Object.entries(action.result).filter(([k]) => !['executed_at', 'action_type', 'simulated'].includes(k)).map(([k, v]) => (
                    <p key={k} className="text-xs text-gray-700 font-mono">
                      <span className="text-gray-400">{k}:</span> {String(v)}
                    </p>
                  ))}
                </div>
              )}
              {action.executed_at && (
                <p className="text-xs text-gray-400">
                  Executed: {format(new Date(action.executed_at), 'HH:mm:ss')}
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-400">No action yet</p>
          )}
        </div>
      </div>

      {/* Raw input */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Raw Input</h3>
        <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed">
          {process.raw_input}
        </pre>
      </div>

      {/* Audit timeline */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5 mb-4">
          <Clock size={14} className="text-gray-400" /> Audit Trail
        </h3>
        <Timeline logs={process.audit_logs} />
      </div>
    </div>
  )
}
