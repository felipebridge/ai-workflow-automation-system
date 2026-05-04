import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Send, Loader2, CheckCircle, Info } from 'lucide-react'
import { processApi } from '../api/processes'

const SOURCES = [
  { value: 'manual', label: 'Manual Entry' },
  { value: 'email', label: 'Email' },
  { value: 'form', label: 'Web Form' },
  { value: 'api', label: 'API / Webhook' },
  { value: 'pdf', label: 'PDF / Document' },
]

const EXAMPLES = [
  {
    label: 'Invoice',
    source: 'email',
    text: `From: vendor@supplies.com
Subject: Invoice #INV-2024-0500 — Office Supplies

Dear Finance Team,

Please process payment for Invoice #INV-2024-0500.
Amount: $1,250.00
Due Date: December 15, 2024
Company: Premium Supplies LLC

Thank you,
Accounts Receivable`,
  },
  {
    label: 'Sales Lead',
    source: 'form',
    text: `Name: Jennifer Park
Title: Head of Operations
Company: ScaleUp Corp
Email: j.park@scaleup.com
Phone: +1-415-555-0199

Message: We're looking for an automation solution to handle our customer onboarding workflow. We process around 300 new customers monthly. Budget is $80,000 annually. Looking to implement in Q2 2025. Please have a sales rep contact me.`,
  },
  {
    label: 'Support Ticket',
    source: 'api',
    text: `Ticket: Support Request
Reporter: user@company.com
Severity: Medium

Our integration with your payment API is returning unexpected errors since this morning. Error code: PAYMENT_DECLINED_INVALID_TOKEN for all transactions. This is affecting 100+ customers. Please investigate urgently.

Environment: Production
Affected endpoints: /api/v1/payments/charge`,
  },
  {
    label: 'Customer Complaint',
    source: 'email',
    text: `From: unhappy.customer@email.com
Subject: Terrible Experience - Order ORD-12345

I am extremely disappointed with my recent order #ORD-12345. The product arrived broken and the packaging was damaged. I've been waiting 2 weeks for a response from customer service. I paid $450 for this and expect either a full refund or replacement immediately. This is unacceptable.

- Amanda Torres`,
  },
]

export default function NewProcess() {
  const navigate = useNavigate()
  const [source, setSource] = useState('manual')
  const [input, setInput] = useState('')
  const [submitted, setSubmitted] = useState<{ id: number; uuid: string } | null>(null)

  const mutation = useMutation({
    mutationFn: () => processApi.submit(source, input),
    onSuccess: (data) => {
      setSubmitted(data)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) mutation.mutate()
  }

  if (submitted) {
    return (
      <div className="p-6 max-w-2xl">
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-emerald-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Process Accepted!</h2>
          <p className="text-gray-500 mt-2">
            The agent is analyzing your input. Process <strong>#{submitted.id}</strong> has been queued.
          </p>
          <div className="flex items-center justify-center gap-3 mt-6">
            <button
              className="btn-primary"
              onClick={() => navigate(`/processes/${submitted.id}`)}
            >
              View Process →
            </button>
            <button
              className="btn-secondary"
              onClick={() => { setSubmitted(null); setInput('') }}
            >
              Submit Another
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-5 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">New Process</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Submit any business input — the agent will classify, extract, and route it automatically
        </p>
      </div>

      {/* Examples */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Info size={14} className="text-blue-500" />
          <span className="text-sm font-medium text-gray-700">Quick Examples</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map(ex => (
            <button
              key={ex.label}
              className="text-xs px-3 py-1.5 rounded-full border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
              onClick={() => { setInput(ex.text); setSource(ex.source) }}
            >
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Source */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Input Source</label>
          <div className="flex flex-wrap gap-2">
            {SOURCES.map(s => (
              <button
                key={s.value}
                type="button"
                onClick={() => setSource(s.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                  source === s.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Raw Input
            <span className="text-gray-400 font-normal ml-1">— paste email, form content, or any business text</span>
          </label>
          <textarea
            className="input min-h-64 resize-y font-mono text-sm"
            placeholder="Paste your email, form submission, document content, or any business text here…"
            value={input}
            onChange={e => setInput(e.target.value)}
            required
          />
          <p className="text-xs text-gray-400 mt-1">{input.length} / 50,000 characters</p>
        </div>

        {mutation.error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {mutation.error.message}
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            className="btn-primary"
            disabled={mutation.isPending || !input.trim()}
          >
            {mutation.isPending ? (
              <><Loader2 size={15} className="animate-spin" /> Processing…</>
            ) : (
              <><Send size={15} /> Submit for Analysis</>
            )}
          </button>
          <button type="button" className="btn-secondary" onClick={() => setInput('')}>
            Clear
          </button>
        </div>
      </form>

      {/* What happens next */}
      <div className="card bg-slate-50 border-slate-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">What happens after submission</h3>
        <div className="space-y-2">
          {[
            { step: '1', text: 'Input is received and a process record is created', color: 'bg-blue-100 text-blue-700' },
            { step: '2', text: 'AI agent classifies the type (invoice, lead, claim, etc.)', color: 'bg-violet-100 text-violet-700' },
            { step: '3', text: 'Structured data is extracted (name, email, amount, date…)', color: 'bg-cyan-100 text-cyan-700' },
            { step: '4', text: 'Validation checks are applied and confidence score calculated', color: 'bg-amber-100 text-amber-700' },
            { step: '5', text: 'Decision engine decides: auto-execute or require human approval', color: 'bg-orange-100 text-orange-700' },
            { step: '6', text: 'Action executed automatically or queued for your review', color: 'bg-emerald-100 text-emerald-700' },
          ].map(({ step, text, color }) => (
            <div key={step} className="flex items-start gap-2.5">
              <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${color} flex-shrink-0`}>{step}</span>
              <span className="text-sm text-gray-600">{text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
