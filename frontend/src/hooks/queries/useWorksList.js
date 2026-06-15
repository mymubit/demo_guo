import { useQuery } from '@tanstack/react-query'
import { works as worksApi } from '@/services/api'

export function useWorksList({ page = 1, status = 'all', keyword = '', ordering = 'newest', pageSize = 12 }) {
  return useQuery({
    queryKey: ['works', page, status, keyword.trim(), ordering, pageSize],
    queryFn: () =>
      worksApi.list(page, status, pageSize, {
        q: keyword.trim(),
        ordering,
      }),
    staleTime: 30_000,
  })
}
