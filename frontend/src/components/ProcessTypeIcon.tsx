import {
  FileText, User, AlertCircle, TrendingUp,
  Headphones, Briefcase, CreditCard, HelpCircle,
} from 'lucide-react'
import type { ProcessType } from '../types'

const ICONS: Record<ProcessType, { Icon: typeof FileText; color: string; bg: string }> = {
  invoice: { Icon: FileText, color: 'text-blue-600', bg: 'bg-blue-50' },
  customer_request: { Icon: User, color: 'text-violet-600', bg: 'bg-violet-50' },
  claim: { Icon: AlertCircle, color: 'text-orange-600', bg: 'bg-orange-50' },
  lead: { Icon: TrendingUp, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  support_ticket: { Icon: Headphones, color: 'text-cyan-600', bg: 'bg-cyan-50' },
  admin_case: { Icon: Briefcase, color: 'text-slate-600', bg: 'bg-slate-50' },
  payment_request: { Icon: CreditCard, color: 'text-red-600', bg: 'bg-red-50' },
  other: { Icon: HelpCircle, color: 'text-gray-500', bg: 'bg-gray-50' },
}

interface Props {
  type: ProcessType
  size?: number
}

export default function ProcessTypeIcon({ type, size = 16 }: Props) {
  const { Icon, color, bg } = ICONS[type] ?? ICONS.other
  return (
    <span className={`inline-flex items-center justify-center rounded-lg p-1.5 ${bg}`}>
      <Icon size={size} className={color} />
    </span>
  )
}
