import { describe, expect, it } from 'vitest'
import {
  axisFieldLabelZh,
  complianceRiskLabelZh,
  localizeProseForDisplay,
  resolveThemeOptionLabel,
} from '@/utils/themeLabels'
import type { ThemeMatrix } from '@/types/workbench'

const matrix: ThemeMatrix = {
  dim_order: ['emotion', 'identity', 'conflict', 'world'],
  axes: {
    emotion: {
      label_zh: '主情绪',
      options: [{ value: 'ambition', label_zh: '野心逐权' }],
    },
    world: {
      label_zh: '时空背景',
      options: [{ value: 'ancient', label_zh: '古代古风' }],
    },
    audience_channel: {
      label_zh: '受众频道',
      options: [{ value: 'female', label_zh: '女频' }],
    },
    protagonist_structure: {
      label_zh: '主角结构',
      options: [{ value: 'single-female', label_zh: '大女主' }],
    },
  },
  flavor_tags: {
    max_select: 5,
    categories: [],
    options: [{ value: 'palace', label_zh: '宫斗宅斗·朝堂', category: 'all' }],
  },
}

describe('themeLabels', () => {
  it('maps axis field keys to Chinese', () => {
    expect(axisFieldLabelZh('flavor_tags')).toBe('风味标签')
    expect(axisFieldLabelZh('audience_channel')).toBe('受众频道')
    expect(axisFieldLabelZh('emotion')).toBe('主情绪')
  })

  it('resolves option values via theme matrix', () => {
    expect(resolveThemeOptionLabel(matrix, 'emotion', 'ambition')).toBe('野心逐权')
    expect(resolveThemeOptionLabel(matrix, 'world', 'ancient')).toBe('古代古风')
    expect(resolveThemeOptionLabel(matrix, 'flavor_tags', 'palace')).toBe('宫斗宅斗·朝堂')
    expect(resolveThemeOptionLabel(matrix, 'audience_channel', 'female')).toBe('女频')
  })

  it('falls back when matrix missing', () => {
    expect(resolveThemeOptionLabel(null, 'emotion', 'ambition')).toBe('野心逐权')
    expect(resolveThemeOptionLabel(undefined, 'flavor_tags', 'palace')).toBe('宫斗宅斗·朝堂')
  })

  it('maps risk levels', () => {
    expect(complianceRiskLabelZh('medium')).toBe('中')
  })

  it('localizes English craft terms in prose', () => {
    expect(localizeProseForDisplay('她的 Want 与 Need 冲突，Hook 要够猛')).toBe(
      '她的 外在欲望 与 内在需求 冲突，钩子 要够猛',
    )
  })
})
