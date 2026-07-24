/** Contract + platform error codes */

export const API_SUCCESS_CODE = 0

export const API_ERROR_CODES = {
  SUCCESS: API_SUCCESS_CODE,
  UNAUTHORIZED: 401,
  TOKEN_EXPIRED: 4011,
  SIGNATURE_INVALID: 40101,
  PERMISSION_DENIED: 403,
  CONFIG_OVERLAY_FORBIDDEN: 40301,
  NOT_FOUND: 404,
  OPTIMISTIC_LOCK_FAILED: 40901,
  IDEMPOTENCY_CONFLICT: 40902,
  SCHEMA_VALIDATION_FAILED: 42201,
  WORKFLOW_GATE_BLOCKED: 42202,
  PLATFORM_POLICY_UNVERIFIED: 42203,
  RATE_LIMITED: 42901,
  SERVER_ERROR: 500,
} as const

export type ApiErrorCode = (typeof API_ERROR_CODES)[keyof typeof API_ERROR_CODES]

export const AUTH_ERROR_CODES = new Set<number>([
  API_ERROR_CODES.UNAUTHORIZED,
  API_ERROR_CODES.TOKEN_EXPIRED,
])

export const ERROR_CODE_MESSAGES: Record<number, string> = {
  [API_ERROR_CODES.UNAUTHORIZED]: '未登录或登录已过期',
  [API_ERROR_CODES.TOKEN_EXPIRED]: '登录已过期，请重新登录',
  [API_ERROR_CODES.PERMISSION_DENIED]: '没有权限执行此操作',
  [API_ERROR_CODES.CONFIG_OVERLAY_FORBIDDEN]: '配置覆盖被策略拒绝',
  [API_ERROR_CODES.NOT_FOUND]: '资源不存在',
  [API_ERROR_CODES.OPTIMISTIC_LOCK_FAILED]: '数据已被他人更新，请刷新后重试（If-Match 冲突）',
  [API_ERROR_CODES.IDEMPOTENCY_CONFLICT]: '幂等冲突：相同 command_id 已使用不同参数',
  [API_ERROR_CODES.SCHEMA_VALIDATION_FAILED]: '请求数据未通过 schema 校验',
  [API_ERROR_CODES.WORKFLOW_GATE_BLOCKED]: '流程门禁未通过，无法执行该命令',
  [API_ERROR_CODES.PLATFORM_POLICY_UNVERIFIED]: '目标平台政策未核验',
  [API_ERROR_CODES.RATE_LIMITED]: '请求过于频繁，请稍后再试',
  [API_ERROR_CODES.SERVER_ERROR]: '服务异常，请稍后重试',
  409: '资源冲突（409）',
  422: '请求无法处理（422）',
}

export class ApiError extends Error {
  readonly code: number
  readonly httpStatus?: number
  readonly data?: unknown
  readonly isAuthError: boolean
  readonly isOptimisticLock: boolean
  readonly isValidationError: boolean
  readonly isIdempotencyConflict: boolean
  readonly isPlatformPolicyUnverified: boolean

  constructor(opts: {
    message?: string
    code?: number
    httpStatus?: number
    data?: unknown
    fallbackMessage?: string
  }) {
    const code = opts.code ?? opts.httpStatus ?? API_ERROR_CODES.SERVER_ERROR
    const mapped = ERROR_CODE_MESSAGES[code] ?? ERROR_CODE_MESSAGES[opts.httpStatus ?? -1]
    const message = opts.message?.trim() || mapped || opts.fallbackMessage || '请求失败'
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.httpStatus = opts.httpStatus
    this.data = opts.data
    this.isAuthError = AUTH_ERROR_CODES.has(code) || opts.httpStatus === 401
    // 40901 vs 40902 must not collapse into a single 409 bucket
    this.isOptimisticLock = code === API_ERROR_CODES.OPTIMISTIC_LOCK_FAILED
    this.isIdempotencyConflict = code === API_ERROR_CODES.IDEMPOTENCY_CONFLICT
    this.isPlatformPolicyUnverified = code === API_ERROR_CODES.PLATFORM_POLICY_UNVERIFIED
    this.isValidationError =
      code === API_ERROR_CODES.SCHEMA_VALIDATION_FAILED ||
      code === API_ERROR_CODES.WORKFLOW_GATE_BLOCKED ||
      code === API_ERROR_CODES.PLATFORM_POLICY_UNVERIFIED ||
      (opts.httpStatus === 422 &&
        code !== API_ERROR_CODES.OPTIMISTIC_LOCK_FAILED &&
        code !== API_ERROR_CODES.IDEMPOTENCY_CONFLICT)
  }
}

export function mapApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  if (error instanceof Error) {
    return new ApiError({ message: error.message, fallbackMessage: '网络异常，请稍后重试' })
  }
  return new ApiError({ message: String(error), fallbackMessage: '未知错误' })
}

export function formatApiError(error: unknown): string {
  return mapApiError(error).message
}

/** 工作台排障：稳定业务码 + 人话（总纲 A11）。 */
export function formatApiErrorWithCode(error: unknown): string {
  const err = mapApiError(error)
  if (err.code > 0 && err.code !== API_ERROR_CODES.SERVER_ERROR) {
    return `[${err.code}] ${err.message}`
  }
  return err.message
}
