import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { Coins, Loader2, Sparkles, TrendingUp, Wallet as WalletIcon } from 'lucide-react'
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

export default function WalletPage() {
  const { wallet, fetchWallet, setWallet } = useWalletStore()
  const [ledgerTab, setLedgerTab] = useState('income')
  const [ledgerPage, setLedgerPage] = useState(1)
  const [paying, setPaying] = useState(null)
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
    <div className="min-h-screen pt-16 pb-20 px-6 relative">
      <div className="particles-bg" />
      <div className="absolute top-32 left-10 w-96 h-96 rounded-full bg-gold-500/10 blur-3xl pointer-events-none" />
      <div className="absolute top-64 right-10 w-[420px] h-[420px] rounded-full bg-purple-600/10 blur-3xl pointer-events-none" />

      <div className="max-w-5xl mx-auto relative z-10 space-y-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center justify-between gap-4 flex-wrap mb-2">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-white flex items-center gap-3">
                <WalletIcon className="w-8 h-8 text-gold-400" />
                <span className="gradient-text">我的{currency}</span>
              </h1>
              <p className="text-navy-300 text-sm mt-2">创作按节点/动作扣费，充值后即时到账</p>
            </div>
            <Link
              to="/member"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm text-gold-300 border border-gold-500/30 hover:bg-gold-500/10 transition-colors"
            >
              会员中心
              <TrendingUp className="w-4 h-4" />
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass-card rounded-[28px] p-8 border border-gold-500/20"
        >
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
            <div>
              <div className="text-navy-400 text-sm mb-2">当前余额</div>
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
                  <span className="text-navy-500">
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
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-gold-400" />
            充值{currency}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {packages.map((pkg) => (
              <motion.div
                key={pkg.id}
                whileHover={{ scale: 1.02 }}
                className="glass-card rounded-2xl p-6 border border-navy-700/40 flex flex-col"
              >
                <div className="font-semibold text-white mb-3">{pkg.name}</div>
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
                <div className="text-xs text-navy-500 mb-4">
                  约 ¥{pkg.unit_price?.toFixed?.(4) ?? pkg.unit_price}/{currency}
                </div>
                <button
                  type="button"
                  disabled={Boolean(paying)}
                  onClick={() => handleRecharge(pkg)}
                  className="mt-auto w-full py-3 rounded-xl btn-gold font-medium disabled:opacity-60 flex items-center justify-center gap-2"
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
                </button>
              </motion.div>
            ))}
            {packages.length === 0 && (
              <div className="md:col-span-3 rounded-2xl border border-dashed border-navy-700/60 p-8 text-center text-navy-400">
                {packagesError || '暂无可用充值档位，请稍后再试'}
              </div>
            )}
          </div>
          {paymentMethod === 'mock' && (
            <p className="text-xs text-navy-500 mt-3">演示环境将使用模拟支付，到账后可在下方查看流水。</p>
          )}
        </section>

        <section>
          <div className="flex items-center justify-between gap-4 flex-wrap mb-4">
            <h2 className="text-lg font-semibold text-white">账户流水</h2>
            <div className="flex gap-2">
              {[
                { key: 'income', label: '收入' },
                { key: 'spend', label: '消耗' },
              ].map((t) => (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => {
                    setLedgerTab(t.key)
                    setLedgerPage(1)
                  }}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                    ledgerTab === t.key
                      ? 'bg-gold-500/20 text-gold-400 border border-gold-500/30'
                      : 'bg-navy-800/50 text-navy-300 border border-navy-700/40 hover:text-white'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-2xl overflow-hidden">
            {ledgerLoading && (
              <div className="px-5 py-3 text-sm text-navy-300 border-b border-navy-800/60 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-gold-400" />
                正在加载流水…
              </div>
            )}
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead>
                  <tr className="border-b border-navy-700/40 text-navy-400">
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
                      <td colSpan={5} className="px-5 py-10 text-center text-navy-500">
                        暂无流水
                      </td>
                    </tr>
                  ) : (
                    ledger.items.map((row) => {
                      const category = ledgerRowCategory(row)
                      return (
                        <tr key={row.id} className="border-b border-navy-800/60 hover:bg-navy-800/20">
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
                          <td className="px-5 py-3 text-right text-navy-500 whitespace-nowrap">
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
                className="px-4 py-2 rounded-xl text-sm bg-navy-800/50 text-navy-200 border border-navy-700/40 disabled:opacity-40 hover:text-white transition-colors"
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
                className="px-4 py-2 rounded-xl text-sm bg-navy-800/50 text-navy-200 border border-navy-700/40 disabled:opacity-40 hover:text-white transition-colors"
              >
                下一页
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
