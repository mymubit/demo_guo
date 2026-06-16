import { CheckCircle2, AlertCircle } from 'lucide-react'

export function GateLogBadge({ passed, label = '质检', acknowledged = false }) {
  if (passed === null || passed === undefined) return null
  const ok = !!passed
  if (!ok && acknowledged) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border bg-green-500/10 border-green-500/30 text-green-300">
        <CheckCircle2 className="w-3 h-3" />
        {label}已确认
      </span>
    )
  }
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border ${
        ok
          ? 'bg-green-500/10 border-green-500/30 text-green-300'
          : 'bg-amber-500/10 border-amber-500/30 text-amber-200'
      }`}
    >
      {ok ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
      {label}
      {ok ? '通过' : '待修'}
    </span>
  )
}

export default function GateLogSection({ gateLog, title = '质检' }) {
  if (!gateLog || Object.keys(gateLog).length === 0) return null
  if (gateLog.skipped) return null
  if (gateLog.passed) return null
  if (gateLog.userAcknowledgedAt) return null

  const issues = gateLog.issues || []

  return (
    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-sm">
      <div className="flex items-center gap-2 mb-1">
        <GateLogBadge passed={false} label={title} />
      </div>
      {issues.length > 0 && (
        <ul className="mt-2 text-xs text-navy-300 space-y-1 list-disc list-inside">
          {issues.slice(0, 5).map((issue, i) => (
            <li key={`${title}-${i}`}>{issue}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
