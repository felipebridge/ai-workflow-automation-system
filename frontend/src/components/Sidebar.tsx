import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, List, CheckSquare, BarChart2,
  PlusCircle, Zap,
} from 'lucide-react'
import clsx from 'clsx'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { to: '/processes', label: 'Processes', icon: List },
  { to: '/approvals', label: 'Approvals', icon: CheckSquare },
  { to: '/metrics', label: 'Metrics', icon: BarChart2 },
  { to: '/new', label: 'New Process', icon: PlusCircle },
]

export default function Sidebar() {
  return (
    <aside className="w-60 bg-slate-900 flex flex-col h-screen flex-shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <p className="text-white font-semibold text-sm leading-tight">AI Workflow</p>
            <p className="text-slate-400 text-xs">Automation Agent</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ to, label, icon: Icon, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-800">
        <p className="text-slate-500 text-xs text-center">v1.0.0 — demo mode</p>
      </div>
    </aside>
  )
}
