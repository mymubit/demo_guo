import { describe, expect, it, beforeEach } from 'vitest'
import {
  formatRelativeTime,
  listRecentProjects,
  rememberRecentProject,
  RECENT_PROJECTS_EVENT,
  sortProjectsByRecent,
  syncRecentProjectsWithList,
} from '@/utils/recentProjects'
import type { DramaProjectSummary } from '@/types/domain'

describe('recentProjects', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('remembers and lists recent projects with newest first', () => {
    rememberRecentProject({ id: 'a', title: '甲' })
    rememberRecentProject({ id: 'b', title: '乙' })
    rememberRecentProject({ id: 'a', title: '甲改' })
    const list = listRecentProjects()
    expect(list.map((x) => x.id)).toEqual(['a', 'b'])
    expect(list[0]?.title).toBe('甲改')
  })

  it('syncs titles and drops deleted projects', () => {
    rememberRecentProject({ id: 'a', title: '旧名' })
    rememberRecentProject({ id: 'gone', title: '已删' })
    const synced = syncRecentProjectsWithList([
      { id: 'a', title: '新名', entry_type: 'original_track' },
    ])
    expect(synced).toHaveLength(1)
    expect(synced[0]?.title).toBe('新名')
  })

  it('sorts project list by recent visit then updated_at', () => {
    rememberRecentProject({ id: 'b', title: 'B' })
    const projects: DramaProjectSummary[] = [
      {
        id: 'a',
        title: 'A',
        entry_type: 'original_track',
        updated_at: '2026-07-16T10:00:00Z',
      },
      {
        id: 'b',
        title: 'B',
        entry_type: 'story_adapt',
        updated_at: '2026-07-15T10:00:00Z',
      },
      {
        id: 'c',
        title: 'C',
        entry_type: 'original_track',
        updated_at: '2026-07-16T12:00:00Z',
      },
    ]
    const sorted = sortProjectsByRecent(projects, listRecentProjects())
    expect(sorted.map((p) => p.id)).toEqual(['b', 'c', 'a'])
  })

  it('formats relative time', () => {
    expect(formatRelativeTime(new Date().toISOString())).toBe('刚刚')
    expect(formatRelativeTime(undefined)).toBe('')
  })

  it('dispatches change event when remembering', () => {
    const seen: string[] = []
    const handler = () => seen.push('ok')
    window.addEventListener(RECENT_PROJECTS_EVENT, handler)
    rememberRecentProject({ id: 'evt', title: '事件' })
    window.removeEventListener(RECENT_PROJECTS_EVENT, handler)
    expect(seen).toEqual(['ok'])
  })
})
