import { useQuery } from '@tanstack/react-query'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { formatApiError } from '@/services/errors'
import { listBillingPlans } from '@/services/v3/billing'
import type { BillingPlan } from '@/types/v3/domain'
import { cn } from '@/utils/cn'

const BILLING_PLANS_QUERY_KEY = ['v3', 'billing', 'plans'] as const

const FEATURED_PLAN_ID = 'pro'

function PlanCard({ plan }: { plan: BillingPlan }) {
  const isFeatured = plan.id === FEATURED_PLAN_ID

  return (
    <article
      data-testid={`billing-plan-${plan.id}`}
      data-featured={isFeatured ? 'true' : 'false'}
      className={cn(
        'relative flex flex-col rounded-xl border bg-surface p-5 shadow-sm',
        isFeatured ? 'border-action ring-1 ring-action/30' : 'border-border',
      )}
    >
      {isFeatured ? (
        <span className="absolute -top-2.5 left-4 rounded-md bg-action px-2 py-0.5 text-xs font-medium text-white">
          最受欢迎
        </span>
      ) : null}

      <h2 className="text-base font-semibold text-ink">{plan.name}</h2>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-ink">{plan.price_label}</p>

      <ul className="mt-4 flex-1 space-y-2 text-sm text-ink-muted">
        {plan.features.map((feature) => (
          <li key={feature} className="flex gap-2">
            <span aria-hidden className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ink-muted/50" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      <Button className="mt-5 w-full" variant={isFeatured ? 'action' : 'secondary'} disabled>
        即将开放
      </Button>
    </article>
  )
}

export function BillingPage() {
  const plansQuery = useQuery({
    queryKey: BILLING_PLANS_QUERY_KEY,
    queryFn: listBillingPlans,
  })

  return (
    <PageShell title="套餐" description="查看可用方案与权益说明。">
      {plansQuery.isLoading ? <p className="text-sm text-ink-muted">正在加载套餐…</p> : null}

      {plansQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(plansQuery.error)}</p>
      ) : null}

      {plansQuery.isSuccess ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            {plansQuery.data.map((plan) => (
              <PlanCard key={plan.id} plan={plan} />
            ))}
          </div>
          <p className="mt-6 text-sm text-ink-muted">当前为展示壳，无支付与配额</p>
        </>
      ) : null}
    </PageShell>
  )
}
