/**
 * 创作页左侧 — 主链节点 + 题材格式
 */
import { cn } from '@/utils/cn'
import { SideSectionTitle } from '@/components/shared/ConsumerSection'
import { formatVariantLabel } from '@/config/fusion'

export default function CreationNodeSidebar({
  pipelineNodes = [],
  formatVariants = [],
  catalog,
  activeFormat,
  onFormatChange,
  formStage = 1,
  readOnlyFormat = false,
}) {
  const activeNodeIndex = formStage === 1 ? 1 : formStage === 2 ? 1 : null

  return (
    <>
      <SideSectionTitle>主链节点</SideSectionTitle>
      <nav className="mt-2 space-y-0.5">
        {pipelineNodes.map((node, idx) => {
          const step = node.step ?? node.index ?? idx + 1
          const isActive = activeNodeIndex === step
          const isDone = formStage === 2 && step === 1
          return (
            <div
              key={node.key || node.name || step}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-xl border px-3 py-2.5 text-left text-sm',
                isActive ? 'border-gold-400/30 bg-gold-400/10 text-white shadow-gold' : 'border-transparent text-navy-200',
              )}
            >
              <span
                className={cn(
                  'grid h-[22px] w-[22px] place-items-center rounded-md border text-[11px]',
                  isActive
                    ? 'border-transparent bg-gradient-to-br from-gold-300 to-gold-500 text-navy-950'
                    : isDone
                      ? 'border-gold-400/30 bg-gold-400/10 text-gold-300'
                      : 'border-white/10 bg-white/5 text-navy-300',
                )}
              >
                {step}
              </span>
              <span className="min-w-0 truncate">{node.name || node.label}</span>
              <span className="ml-auto text-[11px] text-navy-400">
                {isDone ? '✓' : isActive ? '填写中' : '—'}
              </span>
            </div>
          )
        })}
        {!pipelineNodes.length ? (
          <p className="px-3 py-2 text-xs text-navy-400">加载节点配置…</p>
        ) : null}
      </nav>

      {formatVariants.length > 0 ? (
        <>
          <SideSectionTitle>题材格式</SideSectionTitle>
          <nav className="mt-2 space-y-0.5">
            {formatVariants.map((f) => {
              const key = f.key || f.id
              const active = activeFormat === key
              const label = formatVariantLabel(catalog || { formatVariants }, key) || f.name || key
              const Comp = readOnlyFormat || !onFormatChange ? 'div' : 'button'
              return (
                <Comp
                  key={key}
                  type={Comp === 'button' ? 'button' : undefined}
                  onClick={Comp === 'button' ? () => onFormatChange(key) : undefined}
                  className={cn(
                    'flex w-full items-center gap-2.5 rounded-xl border px-3 py-2.5 text-left text-sm transition-colors',
                    active
                      ? 'border-gold-400/30 bg-gold-400/10 text-white shadow-gold'
                      : 'border-transparent text-navy-200',
                    Comp === 'button' && !active && 'hover:bg-white/5 hover:text-white',
                  )}
                >
                  <span
                    className={cn(
                      'grid h-[22px] w-[22px] place-items-center rounded-md text-[11px] font-semibold',
                      active
                        ? 'bg-gradient-to-br from-gold-300 to-gold-500 text-navy-950'
                        : 'bg-white/5 text-navy-300',
                    )}
                  >
                    {key}
                  </span>
                  <span className="min-w-0 truncate">{label}</span>
                </Comp>
              )
            })}
          </nav>
        </>
      ) : null}
    </>
  )
}
