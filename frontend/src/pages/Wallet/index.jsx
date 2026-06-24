import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Coins, Check, Loader2, TrendingUp, Receipt, Crown } from 'lucide-react'
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
import { cn } from '@/utils/cn'
import { Button } from '@/components/ui'
import PageShell from '@/components/layout/PageShell'

const LEDGER_TABS = [
  { key: 'income', label: '收入' },
  { key: 'spend', label: '消耗' },
]

export default function WalletPage() {
  const navigate = useNavigate()
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
      <div className="min-h-screen bg-navy-950 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin text-gold-400" />
          加载钱包…
        </div>
      </div>
    )
  }

  const currency = wallet?.currency_name || '创作币'
  const totalPages = ledger.pagination?.total_pages || 0

  return (
    <PageShell
      title="创作币钱包"
      description="查看余额、充值创作币、管理账户流水"
      backTo="/"
      maxWidth="4xl"
      actions={
        <div className="flex gap-2">
          <Button
            variant="secondary"
            iconLeft={<Receipt className="w-4 h-4" />}
            onClick={() => navigate('/orders')}
          >
            我的订单
          </Button>
          <Button
            variant="gold"
            iconLeft={<Crown className="w-4 h-4" />}
            onClick={() => navigate('/member')}
          >
            会员中心
          </Button>
        </div>
      }
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="relative overflow-hidden rounded-2xl border border-gold-500/20 bg-gradient-to-br from-gold-500/10 via-gold-500/5 to-transparent p-6 sm:p-8 mb-8"
      >
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-gold-400 mb-2">当前余额</div>
            <div className="text-4xl sm:text-5xl font-bold text-white flex items-baseline gap-2">
              {wallet?.balance ?? 0}
              <span className="text-lg text-gold-400 font-medium">{currency}</span>
            </div>
            <p className="text-slate-400 text-sm mt-3">
              大约还能生成{' '}
              <span className="text-gold-400 font-semibold">
                {wallet?.estimated_scripts_remaining ?? 0}
              </span>{' '}
              篇完整剧本
              {wallet?.estimated_auto_cost ? (
                <span className="text-slate-500">
                  {' '}（按一键生成约 {wallet.estimated_auto_cost} 币/篇）
                </span>
              ) : null}
            </p>
          </div>
          <div className="text-sm">
            {catalogQuery.data?.member_recharge_discount &&
            Number(catalogQuery.data.member_recharge_discount) < 1 ? (
              <span className="text-gold-400 flex items-center gap-1.5 bg-gold-500/10 px-3 py-1.5 rounded-lg">
                <TrendingUp className="w-4 h-4" />
                会员充值享额外赠送
              </span>
            ) : (
              <span className="flex items-center gap-2 text-slate-400">
                <TrendingUp className="w-4 h-4" />
                开通会员充值可享额外赠送
              </span>
            )}
          </div>
        </div>
      </motion.div>

      <section className="mb-10">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Coins className="w-5 h-5 text-gold-400" />
          充值{currency}
        </h2>
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
                  ? 'border-gold-500/40 bg-gold-500/10'
                  : 'border-white/10 bg-white/[0.03] hover:border-gold-500/20 hover:bg-white/[0.06]',
              )}
            >
              {pkg.discount_label ? (
                <span className="absolute right-3 top-3 rounded-full bg-gradient-to-r from-gold-400 to-gold-600 px-2 py-0.5 text-[10px] font-bold text-navy-950">
                  {pkg.discount_label}
                </span>
              ) : null}
              {isSelected ? (
                <span className="absolute left-3 top-3 grid h-5 w-5 place-items-center rounded-full bg-gradient-to-br from-gold-400 to-gold-600">
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
                <span className="inline-block text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-lg mb-2 w-fit">
                  {pkg.bonus_coins_text}
                </span>
              ) : null}
              {pkg.member_bonus_hint ? (
                <p className="text-xs text-purple-300 mb-2">{pkg.member_bonus_hint}</p>
              ) : null}
              <div className="text-xs text-slate-500 mb-4">
                约 ¥{pkg.unit_price?.toFixed?.(4) ?? pkg.unit_price}/{currency}
              </div>
              <Button
                variant={isSelected || isFeatured ? 'gold' : 'secondary'}
                size="md"
                className="mt-auto w-full"
                iconLeft={paying === pkg.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Coins className="w-4 h-4" />}
                disabled={paying === pkg.id}
                onClick={(event) => {
                  event.stopPropagation()
                  handleRecharge(pkg)
                }}
              >
                {paying === pkg.id ? '支付中…' : '立即充值'}
              </Button>
            </motion.button>
          )})}
          {packages.length === 0 && (
            <div className="md:col-span-3 rounded-2xl border border-dashed border-white/10 p-8 text-center text-slate-500 bg-white/[0.02]">
              {packagesError || '暂无可用充值档位，请稍后再试'}
            </div>
          )}
        </div>
        {paymentMethod === 'mock' && (
          <p className="mt-3 text-xs text-slate-500">演示环境将使用模拟支付，到账后可在下方查看流水。</p>
        )}
      </section>

      <section>
        <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Receipt className="w-5 h-5 text-gold-400" />
            账户流水
          </h2>
          <div className="flex gap-1 bg-white/5 p-1 rounded-xl border border-white/10">
            {LEDGER_TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => {
                  setLedgerTab(tab.key)
                  setLedgerPage(1)
                }}
                className={cn(
                  'px-3 py-1.5 text-xs font-medium rounded-lg transition-all',
                  ledgerTab === tab.key
                    ? 'bg-gold-500 text-navy-950 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm">
          {ledgerLoading && (
            <div className="px-5 py-3 text-sm text-slate-400 border-b border-white/5 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-gold-400" />
              正在加载流水…
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-white/5 text-slate-500">
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
                    <td colSpan={5} className="px-5 py-10 text-center text-slate-500">
                      暂无流水
                    </td>
                  </tr>
                ) : (
                  ledger.items.map((row) => {
                    const category = ledgerRowCategory(row)
                    return (
                      <tr key={row.id} className="border-b border-white/5 transition-colors hover:bg-white/[0.03]">
                        <td className="px-5 py-3 text-slate-300">{ledgerRowDescription(row)}</td>
                        <td className="px-5 py-3">
                          <span
                            className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${ledgerCategoryClass(category)}`}
                          >
                            {category}
                          </span>
                        </td>
                        <td
                          className={cn(
                            'px-5 py-3 text-right font-medium tabular-nums',
                            row.delta > 0 ? 'text-emerald-400' : 'text-red-400'
                          )}
                        >
                          {formatLedgerDelta(row.delta)}
                        </td>
                        <td className="px-5 py-3 text-right text-slate-400 tabular-nums">
                          {row.balance_after}
                        </td>
                        <td className="px-5 py-3 text-right text-slate-500 whitespace-nowrap">
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
          <div className="flex items-center justify-center gap-4 mt-4 pb-8">
            <button
              type="button"
              disabled={ledgerPage <= 1 || ledgerLoading}
              onClick={() => setLedgerPage((p) => Math.max(1, p - 1))}
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-white/[0.06] hover:text-white disabled:opacity-40"
            >
              上一页
            </button>
            <span className="text-sm text-slate-500 tabular-nums">
              第 {ledgerPage} / {totalPages} 页
            </span>
            <button
              type="button"
              disabled={ledgerPage >= totalPages || ledgerLoading}
              onClick={() => setLedgerPage((p) => p + 1)}
              className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-white/[0.06] hover:text-white disabled:opacity-40"
            >
              下一页
            </button>
          </div>
        )}
      </section>
    </PageShell>
  )
}
