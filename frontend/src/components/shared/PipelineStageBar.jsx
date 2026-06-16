/**
 * 7 节点主链 mini 状态条 — 前台/后台通用
 */
import { cn } from '@/utils/cn'

const DEFAULT_STAGES = ['信息', '结构', '人设', '大纲', '剧本', '审查', '交付']

/**
 * @param {object} props
 * @param {string[]} [props.stages]
 * @param {number} props.currentNode - 1-based 当前节点
 * @param {'running'|'completed'|'failed'|'idle'} [props.state]
 * @param {string} [props.className]
 */
export default function PipelineStageBar({
  stages = DEFAULT_STAGES,
  currentNode = 1,
  state = 'running',
  className,
}) {
  return (
    <div className={cn('grid gap-1.5', className)} style={{ gridTemplateColumns: `repeat(${stages.length}, minmax(0, 1fr))` }}>
      {stages.map((label, i) => {
        const idx = i + 1
        const tone =
          state === 'completed'
            ? 'done'
            : idx < currentNode
              ? 'done'
              : idx === currentNode && state === 'running'
                ? 'run'
                : idx === currentNode && state === 'failed'
                  ? 'fail'
                  : 'idle'
        return (
          <div
            key={label}
            className={cn(
              'rounded-md border py-1.5 text-center text-[10px]',
              tone === 'done' && 'border-success-500/35 bg-success-500/12 text-success-300',
              tone === 'run' && 'border-indigo-500/40 bg-indigo-500/15 text-indigo-300',
              tone === 'fail' && 'border-danger-500/35 bg-danger-500/12 text-danger-300',
              tone === 'idle' && 'border-white/5 bg-white/[0.03] text-slate-500',
            )}
            title={`第 ${idx} 节点 · ${label}`}
          >
            {label}
          </div>
        )
      })}
    </div>
  )
}
