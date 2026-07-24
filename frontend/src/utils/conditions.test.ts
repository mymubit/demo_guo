import { describe, expect, it } from 'vitest'
import { evaluateCondition, settingsConditionContext } from '@/utils/conditions'

describe('evaluateCondition', () => {
  it('evaluates equality on strings and booleans', () => {
    expect(evaluateCondition("entry_type == 'original_track'", { entry_type: 'original_track' })).toBe(true)
    expect(evaluateCondition("entry_type == 'story_adapt'", { entry_type: 'original_track' })).toBe(false)
    expect(evaluateCondition('enable_delivery == true', { enable_delivery: true })).toBe(true)
    expect(evaluateCondition('enable_delivery == false', { enable_delivery: true })).toBe(false)
  })

  it('evaluates contains against arrays', () => {
    expect(
      evaluateCondition("deliverables contains 'budget'", {
        deliverables: ['storyboard', 'budget'],
      }),
    ).toBe(true)
    expect(
      evaluateCondition("deliverables contains 'interactive'", {
        deliverables: ['storyboard', 'budget'],
      }),
    ).toBe(false)
  })

  it('supports and / or combinations', () => {
    expect(
      evaluateCondition("entry_type == 'story_adapt' and enable_delivery == true", {
        entry_type: 'story_adapt',
        enable_delivery: true,
      }),
    ).toBe(true)
    expect(
      evaluateCondition("entry_type == 'original_track' or enable_delivery == true", {
        entry_type: 'story_adapt',
        enable_delivery: true,
      }),
    ).toBe(true)
  })

  it('returns true for empty expression', () => {
    expect(evaluateCondition(undefined, {})).toBe(true)
    expect(evaluateCondition('', {})).toBe(true)
  })

  it('evaluates is not empty for arrays and strings', () => {
    expect(evaluateCondition('reference_dramas is not empty', { reference_dramas: ['某剧'] })).toBe(
      true,
    )
    expect(evaluateCondition('reference_dramas is not empty', { reference_dramas: [] })).toBe(false)
    expect(evaluateCondition('reference_dramas is not empty', {})).toBe(false)
    expect(evaluateCondition('synopsis is not empty', { synopsis: '有梗概' })).toBe(true)
    expect(evaluateCondition('synopsis is not empty', { synopsis: '' })).toBe(false)
  })

  it('reads deliverables from creation_preferences', () => {
    const ctx = settingsConditionContext({
      entry_type: 'original_track',
      creation_preferences: {
        enable_delivery: true,
        deliverables: ['storyboard'],
      },
    })
    expect(ctx.enable_delivery).toBe(true)
    expect(ctx.deliverables).toEqual(['storyboard'])
  })

  it('ignores legacy delivery_items key', () => {
    const ctx = settingsConditionContext({
      creation_preferences: {
        enable_delivery: true,
        delivery_items: ['storyboard'],
      },
    })
    expect(ctx.deliverables).toEqual([])
  })
})
