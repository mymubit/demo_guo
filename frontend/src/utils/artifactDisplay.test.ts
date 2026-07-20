import { describe, expect, it } from 'vitest'
import {
  formatConflictItem,
  formatRootRule,
  formatArcParts,
  looksLikeRawStructure,
  pickMeaningfulText,
} from '@/utils/artifactDisplay'

describe('artifactDisplay', () => {
  it('把 Python dict 字符串格式化为冲突链可读文案', () => {
    const raw =
      "{'stage': 1, 'conflict_type': '外部（宫规）', 'description': '身份暴露危机'}"
    expect(looksLikeRawStructure(raw)).toBe(true)
    expect(formatConflictItem(raw)).toBe('第1幕 · 外部（宫规）：身份暴露危机')
  })

  it('拆分根规则 ｜ 字符串为标题与明细', () => {
    const rule = formatRootRule(
      '宫女不得擅自进入禁宫｜触发：跨入未授权区域｜代价：杖责或处死',
    )
    expect(rule?.title).toBe('宫女不得擅自进入禁宫')
    expect(rule?.details).toEqual([
      { label: '触发', text: '跨入未授权区域' },
      { label: '代价', text: '杖责或处死' },
    ])
  })

  it('读取弧光别名字段并过滤待补充', () => {
    expect(
      formatArcParts({
        start: '隐忍',
        turning_point_1: '待补充',
        turning_point_2: '崩塌',
        end: '规则者',
      }),
    ).toEqual([
      { label: '起点', text: '隐忍' },
      { label: '转折二', text: '崩塌' },
      { label: '终局', text: '规则者' },
    ])
  })

  it('pickMeaningfulText 不返回原始结构串', () => {
    expect(pickMeaningfulText("{'a': 1}", '可读文案')).toBe('可读文案')
    expect(pickMeaningfulText('待补充', '正式内容')).toBe('正式内容')
  })
})
