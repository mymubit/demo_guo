import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { RefreshCw } from 'lucide-react'
import { orders as ordersApi } from '@/services/api'
import OrdersListPanel from '@/components/orders/OrdersListPanel'
import { Button } from '@/components/ui'
import PageShell from '@/components/layout/PageShell'
import EmptyState from '@/components/ui/EmptyState'
import { cn } from '@/utils/cn'

const FILTER_OPTIONS = [
  { key: 'all', label: '全部' },
  { key: 'paid', label: '已支付' },
  { key: 'pending', label: '待支付' },
  { key: 'cancelled', label: '已取消' },
  { key: 'refunded', label: '已退款' },
]

export default function OrdersPage() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [orderActionLoading, setOrderActionLoading] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const pageSize = 10

  const statusParam = filter === 'all' ? undefined : filter
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['orders', statusParam ?? 'all', page],
    queryFn: () => ordersApi.list(statusParam, { page, pageSize }),
  })
  const orders = data?.items ?? []
  const pagination = data?.pagination ?? { page: 1, total_pages: 1, total: 0 }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await refetch()
      toast.success('订单列表已刷新')
    } catch {
      toast.error('刷新失败')
    } finally {
      setRefreshing(false)
    }
  }

  const copyOrderNo = (no) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(no)
      toast.success('订单号已复制')
    } else {
      toast.success(`订单号：${no}`)
    }
  }

  const handlePayOrder = async (orderNo) => {
    if (orderActionLoading) return
    setOrderActionLoading(orderNo)
    try {
      await ordersApi.mockPay(orderNo)
      toast.success('支付成功')
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['orders'] }),
        queryClient.invalidateQueries({ queryKey: ['myMembershipBundle'] }),
      ])
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
      await queryClient.invalidateQueries({ queryKey: ['orders'] })
    } catch (err) {
      toast.error(err.message || '取消失败')
    } finally {
      setOrderActionLoading(null)
    }
  }

  return (
    <PageShell
      title="我的订单"
      description={`共 ${pagination.total} 条订单记录`}
      backTo="/"
      maxWidth="4xl"
      actions={
        <Button
          variant="secondary"
          iconLeft={<RefreshCw className={`w-4 h-4 ${refreshing || isFetching ? 'animate-spin' : ''}`} />}
          onClick={handleRefresh}
          disabled={refreshing || isFetching}
        >
          刷新
        </Button>
      }
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex gap-1 bg-white/5 p-1 rounded-xl border border-white/10 mb-6 overflow-x-auto">
          {FILTER_OPTIONS.map((item) => (
            <button
              key={item.key}
              onClick={() => {
                setFilter(item.key)
                setPage(1)
              }}
              className={cn(
                'px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-all',
                filter === item.key
                  ? 'bg-gold-500 text-navy-950 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              )}
            >
              {item.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20 gap-2 text-slate-400">
            <RefreshCw className="w-5 h-5 animate-spin text-gold-400" />
            加载订单…
          </div>
        ) : orders.length === 0 ? (
          <EmptyState
            title="暂无订单记录"
            description={filter === 'all' ? '你还没有任何订单，去充值会员或创作币开始创作吧' : `暂无${FILTER_OPTIONS.find(o => o.key === filter)?.label}订单`}
            actionLabel="去充值"
            onAction={() => window.location.href = '/wallet'}
          />
        ) : (
          <>
            <OrdersListPanel
              orders={orders}
              orderActionLoading={orderActionLoading}
              onCopyOrderNo={copyOrderNo}
              onPayOrder={handlePayOrder}
              onCancelOrder={handleCancelOrder}
              showHeader={false}
              emptyAction={() => window.location.href = '/wallet'}
            />

            {pagination.total_pages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-6 pb-8">
                <button
                  type="button"
                  disabled={page <= 1 || isFetching}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-white/[0.06] hover:text-white disabled:opacity-40"
                >
                  上一页
                </button>
                <span className="text-sm text-slate-500 tabular-nums">
                  第 {page} / {pagination.total_pages} 页
                </span>
                <button
                  type="button"
                  disabled={page >= pagination.total_pages || isFetching}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-white/[0.06] hover:text-white disabled:opacity-40"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </motion.div>
    </PageShell>
  )
}
