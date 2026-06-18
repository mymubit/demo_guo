/* =========================================================================
 * Member（会员中心）—— API 调用说明（与 services/api.js 重构后的新模块对齐）
 *
 * 当前页面已经在使用 memberApi / orderApi，这些别名在 api.js 中仍被
 * 导出为兼容命名（memberApi -> membership, orderApi -> orders），所以
 * 现有的 import 无需修改即可工作。
 *
 * 建议后续逐步迁移到更语义化的命名空间：
 *
 *   import { membership, orders } from '@/services/api'
 *
 * 本页面应当调用的主要 API 方法如下：
 *
 *  1. 套餐列表（页面顶部"套餐选择"tab）
 *     membership.plans()                       → GET  /api/membership/plans/
 *       返回：{ id, name, price, validity, creation_quota, features[] }[]
 *       位置建议：useEffect 初始化时调用，覆盖本地 PLANS 常量。
 *
 *  2. 当前用户的会员状态（"会员状态卡片"展示）
 *     membership.myMembership()                → GET  /api/membership/me/
 *       返回：{ plan, plan_name, is_active, end_at, creation_quota_used,
 *               creation_quota_total, redeemed_codes[] }
 *       位置建议：与 plans 并行加载，失败时回退本地 mock 结构。
 *
 *  3. 会员汇总信息（可选：展示额度、到期等）
 *     membership.summary()                     → GET  /api/membership/summary/
 *
 *  4. 卡密兑换历史（"卡密兑换"tab 中的兑换记录）
 *     membership.history()                     → GET  /api/membership/history/
 *
 *  5. 卡密兑换（handleRedeem 中）
 *     membership.redeem(code)                  → POST /api/membership/redeem/
 *       body: { code }
 *
 *  6. 订单列表（"我的订单"tab）
 *     orders.list(status?)                     → GET  /api/orders/?status=paid
 *       status 可选：'paid' | 'pending' | 'cancelled'
 *
 *  7. 订单详情（如果后续加"查看详情"）
 *     orders.detail(orderId)                   → GET  /api/orders/:id/
 *
 *  8. 下单（handlePurchase 中）
 *     orders.createOrder({ plan_id, payment_method })
 *                                                → POST /api/orders/create/
 *       建议：payment_method 在演示环境传 'mock'，生产环境按实际接入传。
 *
 *  9. 演示支付（下单后的 mock 支付）
 *     orders.mockPay(orderNo)                  → POST /api/orders/mock_pay/
 *
 * 10. 取消订单
 *     orders.cancel(orderNo)                   → POST /api/orders/:orderNo/cancel/
 *
 * 11. 最近一笔订单（可选：在页面顶部展示"您最近的订单"）
 *     orders.latest()                          → GET  /api/orders/latest/
 *
 * 所有请求会自动：
 *   - 从 localStorage.getItem('scriptforge-auth') 读取 access token 并
 *     附加 Authorization: Bearer <token>
 *   - 解析后端响应 { code, message, data }：code===0 时 resolve(data)，
 *     否则 reject；401 自动清登录态并跳 /login
 *
 * 因此页面中的调用处应改为 try/catch 包裹，并用 toast 提示错误消息：
 *
 *   try {
 *     const data = await membership.plans()
 *     setPlans(data)
 *   } catch (err) {
 *     toast.error(err.message || '加载失败')
 *     // 保留本地 PLANS 作为回退
 *   }
 * ========================================================================= */
import { useState, useEffect, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  Crown,
  Sparkles,
  Check,
  Ticket,
  Zap,
  Gift,
  Shield,
  ChevronRight,
  Loader2,
  Calendar,
  Star,
  Flame,
  FileText,
  Users,
  Award,
  Wallet,
  XCircle,
  ShoppingBag,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useWalletStore } from '@/store/walletStore'
import { membership as membershipApi, orders as ordersApi } from '@/services/api'
import {
  formatDate,
  resolveRemainingDays,
  mergeMembershipState,
} from '@/utils/date'
import PriceWithDiscount from '@/components/commerce/PriceWithDiscount'
import { Button, PageLoading } from '@/components/ui'
import { SectionHeader, PageContainer } from '@/components/shared/ConsumerSection'
import { cn } from '@/utils/cn'
import { renderLucideIcon } from '@/utils/renderLucideIcon'
import { useMyMembership } from '@/hooks/queries/useMyMembership'
import OrdersListPanel from '@/components/orders/OrdersListPanel'

