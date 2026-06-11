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
 *       返回：{ plan, plan_name, is_active, expires_at, creation_quota_used,
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
import { useState, useEffect } from 'react'
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
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { memberApi, orderApi } from '@/services/api'

const PLANS = [
  {
    id: 'basic',
    name: '体验版',
    price: 29,
    originalPrice: 59,
    period: '月',
    creation_quota: 3,
    validity: 30,
    features: [
      '3 次完整剧本创作',
      '8 大题材模板',
      'Markdown 格式导出',
      '基础质量审查',
      '7 天作品云端保存',
    ],
    highlight: false,
    badge: '入门',
  },
  {
    id: 'pro',
    name: '专业版',
    price: 99,
    originalPrice: 299,
    period: '月',
    creation_quota: 20,
    validity: 30,
    features: [
      '20 次完整剧本创作',
      '所有题材模板 + 定制',
      '4 种格式变体导出',
      '高级质量审查评分',
      '30 天作品云端保存',
      '优先创作队列',
      '作品分享链接',
    ],
    highlight: true,
    badge: '🔥 最受欢迎',
  },
  {
    id: 'ultimate',
    name: '旗舰版',
    price: 999,
    originalPrice: 1999,
    period: '年',
    creation_quota: -1,
    validity: 365,
    features: [
      '无限次剧本创作',
      '所有题材 + 定制模板',
      '完整格式 + PDF + DOCX',
      'S 级质量审查与优化建议',
      '永久作品云端保存',
      '最高优先级队列',
      '高级分享与水印',
      '专属客服支持',
      '团队协作功能',
    ],
    highlight: false,
    badge: '专业团队',
  },
]

const MOCK_ORDERS = [
  {
    id: 'ORD-20250610-001',
    plan_name: '专业版',
    amount: 99,
    status: 'paid',
    created_at: '2025-06-10 14:23:11',
    paid_at: '2025-06-10 14:23:45',
    order_no: 'SF202506100001',
  },
  {
    id: 'ORD-20250528-002',
    plan_name: '体验版',
    amount: 29,
    status: 'paid',
    created_at: '2025-05-28 09:15:32',
    paid_at: '2025-05-28 09:16:01',
    order_no: 'SF202505280002',
  },
  {
    id: 'ORD-20250515-003',
    plan_name: '旗舰版',
    amount: 999,
    status: 'paid',
    created_at: '2025-05-15 20:45:08',
    paid_at: '2025-05-15 20:45:49',
    order_no: 'SF202505150003',
  },
  {
    id: 'ORD-20250501-004',
    plan_name: '专业版',
    amount: 99,
    status: 'pending',
    created_at: '2025-05-01 11:22:33',
    paid_at: null,
    order_no: 'SF202505010004',
  },
]

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return dateStr.replace('T', ' ').substring(0, 16)
}

function daysUntil(dateStr) {
  if (!dateStr) return 0
  const target = new Date(dateStr.replace(/-/g, '/')).getTime()
  const now = Date.now()
  return Math.max(0, Math.ceil((target - now) / (1000 * 60 * 60 * 24)))
}

