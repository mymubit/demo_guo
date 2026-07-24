import { describe, expect, it } from 'vitest'
import {
  buildArtifactSections,
  flattenArtifactEntries,
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

  it('flattenArtifactEntries 产出中文标签条目', () => {
    const entries = flattenArtifactEntries({
      title: '逆袭',
      core_idea: '翻盘',
      genre_matrix: { emotion: 'revenge' },
    })
    expect(entries.some((e) => e.label === '标题' && e.value === '逆袭')).toBe(true)
    expect(entries.some((e) => e.label === '核心创意' && e.value === '翻盘')).toBe(true)
    expect(
      entries.some((e) => e.label.includes('主情绪') && e.value === '复仇爽感'),
    ).toBe(true)
  })

  it('buildArtifactSections 跳过技术键并中文化题材矩阵', () => {
    const sections = buildArtifactSections({
      title: '逆袭',
      theme_code: 'matrix',
      matrix_key: 'x',
      genre_matrix: { emotion: 'revenge', world: 'modern' },
      compliance_risk: 'low',
    })
    const titles = sections.map((s) => s.title)
    expect(titles).toContain('概要')
    expect(titles).toContain('题材矩阵')
    const summary = sections.find((s) => s.id === 'summary')
    expect(summary?.rows.some((r) => r.label === '合规风险' && r.value === '低')).toBe(true)
    expect(summary?.rows.some((r) => r.label.includes('theme'))).toBeFalsy()
    const matrix = sections.find((s) => s.id === 'genre_matrix')
    expect(matrix?.rows.some((r) => r.label === '主情绪' && r.value === '复仇爽感')).toBe(true)
  })

  it('角色字段标签与枚举值全部中文', () => {
    const sections = buildArtifactSections({
      characters: [
        {
          name: '林薇',
          role_type: 'protagonist',
          surface_desire: '夺回一切',
          deep_need: '被真正看见',
          ghost: '被抛弃的记忆',
          lie: '示弱才能活',
          flaw: '过度隐忍',
          voice_tag: '冷淡短句',
          visual_anchor: '红绳手串',
        },
      ],
    })
    const text = JSON.stringify(sections)
    expect(text).not.toMatch(/\b(protagonist|surface_desire|deep_need|ghost|lie|flaw)\b/)
    const charSection = sections.find((s) => s.title.includes('角色'))
    expect(charSection?.rows.some((r) => r.label === '角色类型' && r.value === '主角')).toBe(true)
    expect(charSection?.rows.some((r) => r.label === '外在欲望')).toBe(true)
    expect(charSection?.rows.some((r) => r.label === '内在需求')).toBe(true)
    expect(charSection?.rows.some((r) => r.label === '心结')).toBe(true)
  })

  it('完整展开深层嵌套与长数组，不截断', () => {
    const sections = buildArtifactSections({
      rule_params: {
        reversal_density: 0.3,
        emotion_curve: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
      },
      series_structure: {
        six_stage_structure: [
          { name: '开端', description: '被抛弃' },
          { name: '发展', description: '反击' },
        ],
        foreshadowing_table: [{ setup: '红绳', payoff: '真相' }],
      },
    })
    const flat = sections.flatMap((s) => s.rows)
    expect(flat.some((r) => r.label === '反转频率' && r.value.includes('30%'))).toBe(true)
    expect(flat.some((r) => r.label === '全剧情绪走势' && r.value.includes('12'))).toBe(true)
    expect(flat.some((r) => r.value === '被抛弃')).toBe(true)
    expect(flat.some((r) => r.value === '真相')).toBe(true)
    expect(flat.some((r) => r.value.includes('请查看原始 JSON'))).toBe(false)
  })

  it('对标作品卡片化，规则参数用人话解释', () => {
    const sections = buildArtifactSections({
      competitor_references: [
        {
          title: '去有风的地方',
          inspiration: '慢节奏烟火细节',
          avoidance: '避免无冲突散文式散漫',
        },
      ],
      rule_params: {
        reversal_density: 0.4,
        emotion_curve: [3, 2, 1, 4, 7, 8, 9, 10],
        act_ratio: [0.1, 0.2, 0.2, 0.2, 0.15, 0.15],
        hook_types: ['身份反转'],
      },
    })
    const competitors = sections.find((s) => s.id === 'competitor_references')
    expect(competitors?.title).toBe('对标作品')
    expect(competitors?.hint).toContain('学它的优点')
    expect(competitors?.cards?.[0]?.title).toBe('去有风的地方')
    expect(competitors?.cards?.[0]?.rows.some((r) => r.label === '可借鉴')).toBe(true)
    expect(competitors?.cards?.[0]?.rows.some((r) => r.label === '需规避')).toBe(true)

    const rules = sections.find((s) => s.id === 'rule_params')
    expect(rules?.title).toBe('叙事节奏设定')
    expect(rules?.rows.some((r) => r.label === '反转频率' && r.value.includes('偏密'))).toBe(true)
    expect(rules?.rows.some((r) => r.label === '六阶段篇幅占比' && r.value.includes('开篇'))).toBe(
      true,
    )
    expect(rules?.rows.some((r) => r.label === '全剧情绪走势' && r.value.includes('→'))).toBe(true)
  })
})
