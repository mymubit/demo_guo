import { Activity, Bot, Cpu, Layers, Wrench, Zap } from 'lucide-react'

/** AI 配置侧栏对应的 5 个二级分区（页内顶栏导航同步） */
export const AI_CONFIG_SECTIONS = [
  {
    id: 'model',
    path: '/admin/model',
    label: '大模型',
    icon: Cpu,
    description: '厂商凭证、模型接入、Token 单价与全局默认',
  },
  {
    id: 'agent-definitions',
    path: '/admin/agent',
    tab: null,
    label: 'Agent 定义',
    icon: Bot,
    description: 'Drama 12 角色 Prompt 版本、Knowledge 绑定与健康检查',
  },
  {
    id: 'agent-runs',
    path: '/admin/agent',
    tab: 'runs',
    label: '运行记录',
    icon: Activity,
    description: 'Drama 角色执行记录与可读摘要',
  },
  {
    id: 'skills',
    path: '/admin/skills',
    label: '技能定义',
    icon: Wrench,
    description: '各技能的 Prompt、Schema、版本发布与调用统计',
  },
  {
    id: 'tier-rules',
    path: '/admin/tier-rules',
    label: 'Tier 规则库',
    icon: Layers,
    description: 'Tier1–4 全站通用规则：铁律、题材、节点、合规与待审核',
  },
  {
    id: 'evolution',
    path: '/admin/evolution',
    label: '规则进化',
    icon: Zap,
    description: '低分项目分析、规则修改提案与审批流',
  },
]

export function matchAiConfigSection(pathname, search = '') {
  const params = new URLSearchParams(String(search || '').replace(/^\?/, ''))
  const tab = params.get('tab')

  if (pathname.startsWith('/admin/model')) {
    return AI_CONFIG_SECTIONS.find((s) => s.id === 'model')
  }
  if (pathname.startsWith('/admin/skills')) {
    return AI_CONFIG_SECTIONS.find((s) => s.id === 'skills')
  }
  if (pathname.startsWith('/admin/tier-rules')) {
    return AI_CONFIG_SECTIONS.find((s) => s.id === 'tier-rules')
  }
  if (pathname.startsWith('/admin/evolution')) {
    return AI_CONFIG_SECTIONS.find((s) => s.id === 'evolution')
  }
  if (pathname.startsWith('/admin/agent')) {
    if (tab === 'runs') {
      return AI_CONFIG_SECTIONS.find((s) => s.id === 'agent-runs')
    }
    return AI_CONFIG_SECTIONS.find((s) => s.id === 'agent-definitions')
  }
  return null
}

export function aiConfigSectionHref(section) {
  if (!section) return '/admin/model'
  if (section.tab) return `${section.path}?tab=${section.tab}`
  return section.path
}
