import { useQuery, useQueryClient } from '@tanstack/react-query'
import { billing } from '@/services/api'

export function useWalletData({ ledgerTab = 'income', ledgerPage = 1 } = {}) {
  const packagesQuery = useQuery({
    queryKey: ['rechargePackages'],
    queryFn: () => billing.rechargePackages().then((data) => (Array.isArray(data) ? data : [])),
    staleTime: 30_000,
  })

  const ledgerQuery = useQuery({
    queryKey: ['walletLedger', ledgerTab, ledgerPage],
    queryFn: () =>
      billing.ledger(ledgerPage, ledgerTab === 'income' ? 'income' : 'spend').then(
        (data) => data || { items: [], pagination: { page: 1, total_pages: 0 } },
      ),
    staleTime: 30_000,
  })

  const catalogQuery = useQuery({
    queryKey: ['billingCatalog'],
    queryFn: () => billing.catalog(),
    staleTime: 30_000,
  })

  return {
    packagesQuery,
    ledgerQuery,
    catalogQuery,
    isLoading: packagesQuery.isLoading || ledgerQuery.isLoading,
  }
}

export function useInvalidateWalletQueries() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['rechargePackages'] })
    queryClient.invalidateQueries({ queryKey: ['walletLedger'] })
    queryClient.invalidateQueries({ queryKey: ['billingCatalog'] })
  }
}
