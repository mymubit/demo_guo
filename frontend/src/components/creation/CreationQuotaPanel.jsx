/**
 * 创作页右侧 — 节点预估 / 余额 / 质量门槛
 */
import { Lock } from 'lucide-react'
import { Button } from '@/components/ui'
import { SideSectionTitle, KvRow } from '@/components/shared/ConsumerSection'
import { ICON } from '@/constants/iconSizes'
import { cn } from '@/utils/cn'

export default function CreationQuotaPanel({
  billingCatalog,
  billingLoaded = true,
  billingError = '',
  currencyName = '创作币',
  membershipActive = false,
  pipelineNodes = [],
  formStage = 1,
  showLockBanner = false,
}) {
  const balance = billingCatalog?.balance ?? 0
  const submitCost = billingCatalog?.submit_cost ?? 0
  const autoCost = billingCatalog?.estimated_auto_cost ?? 0
  const totalEstimate = autoCost ? autoCost + submitCost : null

  const nodeQuotas = pipelineNodes.slice(0, 3).map((node, idx) => ({
    name: node.name || `节点 ${idx + 1}`,
    pct: Math.max(12, Math.min(88, 100 - idx * 24 - (formStage === 2 ? 8 : 0))),
    cool: idx === 1 && formStage === 2,
  }))

  return (
    <>
      <SideSectionTitle>{formStage === 2 ? '提交预估' : '本阶段预估'}</SideSectionTitle>
      <div className="space-y-1">
        <KvRow label="预计扣费" value={totalEstimate != null ? `${totalEstimate} ${currencyName}` : `≥ ${submitCost} ${currencyName}`} />
        <KvRow label="当前余额" value={billingLoaded && !billingError ? `${balance} ${currencyName}` : '—'} />
        <KvRow label="会员状态" value={membershipActive ? '已开通' : '未开通'} />
        <KvRow label="预计耗时" value="3–5 分钟" />
      </div>

      {nodeQuotas.length > 0 ? (
        <>
          <SideSectionTitle>节点币价（参考）</SideSectionTitle>
          <div className="space-y-2.5">
            {nodeQuotas.map((q) => (
              <div key={q.name}>
                <div className="mb-1 flex justify-between text-[11px] text-navy-300">
                  <span>{q.name}</span>
                  <span>{q.pct}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                  <span
                    className={cn(
                      'block h-full rounded-full',
                      q.cool
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-500'
                        : 'bg-gradient-to-r from-gold-300 to-gold-500',
                    )}
                    style={{ width: `${q.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </>
      ) : null}

      <SideSectionTitle>质量门槛</SideSectionTitle>
      <div className="space-y-1">
        <KvRow label="四维评分" value="≥ 70 通过" />
        <KvRow label="格式审查" value="正则规则集" />
        <KvRow label="敏感词" value="合规清单" />
      </div>

      {showLockBanner || formStage === 2 ? (
        <div className="mt-5 flex flex-col gap-3 rounded-2xl border border-indigo-500/35 bg-gradient-to-r from-indigo-500/15 to-purple-500/15 p-4">
          <div className="flex items-start gap-3">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-white/10 text-white">
              <Lock className={ICON.md} />
            </div>
            <div className="min-w-0 text-sm">
              <b className="block text-white">AI 字段提示已锁定</b>
              <span className="text-navy-200">
                确认简报后，后续节点将以本简报为唯一输入，确保剧本一致性。
              </span>
            </div>
          </div>
          {formStage === 1 ? (
            <Button variant="ghost" size="sm" className="self-start">
              查看提示词策略
            </Button>
          ) : null}
        </div>
      ) : null}
    </>
  )
}
