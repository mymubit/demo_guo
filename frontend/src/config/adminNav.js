import {
  LayoutDashboard,
  FolderKanban,
  Users,
  ShoppingCart,
  Crown,
  SlidersHorizontal,
  Wallet,
  Settings2,
  Wrench,
  BarChart3,
  Bot,
  Cpu,
  Activity,
  BookOpen,
  Zap,
  ClipboardCheck,
  TrendingUp,
  Gauge,
  MessageSquare,
} from 'lucide-react'

/** 后台侧栏 IA — 按运营工作流分组 */
export const ADMIN_NAV_GROUPS = [
  {
    id: 'overview',
    label: '概览',
    items: [
      {
        id: 'dashboard',
        path: '/admin/dashboard',
        label: '数据看板',
        icon: LayoutDashboard,
        description: '今日速览；商业 / 创作 / 成本分区',
      },
      {
        id: 'admin.stats',
        path: '/admin/stats',
        label: '数据统计',
        icon: BarChart3,
        description: '调用量 / 成功率 / 耗时 / 排行',
      },
      {
        id: 'monitoring.business',
        path: '/admin/monitoring',
        label: '系统健康',
        icon: Activity,
        description: '前端异常、接口性能、慢 SQL、告警与埋点',
      },
    ],
  },
  {
    id: 'users-commerce',
    label: '用户与商业',
    items: [
      {
        id: 'users.list',
        path: '/admin/users',
        label: '用户管理',
        icon: Users,
        description: '账号查询、启用/禁用、重置密码',
      },
      {
        id: 'members.plans',
        path: '/admin/members/plans',
        label: '会员与套餐',
        icon: Crown,
        description: '套餐定价、权益对比与兑换码',
      },
      {
        id: 'orders',
        path: '/admin/orders',
        label: '订单',
        icon: ShoppingCart,
        description: '会员与充值订单、退款',
      },
      {
        id: 'commerce.settings',
        path: '/admin/commerce/settings',
        label: '钱包与计费',
        icon: Wallet,
        description: '币种、注册赠币、充值档位与定价',
      },
    ],
  },
  {
    id: 'content-quality',
    label: '内容质量',
    collapsible: true,
    items: [
      {
        id: 'creation.projects',
        path: '/admin/creation/projects',
        label: '创作项目',
        icon: FolderKanban,
        description: '项目列表、执行轨迹与质量缺陷',
      },
      {
        id: 'operations.feedback',
        path: '/admin/operations/feedback',
        label: '用户反馈',
        icon: MessageSquare,
        description: 'P0 优先 + 抽样回访',
      },
      {
        id: 'operations.content-quality',
        path: '/admin/operations/content-quality',
        label: '内容质量评分',
        icon: TrendingUp,
        description: '保存率/导出率/弃用率/卡点人群',
      },
      {
        id: 'operations.checklist',
        path: '/admin/operations/checklist',
        label: '日常 Checklist',
        icon: ClipboardCheck,
        description: '5 分钟巡检 5 步',
      },
      {
        id: 'operations.dashboard',
        path: '/admin/operations/dashboard',
        label: '运营 Dashboard',
        icon: LayoutDashboard,
        description: '5 个核心 SLO 卡片 + 子页面入口',
      },
      {
        id: 'operations.config-hit',
        path: '/admin/operations/config-hit',
        label: '配置命中率',
        icon: Gauge,
        description: '死代码候选 & 24h 热点',
      },
    ],
  },
  {
    id: 'ai-config',
    label: 'AI 配置',
    collapsible: true,
    items: [
      {
        id: 'model.hub',
        path: '/admin/model',
        label: '大模型',
        icon: Cpu,
        description: '厂商 Key、模型目录与 Token 单价',
      },
      {
        id: 'agent.hub',
        path: '/admin/agent',
        label: 'Agent 定义',
        icon: Bot,
        description: '独立 Agent、Prompt 版本与 Knowledge 绑定',
      },
      {
        id: 'agent.runs',
        path: '/admin/agent?tab=runs',
        label: '运行记录',
        icon: Activity,
        description: '独立 Agent 最近执行记录与健康状态',
      },
      {
        id: 'engine.skills',
        path: '/admin/skills',
        label: '技能规则',
        icon: Wrench,
        description: '技能定义、版本管理与进化提案',
      },
      {
        id: 'engine.evolution',
        path: '/admin/evolution',
        label: '规则进化',
        icon: Zap,
        description: 'AI 分析低评分项目 / 生成规则修改提案 / 审批流',
      },
    ],
  },
  {
    id: 'site-config',
    label: '站点配置',
    collapsible: true,
    items: [
      {
        id: 'portal.content',
        path: '/admin/portal',
        label: 'C 端配置',
        icon: SlidersHorizontal,
        description: '创作表单、题材与钩子库',
      },
      {
        id: 'engine.library',
        path: '/admin/library',
        label: '素材库',
        icon: BookOpen,
        description: '参考作品结构化管理 / 创作时自动注入',
      },
      {
        id: 'system.configs',
        path: '/admin/system/configs',
        label: '动态配置中心',
        icon: SlidersHorizontal,
        description: '数据库配置、在线调整与审计',
      },
    ],
  },
  {
    id: 'system',
    label: '系统',
    collapsible: true,
    items: [
      {
        id: 'admin.system',
        path: '/admin/system',
        label: '系统参数',
        icon: Settings2,
        description: '全局开关 / 阈值 / 配额 / 敏感词',
      },
      {
        id: 'system.maintenance',
        path: '/admin/system/maintenance',
        label: '系统维护',
        icon: Wrench,
        description: '部署环境只读快照',
      },
      {
        id: 'system.advanced',
        path: '/admin/system/advanced',
        label: '高级参数',
        icon: Wrench,
        description: '引擎内部开关与实验特性',
      },
    ],
  },
]

