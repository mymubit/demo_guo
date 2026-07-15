import { describe, expect, it } from 'vitest'
import { ApiError, API_ERROR_CODES, formatApiError, mapApiError } from '@/services/errors'

describe('API error mapping', () => {
  it('maps optimistic lock 40901 distinctly from idempotency 40902', () => {
    const lock = new ApiError({ code: API_ERROR_CODES.OPTIMISTIC_LOCK_FAILED, httpStatus: 409 })
    expect(lock.isOptimisticLock).toBe(true)
    expect(lock.isIdempotencyConflict).toBe(false)
    expect(lock.message).toMatch(/If-Match|冲突/)

    const idem = new ApiError({ code: API_ERROR_CODES.IDEMPOTENCY_CONFLICT, httpStatus: 409 })
    expect(idem.isIdempotencyConflict).toBe(true)
    expect(idem.isOptimisticLock).toBe(false)
    expect(idem.message).toMatch(/幂等/)
  })

  it('does not treat bare HTTP 409 as optimistic lock', () => {
    const bare = new ApiError({ httpStatus: 409, message: 'conflict' })
    // code falls back to httpStatus 409 — not 40901
    expect(bare.isOptimisticLock).toBe(false)
    expect(bare.isIdempotencyConflict).toBe(false)
  })

  it('maps platform policy unverified 42203', () => {
    const err = new ApiError({
      code: API_ERROR_CODES.PLATFORM_POLICY_UNVERIFIED,
      httpStatus: 422,
    })
    expect(err.isPlatformPolicyUnverified).toBe(true)
    expect(err.isValidationError).toBe(true)
    expect(formatApiError(err)).toMatch(/平台政策/)
  })

  it('maps schema validation codes', () => {
    const validation = new ApiError({
      code: API_ERROR_CODES.SCHEMA_VALIDATION_FAILED,
      httpStatus: 422,
    })
    expect(validation.isValidationError).toBe(true)
  })

  it('prefers server message when provided', () => {
    const err = new ApiError({
      code: API_ERROR_CODES.WORKFLOW_GATE_BLOCKED,
      message: '蓝图未批准',
      httpStatus: 422,
    })
    expect(formatApiError(err)).toBe('蓝图未批准')
  })

  it('wraps unknown errors', () => {
    const mapped = mapApiError(new Error('boom'))
    expect(mapped).toBeInstanceOf(ApiError)
    expect(mapped.message).toBe('boom')
  })
})
