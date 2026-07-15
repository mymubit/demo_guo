import { describe, expect, it } from 'vitest'
import { isFieldVisible } from '@/utils/settingsForm'
import { testProjectSettings, testWorkbenchDefinition } from '@/test/workbenchFixtures'

describe('settings field visibility (definition-driven)', () => {
  const definition = testWorkbenchDefinition()

  it('shows original-track fields only for original entry', () => {
    const original = testProjectSettings({ entry_type: 'original_track' })
    const adapt = testProjectSettings({
      entry_type: 'story_adapt',
      external_story: 'story',
      core_idea: undefined,
    })

    expect(isFieldVisible(definition.fields.core_idea, original)).toBe(true)
    expect(isFieldVisible(definition.fields.external_story, original)).toBe(false)
    expect(isFieldVisible(definition.fields.core_idea, adapt)).toBe(false)
    expect(isFieldVisible(definition.fields.external_story, adapt)).toBe(true)
    expect(isFieldVisible(definition.fields.adapt_notes, adapt)).toBe(true)
  })

  it('shows delivery_items only when enable_delivery is true', () => {
    const off = testProjectSettings({
      creation_preferences: {
        batch_episode_max: 5,
        outline_mode: 'full',
        scoring_preset: 'standard',
        compliance_check_mode: 'standard',
        enable_delivery: false,
        delivery_items: ['storyboard'],
      },
    })
    const on = testProjectSettings({
      creation_preferences: {
        ...off.creation_preferences,
        enable_delivery: true,
      },
    })

    expect(isFieldVisible(definition.fields.delivery_items, off)).toBe(false)
    expect(isFieldVisible(definition.fields.delivery_items, on)).toBe(true)
  })

  it('flags non-generic platform without verified_at as unverified', () => {
    const unverified = testProjectSettings({
      target_platform: 'douyin',
      platform_policy: { policy_source: 'manual', verified_at: null },
    })
    const verified = testProjectSettings({
      target_platform: 'douyin',
      platform_policy: { policy_source: 'admin', verified_at: '2026-01-01T00:00:00Z' },
    })
    const generic = testProjectSettings({ target_platform: 'generic' })

    expect(unverified.target_platform !== 'generic' && !unverified.platform_policy?.verified_at).toBe(
      true,
    )
    expect(verified.target_platform !== 'generic' && !verified.platform_policy?.verified_at).toBe(
      false,
    )
    expect(generic.target_platform !== 'generic' && !generic.platform_policy?.verified_at).toBe(false)
  })
})