export function flattenAdminNav() {
  return ADMIN_NAV_GROUPS.flatMap((g) =>
    g.items.map((item) => ({ ...item, groupId: g.id, groupLabel: g.label }))
  )
}

function normalizeAdminPathname(pathname) {
  return pathname === '/admin' ? '/admin/dashboard' : pathname
}

export function findAdminNavItem(pathname, search = '') {
  const normalized = normalizeAdminPathname(pathname)
  const currentParams = new URLSearchParams(String(search || '').replace(/^\?/, ''))
  const flat = flattenAdminNav()

  for (const item of flat) {
    const qIdx = item.path.indexOf('?')
    if (qIdx < 0) continue
    const itemPath = item.path.slice(0, qIdx)
    if (normalized !== itemPath && !normalized.startsWith(`${itemPath}/`)) continue
    const itemParams = new URLSearchParams(item.path.slice(qIdx + 1))
    let matched = true
    for (const [key, value] of itemParams.entries()) {
      if (currentParams.get(key) !== value) {
        matched = false
        break
      }
    }
    if (matched) return item
  }

  if (normalized === '/admin/agent' && !currentParams.get('tab')) {
    return flat.find((item) => item.id === 'agent.hub') || null
  }

  const sorted = [...flat]
    .filter((item) => !item.path.includes('?'))
    .sort((a, b) => b.path.length - a.path.length)
  return (
    sorted.find(
      (item) => normalized === item.path || normalized.startsWith(`${item.path}/`)
    ) || null
  )
}

/** 侧栏高亮 */
export function isAdminNavItemActive(pathname, navItem, search = '') {
  const active = findAdminNavItem(pathname, search)
  return active?.id === navItem.id
}

/** 顶栏面包屑（含创作项目监察子页） */
export function getAdminBreadcrumb(pathname, search = '') {
  const normalized = normalizeAdminPathname(pathname)
  const projectTrace = normalized.match(/^\/admin\/creation\/projects\/([^/]+)\/trace\/?$/)
  if (projectTrace) {
    const parent = findAdminNavItem('/admin/creation/projects')
    return [
      '管理后台',
      parent?.groupLabel || '内容质量',
      parent?.label || '创作项目',
      '项目详情',
    ]
  }
  const item = findAdminNavItem(normalized, search)
  if (!item) return ['管理后台']
  return ['管理后台', item.groupLabel, item.label]
}
