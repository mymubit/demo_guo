import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Coins, Check, Loader2, TrendingUp } from 'lucide-react'
import { billing, useConfig } from '@/services/api'
import { useWalletStore } from '@/store/walletStore'
import { useInvalidateWalletQueries, useWalletData } from '@/hooks/queries/useWalletData'
import { formatDateTime } from '@/utils/date'
import {
  formatLedgerDelta,
  ledgerCategoryClass,
  ledgerRowCategory,
  ledgerRowDescription,
} from '@/utils/ledger'
import PriceWithDiscount from '@/components/commerce/PriceWithDiscount'
import { SectionHeader, PillFilterGroup, PageContainer } from '@/components/shared/ConsumerSection'
import { cn } from '@/utils/cn'

export default function WalletPage() {
  const { wallet, fetchWallet, setWallet } = useWalletStore()
  const [ledgerTab, setLedgerTab] = useState('income')
  const [ledgerPage, setLedgerPage] = useState(1)
  const [paying, setPaying] = useState(null)
  const [selectedPkgId, setSelectedPkgId] = useState(null)
  const [walletLoading, setWalletLoading] = useState(true)
  const configPaymentMethod = useConfig('payment.default_method', 'mock')
  const [paymentMethod, setPaymentMethod] = useState(configPaymentMethod)
  const invalidateWalletQueries = useInvalidateWalletQueries()
  const { packagesQuery, ledgerQuery, catalogQuery, isLoading } = useWalletData({
    ledgerTab,
    ledgerPage,
  })

  const packages = packagesQuery.data ?? []
  const packagesError = packagesQuery.error?.message ?? ''
  const ledger = ledgerQuery.data ?? { items: [], pagination: { page: 1, total_pages: 0 } }
  const ledgerLoading = ledgerQuery.isFetching
  const loading = walletLoading || isLoading

  useEffect(() => {
    fetchWallet()
      .catch((err) => toast.error(err.message || '钱包加载失败'))
      .finally(() => setWalletLoading(false))
  }, [fetchWallet])

  useEffect(() => {
    const method = catalogQuery.data?.payment_method || configPaymentMethod
    setPaymentMethod(method)
  }, [catalogQuery.data, configPaymentMethod])

  async function handleRecharge(pkg) {
    if (paying) return
    setPaying(pkg.id)
    try {
      const order = await billing.createRechargeOrder(pkg.id, paymentMethod)
      const result = await billing.mockPayRecharge(order.order_no)
      if (result.wallet) {
        setWallet(result.wallet)
      } else {
        await fetchWallet()
      }
      toast.success(`充值成功，到账 ${result.coins_granted || pkg.total_coins} 创作币`)
      invalidateWalletQueries()
    } catch (err) {
      toast.error(err.message || '充值失败')
    } finally {
      setPaying(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen pt-24">
        <div className="flex items-center justify-center py-32 text-navy-300 gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-gold-400" />
          加载钱包…
        </div>
      </div>
    )
  }

  const currency = wallet?.currency_name || '创作币'
  const totalPages = ledger.pagination?.total_pages || 0

  return (
    <div className="min-h-screen pt-16 pb-20">
      <PageContainer width="5xl" className="space-y-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <SectionHeader
              eyebrow="创作币钱包"
              title={`我的${currency}`}
              subtitle="创作按节点/动作扣费，充值后即时到账"
            />
            <div className="flex flex-wrap items-center gap-2">
              <Link
                to="/orders"
                className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-4 py-2 text-sm text-navy-200 transition-colors hover:bg-white/5"
              >
                我的订单
              </Link>
              <Link
                to="/member"
                className="inline-flex items-center gap-1.5 rounded-xl border border-gold-500/30 px-4 py-2 text-sm text-gold-300 transition-colors hover:bg-gold-500/10"
              >
                会员中心
                <TrendingUp className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="relative overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br from-navy-900 to-navy-950 p-8"
        >
          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="text-xs uppercase tracking-wider text-gold-400">当前余额</div>
              <div className="text-5xl font-bold text-white flex items-baseline gap-2">
                {wallet?.balance ?? 0}
                <span className="text-lg text-gold-400 font-medium">{currency}</span>
              </div>
              <p className="text-navy-300 text-sm mt-3">
                大约还能生成{' '}
                <span className="text-gold-400 font-semibold">
                  {wallet?.estimated_scripts_remaining ?? 0}
                </span>{' '}
                篇完整剧本
                {wallet?.estimated_auto_cost ? (
                  <span className="text-navy-400">
                    （按一键生成约 {wallet.estimated_auto_cost} 币/篇）
                  </span>
                ) : null}
              </p>
            </div>
            <div className="text-sm text-navy-400">
              {catalogQuery.data?.member_recharge_discount &&
              Number(catalogQuery.data.member_recharge_discount) < 1 ? (
                <span className="text-gold-300">会员充值享额外赠送</span>
              ) : (
                <span className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  开通会员充值可享额外赠送
                </span>
              )}
            </div>
          </div>
        </motion.div>

        <section>
          <SectionHeader
            eyebrow="充值"
            title={`充值${currency}`}
            className="mb-4"
          />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {packages.map((pkg) => {
              const isSelected = selectedPkgId === pkg.id
              const isFeatured = Boolean(pkg.discount_label)
              return (
              <motion.button
                key={pkg.id}
                type="button"
                whileHover={{ y: -2 }}
                onClick={() => setSelectedPkgId(pkg.id)}
                className={cn(
                  'group relative flex flex-col rounded-2xl border p-6 text-left transition-all',
                  isSelected || isFeatured
                    ? 'border-gold-400/60 bg-gold-400/10 shadow-gold'
                    : 'border-white/10 bg-white/[0.03] hover:border-gold-400/40 hover:bg-gold-400/5',
                )}
              >
                {pkg.discount_label ? (
                  <span className="absolute right-3 top-3 rounded-full bg-gradient-to-r from-gold-300 to-gold-500 px-2 py-0.5 text-[10px] font-bold text-navy-950">
                    {pkg.discount_label}
                  </span>
                ) : null}
                {isSelected ? (
                  <span className="absolute left-3 top-3 grid h-5 w-5 place-items-center rounded-full bg-gradient-to-br from-gold-300 to-gold-500">
                    <Check className="h-3 w-3 text-navy-950" />
                  </span>
                ) : null}
                <div className={cn('font-semibold text-white mb-3', (isSelected || pkg.discount_label) && 'mt-5')}>
                  {pkg.name}
                </div>
                <PriceWithDiscount
                  price={pkg.price_yuan}
                  originalPrice={pkg.original_price_yuan}
                  discountLabel={pkg.discount_label}
                  discountPercent={pkg.discount_percent}
                  size="md"
                  layout="compact"
                  chargeTone="gold"
                  className="mb-3"
                />
                <div className="text-white text-lg font-medium mb-1">
                  {Number(pkg.total_coins || 0).toLocaleString()} {currency}
                </div>
                {pkg.bonus_coins_text ? (
                  <span className="inline-block text-xs bg-green-500/15 text-green-400 px-2 py-0.5 rounded-lg mb-2 w-fit">
                    {pkg.bonus_coins_text}
                  </span>
                ) : null}
                {pkg.member_bonus_hint ? (
                  <p className="text-xs text-purple-300 mb-2">{pkg.member_bonus_hint}</p>
                ) : null}
                <div className="text-xs text-navy-400 mb-4">
                  约 ¥{pkg.unit_price?.toFixed?.(4) ?? pkg.unit_price}/{currency}
                </div>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(event) => {
                    event.stopPropagation()
                    handleRecharge(pkg)
                  }}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      event.stopPropagation()
                      handleRecharge(pkg)
                    }
                  }}
                  className={cn(
                    'mt-auto w-full py-3 rounded-xl btn-gold font-medium flex items-center justify-center gap-2',
                    paying === pkg.id && 'opacity-60 pointer-events-none',
                  )}
                >
                  {paying === pkg.id ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      支付中…
                    </>
                  ) : (
                    <>
                      <Coins className="w-4 h-4" />
                      立即充值
                    </>
                  )}
                </span>
              </motion.button>
            )})}
            {packages.length === 0 && (
              <div className="md:col-span-3 rounded-2xl border border-dashed border-white/10 p-8 text-center text-navy-400">
                {packagesError || '暂无可用充值档位，请稍后再试'}
              </div>
            )}
          </div>
          {paymentMethod === 'mock' && (
            <p className="mt-3 text-xs text-navy-400">演示环境将使用模拟支付，到账后可在下方查看流水。</p>
          )}
        </section>

        <section>
          <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
            <SectionHeader eyebrow="流水" title="账户流水" className="mb-0" />
            <PillFilterGroup
              options={[
                { key: 'income', label: '收入' },
                { key: 'spend', label: '消耗' },
              ]}
              value={ledgerTab}
              onChange={(key) => {
                setLedgerTab(key)
                setLedgerPage(1)
              }}
            />
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/5 bg-slate-900/60">
            {ledgerLoading && (
              <div className="px-5 py-3 text-sm text-navy-300 border-b border-white/5 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-gold-400" />
                正在加载流水…
              </div>
            )}
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead>
                  <tr className="border-b border-white/5 text-navy-400">
                    <th className="px-5 py-3 text-left font-medium">说明</th>
                    <th className="px-5 py-3 text-left font-medium">类型</th>
                    <th className="px-5 py-3 text-right font-medium">变动</th>
                    <th className="px-5 py-3 text-right font-medium">余额</th>
                    <th className="px-5 py-3 text-right font-medium">时间</th>
                  </tr>
                </thead>
                <tbody>
                  {(ledger.items || []).length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-5 py-10 text-center text-navy-400">
                        暂无流水
                      </td>
                    </tr>
                  ) : (
                    ledger.items.map((row) => {
                      const category = ledgerRowCategory(row)
                      return (
                        <tr key={row.id} className="border-b border-white/5 hover:bg-white/[0.03]">
                          <td className="px-5 py-3 text-navy-200">{ledgerRowDescription(row)}</td>
                          <td className="px-5 py-3">
                            <span
                              className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${ledgerCategoryClass(category)}`}
                            >
                              {category}
                            </span>
                          </td>
                          <td
                            className={`px-5 py-3 text-right font-medium tabular-nums ${
                              row.delta > 0 ? 'text-green-400' : 'text-red-400'
                            }`}
                          >
                            {formatLedgerDelta(row.delta)}
                          </td>
                          <td className="px-5 py-3 text-right text-navy-300 tabular-nums">
                            {row.balance_after}
                          </td>
                          <td className="px-5 py-3 text-right text-navy-400 whitespace-nowrap">
                            {formatDateTime(row.created_at)}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 mt-4">
              <button
                type="button"
                disabled={ledgerPage <= 1 || ledgerLoading}
                onClick={() => setLedgerPage((p) => Math.max(1, p - 1))}
                className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-navy-200 transition-colors hover:bg-white/[0.06] hover:text-white disabled:opacity-40"
              >
                上一页
              </button>
              <span className="text-sm text-navy-400 tabular-nums">
                第 {ledgerPage} / {totalPages} 页
              </span>
              <button
                type="button"
                disabled={ledgerPage >= totalPages || ledgerLoading}
                onClick={() => setLedgerPage((p) => p + 1)}
                className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-navy-200 transition-colors hover:bg-white/[0.06] hover:text-white disabled:opacity-40"
              >
                下一页
              </button>
            </div>
          )}
        </section>
      </PageContainer>
    </div>
  )
}
