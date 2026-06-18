import { useQuery } from '@tanstack/react-query'
import { membership as membershipApi, orders as ordersApi } from '@/services/api'

export function useMyMembership() {
  return useQuery({
    queryKey: ['myMembershipBundle'],
    queryFn: async () => {
      const [membership, plans, ordersResult, history, featureMatrix, summary] = await Promise.all([
        membershipApi.myMembership().catch(() => null),
        membershipApi.plans().catch(() => []),
        ordersApi.list().catch(() => ({ items: [] })),
        membershipApi.history().catch(() => []),
        membershipApi.featureMatrix().catch(() => null),
        membershipApi.summary().catch(() => null),
      ])
      const orders = ordersResult?.items ?? (Array.isArray(ordersResult) ? ordersResult : [])
      return { membership, plans, orders, history, featureMatrix, summary }
    },
    staleTime: 30_000,
  })
}
