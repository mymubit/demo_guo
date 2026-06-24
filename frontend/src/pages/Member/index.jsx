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
  Flame,
  XCircle,
  ShoppingBag,
  Wallet,
  Award,
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
import { Button, Input, PageLoading } from '@/components/ui'
import PageShell from '@/components/layout/PageShell'
import { cn } from '@/utils/cn'
import { renderLucideIcon } from '@/utils/renderLucideIcon'
import { useMyMembership } from '@/hooks/queries/useMyMembership'
import OrdersListPanel from '@/components/orders/OrdersListPanel'
import EmptyState from '@/components/ui/EmptyState'

const DEFAULT_MEMBERSHIP = {
  plan: 'free',
  plan_name: '免费用户',
  is_active: false,
  end_at: null,
  creation_quota_used: 0,
  creation_quota_total: 0,
}

const TABS = [
  { key: 'plans', label: '套餐选择', icon: Crown },
  { key: 'redeem', label: '卡密兑换', icon: Ticket },
  { key: 'orders', label: '我的订单', icon: ShoppingBag },
]

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
      <PageShell title="会员中心" maxWidth="6xl">
        <PageLoading label="加载会员数据…" />
      </PageShell>
    )
  }

  return (
    <PageShell
      title="会员中心"
      description={`你好，${user?.nickname || user?.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') || '创作者'}，解锁专业能力，让创意腾飞`}
      maxWidth="6xl"
      actions={
        <div className="flex flex-wrap gap-2">
          <Link to="/orders">
            <Button variant="secondary" size="sm" iconLeft={<ShoppingBag className="w-4 h-4" />}>
              我的订单
            </Button>
          </Link>
          <Link to="/wallet">
            <Button variant="gold" size="sm" iconLeft={<Wallet className="w-4 h-4" />}>
              创作币钱包
            </Button>
          </Link>
        </div>
      }
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div
          className={cn(
            'relative overflow-hidden rounded-3xl border p-6 md:p-8',
            membershipInfo?.is_active
              ? 'border-gold-500/30 bg-gradient-to-br from-gold-500/15 via-navy-900/80 to-navy-950 shadow-gold'
              : 'border-white/10 bg-white/[0.04] backdrop-blur-sm',
          )}
        >
          <div className="relative flex flex-col gap-6 md:flex-row md:items-center md:gap-10">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-3 mb-4">
                {membershipInfo?.is_active ? (
                  <div className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-gold-400 to-gold-500 px-4 py-1.5 text-sm font-semibold text-navy-950 shadow-gold">
                    <Crown className="w-4 h-4" />
                    {membershipInfo?.plan_name || '会员'}
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold text-slate-300 bg-white/5 border border-white/10">
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

              <h2 className="text-xl md:text-2xl font-bold text-white mb-4">
                {membershipInfo?.is_active ? (
                  <>享受完整的专业创作能力</>
                ) : (
                  <>升级会员，解锁全部创作能力</>
                )}
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
                <div className="p-4 rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm text-slate-400 flex items-center gap-1.5">
                      <Wallet className="w-4 h-4" /> 创作币余额
                    </div>
                    <Link to="/wallet" className="text-xs text-gold-400 hover:text-gold-300 transition-colors">
                      去充值
                    </Link>
                  </div>
                  <div className="text-2xl md:text-3xl font-bold text-white mb-1">
                    <span className="sf-text-gradient-gold">{walletBalance}</span>
                    <span className="text-slate-400 text-base font-normal ml-2">{walletCurrency}</span>
                  </div>
                  <div className="text-xs text-slate-500">创作按节点/动作扣费，开通会员赠送创作币</div>
                </div>

                <div className="p-4 rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm">
                  <div className="text-sm text-slate-400 flex items-center gap-1.5 mb-3">
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

                <div className="p-4 rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm">
                  <div className="text-sm text-slate-400 flex items-center gap-1.5 mb-3">
                    <Shield className="w-4 h-4" /> 专属权益
                  </div>
                  <div className="text-xl font-bold text-white mb-1">
                    {membershipInfo?.is_active ? '全部解锁' : '基础功能'}
                  </div>
                  <div className="text-xs text-slate-500">
                    {membershipInfo?.is_active ? '所有模板和格式可用' : '仅使用免费模板'}
                  </div>
                </div>
              </div>
            </div>

            <div className="hidden md:flex flex-col items-center">
              <div
                className={cn(
                  'relative flex h-28 w-28 items-center justify-center rounded-3xl',
                  membershipInfo?.is_active
                    ? 'bg-gradient-to-br from-gold-400 to-gold-600 shadow-gold'
                    : 'bg-white/5 border border-white/10',
                )}
              >
                <Crown className={cn('w-14 h-14', membershipInfo?.is_active ? 'text-navy-950' : 'text-gold-400')} />
              </div>
              {!membershipInfo?.is_active && (
                <Button
                  variant="gold"
                  size="sm"
                  className="mt-4"
                  iconLeft={<Sparkles className="w-4 h-4" />}
                  onClick={() => setTab('plans')}
                >
                  立即升级
                </Button>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      {featureMatrix && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <h2 className="text-lg font-semibold text-white mb-4">会员与非会员权益对比</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm p-6">
              <h3 className="text-lg font-bold text-white mb-1">
                {featureMatrix.free_tier?.name || '普通用户'}
              </h3>
              <p className="text-xs text-slate-500 mb-4">充值仅到账基础创作币，无额外赠送</p>
              <ul className="space-y-2">
                {(featureMatrix.free_tier?.matrix || []).map((row) => (
                  <li
                    key={row.key}
                    className={cn(
                      'flex items-center justify-between text-sm gap-2 rounded-lg px-3 py-2',
                      row.free !== row.member ? 'bg-white/[0.03]' : '',
                    )}
                  >
                    <span className="text-slate-300">{row.label}</span>
                    {row.free ? (
                      <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-slate-600 flex-shrink-0" />
                    )}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl border border-gold-500/30 bg-gradient-to-br from-gold-500/10 to-navy-900/30 backdrop-blur-sm p-6 shadow-gold/20">
              <h3 className="text-lg font-bold text-gold-400 mb-1">
                {featureMatrix.member_tier?.name || '会员用户'}
              </h3>
              <p className="text-xs text-slate-500 mb-4">开通赠币 + 充值额外赠送创作币</p>
              <ul className="space-y-2">
                {(featureMatrix.member_tier?.matrix || featureMatrix.free_tier?.matrix || []).map((row) => (
                  <li
                    key={row.key}
                    className={cn(
                      'flex items-center justify-between text-sm gap-2 rounded-lg px-3 py-2',
                      row.free !== row.member ? 'bg-gold-500/10 border border-gold-500/10' : '',
                    )}
                  >
                    <span className="text-white flex items-center gap-2">
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
                      <XCircle className="w-4 h-4 text-slate-600 flex-shrink-0" />
                    )}
                  </li>
                ))}
              </ul>
              {!featureMatrix.is_member && (
                <Button
                  variant="gold"
                  className="mt-5 w-full"
                  onClick={() => setTab('plans')}
                >
                  开通会员
                </Button>
              )}
            </div>
          </div>
        </motion.div>
      )}

      <div className="flex flex-wrap gap-2 mb-6">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              'flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-all',
              tab === t.key
                ? 'bg-gradient-to-r from-gold-400 to-gold-500 text-navy-950 shadow-gold'
                : 'border border-white/10 bg-white/5 text-slate-400 hover:text-white hover:bg-white/10',
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
            <div className="text-center mb-8">
              <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">选择适合你的版本</h2>
              <p className="text-slate-400">开通后立即生效，创作次数与创作币将自动到账</p>
            </div>

            {plans.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
                {plans.map((plan, idx) => (
                  <motion.article
                    key={plan.id}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 + idx * 0.1 }}
                    whileHover={{ y: plan.highlight ? -4 : -2 }}
                    className={cn(
                      'relative flex flex-col rounded-3xl border backdrop-blur-sm p-6 md:p-8 transition-all',
                      plan.highlight
                        ? 'border-gold-500/40 bg-gradient-to-br from-gold-500/10 to-navy-900/50 shadow-gold -translate-y-2'
                        : 'border-white/10 bg-white/[0.04] hover:border-white/20',
                    )}
                  >
                    {plan.highlight && plan.badge && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-gradient-to-r from-gold-400 to-gold-500 px-4 py-1.5 text-xs font-bold text-navy-950 shadow-gold">
                        {plan.badge}
                      </div>
                    )}

                    {!plan.highlight && plan.badge && (
                      <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                        {plan.badge}
                      </div>
                    )}

                    <div className="mb-5">
                      <h3 className={cn('text-2xl font-bold', plan.highlight ? 'sf-text-gradient-gold' : 'text-white')}>
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
                      chargeTone="gold"
                      suffix={`/${plan.period}`}
                      className="mb-6"
                    />

                    <ul className="mb-8 min-h-[180px] space-y-2.5">
                      {plan.features.map((feat) => (
                        <li key={feat} className="flex items-start gap-2 text-sm text-slate-300">
                          <Check className={cn('mt-0.5 h-4 w-4 flex-shrink-0', plan.highlight ? 'text-gold-400' : 'text-slate-500')} />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>

                    <Button
                      variant={plan.highlight ? 'gold' : 'secondary'}
                      className="mt-auto w-full"
                      isLoading={!!payLoading[plan.id]}
                      iconLeft={!payLoading[plan.id] && <Zap className="w-4 h-4" />}
                      onClick={() => handlePurchase(plan.id)}
                      disabled={!!payLoading[plan.id]}
                    >
                      {payLoading[plan.id] ? '处理中...' : '立即开通'}
                    </Button>
                  </motion.article>
                ))}
              </div>
            ) : (
              <EmptyState
                type="no-data"
                title="暂无套餐"
                description="请稍后再试或联系客服"
                compact
              />
            )}

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="rounded-2xl border border-gold-500/20 bg-gold-500/5 p-6"
            >
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-slate-400">
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
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm p-6 md:p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-gold-500/10 border border-gold-500/20">
                  <Ticket className="w-6 h-6 text-gold-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">卡密兑换</h3>
                  <p className="text-sm text-slate-400">输入您的卡密，立即激活会员</p>
                </div>
              </div>

              <form onSubmit={handleRedeem} className="space-y-5">
                <Input
                  label="卡密"
                  type="text"
                  placeholder="请输入卡密（例如 SF-XXXX-XXXX-XXXX）"
                  value={redeemCode}
                  onChange={(e) => setRedeemCode(e.target.value.toUpperCase())}
                  inputClassName="font-mono tracking-wider"
                />

                <Button
                  type="submit"
                  variant="gold"
                  size="lg"
                  className="w-full"
                  isLoading={redeemLoading}
                  iconLeft={!redeemLoading && <Gift className="w-5 h-5" />}
                  disabled={redeemLoading}
                >
                  {redeemLoading ? '兑换中...' : '立即兑换'}
                </Button>
              </form>

              <div className="mt-6 pt-6 border-t border-white/10">
                <div className="text-xs text-slate-500 space-y-1.5">
                  <p>• 卡密格式：字母和数字组成，输入时自动转为大写</p>
                  <p>• 每张卡密仅可使用一次，兑换后立即生效</p>
                  <p>• 如有问题请联系客服</p>
                  <p>• 卡密由管理员批量生成，请向渠道方获取</p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm p-6 md:p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <Award className="w-6 h-6 text-gold-400" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">兑换记录</h3>
                  <p className="text-sm text-slate-400">查看您的卡密兑换历史</p>
                </div>
              </div>

              {redeemHistory.length > 0 ? (
                <div className="space-y-3">
                  {redeemHistory.map((record) => (
                    <div key={record.id} className="p-4 rounded-xl border border-white/10 bg-white/[0.03] flex items-center justify-between">
                      <div>
                        <div className="text-sm text-white font-semibold">{record.plan_name}</div>
                        <div className="text-xs text-slate-500 mt-1">开通于 {formatDate(record.redeemed_at)}</div>
                        {record.end_at && (
                          <div className="text-xs text-slate-500 mt-0.5">到期 {formatDate(record.end_at)}</div>
                        )}
                      </div>
                      <div className="text-xs text-gold-400 font-semibold">已激活</div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  type="no-data"
                  title="暂无兑换记录"
                  description="使用卡密激活会员后将显示在此处"
                  compact
                  icon={<Ticket className="w-10 h-10 text-slate-600" />}
                />
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
            className="rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-sm p-6 md:p-8"
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
    </PageShell>
  )
}
