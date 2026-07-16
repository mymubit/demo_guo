import type { DramaProjectSummary } from '@/types/domain'

const RECENT_PROJECTS_KEY = 'scriptforge-recent-projects'
const MAX_RECENT = 8
export const RECENT_PROJECTS_EVENT = 'scriptforge:recent-projects'

export type RecentProjectRef = {
  id: string
  title: string
  entry_type?: string
  visited_at: string
}

function readRaw(): RecentProjectRef[] {
  try {
    const raw = localStorage.getItem(RECENT_PROJECTS_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as RecentProjectRef[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeRaw(items: RecentProjectRef[]): void {
  localStorage.setItem(RECENT_PROJECTS_KEY, JSON.stringify(items.slice(0, MAX_RECENT)))
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(RECENT_PROJECTS_EVENT))
  }
}

export function listRecentProjects(): RecentProjectRef[] {
  return readRaw()
    .filter((item) => item?.id)
    .sort((a, b) => Date.parse(b.visited_at) - Date.parse(a.visited_at))
    .slice(0, MAX_RECENT)
}

export function rememberRecentProject(input: {
  id: string
  title?: string
  entry_type?: string
}): void {
  if (!input.id) return
  const next: RecentProjectRef = {
    id: input.id,
    title: input.title?.trim() || '未命名项目',
    entry_type: input.entry_type,
    visited_at: new Date().toISOString(),
  }
  const others = readRaw().filter((item) => item.id !== input.id)
  writeRaw([next, ...others])
}

/** 用服务端列表刷新最近项目标题，并剔除已删除项 */
export function syncRecentProjectsWithList(projects: DramaProjectSummary[]): RecentProjectRef[] {
  const byId = new Map(projects.map((p) => [p.id, p]))
  const synced = listRecentProjects()
    .map((item) => {
      const live = byId.get(item.id)
      if (!live) return null
      return {
        ...item,
        title: live.title || item.title,
        entry_type: live.entry_type || item.entry_type,
      }
    })
    .filter((item): item is RecentProjectRef => Boolean(item))
  writeRaw(synced)
  return synced
}

export function sortProjectsByRecent(
  projects: DramaProjectSummary[],
  recent: RecentProjectRef[],
): DramaProjectSummary[] {
  const rank = new Map(recent.map((item, index) => [item.id, index]))
  return [...projects].sort((a, b) => {
    const ra = rank.has(a.id) ? rank.get(a.id)! : Number.MAX_SAFE_INTEGER
    const rb = rank.has(b.id) ? rank.get(b.id)! : Number.MAX_SAFE_INTEGER
    if (ra !== rb) return ra - rb
    const ta = a.updated_at ? Date.parse(a.updated_at) : 0
    const tb = b.updated_at ? Date.parse(b.updated_at) : 0
    return tb - ta
  })
}

export function formatRelativeTime(iso?: string | null): string {
  if (!iso) return ''
  const ts = Date.parse(iso)
  if (Number.isNaN(ts)) return ''
  const diffMs = Date.now() - ts
  const minute = 60_000
  const hour = 60 * minute
  const day = 24 * hour
  if (diffMs < minute) return '刚刚'
  if (diffMs < hour) return `${Math.floor(diffMs / minute)} 分钟前`
  if (diffMs < day) return `${Math.floor(diffMs / hour)} 小时前`
  if (diffMs < 7 * day) return `${Math.floor(diffMs / day)} 天前`
  return new Date(ts).toLocaleDateString()
}
