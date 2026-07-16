import { useEffect, useState } from 'react'
import {
  listRecentProjects,
  RECENT_PROJECTS_EVENT,
  type RecentProjectRef,
} from '@/utils/recentProjects'

/** 订阅本地最近项目列表（同页写入会即时刷新） */
export function useRecentProjects(limit = 3): RecentProjectRef[] {
  const [items, setItems] = useState<RecentProjectRef[]>(() => listRecentProjects().slice(0, limit))

  useEffect(() => {
    const refresh = () => setItems(listRecentProjects().slice(0, limit))
    refresh()
    window.addEventListener(RECENT_PROJECTS_EVENT, refresh)
    window.addEventListener('storage', refresh)
    return () => {
      window.removeEventListener(RECENT_PROJECTS_EVENT, refresh)
      window.removeEventListener('storage', refresh)
    }
  }, [limit])

  return items
}
