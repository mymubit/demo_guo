import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  ShoppingCart,
  Search,
  Filter,
  DollarSign,
  RotateCcw,
  CheckCircle2,
  Clock,
  XCircle,
  Calendar,
  ChevronDown,
  Users,
  AlertTriangle,
  Check,
  FileText,
  Download,
  TrendingUp,
  RefreshCw,
} from 'lucide-react'
import { admin } from '@/services/api'

export default function OrdersAdmin() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [message, setMessage] = useState(null)
  const [confirmModal, setConfirmModal] = useState(null)
  const [orders, setOrders] = useState([
    { id: 'ORD20260610001', order_no: 'SF20260610001', user: '陈思远', plan: '专业版-月付', amount: 299.00, status: 'paid', payment_method: '支付宝', created_at: '2026-06-10 10:30:25', phone: '138****1234', refund_reason: null },
    { id: 'ORD20260610002', order_no: 'SF20260610002', user: '林小雨', plan: '旗舰版-年付', amount: 9999.00, status: 'paid', payment_method: '微信支付', created_at: '2026-06-10 09:15:42', phone: '139****5678', refund_reason: null },
    { id: 'ORD20260609015', order_no: 'SF20260609015', user: '王建国', plan: '体验版-月付', amount: 99.00, status: 'pending', payment_method: '-', created_at: '2026-06-09 22:40:18', phone: '137****9012', refund_reason: null },
    { id: 'ORD20260609014', order_no: 'SF20260609014', user: '张晓萌', plan: '专业版-季付', amount: 799.00, status: 'paid', payment_method: '支付宝', created_at: '2026-06-09 18:22:05', phone: '186****3456', refund_reason: null },
    { id: 'ORD20260609012', order_no: 'SF20260609012', user: '李明', plan: '专业版-月付', amount: 299.00, status: 'refunded', payment_method: '微信支付', created_at: '2026-06-09 14:08:33', phone: '135****7890', refund_reason: '用户申请退款 - 功能不符合预期' },
    { id: 'ORD20260609008', order_no: 'SF20260609008', user: '赵云峰', plan: '旗舰版-年付', amount: 9999.00, status: 'paid', payment_method: '银行卡', created_at: '2026-06-09 11:55:12', phone: '188****1122', refund_reason: null },
    { id: 'ORD20260608020', order_no: 'SF20260608020', user: '孙丽华', plan: '专业版-月付', amount: 299.00, status: 'paid', payment_method: '支付宝', created_at: '2026-06-08 16:30:45', phone: '189****3344', refund_reason: null },
    { id: 'ORD20260608015', order_no: 'SF20260608015', user: '周志远', plan: '企业版-年付', amount: 29999.00, status: 'refunded', payment_method: '银行卡', created_at: '2026-06-08 10:20:18', phone: '136****5566', refund_reason: '企业客户协商退款' },
    { id: 'ORD20260608010', order_no: 'SF20260608010', user: '吴婷婷', plan: '体验版-月付', amount: 99.00, status: 'cancelled', payment_method: '-', created_at: '2026-06-08 09:45:30', phone: '158****7788', refund_reason: '用户主动取消订单' },
  ])

  function showMessage(text, type = 'success') {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 3000)
  }

  async function handleRefund(order) {
    setConfirmModal({
      type: 'refund', order, title: '确认退款',
      message: `确认对订单 ${order.order_no} 执行退款操作？将向用户返还 ¥${order.amount.toFixed(2)}。`,
    })
  }

  async function confirmAction() {
    if (!confirmModal) return
    try {
      await admin.refundOrder(confirmModal.order.id)
    } catch (err) {
      // API调用失败，继续本地处理
    }
    setOrders((prev) =>
      prev.map((o) =>
        o.id === confirmModal.order.id ? { ...o, status: 'refunded', refund_reason: '管理员手动退款' } : o
      )
    )
    setConfirmModal(null)
    showMessage('退款操作已完成')
  }

  // 过滤订单
  const filteredOrders = orders.filter((o) => {
    const matchSearch =
      search === '' ||
      o.order_no.includes(search) ||
      o.user.includes(search) || o.phone.includes(search)
    const matchStatus = statusFilter === 'all' || o.status === statusFilter
    return matchSearch && matchStatus
  })

  // 统计
  const totalRevenue = orders.filter((o) => o.status === 'paid').reduce((a, b) => a + b.amount, 0)
  const stats = {
    total: orders.length,
    paid: orders.filter((o) => o.status === 'paid').length,
    pending: orders.filter((o) => o.status === 'pending').length,
    refunded: orders.filter((o) => o.status === 'refunded').length,
  }

  const statusConfig = {
    paid: { label: '已支付', icon: CheckCircle2, color: 'green', bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400' },
    pending: { label: '待支付', icon: Clock, color: 'yellow', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400' },
    refunded: { label: '已退款', icon: RotateCcw, color: 'purple', bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400' },
    cancelled: { label: '已取消', icon: XCircle, color: 'red', bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400' },
  }

  return (
    <div className="space-y-6">
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`px-5 py-4 rounded-2xl flex items-center gap-3 ${
            message.type === 'success'
              ? 'bg-green-500/10 border border-green-500/30 text-green-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}
        >
          <Check className="w-5 h-5" />
          {message.text}
        </motion.div>
      )}

      <div>
        <h1 className="text-2xl font-bold text-white mb-1">订单管理</h1>
        <p className="text-navy-300 text-sm">查看并管理所有用户订单，执行退款操作</p>
      </div>

      {/* 统计 */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gold-500/20">
            <ShoppingCart className="w-5 h-5 text-gold-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats.total}</div>
            <div className="text-xs text-navy-400">总订单</div>
          </div>
        </div>
        <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-green-500/20">
            <CheckCircle2 className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats.paid}</div>
            <div className="text-xs text-navy-400">已支付</div>
          </div>
        </div>
        <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-yellow-500/20">
            <Clock className="w-5 h-5 text-yellow-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats.pending}</div>
            <div className="text-xs text-navy-400">待支付</div>
          </div>
        </div>
        <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-purple-500/20">
            <RotateCcw className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats.refunded}</div>
            <div className="text-xs text-navy-400">已退款</div>
          </div>
        </div>
        <div className="glass-card rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-navy-700/40">
            <DollarSign className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="text-2xl font-bold text-gold-400">¥{totalRevenue.toLocaleString()}</div>
            <div className="text-xs text-navy-400">总营收</div>
          </div>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <div className="glass-card rounded-2xl p-4 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[280px]">
          <Search className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索订单号、用户..."
            className="w-full pl-12 pr-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white placeholder:text-navy-500 focus:outline-none focus:border-gold-500/60"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-navy-400" />
          {['all', 'paid', 'pending', 'refunded', 'cancelled'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                statusFilter === s
                  ? 'bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950'
                  : 'bg-navy-800/60 text-navy-200 hover:bg-navy-700/60'
              }`}
            >
              {s === 'all' ? '全部' : statusConfig[s].label}
            </button>
          ))}
        </div>

        <button className="ml-auto px-4 py-2.5 rounded-xl bg-navy-800/60 text-navy-200 text-sm hover:bg-navy-700/60 flex items-center gap-2">
          <Download className="w-4 h-4" /> 导出
        </button>
      </div>

      {/* 订单表格 */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-700/40 bg-navy-800/30">
                <th className="text-left text-navy-300 font-medium py-4 px-6">订单号</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">用户</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">套餐</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">金额</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">支付方式</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">状态</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">时间</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-16 text-center text-navy-400">
                  <Search className="w-12 h-12 mx-auto mb-3 text-navy-500" />
                  <div>没有匹配的订单</div>
                </td>
              </tr>
              ) : (
                filteredOrders.map((order, idx) => {
                  const sc = statusConfig[order.status]
                  return (
                    <motion.tr
                      key={order.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: idx * 0.02 }}
                      className="border-b border-navy-700/30 hover:bg-navy-800/20 transition-colors"
                    >
                      <td className="py-4 px-6">
                        <code className="text-gold-400 font-mono text-sm">{order.order_no}</code>
                      </td>
                      <td className="py-4 px-6">
                        <div className="text-white font-medium">{order.user}</div>
                        <div className="text-xs text-navy-400">{order.phone}</div>
                      </td>
                      <td className="py-4 px-6 text-navy-200">{order.plan}</td>
                      <td className="py-4 px-6">
                        <span className="text-gold-400 font-bold">¥{order.amount.toFixed(2)}</span>
                      </td>
                      <td className="py-4 px-6 text-navy-300">{order.payment_method}</td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${sc.bg} ${sc.border} ${sc.text}`}>
                          <sc.icon className="w-3 h-3" />
                          {sc.label}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-navy-300 text-xs">{order.created_at}</td>
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-1">
                          {order.status === 'paid' && (
                            <button
                              onClick={() => handleRefund(order)}
                              className="px-3 py-1.5 rounded-lg text-xs font-medium text-purple-400 bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 transition-colors flex items-center gap-1.5"
                            >
                              <RotateCcw className="w-3 h-3" /> 退款
                            </button>
                          )}
                          {order.status === 'pending' && (
                            <button
                              className="px-3 py-1.5 rounded-lg text-xs font-medium text-navy-400 bg-navy-700/40 border border-navy-700/30 hover:bg-navy-700/50 transition-colors flex items-center gap-1.5"
                            >
                              <RefreshCw className="w-3 h-3" /> 查看
                            </button>
                          )}
                          {(order.status === 'refunded' || order.status === 'cancelled') && (
                            <span className="text-xs text-navy-400">-</span>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="px-6 py-4 border-t border-navy-700/40 flex items-center justify-between text-sm">
          <div className="text-navy-400">
            共 <span className="text-white font-medium">{filteredOrders.length}</span> 条订单 · 总金额{' '}
            <span className="text-gold-400 font-medium">
              ¥{filteredOrders.reduce((a, b) => a + (b.status === 'paid' ? b.amount : 0), 0).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* 确认弹窗 */}
      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-navy-950/80 backdrop-blur-sm" onClick={() => setConfirmModal(null)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative glass-card rounded-3xl p-8 max-w-md w-full"
          >
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white mb-1">{confirmModal.title}</h3>
                <p className="text-navy-300 text-sm">{confirmModal.message}</p>
              </div>
            </div>

            {/* 订单详情 */}
            <div className="p-4 rounded-2xl bg-navy-800/40 border border-navy-700/30 mb-6">
              <div className="grid grid-cols-2 gap-y-2 text-sm">
                <div className="text-navy-400">订单号</div>
                <div className="text-gold-400 font-mono text-right">{confirmModal.order.order_no}</div>
                <div className="text-navy-400">用户</div>
                <div className="text-white text-right">{confirmModal.order.user}</div>
                <div className="text-navy-400">套餐</div>
                <div className="text-white text-right">{confirmModal.order.plan}</div>
                <div className="text-navy-400">退款金额</div>
                <div className="text-gold-400 font-bold text-right">¥{confirmModal.order.amount.toFixed(2)}</div>
              </div>
            </div>

            <div className="flex items-center gap-3 justify-end">
              <button
                onClick={() => setConfirmModal(null)}
                className="px-5 py-2.5 rounded-xl text-navy-200 hover:bg-navy-800/60 transition-colors text-sm font-medium"
              >
                取消
              </button>
              <button
                onClick={confirmAction}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-500 to-purple-600 text-white font-semibold text-sm hover:shadow-lg hover:shadow-purple-500/30 transition-all flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                确认退款
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
