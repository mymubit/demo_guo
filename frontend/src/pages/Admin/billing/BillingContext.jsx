import { createContext, useContext } from 'react'
import { useBillingAdmin } from '@/hooks/useBillingAdmin'

const BillingContext = createContext(null)

export function BillingProvider({ forcedTab, children }) {
  const value = useBillingAdmin(forcedTab)
  return <BillingContext.Provider value={value}>{children}</BillingContext.Provider>
}

export function useBilling() {
  const ctx = useContext(BillingContext)
  if (!ctx) throw new Error('useBilling must be used within BillingProvider')
  return ctx
}
