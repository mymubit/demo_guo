import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'

function IssueList({ items, emptyText = '暂无问题' }) {
  if (!items?.length) {
    return <p className="text-sm text-navy-400">{emptyText}</p>
  }
  return (
    <ul className="space-y-2 text-sm text-navy-200">
      {items.map((item, index) => (
        <li key={`${String(item)}-${index}`} className="flex gap-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-gold-400" />
          <span>{String(item)}</span>
        </li>
      ))}
    </ul>
  )
}

export default function ReviewReportPanel({ payload }) {
  if (!payload) {
    return <p className="text-sm text-navy-400">暂无审查报告。</p>
  }

  const passed = Boolean(payload.passed)
  const issues = payload.issues || []
  const geval = payload.geval || {}
  const failedDimensions = geval.failedDimensions || []

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {passed ? (
          <CheckCircle2 className="h-5 w-5 text-green-400" />
        ) : (
          <XCircle className="h-5 w-5 text-red-400" />
        )}
        <span className={`font-semibold ${passed ? 'text-green-400' : 'text-red-300'}`}>
          {passed ? '审查通过' : '审查未通过'}
        </span>
      </div>

      {failedDimensions.length > 0 && (
        <div>
          <p className="mb-2 text-xs uppercase tracking-wide text-navy-400">未通过维度</p>
          <div className="flex flex-wrap gap-2">
            {failedDimensions.map((dim) => (
              <span
                key={dim}
                className="rounded-full border border-red-400/30 bg-red-400/10 px-2 py-0.5 text-xs text-red-200"
              >
                {dim}
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-navy-400">问题清单</p>
        <IssueList items={issues} />
      </div>
    </div>
  )
}
