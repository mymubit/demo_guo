export const PROJECT_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  AWAITING: 'awaiting',
  COMPLETED: 'completed',
  FAILED: 'failed',
}

export const UI_WORK_STATUS_TO_API_STATUS = {
  all: undefined,
  draft: PROJECT_STATUS.PENDING,
  generating: PROJECT_STATUS.RUNNING,
  awaiting: PROJECT_STATUS.AWAITING,
}

export const CREATION_STATUS_TEXT = {
  [PROJECT_STATUS.PENDING]: '待生成',
  [PROJECT_STATUS.RUNNING]: '生成中',
  [PROJECT_STATUS.AWAITING]: '待确认',
  [PROJECT_STATUS.COMPLETED]: '已完成',
  [PROJECT_STATUS.FAILED]: '生成失败',
}

export const DRAMA_STAGE = {
  STRATEGY: 'strategy',
  WORLDBUILDING: 'worldbuilding',
  PLOT_DESIGN: 'plot_design',
  WRITING: 'writing',
  REVIEW: 'review',
  POLISH: 'polish',
  PRODUCTION: 'production',
  COMPLIANCE: 'compliance',
  DELIVERED: 'delivered',
  READY: 'ready',
}

export const ORDER_STATUS = {
  PENDING: 'pending',
  PAID: 'paid',
  CANCELLED: 'cancelled',
  REFUNDED: 'refunded',
}

export const PAYMENT_METHOD = {
  WECHAT: 'wechat',
  ALIPAY: 'alipay',
  MOCK: 'mock',
}

export const ADMIN_PERMISSION_FIELDS = {
  STAFF: 'is_staff',
  SUPERUSER: 'is_superuser',
}

export const AGENT_FIELD = {
  CURRENT: 'agent_id',
}

export const DEFAULT_PAGE = 1
export const DEFAULT_PAGE_SIZE = 10
export const MAX_PAGE_SIZE = 100
