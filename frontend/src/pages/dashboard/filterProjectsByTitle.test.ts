import { describe, expect, it } from 'vitest'
import type { ProjectSummary } from '@/types/v3/domain'
import { filterProjectsByTitle } from './filterProjectsByTitle'

const projects: ProjectSummary[] = [
  {
    id: '1',
    title: 'Alpha Drama',
    entry_type: 'original',
    stage: 'topic',
    updated_at: '2026-07-23T08:00:00Z',
  },
  {
    id: '2',
    title: 'beta 改编',
    entry_type: 'adapt',
    stage: 'writing',
    updated_at: '2026-07-23T09:00:00Z',
  },
]

describe('filterProjectsByTitle', () => {
  it('returns all projects when query is blank', () => {
    expect(filterProjectsByTitle(projects, '')).toEqual(projects)
    expect(filterProjectsByTitle(projects, '   ')).toEqual(projects)
  })

  it('filters case-insensitively by title substring', () => {
    expect(filterProjectsByTitle(projects, 'alpha')).toEqual([projects[0]])
    expect(filterProjectsByTitle(projects, 'BETA')).toEqual([projects[1]])
  })
})
