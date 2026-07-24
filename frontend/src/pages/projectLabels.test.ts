import { describe, expect, it } from 'vitest'
import { resolveNextStageCta, resolveOverviewStageCta } from './projectLabels'

describe('resolveNextStageCta', () => {
  it('maps each stage to the following workbench path', () => {
    expect(resolveNextStageCta('p1', 'topic')).toEqual({
      kind: 'link',
      to: '/projects/p1/blueprint',
      label: '去故事蓝图',
    })
    expect(resolveNextStageCta('p1', 'writing')).toEqual({
      kind: 'link',
      to: '/projects/p1/quality',
      label: '去质检中心',
    })
    expect(resolveNextStageCta('p1', 'delivery')).toBeNull()
  })

  it('overview CTA still points at current stage path', () => {
    expect(resolveOverviewStageCta('p1', 'writing')).toEqual({
      kind: 'link',
      to: '/projects/p1/editor',
      label: '去正文编辑',
    })
  })
})
