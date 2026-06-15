import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { RotateCcw } from 'lucide-react'
import { admin } from '@/services/api'
import AdminShell from '@/components/admin/AdminShell'
import AdminDashboardHints from '@/components/admin/AdminDashboardHints'
import {
  AdminStatGrid,
  AdminToolbar,
  AdminSearchInput,
  AdminTable,
  AdminPagination,
  AdminLoading,
  AdminMessage,
  AdminConfirmDialog,
  AdminBadge,
  formatDateTime,
} from '@/components/admin/AdminUI'
import { ORDERS_PAGE_NOTE } from '@/utils/adminEconomics'

const STATUS_TABS = [
  { key: 'all', label: '全部' },
  { key: 'paid', label: '已支付' },
  { key: 'pending', label: '待支付' },
  { key: 'refunded', label: '已退款' },
  { key: 'cancelled', label: '已取消' },
]

export default function OrdersAdmin() {
  const [searchParams] = useSearchParams()
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState(() => searchParams.get('status') || 'all')
  const [page, setPage] = useState(1)
  const [orders, setOrders] = useState([])
  const [pagination, setPagination] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)
  const [confirm, setConfirm] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const loadOrders = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: 10 }
      if (keyword.trim()) params.keyword = keyword.trim()
      if (status !== 'all') params.status = status
      const res = await admin.listOrders(params)
      setOrders(res.items)
      setPagination(res.pagination)
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '加载订单失败' })
    } finally {
      setLoading(false)
    }
  }, [page, keyword, status])

  useEffect(() => {
    loadOrders()
  }, [loadOrders])

  useEffect(() => {
    const s = searchParams.get('status')
    if (s && STATUS_TABS.some((t) => t.key === s)) {
      setStatus(s)
      setPage(1)
    }
  }, [searchParams])

  const paidTotal = orders
    .filter((o) => o.status === 'paid')
    .reduce((sum, o) => sum + Number(o.amount || 0), 0)

  async function handleRefund() {
    if (!confirm?.order) return
    setActionLoading(true)
    try {
      await admin.refundOrder(confirm.order.id)
      setMessage({ type: 'success', text: '退款处理完成' })
      setConfirm(null)
      loadOrders()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '退款失败' })
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <AdminShell actions={<AdminDashboardHints scope="orders" />}>
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <p className="text-sm text-navy-400 rounded-xl border border-navy-700/40 bg-navy-900/40 px-4 py-3 mb-4">
        {ORDERS_PAGE_NOTE}
      </p>

      <AdminStatGrid
        items={[
          { label: '当前页订单', value: orders.length },
          { label: '总记录', value: pagination?.total ?? '—' },
          { label: '当前页人民币到账', value: `¥${paidTotal.toFixed(2)}`, hint: '已支付订单金额合计' },
        ]}
      />

      <AdminToolbar>
        <AdminSearchInput
          value={keyword}
          onChange={(v) => {
            setKeyword(v)
            setPage(1)
          }}
          placeholder="搜索订单号、用户手机号…"
        />
        <div className="flex flex-wrap gap-2">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => {
                setStatus(tab.key)
                setPage(1)
              }}
              className={`px-4 py-2.5 rounded-xl text-sm ${
                status === tab.key ? 'btn-gold' : 'bg-navy-800/60 text-navy-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </AdminToolbar>

      {loading ? (
        <AdminLoading />
      ) : (
        <>
          <AdminTable
            rowKey="id"
            rows={orders}
            emptyText="暂无订单"
            columns={[
              { key: 'order_no', title: '订单号' },
              { key: 'user_nickname', title: '用户', render: (r) => r.user_nickname || r.user_phone },
              { key: 'plan_name', title: '套餐' },
              { key: 'amount', title: '人民币', render: (r) => r.display_amount || `¥${r.amount}` },
              {
                key: 'status',
                title: '状态',
                render: (r) => (
                  <AdminBadge
                    tone={
                      r.status === 'paid'
                        ? 'success'
                        : r.status === 'pending'
                        ? 'warning'
                        : r.status === 'refunded'
                        ? 'danger'
                        : 'default'
                    }
                  >
                    {r.status_text || r.status}
                  </AdminBadge>
                ),
              },
              { key: 'payment_method_text', title: '支付方式', render: (r) => r.payment_method_text || r.payment_method },
              { key: 'created_at', title: '创建时间', render: (r) => formatDateTime(r.created_at) },
              {
                key: 'actions',
                title: '操作',
                render: (r) =>
                  r.status === 'paid' ? (
                    <button
                      type="button"
                      onClick={() =>
                        setConfirm({
                          order: r,
                          title: '确认退款',
                          message: `订单 ${r.order_no}，金额 ${r.display_amount || r.amount}，确认退款？`,
                        })
                      }
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 text-sm"
                    >
                      <RotateCcw className="w-4 h-4" />
                      退款
                    </button>
                  ) : (
                    '—'
                  ),
              },
            ]}
          />
          <AdminPagination
            page={pagination?.page || page}
            totalPages={pagination?.total_pages || 1}
            total={pagination?.total || 0}
            onPageChange={setPage}
          />
        </>
      )}

      <AdminConfirmDialog
        open={!!confirm}
        title={confirm?.title}
        message={confirm?.message}
        confirmText="确认退款"
        loading={actionLoading}
        onCancel={() => setConfirm(null)}
        onConfirm={handleRefund}
      />
    </AdminShell>
  )
}
