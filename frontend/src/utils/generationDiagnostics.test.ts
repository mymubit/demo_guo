import { describe, expect, it } from 'vitest'
import {
  diagnoseGenerationFailure,
  formatGenerationTroubleMessage,
} from '@/utils/generationDiagnostics'

describe('diagnoseGenerationFailure', () => {
  it('maps disabled llm', () => {
    const t = diagnoseGenerationFailure('LLM 不可用 (disabled)，未冒充成功', {
      status: 'disabled',
    })
    expect(t?.kind).toBe('llm_disabled')
    expect(t?.showModelHubLink).toBe(true)
    expect(formatGenerationTroubleMessage(t!)).toMatch(/模型管理/)
  })

  it('maps misconfigured', () => {
    expect(diagnoseGenerationFailure('LLM 配置不完整')?.kind).toBe('llm_misconfigured')
  })

  it('maps 401 api key', () => {
    expect(diagnoseGenerationFailure('LLM HTTP 401: Incorrect API key')?.kind).toBe('llm_auth')
  })

  it('maps openai overseas / timeout', () => {
    expect(
      diagnoseGenerationFailure('LLM HTTP 500: connecting to api.openai.com failed')?.kind,
    ).toBe('llm_openai_overseas')
    expect(diagnoseGenerationFailure('Read timed out')?.kind).toBe('llm_timeout')
  })

  it('maps quota', () => {
    expect(diagnoseGenerationFailure('LLM HTTP 429: rate limit exceeded')?.kind).toBe('llm_quota')
  })

  it('returns null for empty non-terminal', () => {
    expect(diagnoseGenerationFailure('', { status: 'running' })).toBeNull()
  })
})
