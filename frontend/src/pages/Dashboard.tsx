import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import {
  Layers, Clock, CheckCircle2, AlertCircle,
  Zap, Users, ChevronRight,
} from 'lucide-react'
import { format } from 'date-fns'
import { metricsApi } from '../api/metrics'
import { processApi } from '../api/processes'
import { approvalApi } from '../api/approvals'
import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'
import PriorityBadge from '../components/PriorityBadge'
import ConfidenceBar from '../components/ConfidenceBar'
import ProcessTypeIcon from '../components/ProcessTypeIcon'
import type { ProcessType } from '../types'

const TYPE_COLORS: Record<string, string> = {
  invoice: '#3b82f6',
  customer_request: '#8b5cf6',
  claim: '#f97316',
  lead: '#10b981',
  support_ticket: '#06b6d4',
  admin_case: '#64748b',
  payment_request: '#ef4444',
  other: '#9ca3af',
}

export default function Dashboard() {
  const { data: summary } = useQuery({
    queryKey: ['metrics', 'summary'],
    queryFn: metricsApi.summary,
    refetchInterval: 8_000,
  })
  const { data: volume } = useQuery({
    queryKey: ['metrics', 'volume', 7],
    queryFn: () => metricsApi.volume(7),
    refetchInterval: 30_000,
  })
  const { data: breakdown } = useQuery({
    queryKey: ['metrics', 'breakdown'],
    queryFn: metricsApi.breakdown,
    refetchInterval: 30_000,
  })
  const { data: recent } = useQuery({
    queryKey: ['processes', 'recent'],
    queryFn: () => processApi.list({ per_page: 8, page: 1 }),
    refetchInterval: 8_000,
  })
  const { data: pendingApprovals } = useQuery({
    queryKey: ['approvals', 'pending'],
    queryFn: () => approvalApi.list('pending'),
    refetchInterval: 8_000,
  })

  const pieData = breakdown?.by_type.slice(0, 6).map(t => ({
    name: t.process_type.replace('_', ' '),
    value: t.count,
    color: TYPE_COLORS[t.process_type] ?? '#9ca3af',
  })) ?? []

  return (
    <div className="p-6 space-y-6 max-w-[1400px]">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">Real-time overview of all automated processes</p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard
          title="Total Processes"
          value={summary?.total_processes ?? '—'}
          icon={<Layers size={18} className="text-blue-600" />}
          iconBg="bg-blue-50"
          subtitle="all time"
        />
        <MetricCard
          title="Automation Rate"
          value={summary ? `${summary.automation_rate}%` : '—'}
          icon={<Zap size={18} className="text-emerald-600" />}
          iconBg="bg-emerald-50"
          subtitle={`${summary?.automated_count ?? 0} auto-executed`}
        />
        <MetricCard
          title="Awaiting Approval"
          value={summary?.awaiting_approval ?? '—'}
          icon={<Clock size={18} className="text-orange-600" />}
          iconBg="bg-orange-50"
          subtitle="pending human review"
        />
        <MetricCard
          title="Avg Confidence"
          value={summary ? `${summary.avg_confidence}%` : '—'}
          icon={<CheckCircle2 size={18} className="text-violet-600" />}
          iconBg="bg-violet-50"
          subtitle="across all processes"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Volume chart */}
        <div className="card xl:col-span-2">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Process Volume — Last 7 Days</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={volume ?? []} barGap={2}>
              <XAxis
                dataKey="date"
                tickFormatter={d => format(new Date(d + 'T12:00:00'), 'MMM d')}
                tick={{ fontSize: 11, fill: '#9ca3af' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                labelFormatter={d => format(new Date(d + 'T12:00:00'), 'MMM d, yyyy')}
              />
              <Bar dataKey="total" name="Total" fill="#e0e7ff" radius={[4, 4, 0, 0]} />
              <Bar dataKey="automated" name="Automated" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="human_reviewed" name="Human" fill="#f97316" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Breakdown pie */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Process Types</h2>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Legend
                  formatter={v => <span className="text-xs text-gray-600 capitalize">{v}</span>}
                  iconSize={8}
                  iconType="circle"
                />
                <Tooltip contentStyle={{ borderRadius: 8, border: 'none' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-sm text-gray-400">No data yet</div>
          )}
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        {/* Recent processes */}
        <div className="card xl:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700">Recent Processes</h2>
            <Link to="/processes" className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-0.5">
              View all <ChevronRight size={12} />
            </Link>
          </div>
          <div className="space-y-2">
            {(recent?.items ?? []).slice(0, 6).map(p => (
              <Link
                key={p.id}
                to={`/processes/${p.id}`}
                className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-gray-50 transition-colors group"
              >
                <ProcessTypeIcon type={p.process_type as ProcessType} size={14} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{p.title ?? p.raw_input.slice(0, 60)}</p>
                  <p className="text-xs text-gray-400">{format(new Date(p.created_at), 'MMM d, HH:mm')}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <ConfidenceBar value={p.confidence_score} showLabel={false} />
                  <StatusBadge status={p.status} size="sm" />
                </div>
              </Link>
            ))}
            {!recent?.items.length && (
              <p className="text-sm text-gray-400 text-center py-4">No processes yet. Submit one to get started.</p>
            )}
          </div>
        </div>

        {/* Pending approvals */}
        <div className="card xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
              <AlertCircle size={14} className="text-orange-500" />
              Pending Approvals
              {(pendingApprovals?.length ?? 0) > 0 && (
                <span className="badge bg-orange-100 text-orange-700 text-xs ml-1">
                  {pendingApprovals!.length}
                </span>
              )}
            </h2>
            <Link to="/approvals" className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-0.5">
              Review <ChevronRight size={12} />
            </Link>
          </div>
          <div className="space-y-2">
            {(pendingApprovals ?? []).slice(0, 5).map(a => (
              <Link
                key={a.id}
                to={`/processes/${a.process_id}`}
                className="block p-3 rounded-lg border border-orange-100 bg-orange-50 hover:bg-orange-100 transition-colors"
              >
                <p className="text-sm font-medium text-gray-800 truncate">
                  {a.process?.title ?? `Process #${a.process_id}`}
                </p>
                <p className="text-xs text-orange-700 mt-0.5 truncate">{a.reason}</p>
                <div className="flex items-center gap-2 mt-1.5">
                  <PriorityBadge priority={(a.process?.priority ?? 'medium') as any} />
                  <span className="text-xs text-gray-400">{format(new Date(a.created_at), 'MMM d, HH:mm')}</span>
                </div>
              </Link>
            ))}
            {!(pendingApprovals?.length) && (
              <div className="text-center py-6">
                <Users size={24} className="mx-auto text-gray-300 mb-2" />
                <p className="text-sm text-gray-400">No pending approvals</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Stats footer */}
      {summary && (
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {[
            { label: 'Completed', val: summary.completed, color: 'text-emerald-600' },
            { label: 'Failed', val: summary.failed, color: 'text-red-500' },
            { label: 'Escalated', val: summary.escalated, color: 'text-purple-600' },
            { label: 'Processing', val: summary.processing, color: 'text-blue-600' },
            { label: 'Approved', val: summary.approved, color: 'text-emerald-700' },
            { label: 'Rejected', val: summary.rejected, color: 'text-red-700' },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-lg border border-gray-100 p-3 text-center">
              <p className={`text-xl font-bold ${s.color}`}>{s.val}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
