import type { ProjectSummary } from '@/types/v3/domain'

/** 按标题本地过滤（大小写不敏感包含匹配）。 */
export function filterProjectsByTitle(
  projects: ProjectSummary[],
  query: string,
): ProjectSummary[] {
  const normalized = query.trim().toLowerCase()
  if (!normalized) return projects
  return projects.filter((project) => project.title.toLowerCase().includes(normalized))
}
