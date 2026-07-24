import { describe, expect, it } from 'vitest'
import { V3_NAV_ITEMS, V3_NAV_PATHS } from './router'

describe('v3 router paths', () => {
  it('exposes product IA paths and not studio', () => {
    expect(V3_NAV_PATHS).toEqual(
      expect.arrayContaining([
        '/dashboard',
        '/templates',
        '/knowledge',
        '/models',
        '/logs',
        '/usage',
        '/system',
        '/billing',
      ]),
    )
    expect(V3_NAV_PATHS.some((p) => p.startsWith('/studio'))).toBe(false)
  })

  it('derives paths from V3_NAV_ITEMS single source', () => {
    expect(V3_NAV_PATHS).toEqual(V3_NAV_ITEMS.map((item) => item.to))
    expect(V3_NAV_ITEMS).toHaveLength(8)
    expect(V3_NAV_ITEMS.every((item) => item.label && item.hint && item.icon)).toBe(true)
  })

  it('places templates and knowledge near dashboard', () => {
    const paths = V3_NAV_ITEMS.map((item) => item.to)
    expect(paths.indexOf('/dashboard')).toBeLessThan(paths.indexOf('/templates'))
    expect(paths.indexOf('/templates')).toBeLessThan(paths.indexOf('/knowledge'))
    expect(paths.indexOf('/knowledge')).toBeLessThan(paths.indexOf('/models'))
    expect(V3_NAV_ITEMS.find((item) => item.to === '/templates')).toMatchObject({
      label: '模板库',
      hint: '内置与自定义模板',
    })
    expect(V3_NAV_ITEMS.find((item) => item.to === '/knowledge')).toMatchObject({
      label: '知识库',
      hint: '创作知识文档',
    })
  })

  it('places usage nav between logs and system', () => {
    const labels = V3_NAV_ITEMS.map((item) => item.label)
    expect(labels.indexOf('执行日志')).toBeLessThan(labels.indexOf('用量'))
    expect(labels.indexOf('用量')).toBeLessThan(labels.indexOf('系统配置'))
    expect(V3_NAV_ITEMS.find((item) => item.to === '/usage')).toMatchObject({
      label: '用量',
      hint: 'Token 与费用',
    })
  })
})