const DEFAULT_MEMBERSHIP = {
  plan: 'free',
  plan_name: '免费用户',
  is_active: false,
  end_at: null,
  creation_quota_used: 0,
  creation_quota_total: 0,
}


export default function Member() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const { wallet, fetchWallet } = useWalletStore()
  const { data, isLoading, refetch } = useMyMembership()
  const [redeemCode, setRedeemCode] = useState('')
  const [redeemLoading, setRedeemLoading] = useState(false)
  const [payLoading, setPayLoading] = useState({})
  const [orderActionLoading, setOrderActionLoading] = useState(null)
  const [tab, setTab] = useState('plans')
  const loading = isLoading

  const featureMatrix = data?.featureMatrix ?? null
  const membershipInfo = useMemo(
    () => mergeMembershipState(data?.membership, data?.summary, DEFAULT_MEMBERSHIP),
    [data?.membership, data?.summary],
  )
  const plans = useMemo(() => {
    const p = data?.plans
    if (!Array.isArray(p) || !p.length) return []
    return p.map((plan) => ({
      ...plan,
      period: plan.validity_days >= 365 ? '年' : '月',
      validity: plan.validity_days,
      features: plan.features,
      highlight: plan.is_recommended,
      badge: plan.is_recommended ? '🔥 最受欢迎' : undefined,
    }))
  }, [data?.plans])
  const orderList = useMemo(() => (Array.isArray(data?.orders) ? data.orders : []), [data?.orders])
  const redeemHistory = useMemo(
    () =>
      Array.isArray(data?.history)
        ? data.history.map((item) => ({
            id: item.id,
            plan_name: item.plan?.name || '会员套餐',
            redeemed_at: item.created_at || item.start_at,
            end_at: item.end_at,
          }))
        : [],
    [data?.history],
  )

  useEffect(() => {
    if (data) fetchWallet().catch(() => {})
  }, [data, fetchWallet])

  const reloadMembershipData = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['myMembershipBundle'] }),
      refetch(),
      fetchWallet(),
    ])
  }

  const handleRedeem = async (e) => {
    e.preventDefault()
    if (redeemLoading) return
    const code = redeemCode.trim().toUpperCase()
    if (!code) {
      toast.error('请输入卡密')
      return
    }
    setRedeemLoading(true)
    try {
      await membershipApi.redeem(code)
      toast.success('卡密兑换成功！会员权益已激活')
      setRedeemCode('')
      await reloadMembershipData()
    } catch (err) {
      toast.error(err.message || '卡密兑换失败')
    } finally {
      setRedeemLoading(false)
    }
  }

  const handlePurchase = async (planId) => {
    if (payLoading[planId]) return
    setPayLoading((p) => ({ ...p, [planId]: true }))
    try {
      const order = await ordersApi.createOrder({ plan_id: planId, payment_method: 'mock' })
      const orderNo = order?.order_no
      if (!orderNo) throw new Error('订单创建失败')
      await ordersApi.mockPay(orderNo)
      toast.success('支付成功！会员已激活')
      await reloadMembershipData()
    } catch (err) {
      toast.error(err.message || '购买失败，请稍后重试')
    } finally {
      setPayLoading((p) => ({ ...p, [planId]: false }))
    }
  }

  const copyOrderNo = (no) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(no)
      toast.success('订单号已复制')
    } else {
      toast.success('订单号：' + no)
    }
  }

  const handlePayOrder = async (orderNo) => {
    if (orderActionLoading) return
    setOrderActionLoading(orderNo)
    try {
      await ordersApi.mockPay(orderNo)
      toast.success('支付成功')
      await reloadMembershipData()
    } catch (err) {
      toast.error(err.message || '支付失败')
    } finally {
      setOrderActionLoading(null)
    }
  }

  const handleCancelOrder = async (orderNo) => {
    if (orderActionLoading) return
    setOrderActionLoading(orderNo)
    try {
      await ordersApi.cancel(orderNo)
      toast.success('订单已取消')
      await reloadMembershipData()
    } catch (err) {
      toast.error(err.message || '取消失败')
    } finally {
      setOrderActionLoading(null)
    }
  }

  const remainingDays = resolveRemainingDays(membershipInfo)
  const walletBalance = wallet?.balance ?? membershipInfo?.wallet?.balance ?? 0
  const walletCurrency = wallet?.currency_name || membershipInfo?.wallet?.currency_name || '创作币'

  if (loading) {
    return (
      <div className="min-h-screen pt-24">
        <PageLoading label="加载会员数据…" />
      </div>
    )
  }

  return (
    <div className="min-h-screen pt-16 pb-20">
      <PageContainer width="6xl">
        {/* 页面标题 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 flex items-center gap-3">
            <span className="gradient-text">会员中心</span>
            <Crown className="w-10 h-10 text-gold-400" />
          </h1>
          <p className="text-navy-300 text-lg flex flex-wrap items-center gap-3">
            <span>
              你好，<span className="text-white font-semibold">{user?.nickname || user?.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') || '创作者'}</span>
              ，解锁专业能力，让创意腾飞
            </span>
            <Link
              to="/orders"
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-sm text-navy-200 border border-white/10 hover:bg-white/5 transition-colors"
            >
              <ShoppingBag className="w-4 h-4" />
              我的订单
            </Link>
            <Link
              to="/wallet"
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-sm text-gold-300 border border-gold-500/30 hover:bg-gold-500/10 transition-colors"
            >
              <Wallet className="w-4 h-4" />
              创作币钱包
            </Link>
          </p>
        </motion.div>

        {/* 会员状态卡片 */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-10"
        >
          <div
            className={cn(
              'relative overflow-hidden rounded-3xl border p-8 md:p-10',
              membershipInfo?.is_active
                ? 'border-gold-400/35 bg-gradient-to-br from-gold-400/15 via-navy-900/80 to-navy-950 shadow-gold'
                : 'border-white/5 bg-gradient-to-br from-navy-900/65 to-navy-950/65',
            )}
          >
            <div className="relative flex flex-col gap-8 md:flex-row md:items-center md:gap-12">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  {membershipInfo?.is_active ? (
                    <div className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-[#f6d365] to-[#fda085] px-4 py-1.5 text-sm font-semibold text-navy-950">
                      <Crown className="w-4 h-4" />
                      {membershipInfo?.plan_name || '会员'}
                    </div>
                  ) : (
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold text-navy-200 bg-slate-700/50 border border-white/10">
                      <Gift className="w-4 h-4" />
                      {membershipInfo?.plan_name || '免费用户'}
                    </div>
                  )}
                  {membershipInfo?.is_active && remainingDays > 0 && (
                    <span className="inline-flex items-center gap-1.5 text-sm text-gold-300">
                      <Flame className="w-4 h-4" /> 剩余 {remainingDays} 天
                    </span>
                  )}
                </div>

                <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
                  {membershipInfo?.is_active ? (
                    <>享受完整的专业创作能力</>
                  ) : (
                    <>升级会员，解锁全部创作能力</>
                  )}
                </h2>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
                  {/* 创作次数 */}
                  <div className="p-5 rounded-2xl bg-slate-900/40 border border-white/10">
                    <div className="flex items-center justify-between mb-3">
                      <div className="text-sm text-navy-300 flex items-center gap-1.5">
                        <Wallet className="w-4 h-4" /> 创作币余额
                      </div>
                      <Link to="/wallet" className="text-xs text-gold-400 hover:underline">
                        去充值
                      </Link>
                    </div>
                    <div className="text-3xl font-bold text-white mb-1">
                      <span className="gradient-text">{walletBalance}</span>
                      <span className="text-navy-400 text-lg font-normal ml-2">{walletCurrency}</span>
                    </div>
                    <div className="text-xs text-navy-400">创作按节点/动作扣费，开通会员赠送创作币</div>
                  </div>

                  {/* 到期时间 */}
                  <div className="p-5 rounded-2xl bg-slate-900/40 border border-white/10">
                    <div className="text-sm text-navy-300 flex items-center gap-1.5 mb-3">
                      <Calendar className="w-4 h-4" /> 会员到期时间
                    </div>
                    <div className="text-xl font-bold text-white mb-1">
                      {membershipInfo?.is_active ? formatDate(membershipInfo.end_at) : '未开通'}
                    </div>
                    {membershipInfo?.is_active && remainingDays > 0 && (
                      <div className="text-xs text-gold-400">
                        还有 {remainingDays} 天到期
                      </div>
                    )}
                  </div>

                  {/* 会员权益 */}
                  <div className="p-5 rounded-2xl bg-slate-900/40 border border-white/10">
                    <div className="text-sm text-navy-300 flex items-center gap-1.5 mb-3">
                      <Shield className="w-4 h-4" /> 专属权益
                    </div>
                    <div className="text-xl font-bold text-white mb-1">
                      {membershipInfo?.is_active ? '全部解锁' : '基础功能'}
                    </div>
                    <div className="text-xs text-navy-300">
                      {membershipInfo?.is_active ? '所有模板和格式可用' : '仅使用免费模板'}
                    </div>
                  </div>
                </div>
              </div>

              {/* 右侧图标 */}
              <div className="hidden md:flex flex-col items-center">
                <div
                  className={cn(
                    'relative flex h-32 w-32 items-center justify-center rounded-3xl',
                    membershipInfo?.is_active
                      ? 'bg-gradient-to-br from-[#f6d365] to-[#fda085] shadow-gold'
                      : 'bg-gradient-to-br from-indigo-500/30 to-purple-600/30',
                  )}
                >
                  <Crown className={`w-16 h-16 ${membershipInfo?.is_active ? 'text-navy-950' : 'text-gold-400'}`} />
                </div>
                {!membershipInfo?.is_active && (
                  <button
                    onClick={() => setTab('plans')}
                    className="mt-5 inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-[#f6d365] to-[#fda085] px-6 py-2.5 text-sm font-semibold text-navy-950"
                  >
                    <Sparkles className="w-4 h-4" />
                    立即升级
                  </button>
                )}
              </div>
            </div>
          </div>
        </motion.div>

        {featureMatrix && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-10"
          >
            <h2 className="text-lg font-semibold text-white mb-4">会员与非会员权益对比</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-2xl border border-white/5 bg-gradient-to-br from-navy-900/65 to-navy-950/65 p-6">
              <h3 className="text-lg font-bold text-white mb-1">
                {featureMatrix.free_tier?.name || '普通用户'}
              </h3>
              <p className="text-xs text-navy-400 mb-4">充值仅到账基础创作币，无额外赠送</p>
              <ul className="space-y-2">
                {(featureMatrix.free_tier?.matrix || []).map((row) => (
                  <li
                    key={row.key}
                    className={`flex items-center justify-between text-sm gap-2 rounded-lg px-2 py-1.5 ${
                      row.free !== row.member ? 'bg-white/[0.04]' : ''
                    }`}
                  >
                    <span className="text-navy-200">{row.label}</span>
                    {row.free ? (
                      <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-navy-500 flex-shrink-0" />
                    )}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl border border-gold-400/30 bg-gradient-to-br from-navy-900/65 to-navy-950/65 p-6 shadow-gold">
              <h3 className="text-lg font-bold text-gold-400 mb-1">
                {featureMatrix.member_tier?.name || '会员用户'}
              </h3>
              <p className="text-xs text-navy-400 mb-4">开通赠币 + 充值额外赠送创作币</p>
              <ul className="space-y-2">
                {(featureMatrix.member_tier?.matrix || featureMatrix.free_tier?.matrix || []).map((row) => (
                  <li
                    key={row.key}
                    className={`flex items-center justify-between text-sm gap-2 rounded-lg px-2 py-1.5 ${
                      row.free !== row.member ? 'bg-gold-500/5 border border-gold-500/10' : ''
                    }`}
                  >
                    <span className="text-navy-100 flex items-center gap-2">
                      {row.label}
                      {row.coming_soon && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300">
                          即将上线
                        </span>
                      )}
                    </span>
                    {row.member ? (
                      <Check className="w-4 h-4 text-gold-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-navy-500 flex-shrink-0" />
                    )}
                  </li>
                ))}
              </ul>
              {!featureMatrix.is_member && (
                <button
                  type="button"
                  onClick={() => setTab('plans')}
                  className="mt-5 w-full py-2.5 rounded-xl btn-gold text-sm font-semibold"
                >
                  开通会员
                </button>
              )}
            </div>
            </div>
          </motion.div>
        )}

        {/* Tabs */}
        <div className="flex flex-wrap gap-2 mb-8">
          {[
            { key: 'plans', label: '套餐选择', icon: Crown },
            { key: 'redeem', label: '卡密兑换', icon: Ticket },
            { key: 'orders', label: '我的订单', icon: ShoppingBag },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={cn(
                'flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all',
                tab === t.key
                  ? 'bg-gradient-to-br from-[#f6d365] to-[#fda085] text-navy-950 shadow-gold'
                  : 'border border-white/10 bg-slate-800/50 text-navy-200 hover:border-white/20 hover:text-white',
              )}
            >
              {renderLucideIcon(t.icon, 'w-4 h-4')}
              {t.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {tab === 'plans' && (
            <motion.div
              key="plans"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <SectionHeader
                align="center"
                eyebrow="套餐选择"
                title="选择适合你的版本"
                subtitle="开通后立即生效，创作次数与创作币将自动到账"
                className="mb-10"
              />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
                {plans.map((plan, idx) => (
                  <motion.article
                    key={plan.id}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + idx * 0.1 }}
                    whileHover={{ y: plan.highlight ? -4 : -2 }}
                    className={cn(
                      'relative flex flex-col rounded-3xl border border-white/5 bg-gradient-to-br from-navy-900/65 to-navy-950/65 p-8 transition-shadow',
                      plan.highlight && 'border-gold-400/50 shadow-gold -translate-y-1.5',
                    )}
                  >
                    {plan.highlight && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-gradient-to-br from-[#f6d365] to-[#fda085] px-4 py-1.5 text-xs font-bold text-navy-950">
                        {plan.badge}
                      </div>
                    )}

                    {!plan.highlight && plan.badge && (
                      <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-navy-400">
                        {plan.badge}
                      </div>
                    )}

                    <div className="mb-5">
                      <h3 className={cn('text-2xl font-bold', plan.highlight ? 'gradient-text' : 'text-white')}>
                        {plan.name}
                      </h3>
                    </div>

                    <PriceWithDiscount
                      price={plan.price}
                      displayPrice={plan.display_price}
                      originalPrice={plan.original_price}
                      displayOriginalPrice={plan.display_original_price}
                      discountLabel={plan.discount_label}
                      discountPercent={plan.discount_percent}
                      validityDays={plan.validity_days ?? plan.validity}
                      size="lg"
                      layout="stack"
                      framed
                      chargeTone="white"
                      suffix={`/${plan.period}`}
                      className="mb-6"
                    />

                    <ul className="mb-8 min-h-[200px] space-y-2.5">
                      {plan.features.map((feat) => (
                        <li key={feat} className="flex items-start gap-2 text-sm text-navy-100">
                          <Check className={cn('mt-0.5 h-4 w-4 flex-shrink-0', plan.highlight ? 'text-gold-400' : 'text-navy-400')} />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>

                    <motion.button
                      onClick={() => handlePurchase(plan.id)}
                      disabled={!!payLoading[plan.id]}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={cn(
                        'mt-auto flex w-full items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold transition-all disabled:cursor-not-allowed disabled:opacity-60',
                        plan.highlight
                          ? 'bg-gradient-to-br from-[#f6d365] to-[#fda085] text-navy-950 shadow-gold'
                          : 'border border-white/10 bg-indigo-500/20 text-white',
                      )}
                    >
                      {payLoading[plan.id] ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          处理中...
                        </>
                      ) : (
                        <>
                          <Zap className="w-4 h-4" />
                          立即开通
                        </>
                      )}
                    </motion.button>
                  </motion.article>
                ))}
              </div>

              {/* 支付说明 */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="rounded-2xl border border-gold-400/30 bg-gold-400/5 p-6"
              >
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-navy-200">
                    <div className="font-semibold text-white mb-1">安全支付说明</div>
                    <p>演示环境中点击"立即开通"将模拟支付流程，真实支付请在生产环境接入第三方支付渠道。会员开通后立即生效，创作次数将自动累加。</p>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}

          {tab === 'redeem' && (
            <motion.div
              key="redeem"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="grid grid-cols-1 lg:grid-cols-2 gap-6"
            >
              {/* 兑换表单 */}
              <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-gold-400/15 border border-gold-400/30">
                    <Ticket className="w-6 h-6 text-gold-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">卡密兑换</h3>
                    <p className="text-sm text-navy-300">输入您的卡密，立即激活会员</p>
                  </div>
                </div>

                <form onSubmit={handleRedeem} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-navy-200 mb-2">卡密</label>
                    <input
                      type="text"
                      placeholder="请输入卡密（例如 SF-XXXX-XXXX-XXXX）"
                      value={redeemCode}
                      onChange={(e) => setRedeemCode(e.target.value.toUpperCase())}
                      className="w-full px-5 py-4 rounded-xl bg-slate-900/60 border border-white/10 focus:border-gold-400 text-white placeholder-navy-400 outline-none transition-all focus:ring-2 focus:ring-gold-400/20 text-sm tracking-wider font-mono"
                    />
                  </div>

                  <motion.button
                    type="submit"
                    disabled={redeemLoading}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-[#f6d365] to-[#fda085] py-4 text-base font-bold text-navy-950 shadow-gold transition-all disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {redeemLoading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        兑换中...
                      </>
                    ) : (
                      <>
                        <Gift className="w-5 h-5" />
                        立即兑换
                      </>
                    )}
                  </motion.button>
                </form>

                <div className="mt-6 pt-6 border-t border-white/10">
                  <div className="text-xs text-navy-400 space-y-1.5">
                    <p>• 卡密格式：字母和数字组成，输入时自动转为大写</p>
                    <p>• 每张卡密仅可使用一次，兑换后立即生效</p>
                    <p>• 如有问题请联系客服</p>
                    <p>• 卡密由管理员批量生成，请向渠道方获取</p>
                  </div>
                </div>
              </div>

              {/* 卡密信息 */}
              <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-slate-700/50 flex items-center justify-center">
                    <Award className="w-6 h-6 text-gold-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">兑换记录</h3>
                    <p className="text-sm text-navy-300">查看您的卡密兑换历史</p>
                  </div>
                </div>

                {redeemHistory.length > 0 ? (
                  <div className="space-y-3">
                    {redeemHistory.map((record) => (
                      <div key={record.id} className="p-4 rounded-xl bg-slate-900/40 border border-white/10 flex items-center justify-between">
                        <div>
                          <div className="text-sm text-white font-semibold">{record.plan_name}</div>
                          <div className="text-xs text-navy-400 mt-1">开通于 {formatDate(record.redeemed_at)}</div>
                          {record.end_at && (
                            <div className="text-xs text-navy-400 mt-0.5">到期 {formatDate(record.end_at)}</div>
                          )}
                        </div>
                        <div className="text-xs text-gold-400 font-semibold">已激活</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Ticket className="w-16 h-16 text-navy-500 mx-auto mb-4" />
                    <p className="text-navy-300 mb-1">暂无兑换记录</p>
                    <p className="text-xs text-navy-400">使用卡密激活会员后将显示在此处</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {tab === 'orders' && (
            <motion.div
              key="orders"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="rounded-2xl border border-white/5 bg-slate-900/60 p-6 md:p-8"
            >
              <OrdersListPanel
                orders={orderList}
                orderActionLoading={orderActionLoading}
                onCopyOrderNo={copyOrderNo}
                onPayOrder={handlePayOrder}
                onCancelOrder={handleCancelOrder}
                onRefresh={async () => {
                  try {
                    await reloadMembershipData()
                    toast.success('订单列表已刷新')
                  } catch {
                    toast.error('刷新失败')
                  }
                }}
                emptyAction={
                  <Button
                    variant="gold"
                    size="sm"
                    iconRight={<ChevronRight className="w-4 h-4" />}
                    onClick={() => setTab('plans')}
                  >
                    去选购套餐
                  </Button>
                }
              />
            </motion.div>
          )}
        </AnimatePresence>
      </PageContainer>
    </div>
  )
}
