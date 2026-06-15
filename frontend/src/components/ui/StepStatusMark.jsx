import { Check, Minus, X } from 'lucide-react'
import { ICON } from '@/constants/iconSizes'

/** 统一步骤/门禁状态符号（替代 ✓ ✗ — 文本） */
export default function StepStatusMark({ status, passed, skipped, className = ICON.sm }) {
  const resolved =
    status ||
    (skipped ? 'skipped' : passed === true ? 'passed' : passed === false ? 'failed' : 'pending')

  if (resolved === 'skipped') return <Minus className={className} aria-hidden />
  if (resolved === 'failed') return <X className={className} aria-hidden />
  if (resolved === 'passed' || resolved === 'success' || resolved === 'completed') {
    return <Check className={className} aria-hidden />
  }
  return null
}

/** API Key / 布尔配置行内状态 */
export function BoolStatus({ ok, label, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1 ${className}`}>
      {label ? <span>{label}</span> : null}
      {ok ? (
        <Check className={`${ICON.sm} text-green-400`} aria-label="已配置" />
      ) : (
        <X className={`${ICON.sm} text-red-400`} aria-label="未配置" />
      )}
    </span>
  )
}
