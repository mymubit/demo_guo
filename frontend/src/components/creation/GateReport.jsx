import { ClipboardCheck, AlertTriangle, CheckCircle2 } from 'lucide-react'

import { gatePassRate } from '@/utils/number'

/** 节点5 逐集 sub-gate 汇总 */
export default function GateReport({ summary, className = '' }) {
  if (!summary || !summary.total) return null

  const { total, passed, failed, failedEpisodes = [] } = summary
  const passRate = gatePassRate(summary)
  const allOk = failed === 0

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-navy-200">
          <ClipboardCheck className="w-5 h-5 text-gold-400" />
          <span>逐集质检 (sub-gate)</span>
        </div>
        <span className={`font-semibold ${allOk ? 'text-green-400' : 'text-gold-400'}`}>
          {passed}/{total} 通过 · {passRate}%
        </span>
      </div>

      {allOk ? (
        <div className="flex items-center gap-2 text-sm text-green-400">
          <CheckCircle2 className="w-4 h-4" />
          全部集数通过逐集闸门
        </div>
      ) : (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {failedEpisodes.map((ep) => (
            <div
              key={ep.episodeNumber}
              className="text-sm p-3 rounded-xl bg-navy-800/40 border border-navy-600/30"
            >
              <div className="flex items-center gap-2 text-red-300 mb-1">
                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>
                  第{ep.episodeNumber}集 {ep.title ? `· ${ep.title}` : ''}
                </span>
              </div>
              <ul className="text-xs text-navy-400 space-y-0.5 pl-5 list-disc">
                {(ep.issues || []).slice(0, 3).map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
