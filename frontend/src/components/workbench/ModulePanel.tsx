import { groupModulesByDomain, modulesForStageFromDefinition } from '@/utils/modules'
import { Badge } from '@/components/ui/Badge'
import { X } from 'lucide-react'
import { cn } from '@/utils/cn'
import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
import type { ProjectSettings } from '@/types/domain'
import type { StageDefinition } from '@/types/workbench'

const DOMAIN_LABELS: Record<string, string> = {
  concept: '创意',
  character: '人物',
  structure: '结构',
  emotion: '情绪',
  plotting: '情节',
  episode: '分集',
  writing: '写作',
  production: '制作',
  quality: '质检',
  revision: '修复',
  marketing: '宣发',
  delivery: '交付',
  derivative: '衍生',
}

const KIND_LABELS: Record<string, string> = {
  core: '核心',
  extension: '扩展',
}

export function ModulePanel({
  stage,
  settings,
  className,
  onClose,
}: {
  stage: StageDefinition | null
  settings: ProjectSettings
  className?: string
  onClose?: () => void
}) {
  const { definition } = useWorkbenchDefinition()
  const modules = modulesForStageFromDefinition(definition, stage, settings)
  const groups = groupModulesByDomain(modules)

  return (
    <aside
      className={cn(
        'flex h-full w-[clamp(15rem,18vw,18.75rem)] shrink-0 flex-col border-l border-slate-200 bg-white',
        className,
      )}
    >
      <div className="border-b border-slate-200 px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <div className="text-xs font-medium tracking-wide text-ink-faint">本阶段能力</div>
          {onClose ? (
            <button
              type="button"
              aria-label="关闭能力模块"
              className="rounded-md p-1 text-ink-muted transition hover:bg-slate-100 hover:text-ink"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>
        <div className="mt-1 text-sm font-semibold text-ink">
          {stage ? stage.label_zh : '能力模块'}
        </div>
        {stage ? (
          <div className="mt-1 truncate text-xs text-ink-muted">
            角色：{stage.role_label ?? stage.role}
          </div>
        ) : null}
        <p className="mt-2 text-[11px] leading-relaxed text-ink-muted">
          以下为当前阶段会加载的技能模块（只读目录）。执行请用画布中的「执行本阶段」。
        </p>
      </div>
      <div className="flex-1 space-y-4 overflow-auto p-3">
        {groups.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 px-3 py-6 text-center text-sm text-ink-muted">
            当前阶段暂无可见模块。可先完善创作设定，或切换到其他流水线阶段。
          </div>
        ) : (
          groups.map(([domain, items]) => (
            <section key={domain}>
              <div className="mb-2 px-1 text-xs font-medium tracking-wide text-ink-faint">
                {DOMAIN_LABELS[domain] ?? domain}
              </div>
              <ul className="space-y-1.5">
                {items.map((m) => (
                  <li
                    key={m.id}
                    className="rounded-lg border border-slate-200 bg-canvas px-3 py-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm text-ink">{m.label_zh}</span>
                      <Badge tone={m.kind === 'core' ? 'brand' : 'default'}>
                        {KIND_LABELS[m.kind] ?? m.kind}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}
      </div>
    </aside>
  )
}
