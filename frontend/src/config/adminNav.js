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
 * 后台 IA — 对齐十大中心
 *
 * | 中心       | 导航分组     | 路径 |
 * |------------|-------------|------|
 * | 监控中心   | 监控中心    | /admin/dashboard |
 * | 用户中心   | 用户中心    | users / members/* |
 * | 创作中心   | 创作中心    | creation/* |
 * | 主链工作室 | 主链工作室  | /admin/main-chain |
 * | Agent 中心 | Agent 中心  | /admin/agent |
 * | 调度中心   | 调度中心    | /admin/orchestration |
 * | 模型中心   | 模型中心    | /admin/model |
 * | 配置中心   | 配置中心    | /admin/portal |
 * | 商业中心   | 商业中心    | commerce/* / orders |
 * | 系统       | 系统        | system/* |
 */

/** 后台导航 IA */
export const ADMIN_NAV_GROUPS = [
  {
    id: 'monitor',
    label: '监控中心',
    items: [
      {
        id: 'dashboard',
        path: '/admin/dashboard',
        label: '数据概览',
        icon: LayoutDashboard,
        description: '今日速览；商业 / 创作 / 成本分区下钻',
      },
      {
        id: 'monitoring.business',
        path: '/admin/monitoring',
        label: '业务监控',
        icon: Activity,
        description: '前端异常、接口性能、慢 SQL、告警与埋点分析',
      },
    ],
  },
  {
    id: 'identity',
    label: '用户中心',
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
    ],
  },
  {
    id: 'creation',
    label: '创作中心',
    collapsible: true,
    items: [
      {
        id: 'creation.hub',
        path: '/admin/creation',
        label: '创作总览',
        icon: LayoutGrid,
        description: '流水线总览与快捷入口',
      },
      {
        id: 'creation.projects',
        path: '/admin/creation/projects',
        label: '创作项目',
        icon: FolderKanban,
        description: '项目列表与执行监察',
      },
    ],
  },
  {
    id: 'main-chain',
    label: '主链工作室',
    items: [
      {
        id: 'main-chain.studio',
        path: '/admin/main-chain',
        label: '主链蓝图',
        icon: Layers,
        description: '步骤编排、Agent 绑定、模型路由与运营配置',
      },
    ],
  },
  {
    id: 'agent',
    label: 'Agent 中心',
    items: [
      {
        id: 'agent.hub',
        path: '/admin/agent',
        label: 'Agent 配置',
        icon: Bot,
        description: '注册表、写作规则、质检评分（高级配置）',
      },
    ],
  },
  {
    id: 'orchestration',
    label: '调度中心',
    items: [
      {
        id: 'orchestration.monitor',
        path: '/admin/orchestration',
        label: '调度监控',
        icon: BarChart3,
        description: '子技能执行健康度与失败分布',
      },
    ],
  },
  {
    id: 'model',
    label: '模型中心',
    items: [
      {
        id: 'model.hub',
        path: '/admin/model',
        label: '大模型',
        icon: Cpu,
        description: '厂商 Key、模型目录与 Token 单价',
      },
    ],
  },
  {
    id: 'portal',
    label: '配置中心',
    items: [
      {
        id: 'portal.content',
        path: '/admin/portal',
        label: 'C 端配置',
        icon: SlidersHorizontal,
        description: '创作表单、填表 AI、题材与钩子库',
      },
    ],
  },
  {
    id: 'commerce',
    label: '商业中心',
    items: [
      {
        id: 'commerce.settings',
        path: '/admin/commerce/settings',
        label: '商业与订单',
        icon: Wallet,
        description: '币种、注册赠币、充值档位',
      },
    ],
  },
  {
    id: 'system',
    label: '系统',
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
        description: '数据库配置中心、在线调整、缓存刷新与审计',
      },
      {
        id: 'system.advanced',
        path: '/admin/system/advanced',
        label: '高级参数',
        icon: Wrench,
        description: '引擎内部开关；模型与 Agent 见各中心',
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

export function findAdminNavItem(pathname) {
  const normalized = normalizeAdminPathname(pathname)
  const flat = flattenAdminNav()
  const sorted = [...flat].sort((a, b) => b.path.length - a.path.length)
  return sorted.find(
    (item) => normalized === item.path || normalized.startsWith(`${item.path}/`)
  )
}

/** 侧栏高亮 */
export function isAdminNavItemActive(pathname, navItem) {
  const active = findAdminNavItem(pathname)
  return active?.id === navItem.id
}

/** 顶栏面包屑（含创作项目监察子页） */
export function getAdminBreadcrumb(pathname) {
  const normalized = normalizeAdminPathname(pathname)
  const projectTrace = normalized.match(/^\/admin\/creation\/projects\/([^/]+)\/trace\/?$/)
  if (projectTrace) {
    const parent = findAdminNavItem('/admin/creation/projects')
    return [
      '管理后台',
      parent?.groupLabel || '创作中心',
      parent?.label || '创作项目',
      '项目监察',
    ]
  }
  const item = findAdminNavItem(normalized)
  if (!item) return ['管理后台']
  return ['管理后台', item.groupLabel, item.label]
}
