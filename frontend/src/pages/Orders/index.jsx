import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { orders as ordersApi } from '@/services/api'
import { SectionHeader, PillFilterGroup, PageContainer } from '@/components/shared/ConsumerSection'
import OrdersListPanel from '@/components/orders/OrdersListPanel'
import { PageLoading } from '@/components/ui'
import { pageEnter } from '@/constants/motion'

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
  const pageSize = 10

  const statusParam = filter === 'all' ? undefined : filter
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['orders', statusParam ?? 'all', page],
    queryFn: () => ordersApi.list(statusParam, { page, pageSize }),
  })
  const orders = data?.items ?? []
  const pagination = data?.pagination ?? { page: 1, total_pages: 1, total: 0 }

  const filterOptions = useMemo(() => FILTER_OPTIONS.map((item) => item.label), [])
  const filterLabel = FILTER_OPTIONS.find((item) => item.key === filter)?.label ?? '全部'

  const handleRefresh = async () => {
    try {
      await refetch()
      toast.success('订单列表已刷新')
    } catch {
      toast.error('刷新失败')
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

  if (isLoading) {
    return (
      <div className="min-h-screen py-24">
        <PageLoading label="加载订单…" />
      </div>
    )
  }

  return (
    <motion.div {...pageEnter} className="relative min-h-screen py-12">
      <PageContainer width="7xl" className="py-12">
        <SectionHeader
          eyebrow="订单"
          title="我的订单"
          subtitle="支持按状态筛选，待支付订单可在此完成支付或取消"
          className="mb-6"
        />

        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <PillFilterGroup
            options={filterOptions}
            value={filterLabel}
            onChange={(label) => {
              const next = FILTER_OPTIONS.find((item) => item.label === label)
              if (next) {
                setFilter(next.key)
                setPage(1)
              }
            }}
          />
          <Link
            to="/member"
            className="inline-flex h-9 items-center gap-1 rounded-xl border border-gray-200 px-3 text-xs text-gray-600 transition-colors hover:bg-white/5"
          >
            会员中心
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white border border-gray-200 p-6 md:p-8">
          <OrdersListPanel
            orders={orders}
            orderActionLoading={orderActionLoading}
            onCopyOrderNo={copyOrderNo}
            onPayOrder={handlePayOrder}
            onCancelOrder={handleCancelOrder}
            onRefresh={handleRefresh}
            refreshing={isFetching}
            emptyAction={
              <Link
                to="/member"
                className="inline-flex h-9 items-center gap-1 rounded-xl bg-gradient-to-r from-gold-300 to-gold-500 px-3 text-xs font-semibold text-navy-950"
              >
                去选购套餐
                <ChevronRight className="h-4 w-4" />
              </Link>
            }
          />
          {pagination.total_pages > 1 && (
            <div className="mt-6 flex items-center justify-between gap-3 text-sm text-gray-500">
              <span>
                第 {pagination.page} / {pagination.total_pages} 页 · 共 {pagination.total} 条
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={pagination.page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded-lg border border-gray-200 px-3 py-1.5 disabled:opacity-40"
                >
                  上一页
                </button>
                <button
                  type="button"
                  disabled={pagination.page >= pagination.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                  className="rounded-lg border border-gray-200 px-3 py-1.5 disabled:opacity-40"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </div>
      </PageContainer>
    </motion.div>
  )
}
