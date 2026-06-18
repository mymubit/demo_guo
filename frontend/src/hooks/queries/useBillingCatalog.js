import { useQuery } from '@tanstack/react-query'
import { billing } from '@/services/api'

const CATALOG_STALE_MS = 5 * 60 * 1000

export function useBillingCatalog() {
  return useQuery({
    queryKey: ['billingCatalog'],
    queryFn: () => billing.catalog(),
    staleTime: CATALOG_STALE_MS,
  })
}
