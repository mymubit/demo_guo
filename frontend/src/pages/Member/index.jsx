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
  Clock,
  Zap,
  Gift,
  Shield,
  ChevronRight,
  Loader2,
  Calendar,
  CheckCircle2,
  XCircle,
  Copy,
  ShoppingBag,
  RefreshCw,
  Star,
  Flame,
  FileText,
  Users,
  Award,
  Wallet,
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
import { Badge, Button, EmptyState, PageLoading } from '@/components/ui'
import { useMyMembership } from '@/hooks/queries/useMyMembership'

const DEFAULT_MEMBERSHIP = {
  plan: 'free',
  plan_name: '免费用户',
  is_active: false,
  end_at: null,
  creation_quota_used: 0,
  creation_quota_total: 0,
}

function OrderStatusBadge({ status }) {
  if (status === 'paid') {
    return (
      <Badge tone="success" icon={<CheckCircle2 className="w-3.5 h-3.5" />}>
        已支付
      </Badge>
    )
  }
  if (status === 'cancelled') {
    return (
      <Badge tone="default" icon={<XCircle className="w-3.5 h-3.5" />}>
        已取消
      </Badge>
    )
  }
  if (status === 'refunded') {
    return <Badge tone="info">已退款</Badge>
  }
  return (
    <Badge tone="warning" icon={<Clock className="w-3.5 h-3.5" />}>
      待支付
    </Badge>
  )
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
    <div className="min-h-screen pt-16 pb-20 px-6 relative">
      <div className="particles-bg" />
      <div className="absolute top-40 left-10 w-96 h-96 rounded-full bg-gold-500/10 blur-3xl pointer-events-none" />
      <div className="absolute top-80 right-10 w-[500px] h-[500px] rounded-full bg-purple-600/10 blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
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
          <div className="relative overflow-hidden rounded-[32px] p-8 md:p-10" style={{
            background: membershipInfo?.is_active
              ? 'linear-gradient(135deg, rgba(244, 183, 25, 0.15) 0%, rgba(253, 160, 133, 0.1) 50%, rgba(102, 126, 234, 0.1) 100%)'
              : 'linear-gradient(135deg, rgba(15, 42, 92, 0.6) 0%, rgba(15, 42, 92, 0.3) 100%)',
            border: membershipInfo?.is_active ? '1px solid rgba(244, 183, 25, 0.35)' : '1px solid rgba(102, 126, 234, 0.2)',
            backdropFilter: 'blur(20px)',
            boxShadow: membershipInfo?.is_active ? '0 20px 60px -20px rgba(244, 183, 25, 0.3)' : 'none',
          }}>
            {/* 装饰 */}
            <div className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-30 blur-3xl pointer-events-none"
              style={{ background: membershipInfo?.is_active ? 'radial-gradient(circle, #f4b719 0%, transparent 70%)' : 'radial-gradient(circle, #667eea 0%, transparent 70%)' }} />

            <div className="relative z-10 flex flex-col md:flex-row gap-8 md:gap-12 items-start md:items-center">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  {membershipInfo?.is_active ? (
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold text-navy-950"
                      style={{ background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' }}>
                      <Crown className="w-4 h-4" />
                      {membershipInfo?.plan_name || '会员'}
                    </div>
                  ) : (
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold text-navy-200 bg-navy-700/50 border border-navy-600/40">
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
                  <div className="p-5 rounded-2xl bg-navy-900/40 border border-navy-600/30">
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
                  <div className="p-5 rounded-2xl bg-navy-900/40 border border-navy-600/30">
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
                  <div className="p-5 rounded-2xl bg-navy-900/40 border border-navy-600/30">
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
                <div className="relative w-32 h-32 rounded-3xl flex items-center justify-center"
                  style={{
                    background: membershipInfo?.is_active
                      ? 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)'
                      : 'linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%)',
                    boxShadow: membershipInfo?.is_active ? '0 20px 40px -10px rgba(244, 183, 25, 0.4)' : 'none',
                  }}>
                  <Crown className={`w-16 h-16 ${membershipInfo?.is_active ? 'text-navy-950' : 'text-gold-400'}`} />
                </div>
                {!membershipInfo?.is_active && (
                  <button
                    onClick={() => setTab('plans')}
                    className="mt-5 px-6 py-2.5 rounded-xl font-semibold text-navy-950 text-sm inline-flex items-center gap-2"
                    style={{ background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' }}>
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
            <div className="glass-card rounded-2xl p-6 border border-navy-700/40">
              <h3 className="text-lg font-bold text-white mb-1">
                {featureMatrix.free_tier?.name || '普通用户'}
              </h3>
              <p className="text-xs text-navy-500 mb-4">充值仅到账基础创作币，无额外赠送</p>
              <ul className="space-y-2">
                {(featureMatrix.free_tier?.matrix || []).map((row) => (
                  <li
                    key={row.key}
                    className={`flex items-center justify-between text-sm gap-2 rounded-lg px-2 py-1.5 ${
                      row.free !== row.member ? 'bg-navy-800/40' : ''
                    }`}
                  >
                    <span className="text-navy-200">{row.label}</span>
                    {row.free ? (
                      <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-navy-600 flex-shrink-0" />
                    )}
                  </li>
                ))}
              </ul>
            </div>
            <div className="glass-card rounded-2xl p-6 border border-gold-500/30">
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
                      <XCircle className="w-4 h-4 text-navy-600 flex-shrink-0" />
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
              className={`px-5 py-2.5 rounded-xl font-semibold text-sm flex items-center gap-2 transition-all ${
                tab === t.key
                  ? 'text-navy-950'
                  : 'text-navy-200 hover:text-white bg-navy-800/50 border border-navy-600/30 hover:border-navy-500/40'
              }`}
              style={tab === t.key ? {
                background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
                boxShadow: '0 8px 20px -8px rgba(244, 183, 25, 0.5)',
              } : {}}>
              <t.icon className="w-4 h-4" />
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {plans.map((plan, idx) => (
                  <motion.div
                    key={plan.id}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + idx * 0.1 }}
                    whileHover={{ y: -5 }}
                    className={`relative rounded-[28px] p-8 ${
                      plan.highlight ? 'scale-105 md:scale-100' : ''
                    }`}
                    style={{
                      background: plan.highlight
                        ? 'linear-gradient(135deg, rgba(244, 183, 25, 0.12) 0%, rgba(253, 160, 133, 0.08) 50%, rgba(15, 42, 92, 0.5) 100%)'
                        : 'rgba(15, 42, 92, 0.5)',
                      border: plan.highlight ? '1px solid rgba(244, 183, 25, 0.4)' : '1px solid rgba(102, 126, 234, 0.2)',
                      backdropFilter: 'blur(20px)',
                      boxShadow: plan.highlight ? '0 20px 60px -20px rgba(244, 183, 25, 0.4)' : 'none',
                    }}>
                    {plan.highlight && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full text-xs font-bold text-navy-950 whitespace-nowrap"
                        style={{ background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' }}>
                        {plan.badge}
                      </div>
                    )}

                    {!plan.highlight && plan.badge && (
                      <div className="text-xs text-navy-400 font-semibold uppercase tracking-wider mb-3">
                        {plan.badge}
                      </div>
                    )}

                    <div className="mb-5">
                      <h3 className={`text-2xl font-bold ${plan.highlight ? 'gradient-text' : 'text-white'}`}>
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

                    <ul className="space-y-2.5 mb-8 min-h-[200px]">
                      {plan.features.map((feat) => (
                        <li key={feat} className="flex items-start gap-2 text-sm text-navy-100">
                          <Check className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.highlight ? 'text-gold-400' : 'text-navy-400'}`} />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>

                    <motion.button
                      onClick={() => handlePurchase(plan.id)}
                      disabled={!!payLoading[plan.id]}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={`w-full py-3.5 rounded-xl font-bold text-sm flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed transition-all ${
                        plan.highlight ? 'text-navy-950' : 'text-white'
                      }`}
                      style={plan.highlight ? {
                        background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
                        boxShadow: '0 10px 30px -10px rgba(244, 183, 25, 0.5)',
                      } : {
                        background: 'rgba(102, 126, 234, 0.2)',
                        border: '1px solid rgba(102, 126, 234, 0.4)',
                      }}>
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
                  </motion.div>
                ))}
              </div>

              {/* 支付说明 */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="p-6 rounded-2xl glass-card-gold">
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
              <div className="p-8 rounded-[28px] glass-card">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
                    style={{ background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' }}>
                    <Ticket className="w-6 h-6 text-navy-950" />
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
                      className="w-full px-5 py-4 rounded-xl bg-navy-900/60 border border-navy-600/40 focus:border-gold-400 text-white placeholder-navy-400 outline-none transition-all focus:ring-2 focus:ring-gold-400/20 text-sm tracking-wider font-mono"
                    />
                  </div>

                  <motion.button
                    type="submit"
                    disabled={redeemLoading}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full py-4 rounded-xl font-bold text-navy-950 text-base flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed transition-all"
                    style={{
                      background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
                      boxShadow: '0 10px 30px -10px rgba(244, 183, 25, 0.5)',
                    }}>
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

                <div className="mt-6 pt-6 border-t border-navy-600/30">
                  <div className="text-xs text-navy-400 space-y-1.5">
                    <p>• 卡密格式：字母和数字组成，区分大小写</p>
                    <p>• 每张卡密仅可使用一次，兑换后立即生效</p>
                    <p>• 如有问题请联系客服</p>
                    <p>• 卡密由管理员批量生成，请向渠道方获取</p>
                  </div>
                </div>
              </div>

              {/* 卡密信息 */}
              <div className="p-8 rounded-[28px] glass-card">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-navy-700/50 flex items-center justify-center">
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
                      <div key={record.id} className="p-4 rounded-xl bg-navy-900/40 border border-navy-600/30 flex items-center justify-between">
                        <div>
                          <div className="text-sm text-white font-semibold">{record.plan_name}</div>
                          <div className="text-xs text-navy-400 mt-1">开通于 {formatDate(record.redeemed_at)}</div>
                          {record.end_at && (
                            <div className="text-xs text-navy-500 mt-0.5">到期 {formatDate(record.end_at)}</div>
                          )}
                        </div>
                        <div className="text-xs text-gold-400 font-semibold">已激活</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Ticket className="w-16 h-16 text-navy-600 mx-auto mb-4" />
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
              className="p-6 md:p-8 rounded-[28px] glass-card"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-navy-700/50 flex items-center justify-center">
                    <ShoppingBag className="w-6 h-6 text-gold-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">我的订单</h3>
                    <p className="text-sm text-navy-300">共 {orderList.length} 条订单记录</p>
                  </div>
                </div>
                <button
                  onClick={async () => {
                    try {
                      await reloadMembershipData()
                      toast.success('订单列表已刷新')
                    } catch {
                      toast.error('刷新失败')
                    }
                  }}
                  className="p-2.5 rounded-xl bg-navy-800/50 border border-navy-600/30 text-navy-300 hover:text-white hover:border-navy-500/40 transition-all">
                  <RefreshCw className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-3 md:hidden">
                {orderList.map((order) => (
                  <div
                    key={order.id || order.order_no}
                    className="rounded-2xl border border-navy-700/35 bg-navy-900/45 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <button
                          type="button"
                          onClick={() => copyOrderNo(order.order_no)}
                          className="flex max-w-full items-center gap-1.5 truncate font-mono text-sm text-white hover:text-gold-400"
                        >
                          <span className="truncate">{order.order_no}</span>
                          <Copy className="w-3.5 h-3.5 shrink-0 text-navy-400" />
                        </button>
                        <p className="mt-1 text-xs text-navy-500">创建于 {formatDate(order.created_at)}</p>
                      </div>
                      <OrderStatusBadge status={order.status} />
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <p className="text-xs text-navy-500">套餐</p>
                        <p className="mt-1 font-semibold text-white">{order.plan_name}</p>
                      </div>
                      <div>
                        <p className="text-xs text-navy-500">金额</p>
                        <p className="mt-1 text-lg font-bold gradient-text">¥{order.amount}</p>
                      </div>
                      <div className="col-span-2">
                        <p className="text-xs text-navy-500">支付时间</p>
                        <p className="mt-1 text-navy-300">{order.paid_at ? formatDate(order.paid_at) : '-'}</p>
                      </div>
                    </div>
                    {order.status === 'pending' && (
                      <div className="mt-4 grid grid-cols-2 gap-2">
                        <Button
                          size="sm"
                          variant="gold"
                          isLoading={orderActionLoading === order.order_no}
                          onClick={() => handlePayOrder(order.order_no)}
                        >
                          去支付
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={orderActionLoading === order.order_no}
                          onClick={() => handleCancelOrder(order.order_no)}
                        >
                          取消
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="hidden overflow-x-auto overscroll-x-contain md:block">
                <table className="w-full min-w-[700px]">
                  <thead>
                    <tr className="border-b border-navy-600/30">
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">订单信息</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">套餐</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">金额</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">状态</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">时间</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orderList.map((order) => (
                      <tr key={order.id} className="border-b border-navy-600/20 hover:bg-navy-800/20 transition-colors">
                        <td className="py-5 px-4">
                          <div className="flex items-center gap-3">
                            <div className="text-sm">
                              <div className="font-mono text-white cursor-pointer hover:text-gold-400 transition-colors flex items-center gap-1.5"
                                onClick={() => copyOrderNo(order.order_no)}>
                                {order.order_no}
                                <Copy className="w-3.5 h-3.5 text-navy-400" />
                              </div>
                              <div className="text-xs text-navy-400 mt-1">
                                创建于 {formatDate(order.created_at)}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-5 px-4 text-sm text-white font-semibold">
                          {order.plan_name}
                        </td>
                        <td className="py-5 px-4">
                          <span className="text-lg font-bold gradient-text">¥{order.amount}</span>
                        </td>
                        <td className="py-5 px-4">
                          <OrderStatusBadge status={order.status} />
                        </td>
                        <td className="py-5 px-4 text-sm text-navy-300">
                          {order.paid_at ? formatDate(order.paid_at) : '-'}
                        </td>
                        <td className="py-5 px-4">
                          {order.status === 'pending' && (
                            <div className="flex gap-2">
                              <button
                                disabled={orderActionLoading === order.order_no}
                                onClick={() => handlePayOrder(order.order_no)}
                                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-navy-950 bg-gold-400 hover:bg-gold-300 disabled:opacity-50"
                              >
                                {orderActionLoading === order.order_no ? '处理中' : '去支付'}
                              </button>
                              <button
                                disabled={orderActionLoading === order.order_no}
                                onClick={() => handleCancelOrder(order.order_no)}
                                className="px-3 py-1.5 rounded-lg text-xs text-navy-300 border border-navy-600/40 hover:text-white disabled:opacity-50"
                              >
                                取消
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {orderList.length === 0 && (
                <EmptyState
                  compact
                  icon={ShoppingBag}
                  title="暂无订单记录"
                  description="购买套餐后将显示在此处"
                  action={
                    <Button
                      variant="gold"
                      size="sm"
                      iconRight={<ChevronRight className="w-4 h-4" />}
                      onClick={() => setTab('plans')}
                    >
                      去选购套餐
                    </Button>
                  }
                  className="mt-4"
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
