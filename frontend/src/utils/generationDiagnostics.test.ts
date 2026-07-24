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

  it('maps illegal json parse errors', () => {
    const t = diagnoseGenerationFailure(
      'LLM 输出不是合法 JSON: Expecting property name enclosed in double quotes: line 326 column 73',
      { status: 'failed' },
    )
    expect(t?.title).toMatch(/无法解析/)
    expect(t?.steps.join(' ')).toMatch(/执行本阶段/)
  })

  it('maps compliance skipped when score below threshold', () => {
    const t = diagnoseGenerationFailure(
      '因评分 60 未达 B 档阈值 75，本轮跳过合规检查以节省调用。',
      { status: 'failed' },
    )
    expect(t?.kind).toBe('substance_gate')
    expect(t?.title).toMatch(/合规未跑/)
  })

  it('maps project_brief substance gate', () => {
    const t = diagnoseGenerationFailure(
      '选题简报过空：竞品须为真实作品名（禁止「竞品1」），每条含可执行的借鉴/避雷',
      { status: 'failed' },
    )
    expect(t?.kind).toBe('substance_gate')
    expect(t?.title).toMatch(/实质门禁/)
    expect(t?.showModelHubLink).toBe(false)
  })

  it('maps quality_report substance gate', () => {
    const t = diagnoseGenerationFailure(
      '十维评分缺少有效 evidence 或总评过短（禁止空壳分数报告）。',
      { status: 'failed' },
    )
    expect(t?.kind).toBe('substance_gate')
    expect(t?.title).toMatch(/评分报告/)
  })

  it('maps compliance_report substance gate', () => {
    const t = diagnoseGenerationFailure(
      '合规报告缺少具体阻断/风险描述（title+description）。禁止空标题或空话。',
      { status: 'failed' },
    )
    expect(t?.kind).toBe('substance_gate')
    expect(t?.title).toMatch(/合规报告/)
  })

  it('maps schema validation after successful llm', () => {
    const t = diagnoseGenerationFailure(
      "产物 Schema 校验失败（模型已返回内容，但结构不合规，未落库）: 'short' is a required property",
      { status: 'failed' },
    )
    expect(t?.kind).toBe('schema_validation')
    expect(t?.summary).toMatch(/调用日志/)
    expect(t?.showModelHubLink).toBe(false)
  })

  it('uses external review retry hints', () => {
    const t = diagnoseGenerationFailure('合规子任务失败', {
      status: 'failed',
      context: 'external_review',
    })
    expect(t?.steps.join(' ')).toMatch(/重新解析/)
    expect(t?.steps.join(' ')).not.toMatch(/工作台/)
  })

  it('returns null for empty non-terminal', () => {
    expect(diagnoseGenerationFailure('', { status: 'running' })).toBeNull()
  })
})
