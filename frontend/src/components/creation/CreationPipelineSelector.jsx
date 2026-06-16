import { GitBranch } from 'lucide-react'
import { cn } from '@/utils/cn'

/** 创作入口：可选已发布流水线 */
export default function CreationPipelineSelector({
  pipelines = [],
  selectedId = '',
  onChange,
  disabled = false,
}) {
  if (!pipelines.length) return null

  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5">
      <div className="flex items-center gap-2 mb-3">
        <GitBranch className="w-4 h-4 text-gold-400" />
        <h3 className="text-sm font-semibold text-white">选择流水线</h3>
        <span className="text-xs text-navy-400">不同模板对应不同 Agent 组合与步骤顺序</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {pipelines.map((pipe) => {
          const active = pipe.id === selectedId
          return (
            <button
              key={pipe.id}
              type="button"
              disabled={disabled}
              onClick={() => onChange?.(pipe.id)}
              className={cn(
                'text-left rounded-xl border px-4 py-3 transition-all disabled:opacity-50',
                active
                  ? 'border-gold-400/40 bg-gold-400/10 text-white'
                  : 'border-white/10 bg-white/[0.03] hover:border-white/20',
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-white">{pipe.displayName}</span>
                {pipe.isDefault ? (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-300 shrink-0">
                    推荐
                  </span>
                ) : null}
              </div>
              {pipe.description ? (
                <p className="text-xs text-navy-400 mt-1 line-clamp-2">{pipe.description}</p>
              ) : null}
              <p className="text-[11px] text-navy-500 mt-2">
                {pipe.stepCount || 0} 步
                {(pipe.stepPreview || []).length > 0
                  ? ` · ${pipe.stepPreview.slice(0, 4).join(' → ')}`
                  : ''}
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}
