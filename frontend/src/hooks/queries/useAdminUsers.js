import { useQuery } from '@tanstack/react-query'
import { admin } from '@/services/api'

export function useAdminUsers({ page = 1, keyword = '', filter = 'all', pageSize = 10 }) {
  return useQuery({
    queryKey: ['adminUsers', page, keyword.trim(), filter, pageSize],
    queryFn: async () => {
      const params = { page, page_size: pageSize }
      if (keyword.trim()) params.keyword = keyword.trim()
      if (filter === 'active') params.is_active = 'true'
      if (filter === 'inactive') params.is_active = 'false'
      if (filter === 'member') params.member = 'active'
      if (filter === 'free') params.member = 'free'
      return admin.listUsers(params)
    },
    staleTime: 30_000,
  })
}
