import { describe, expect, it } from 'vitest'
import type { ArtifactRecord, StoryBibleApprovalRequest } from '@/types/domain'

describe('dramaApi surface', () => {
  it('exposes contract-aligned generation and metadata methods', async () => {
    const { dramaApi } = await import('@/services/drama')
    expect(dramaApi.getThemeMatrix).toBeTypeOf('function')
    expect(dramaApi.startGeneration).toBeTypeOf('function')
    expect(dramaApi.getGenerationStatus).toBeTypeOf('function')
    expect(dramaApi.getJob).toBeTypeOf('function')
    expect(dramaApi.postWorkflowCommand).toBeTypeOf('function')
    expect(dramaApi.getArtifact).toBeTypeOf('function')
  })

  it('startGeneration accepts command_id and expected_version', () => {
    const body = {
      command_id: 'cmd',
      expected_version: 0,
      role: 'drama.topic-director',
    } satisfies import('@/types/domain').GenerationStartRequest
    expect(body.command_id).toBe('cmd')
  })

  it('getArtifact returns ArtifactRecord wrapper with payload', () => {
    const record: ArtifactRecord<{ title: string }> = {
      artifact_key: 'project_brief',
      version: 1,
      schema_version: 'project-brief.v1',
      payload: { title: 'demo' },
    }
    expect(record.payload?.title).toBe('demo')

    const empty: ArtifactRecord = {
      artifact_key: 'story_bible',
      version: null,
      payload: null,
    }
    expect(empty.payload).toBeNull()
  })

  it('StoryBibleApprovalRequest has no comment field', () => {
    const body: StoryBibleApprovalRequest = {
      command_id: 'c1',
      decision: 'approve',
      expected_version: 2,
    }
    expect('comment' in body).toBe(false)
  })
})
