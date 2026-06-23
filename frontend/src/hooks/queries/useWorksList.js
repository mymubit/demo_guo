import { useQuery } from '@tanstack/react-query'
import { works as worksApi } from '@/services/api'

export function useWorksList({ page = 1, status = 'all', keyword = '', ordering = 'newest', pageSize = 12 }) {
  return useQuery({
    queryKey: ['works', page, status, keyword.trim(), ordering, pageSize],
    queryFn: () =>
      worksApi.list(page, status, pageSize, {
        q: keyword.trim(),
        ordering,
        scope: 'drama',
      }),
    staleTime: 30_000,
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? []
      const hasActive = items.some(
        (work) =>
          work.raw_status === 'running' ||
          work.raw_status === 'pending' ||
          work.status === 'generating'
      )
      return hasActive ? 5000 : false
    },
  })
}
