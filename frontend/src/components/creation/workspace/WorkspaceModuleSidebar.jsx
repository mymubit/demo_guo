/**
 * Agent 工作台左侧 — 主链模块导航
 */
import { Sparkles } from 'lucide-react'
import { PIPELINE_NODE_ICONS } from '@/config/fusion'
import { SideSectionTitle } from '@/components/shared/ConsumerSection'
import { cn } from '@/utils/cn'

function tabStatusDot(skill) {
  const kind = skill?.content_kind
  if (skill?.status === 'running') return 'bg-gold-400 animate-pulse'
  if (skill?.status === 'failed') return 'bg-red-400'
  if (skill?.index === 1 && skill?.has_content && kind === 'user_confirmed') return 'bg-green-400'
  if (kind === 'agent_generated' || (skill?.status === 'completed' && skill?.has_content)) return 'bg-green-400'
  if (kind === 'user_confirmed' || (skill?.index === 1 && skill?.has_content)) return 'bg-gold-300'
  return 'bg-slate-600'
}

function tabStatusLabel(skill) {
  const kind = skill?.content_kind
  if (skill?.status === 'running') return '生成中'
  if (skill?.status === 'failed') return '失败'
  if (skill?.index === 1 && skill?.has_content && kind === 'user_confirmed') return '已确认'
  if (kind === 'agent_generated' || (skill?.status === 'completed' && skill?.has_content)) return '已生成'
  if (kind === 'user_confirmed' || (skill?.index === 1 && skill?.has_content)) return '已确认'
  if (skill?.has_content) return '草稿'
  return '待生成'
}

function tabStatusClass(skill) {
  const kind = skill?.content_kind
  if (skill?.status === 'running') return 'border-gold-400/25 bg-gold-400/10 text-gold-300'
  if (skill?.status === 'failed') return 'border-red-400/25 bg-red-500/10 text-red-300'
  if (kind === 'agent_generated' || (skill?.status === 'completed' && skill?.has_content)) {
    return 'border-green-400/20 bg-green-500/10 text-green-300'
  }
  if (kind === 'user_confirmed' || (skill?.index === 1 && skill?.has_content)) {
    return 'border-gold-400/20 bg-gold-400/10 text-gold-300'
  }
  return 'border-white/10 bg-white/[0.03] text-navy-400'
}

export default function WorkspaceModuleSidebar({
  modules = [],
  activeIndex,
  onSelect,
  agentTabName,
}) {
  return (
    <>
      <SideSectionTitle>主链模块</SideSectionTitle>
      <nav className="mt-2 space-y-0.5">
        {modules.map((skill) => {
          const Icon = PIPELINE_NODE_ICONS[(skill.index || 1) - 1] || Sparkles
          const active = skill.index === activeIndex
          return (
            <button
              key={skill.index}
              type="button"
              onClick={() => onSelect(skill.index)}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-xl border px-3 py-2.5 text-left text-sm transition-colors',
                active
                  ? 'border-gold-400/30 bg-gold-400/10 text-white shadow-gold'
                  : 'border-transparent text-navy-200 hover:bg-white/5 hover:text-white',
              )}
            >
              <span
                className={cn(
                  'grid h-[22px] w-[22px] shrink-0 place-items-center rounded-md text-[11px]',
                  active
                    ? 'bg-gradient-to-br from-gold-300 to-gold-500 text-navy-950'
                    : 'border border-white/10 bg-white/5 text-navy-300',
                )}
              >
                {skill.index}
              </span>
              <span className="min-w-0 flex-1 truncate">{agentTabName(skill)}</span>
              <span
                className={cn(
                  'inline-flex shrink-0 items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] leading-none',
                  tabStatusClass(skill),
                )}
              >
                <span className={cn('h-1.5 w-1.5 rounded-full', tabStatusDot(skill))} />
                {tabStatusLabel(skill)}
              </span>
            </button>
          )
        })}
      </nav>
    </>
  )
}
