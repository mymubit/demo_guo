import { describe, expect, it } from 'vitest'
import { formatRoleLabel, ROLE_LABEL_ZH } from './roleLabels'

describe('formatRoleLabel', () => {
  it('优先使用接口返回的 role_label', () => {
    expect(formatRoleLabel('drama.topic-director', '选题定调官')).toBe('选题定调官')
  })

  it('回退到本地中文映射', () => {
    expect(formatRoleLabel('drama.script-writer')).toBe(ROLE_LABEL_ZH['drama.script-writer'])
  })

  it('未知角色去掉前缀', () => {
    expect(formatRoleLabel('drama.unknown-role')).toBe('unknown-role')
  })
})
