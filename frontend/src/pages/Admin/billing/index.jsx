import { BillingProvider } from './BillingContext.jsx'
import BillingAdminView from './BillingAdminView.jsx'

export default function BillingAdmin({ forcedTab }) {
  return (
    <BillingProvider forcedTab={forcedTab}>
      <BillingAdminView />
    </BillingProvider>
  )
}