export default function Member() {
  const { user } = useAuthStore()
  const [membership, setMembership] = useState(null)
  const [plans, setPlans] = useState(PLANS)
  const [orders, setOrders] = useState(MOCK_ORDERS)
  const [redeemCode, setRedeemCode] = useState('')
  const [redeemLoading, setRedeemLoading] = useState(false)
  const [payLoading, setPayLoading] = useState({})
  const [tab, setTab] = useState('plans')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [m, p, o] = await Promise.all([
          memberApi.getMyMembership().catch(() => null),
          memberApi.getPlans().catch(() => null),
          orderApi.list().catch(() => null),
        ])
        if (m) setMembership(m)
        else {
          setMembership({
            plan: 'free',
            plan_name: '免费用户',
            is_active: false,
            expires_at: null,
            creation_quota_used: 0,
            creation_quota_total: 0,
            redeemed_codes: [],
          })
        }
        if (p && Array.isArray(p) && p.length) setPlans(p)
        if (o && Array.isArray(o) && o.length) setOrders(o)
      } catch (e) {
        // ignore
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleRedeem = async (e) => {
    e.preventDefault()
    const code = redeemCode.trim().toUpperCase()
    if (!code) {
      toast.error('请输入卡密')
      return
    }
    setRedeemLoading(true)
    try {
      await memberApi.redeemCode(code)
      toast.success('卡密兑换成功！会员权益已激活')
      setMembership((m) => ({
        ...m,
        plan: 'pro',
        plan_name: '专业版（卡密激活）',
        is_active: true,
        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().replace('T', ' ').substring(0, 19),
        creation_quota_total: (m?.creation_quota_total || 0) + 20,
      }))
      setRedeemCode('')
    } catch (err) {
      toast.success('演示模式：卡密兑换成功！')
      setMembership((m) => ({
        ...m,
        plan: 'pro',
        plan_name: '专业版（卡密激活）',
        is_active: true,
        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().replace('T', ' ').substring(0, 19),
        creation_quota_total: (m?.creation_quota_total || 0) + 20,
      }))
      setRedeemCode('')
    } finally {
      setRedeemLoading(false)
    }
  }

  const handlePurchase = async (planId) => {
    setPayLoading((p) => ({ ...p, [planId]: true }))
    try {
      const order = await orderApi.create(planId)
      const orderNo = order?.order_no || `SF${Date.now()}`
      try {
        await orderApi.mockPay(orderNo)
        toast.success('演示支付成功！会员已激活')
      } catch (payErr) {
        toast.success('演示支付成功！')
      }
      const plan = plans.find((p) => p.id === planId) || PLANS.find((p) => p.id === planId)
      const now = new Date()
      setMembership((m) => ({
        ...m,
        plan: planId,
        plan_name: plan?.name || '会员',
        is_active: true,
        expires_at: new Date(now.getTime() + (plan?.validity || 30) * 24 * 60 * 60 * 1000).toISOString().replace('T', ' ').substring(0, 19),
        creation_quota_total: (m?.creation_quota_total || 0) + (plan?.creation_quota === -1 ? 9999 : plan?.creation_quota || 0),
      }))
      setOrders((prev) => [
        {
          id: `ORD-${Date.now()}`,
          plan_name: plan?.name || '会员',
          amount: plan?.price || 0,
          status: 'paid',
          created_at: now.toISOString().replace('T', ' ').substring(0, 19),
          paid_at: now.toISOString().replace('T', ' ').substring(0, 19),
          order_no: orderNo,
        },
        ...prev,
      ])
    } catch (err) {
      const plan = plans.find((p) => p.id === planId) || PLANS.find((p) => p.id === planId)
      const now = new Date()
      toast.success('演示模式：订单创建成功！')
      setMembership((m) => ({
        ...m,
        plan: planId,
        plan_name: plan?.name || '会员',
        is_active: true,
        expires_at: new Date(now.getTime() + (plan?.validity || 30) * 24 * 60 * 60 * 1000).toISOString().replace('T', ' ').substring(0, 19),
        creation_quota_total: (m?.creation_quota_total || 0) + (plan?.creation_quota === -1 ? 9999 : plan?.creation_quota || 0),
      }))
      setOrders((prev) => [
        {
          id: `ORD-${Date.now()}`,
          plan_name: plan?.name || '会员',
          amount: plan?.price || 0,
          status: 'paid',
          created_at: now.toISOString().replace('T', ' ').substring(0, 19),
          paid_at: now.toISOString().replace('T', ' ').substring(0, 19),
          order_no: `SF${Date.now()}`,
        },
        ...prev,
      ])
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

  const remainingDays = membership?.expires_at ? daysUntil(membership.expires_at) : 0
  const quotaPercent = membership && membership.creation_quota_total > 0
    ? Math.min(100, ((membership.creation_quota_total - membership.creation_quota_used) / membership.creation_quota_total) * 100)
    : 0
  const remainingQuota = membership
    ? Math.max(0, membership.creation_quota_total - membership.creation_quota_used)
    : 0

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
          <p className="text-navy-300 text-lg">
            你好，<span className="text-white font-semibold">{user?.nickname || user?.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') || '创作者'}</span>
            ，解锁专业能力，让创意腾飞
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
            background: membership?.is_active
              ? 'linear-gradient(135deg, rgba(244, 183, 25, 0.15) 0%, rgba(253, 160, 133, 0.1) 50%, rgba(102, 126, 234, 0.1) 100%)'
              : 'linear-gradient(135deg, rgba(15, 42, 92, 0.6) 0%, rgba(15, 42, 92, 0.3) 100%)',
            border: membership?.is_active ? '1px solid rgba(244, 183, 25, 0.35)' : '1px solid rgba(102, 126, 234, 0.2)',
            backdropFilter: 'blur(20px)',
            boxShadow: membership?.is_active ? '0 20px 60px -20px rgba(244, 183, 25, 0.3)' : 'none',
          }}>
            {/* 装饰 */}
            <div className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-30 blur-3xl pointer-events-none"
              style={{ background: membership?.is_active ? 'radial-gradient(circle, #f4b719 0%, transparent 70%)' : 'radial-gradient(circle, #667eea 0%, transparent 70%)' }} />

            <div className="relative z-10 flex flex-col md:flex-row gap-8 md:gap-12 items-start md:items-center">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  {membership?.is_active ? (
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold text-navy-950"
                      style={{ background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)' }}>
                      <Crown className="w-4 h-4" />
                      {membership.plan_name || '会员'}
                    </div>
                  ) : (
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold text-navy-200 bg-navy-700/50 border border-navy-600/40">
                      <Gift className="w-4 h-4" />
                      {membership?.plan_name || '免费用户'}
                    </div>
                  )}
                  {membership?.is_active && (
                    <span className="inline-flex items-center gap-1.5 text-sm text-gold-300">
                      <Flame className="w-4 h-4" /> 剩余 {remainingDays} 天
                    </span>
                  )}
                </div>

                <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
                  {membership?.is_active ? (
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
                        <FileText className="w-4 h-4" /> 剩余创作次数
                      </div>
                    </div>
                    <div className="text-3xl font-bold text-white mb-3">
                      {membership?.creation_quota_total === 9999 || membership?.creation_quota === -1 ? (
                        <span className="gradient-text">∞</span>
                      ) : (
                        <>
                          <span className="gradient-text">{remainingQuota}</span>
                          <span className="text-navy-400 text-lg font-normal"> / {membership?.creation_quota_total || 0}</span>
                        </>
                      )}
                    </div>
                    {(membership?.creation_quota_total && membership.creation_quota_total < 9999) && (
                      <div className="h-1.5 rounded-full bg-navy-800 overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-500"
                          style={{ width: `${quotaPercent}%`, background: 'linear-gradient(90deg, #f6d365 0%, #fda085 100%)' }} />
                      </div>
                    )}
                  </div>

                  {/* 到期时间 */}
                  <div className="p-5 rounded-2xl bg-navy-900/40 border border-navy-600/30">
                    <div className="text-sm text-navy-300 flex items-center gap-1.5 mb-3">
                      <Calendar className="w-4 h-4" /> 会员到期时间
                    </div>
                    <div className="text-xl font-bold text-white mb-1">
                      {membership?.is_active ? formatDate(membership.expires_at) : '未开通'}
                    </div>
                    {membership?.is_active && (
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
                      {membership?.is_active ? '全部解锁' : '基础功能'}
                    </div>
                    <div className="text-xs text-navy-300">
                      {membership?.is_active ? '所有模板和格式可用' : '仅使用免费模板'}
                    </div>
                  </div>
                </div>
              </div>

              {/* 右侧图标 */}
              <div className="hidden md:flex flex-col items-center">
                <div className="relative w-32 h-32 rounded-3xl flex items-center justify-center"
                  style={{
                    background: membership?.is_active
                      ? 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)'
                      : 'linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%)',
                    boxShadow: membership?.is_active ? '0 20px 40px -10px rgba(244, 183, 25, 0.4)' : 'none',
                  }}>
                  <Crown className={`w-16 h-16 ${membership?.is_active ? 'text-navy-950' : 'text-gold-400'}`} />
                </div>
                {!membership?.is_active && (
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
                      <h3 className={`text-2xl font-bold mb-2 ${plan.highlight ? 'gradient-text' : 'text-white'}`}>
                        {plan.name}
                      </h3>
                      <p className="text-sm text-navy-300">
                        {plan.creation_quota === -1 ? '无限剧本创作' : `${plan.creation_quota} 次剧本创作`}
                      </p>
                    </div>

                    <div className="flex items-baseline gap-1 mb-6">
                      <span className="text-5xl font-bold text-white">¥{plan.price}</span>
                      <span className="text-navy-400">/{plan.period}</span>
                      {plan.originalPrice && (
                        <span className="ml-2 text-sm text-navy-500 line-through">¥{plan.originalPrice}</span>
                      )}
                    </div>

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
                    <p>• <span className="text-gold-400">演示提示：任意输入即可模拟成功兑换</span></p>
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

                {membership?.redeemed_codes && membership.redeemed_codes.length > 0 ? (
                  <div className="space-y-3">
                    {membership.redeemed_codes.map((code, idx) => (
                      <div key={idx} className="p-4 rounded-xl bg-navy-900/40 border border-navy-600/30 flex items-center justify-between">
                        <div>
                          <div className="font-mono text-sm text-white">{code.code}</div>
                          <div className="text-xs text-navy-400 mt-1">{formatDate(code.redeemed_at)}</div>
                        </div>
                        <div className="text-xs text-gold-400 font-semibold">{code.plan_name}</div>
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
                    <p className="text-sm text-navy-300">共 {orders.length} 条订单记录</p>
                  </div>
                </div>
                <button
                  onClick={() => toast.info('已刷新订单列表')}
                  className="p-2.5 rounded-xl bg-navy-800/50 border border-navy-600/30 text-navy-300 hover:text-white hover:border-navy-500/40 transition-all">
                  <RefreshCw className="w-5 h-5" />
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[600px]">
                  <thead>
                    <tr className="border-b border-navy-600/30">
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">订单信息</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">套餐</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">金额</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">状态</th>
                      <th className="text-left py-3 px-4 text-xs font-semibold text-navy-400 uppercase tracking-wider">时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order, idx) => (
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
                          {order.status === 'paid' ? (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-green-400 bg-green-500/10 border border-green-500/30">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              已支付
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-orange-400 bg-orange-500/10 border border-orange-500/30">
                              <Clock className="w-3.5 h-3.5" />
                              待支付
                            </span>
                          )}
                        </td>
                        <td className="py-5 px-4 text-sm text-navy-300">
                          {order.paid_at ? formatDate(order.paid_at) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {orders.length === 0 && (
                <div className="text-center py-16">
                  <ShoppingBag className="w-16 h-16 text-navy-600 mx-auto mb-4" />
                  <p className="text-navy-300 mb-1">暂无订单记录</p>
                  <button
                    onClick={() => setTab('plans')}
                    className="text-gold-400 text-sm font-semibold hover:text-gold-300 transition-colors inline-flex items-center gap-1 mt-2">
                    去选购套餐 <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
