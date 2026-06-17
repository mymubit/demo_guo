/**
 * api.js —— ScriptForge 前端 API 聚合导出
 *
 * 本文件仅作聚合 re-export，具体实现已按模块拆分至：
 *   services/http.js         - axios 单例 + 请求基础层
 *   services/auth.js         - 登录/注册/登出
 *   services/users.js        - 用户信息
 *   services/membership.js   - 会员套餐
 *   services/billing.js      - 钱包/账单/充值
 *   services/orders.js       - 订单
 *   services/creation.js     - 创作任务
 *   services/works.js        - 作品
 *   services/skill.js        - 技能/题材
 *   services/share.js        - 分享
 *   services/admin/          - 后台管理各中心
 */

export { auth } from './auth'
export { users } from './users'
export { membership } from './membership'
export { billing, DEFAULT_PAYMENT_METHOD, resolvePaymentMethod } from './billing'
export { orders } from './orders'
export { creation } from './creation'
export { works } from './works'
export { skill } from './skill'
export { share } from './share'
export { systemConfig } from './config/systemConfig'
export { useConfig, useConfigs, useConfigReady } from './config/useConfig'
export { useConfigStore, getConfigValue } from './config/configStore'
export {
  admin,
  adminMainChain,
  adminWorkflow,
  adminAgent,
  adminOrchestration,
  adminModel,
  adminMonitoring,
  adminStats,
  adminSystemConfig,
} from './admin'
export { API_BASE_URL as API_BASE } from './http'
export * from './constants/errorCodes'
export * from './constants/businessEnums'

import { auth } from './auth'
import { users } from './users'
import { membership } from './membership'
import { billing } from './billing'
import { orders } from './orders'
import { creation } from './creation'
import { works } from './works'
import { skill } from './skill'
import { share } from './share'
import { systemConfig } from './config/systemConfig'
import { admin, adminMainChain, adminWorkflow, adminAgent, adminOrchestration, adminModel, adminMonitoring, adminStats, adminSystemConfig } from './admin'
import { API_BASE_URL } from './http'

export default {
  auth,
  users,
  membership,
  billing,
  orders,
  creation,
  works,
  skill,
  share,
  systemConfig,
  admin,
  adminMainChain,
  adminWorkflow,
  adminAgent,
  adminOrchestration,
  adminModel,
  adminMonitoring,
  adminStats,
  adminSystemConfig,
  API_BASE: API_BASE_URL,
}
