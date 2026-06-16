import { Copy, RefreshCw, ShoppingBag } from 'lucide-react'
import { Link } from 'react-router-dom'
import { formatDate } from '@/utils/date'
import { Button, EmptyState } from '@/components/ui'
import OrderStatusBadge from './OrderStatusBadge'

export default function OrdersListPanel({
  orders = [],
  orderActionLoading = null,
  onCopyOrderNo,
  onPayOrder,
  onCancelOrder,
  onRefresh,
  refreshing = false,
  showHeader = true,
  emptyAction,
  className = '',
}) {
  return (
    <div className={className}>
      {showHeader ? (
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-700/50">
              <ShoppingBag className="h-6 w-6 text-gold-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">我的订单</h3>
              <p className="text-sm text-navy-300">共 {orders.length} 条订单记录</p>
            </div>
          </div>
          {onRefresh ? (
            <button
              type="button"
              onClick={onRefresh}
              disabled={refreshing}
              className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5 text-navy-300 transition-all hover:border-white/20 hover:text-white disabled:opacity-50"
            >
              <RefreshCw className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          ) : null}
        </div>
      ) : null}

      <div className="space-y-3 md:hidden">
        {orders.map((order) => (
          <div
            key={order.id || order.order_no}
            className="rounded-2xl border border-white/5 bg-slate-900/40 p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <button
                  type="button"
                  onClick={() => onCopyOrderNo?.(order.order_no)}
                  className="flex max-w-full items-center gap-1.5 truncate font-mono text-sm text-white hover:text-gold-400"
                >
                  <span className="truncate">{order.order_no}</span>
                  <Copy className="h-3.5 w-3.5 shrink-0 text-navy-400" />
                </button>
                <p className="mt-1 text-xs text-navy-400">创建于 {formatDate(order.created_at)}</p>
              </div>
              <OrderStatusBadge status={order.status} />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs text-navy-400">套餐</p>
                <p className="mt-1 font-semibold text-white">{order.plan_name}</p>
              </div>
              <div>
                <p className="text-xs text-navy-400">金额</p>
                <p className="mt-1 text-lg font-bold gradient-text">¥{order.amount}</p>
              </div>
              <div className="col-span-2">
                <p className="text-xs text-navy-400">支付时间</p>
                <p className="mt-1 text-navy-300">{order.paid_at ? formatDate(order.paid_at) : '-'}</p>
              </div>
            </div>
            {order.status === 'pending' && (
              <div className="mt-4 grid grid-cols-2 gap-2">
                <Button
                  size="sm"
                  variant="gold"
                  isLoading={orderActionLoading === order.order_no}
                  onClick={() => onPayOrder?.(order.order_no)}
                >
                  去支付
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={orderActionLoading === order.order_no}
                  onClick={() => onCancelOrder?.(order.order_no)}
                >
                  取消
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="hidden overflow-hidden rounded-2xl border border-white/5 bg-slate-900/40 md:block">
        <div className="overflow-x-auto overscroll-x-contain">
          <table className="w-full min-w-[700px]">
            <thead>
              <tr className="border-b border-white/5">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-navy-400">
                  订单信息
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-navy-400">
                  套餐
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-navy-400">
                  金额
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-navy-400">
                  状态
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-navy-400">
                  时间
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-navy-400">
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id || order.order_no} className="border-b border-white/5 transition-colors hover:bg-white/[0.03]">
                  <td className="px-4 py-5">
                    <button
                      type="button"
                      onClick={() => onCopyOrderNo?.(order.order_no)}
                      className="flex cursor-pointer items-center gap-1.5 font-mono text-sm text-white transition-colors hover:text-gold-400"
                    >
                      {order.order_no}
                      <Copy className="h-3.5 w-3.5 text-navy-400" />
                    </button>
                    <div className="mt-1 text-xs text-navy-400">创建于 {formatDate(order.created_at)}</div>
                  </td>
                  <td className="px-4 py-5 text-sm font-semibold text-white">{order.plan_name}</td>
                  <td className="px-4 py-5">
                    <span className="text-lg font-bold gradient-text">¥{order.amount}</span>
                  </td>
                  <td className="px-4 py-5">
                    <OrderStatusBadge status={order.status} />
                  </td>
                  <td className="px-4 py-5 text-sm text-navy-300">
                    {order.paid_at ? formatDate(order.paid_at) : '-'}
                  </td>
                  <td className="px-4 py-5">
                    {order.status === 'pending' && (
                      <div className="flex gap-2">
                        <button
                          type="button"
                          disabled={orderActionLoading === order.order_no}
                          onClick={() => onPayOrder?.(order.order_no)}
                          className="rounded-lg bg-gold-400 px-3 py-1.5 text-xs font-semibold text-navy-950 hover:bg-gold-300 disabled:opacity-50"
                        >
                          {orderActionLoading === order.order_no ? '处理中' : '去支付'}
                        </button>
                        <button
                          type="button"
                          disabled={orderActionLoading === order.order_no}
                          onClick={() => onCancelOrder?.(order.order_no)}
                          className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-300 hover:bg-white/[0.05] hover:text-white disabled:opacity-50"
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
      </div>

      {orders.length === 0 && (
        <EmptyState
          compact
          icon={ShoppingBag}
          title="暂无订单记录"
          description="购买套餐或充值后将显示在此处"
          action={
            emptyAction || (
              <Link to="/member" className="inline-flex h-9 items-center rounded-xl bg-gradient-to-r from-gold-300 to-gold-500 px-3 text-xs font-semibold text-navy-950">
                去会员中心
              </Link>
            )
          }
          className="mt-4"
        />
      )}
    </div>
  )
}
