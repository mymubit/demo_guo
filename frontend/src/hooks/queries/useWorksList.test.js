import { describe, it, expect } from 'vitest'
import { normalizeWorkItem } from '@/services/adapters/businessAdapters'

describe('useWorksList polling status helpers', () => {
  it('detects active works via raw_status pending', () => {
    const items = [
      normalizeWorkItem({ project_id: '1', status: 'pending', episode_count: 10 }),
    ]
    const hasActive = items.some(
      (work) =>
        work.raw_status === 'running' ||
        work.raw_status === 'pending' ||
        work.status === 'generating'
    )
    expect(hasActive).toBe(true)
  })
})
