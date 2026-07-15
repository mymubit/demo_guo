import { groupModulesByDomain, modulesForStage } from '@/utils/modules'
import { Badge } from '@/components/ui/Badge'
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

const ROLE_LABELS: Record<string, string> = {
  'drama.topic-director': '选题定调官',
  'drama.story-bible': '剧本蓝图官',
  'drama.episode-designer': '分集设计官',
  'drama.script-writer': '剧本正文官',
  'drama.script-scorer': '剧本评分官',
  'drama.compliance-guard': '合规审查官',
  'drama.revision-master': '剧本修复官',
  'drama.delivery-tool': '宣发交付工具',
}

export function ModulePanel({
  stage,
  settings,
}: {
  stage: StageDefinition | null
  settings: ProjectSettings
}) {
  const modules = modulesForStage(stage, settings)
  const groups = groupModulesByDomain(modules)

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-l border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-3">
        <div className="text-xs font-medium tracking-wide text-ink-faint">能力模块</div>
        <div className="mt-1 text-sm font-semibold text-ink">
          {stage ? stage.label_zh : '能力模块'}
        </div>
        {stage ? (
          <div className="mt-1 truncate text-xs text-ink-muted">
            {ROLE_LABELS[stage.role] ?? stage.role}
          </div>
        ) : null}
      </div>
      <div className="flex-1 space-y-4 overflow-auto p-3">
        {groups.length === 0 ? (
          <p className="px-1 text-sm text-ink-muted">当前阶段无可展示模块</p>
        ) : (
          groups.map(([domain, items]) => (
            <section key={domain}>
              <div className="mb-2 px-1 text-xs font-medium uppercase tracking-wide text-ink-faint">
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
