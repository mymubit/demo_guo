import { useQuery } from '@tanstack/react-query'
import { works as worksApi } from '@/services/api'

export function useWorkDetail(projectId) {
  return useQuery({
    queryKey: ['work', projectId],
    queryFn: async () => {
      const data = await worksApi.detail(projectId)
      if (!data?.project_id) {
        throw new Error('作品不存在')
      }
      return data
    },
    enabled: Boolean(projectId),
    staleTime: 30_000,
  })
}
