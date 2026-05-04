import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell, Legend, CartesianGrid,
} from 'recharts'
import { format } from 'date-fns'
import { Zap, Users, TrendingUp, Clock } from 'lucide-react'
import { metricsApi } from '../api/metrics'
import MetricCard from '../components/MetricCard'

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

const CONF_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#10b981', '#3b82f6']

export default function Metrics() {
  const [days, setDays] = useState(7)

  const { data: summary } = useQuery({
    queryKey: ['metrics', 'summary'],
    queryFn: metricsApi.summary,
    refetchInterval: 30_000,
  })
  const { data: volume } = useQuery({
    queryKey: ['metrics', 'volume', days],
    queryFn: () => metricsApi.volume(days),
    refetchInterval: 30_000,
  })
  const { data: breakdown } = useQuery({
    queryKey: ['metrics', 'breakdown'],
    queryFn: metricsApi.breakdown,
    refetchInterval: 30_000,
  })

  const pieData = breakdown?.by_type.slice(0, 6).map(t => ({
    name: t.process_type.replace('_', ' '),
    value: t.count,
    color: TYPE_COLORS[t.process_type] ?? '#9ca3af',
  })) ?? []

  const confData = breakdown?.confidence_distribution.map((b, i) => ({
    name: b.label.split(' ')[0],
    count: b.count,
    fill: CONF_COLORS[i] ?? '#9ca3af',
  })) ?? []

  const avgTime = summary?.avg_processing_time_seconds ?? 0
  const avgTimeLabel = avgTime < 60 ? `${avgTime.toFixed(1)}s` : `${(avgTime / 60).toFixed(1)}m`

  return (
    <div className="p-6 space-y-6 max-w-[1200px]">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics & Metrics</h1>
        <p className="text-sm text-gray-500 mt-0.5">Performance overview and automation efficiency</p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard
          title="Automation Rate"
          value={summary ? `${summary.automation_rate}%` : '—'}
          subtitle={`${summary?.automated_count ?? 0} auto · ${summary?.human_reviewed_count ?? 0} human`}
          icon={<Zap size={18} className="text-emerald-600" />}
          iconBg="bg-emerald-50"
        />
        <MetricCard
          title="Total Processed"
          value={summary?.total_processes ?? '—'}
          subtitle={`${summary?.completed ?? 0} completed · ${summary?.failed ?? 0} failed`}
          icon={<TrendingUp size={18} className="text-blue-600" />}
          iconBg="bg-blue-50"
        />
        <MetricCard
          title="Avg. Confidence"
          value={summary ? `${summary.avg_confidence}%` : '—'}
          subtitle="across all classifications"
          icon={<Users size={18} className="text-violet-600" />}
          iconBg="bg-violet-50"
        />
        <MetricCard
          title="Avg. Process Time"
          value={avgTimeLabel}
          subtitle="from submission to completion"
          icon={<Clock size={18} className="text-amber-600" />}
          iconBg="bg-amber-50"
        />
      </div>

      {/* Volume chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-700">Process Volume Over Time</h2>
          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
            {[7, 14, 30].map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  days === d ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={volume ?? []}>
            <defs>
              <linearGradient id="gTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gAuto" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
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
            <Area type="monotone" dataKey="total" name="Total" stroke="#3b82f6" fill="url(#gTotal)" strokeWidth={2} />
            <Area type="monotone" dataKey="automated" name="Automated" stroke="#10b981" fill="url(#gAuto)" strokeWidth={2} />
            <Area type="monotone" dataKey="human_reviewed" name="Human" stroke="#f97316" fill="none" strokeWidth={2} strokeDasharray="4 2" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Process types distribution */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Process Type Distribution</h2>
          <div className="flex items-center gap-4">
            <ResponsiveContainer width={180} height={180}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 8, border: 'none' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {(breakdown?.by_type ?? []).slice(0, 6).map(t => (
                <div key={t.process_type} className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: TYPE_COLORS[t.process_type] ?? '#9ca3af' }} />
                  <span className="text-xs text-gray-600 capitalize flex-1">{t.process_type.replace('_', ' ')}</span>
                  <span className="text-xs font-semibold text-gray-800">{t.count}</span>
                  <span className="text-xs text-gray-400 w-8 text-right">{t.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Confidence distribution */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Confidence Distribution</h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={confData} barCategoryGap={8}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip contentStyle={{ borderRadius: 8, border: 'none' }} />
              <Bar dataKey="count" name="Processes" radius={[4, 4, 0, 0]}>
                {confData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex justify-between text-xs text-gray-400 mt-1 px-1">
            <span>Low confidence → human review</span>
            <span>High confidence → auto</span>
          </div>
        </div>
      </div>

      {/* Status breakdown table */}
      {breakdown?.by_status && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Status Breakdown</h2>
          <div className="grid grid-cols-4 md:grid-cols-8 gap-3">
            {breakdown.by_status.map(({ status, count }) => (
              <div key={status} className="text-center p-3 rounded-lg bg-gray-50">
                <p className="text-xl font-bold text-gray-900">{count}</p>
                <p className="text-xs text-gray-500 capitalize mt-0.5">{status.replace('_', ' ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
