import {
  LayoutDashboard,
  FolderKanban,
  Users,
  ShoppingCart,
  Crown,
  SlidersHorizontal,
  Layers,
  Wallet,
  Settings2,
  Wrench,
  LayoutGrid,
  BarChart3,
  Bot,
  Cpu,
  Activity,
} from 'lucide-react'

/**
 * 后台侧栏 IA
 *
 * 分组原则：按日常工作流，而非历史「十大中心」拆碎。
 * - 概览：运营数据与平台监控
 * - 创作：项目与流水线总览
 * - AI 引擎：大模型 → Agent → 流程编排 → 运行监察（配置与运行一体）
 * - 用户与商业：账号、订单、会员、计费
 * - 站点 / 系统
 */

/** 后台导航 IA */
export const ADMIN_NAV_GROUPS = [
  {
    id: 'overview',
    label: '概览',
    items: [
      {
        id: 'dashboard',
        path: '/admin/dashboard',
        label: '数据概览',
        icon: LayoutDashboard,
        description: '今日速览；商业 / 创作 / 成本分区',
      },
      {
        id: 'monitoring.business',
        path: '/admin/monitoring',
        label: '业务监控',
        icon: Activity,
        description: '前端异常、接口性能、慢 SQL、告警与埋点',
      },
    ],
  },
  {
    id: 'creation',
    label: '创作',
    collapsible: true,
    items: [
      {
        id: 'creation.hub',
        path: '/admin/creation',
        label: '创作总览',
        icon: LayoutGrid,
        description: '流水线总览与项目概况',
      },
      {
        id: 'creation.projects',
        path: '/admin/creation/projects',
        label: '创作项目',
        icon: FolderKanban,
        description: '项目列表与执行轨迹',
      },
    ],
  },
  {
    id: 'engine',
    label: 'AI 引擎',
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
        label: 'Agent 配置',
        icon: Bot,
        description: 'Agent 全景、填表 Agent、注册表与 LLM 路由',
      },
      {
        id: 'orchestration.flow',
        path: '/admin/orchestration?tab=flow',
        label: '流程编排',
        icon: Layers,
        description: '拖拽排序、并行分支、流水线步骤与 Prompt',
      },
      {
        id: 'orchestration.monitor',
        path: '/admin/orchestration?tab=monitor',
        label: '运行监察',
        icon: BarChart3,
        description: '子技能执行健康度与失败分布',
      },
      {
        id: 'engine.skills',
        path: '/admin/skills',
        label: '技能管理',
        icon: Wrench,
        description: 'Agent 技能定义 / 版本管理 / 调用统计',
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
        label: '用户',
        icon: Users,
        description: '账号查询、启用/禁用、重置密码',
      },
      {
        id: 'orders',
        path: '/admin/orders',
        label: '订单',
        icon: ShoppingCart,
        description: '会员与充值订单、退款',
      },
      {
        id: 'members.plans',
        path: '/admin/members/plans',
        label: '会员与卡密',
        icon: Crown,
        description: '套餐定价、权益对比与兑换码',
      },
      {
        id: 'commerce.settings',
        path: '/admin/commerce/settings',
        label: '商业设置',
        icon: Wallet,
        description: '币种、注册赠币、充值档位',
      },
    ],
  },
  {
    id: 'portal',
    label: '站点',
    items: [
      {
        id: 'portal.content',
        path: '/admin/portal',
        label: 'C 端配置',
        icon: SlidersHorizontal,
        description: '创作表单、题材与钩子库',
      },
    ],
  },
  {
    id: 'system',
    label: '系统',
    collapsible: true,
    items: [
      {
        id: 'system.maintenance',
        path: '/admin/system',
        label: '系统维护',
        icon: Settings2,
        description: '部署环境只读快照',
      },
      {
        id: 'system.configs',
        path: '/admin/system/configs',
        label: '动态配置',
        icon: SlidersHorizontal,
        description: '数据库配置、在线调整与审计',
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

  if (normalized === '/admin/orchestration' && !currentParams.get('tab')) {
    return flat.find((item) => item.id === 'orchestration.flow') || null
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
      parent?.groupLabel || '创作',
      parent?.label || '创作项目',
      '项目监察',
    ]
  }
  const item = findAdminNavItem(normalized, search)
  if (!item) return ['管理后台']
  return ['管理后台', item.groupLabel, item.label]
}
