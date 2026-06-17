/**
 * C 端导航与路由对齐清单。
 * MainLayout 顶栏、ToolsShell、404 建议入口应与此保持一致。
 */

/** 顶栏导航（不含个人中心 — 在用户菜单中） */
export const CONSUMER_TOP_NAV = [
  { path: '/', label: '首页' },
  { path: '/creation', label: '开始创作' },
  { path: '/evaluate', label: '剧本评估' },
  { path: '/pull-sheet', label: '拉片分析' },
  { path: '/works', label: '我的作品' },
  { path: '/wallet', label: '创作币' },
  { path: '/member', label: '会员中心' },
  { path: '/orders', label: '我的订单' },
]

/** 需登录但不在顶栏的路由 */
export const CONSUMER_PRIVATE_ROUTES = [{ path: '/profile', label: '个人中心' }]

/** 公开独立页（分享等） */
export const CONSUMER_PUBLIC_ROUTES = [{ path: '/share/:token', label: '作品分享' }]

/** 路径别名（重定向，仍须在 router 注册） */
export const CONSUMER_ROUTE_ALIASES = [
  { path: '/tools', redirectTo: '/evaluate' },
  { path: '/tools/evaluate', redirectTo: '/evaluate' },
  { path: '/tools/pull-sheet', redirectTo: '/pull-sheet' },
]

export function flattenConsumerRoutePaths() {
  return [
    ...CONSUMER_TOP_NAV.map((item) => item.path),
    ...CONSUMER_PRIVATE_ROUTES.map((item) => item.path),
    ...CONSUMER_PUBLIC_ROUTES.map((item) => item.path),
    ...CONSUMER_ROUTE_ALIASES.map((item) => item.path),
  ]
}
