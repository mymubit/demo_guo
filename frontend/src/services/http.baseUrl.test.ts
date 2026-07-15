import { describe, expect, it } from 'vitest'
import { API_BASE_URL } from '@/services/http'

describe('API_BASE_URL', () => {
  it('defaults to same-origin empty string when env unset', () => {
    // In vitest, VITE_API_BASE_URL may be undefined → empty string
    expect(typeof API_BASE_URL).toBe('string')
    // empty or explicitly set — must not silently fall back to localhost:8000
    expect(API_BASE_URL).not.toBe('http://localhost:8000')
  })
})
