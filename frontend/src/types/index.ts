export type ProcessType =
  | 'invoice'
  | 'customer_request'
  | 'claim'
  | 'lead'
  | 'support_ticket'
  | 'admin_case'
  | 'payment_request'
  | 'other'

export type ProcessStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'awaiting_approval'
  | 'approved'
  | 'rejected'
  | 'escalated'

export type Priority = 'low' | 'medium' | 'high' | 'critical'

export type ActionType =
  | 'send_email'
  | 'create_record'
  | 'update_record'
  | 'generate_response'
  | 'escalate'
  | 'request_information'
  | 'approve_payment'
  | 'close_case'
  | 'notify_team'

export type ActionStatus = 'pending' | 'pending_approval' | 'executed' | 'failed' | 'cancelled'

export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export interface ExtractedData {
  name: string | null
  email: string | null
  phone: string | null
  date: string | null
  amount: number | null
  currency: string | null
  description: string | null
  order_number: string | null
  priority: Priority
  urgency_indicators: string[]
  key_entities: Record<string, string>
  summary: string | null
}

export interface Process {
  id: number
  uuid: string
  source: string
  raw_input: string
  process_type: ProcessType
  status: ProcessStatus
  priority: Priority
  confidence_score: number
  extracted_data: ExtractedData | null
  title: string | null
  created_at: string
  updated_at: string | null
  processed_at: string | null
}

export interface Decision {
  id: number
  process_id: number
  classification: string
  reasoning: string
  confidence: number
  requires_human: boolean
  auto_executable: boolean
  validation_errors: string[]
  missing_fields: string[]
  ai_mode: string
  created_at: string
}

export interface Action {
  id: number
  process_id: number
  action_type: ActionType
  parameters: Record<string, unknown>
  status: ActionStatus
  result: Record<string, unknown> | null
  executed_at: string | null
  created_at: string
}

export interface AuditLog {
  id: number
  process_id: number | null
  event_type: string
  event_data: Record<string, unknown>
  actor: string
  created_at: string
}

export interface Approval {
  id: number
  process_id: number
  reason: string
  status: ApprovalStatus
  reviewer: string | null
  review_notes: string | null
  created_at: string
  reviewed_at: string | null
  process?: Process
}

export interface ProcessDetail extends Process {
  decisions: Decision[]
  actions: Action[]
  audit_logs: AuditLog[]
  approval: Approval | null
}

export interface ProcessListResponse {
  items: Process[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface MetricsSummary {
  total_processes: number
  pending: number
  processing: number
  completed: number
  failed: number
  awaiting_approval: number
  approved: number
  rejected: number
  escalated: number
  automated_count: number
  human_reviewed_count: number
  automation_rate: number
  avg_confidence: number
  avg_processing_time_seconds: number
}

export interface VolumeDataPoint {
  date: string
  total: number
  automated: number
  human_reviewed: number
}

export interface TypeBreakdown {
  process_type: ProcessType
  count: number
  percentage: number
}

export interface ConfidenceBucket {
  label: string
  min_val: number
  max_val: number
  count: number
}

export interface MetricsBreakdown {
  by_type: TypeBreakdown[]
  by_status: Array<{ status: string; count: number }>
  confidence_distribution: ConfidenceBucket[]
}
