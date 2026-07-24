import { http } from '@/services/http'
import type { BillingPlan } from '@/types/v3/domain'

const BILLING_PLANS_PATH = '/api/v3/billing/plans/'

type BillingPlansResponse = {
  items: BillingPlan[]
}

/** 只读套餐列表（展示壳，无支付）。 */
export async function listBillingPlans(): Promise<BillingPlan[]> {
  const data = await http.get<BillingPlansResponse>(BILLING_PLANS_PATH)
  return data.items
}
