/**
 * Orders.jsx — 我的订单
 *
 * 对应后端：portal/orders/views.py
 * 视觉：状态过滤 + 列表 + 发票申请 / 退款
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Receipt, RotateCcw, Download } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'
import { PageHeader, ToolbarSearch, DataTable, Panel } from './components'

const FILTERS = ['全部', '已支付', '待支付', '已退款']

const ORDERS = [
  { id: 'SF-2026-0616-001', item: '旗舰版续费', amount: '¥ 2,880', state: 'paid', time: '06-16 10:24' },
  { id: 'SF-2026-0616-002', item: '1000 币 充值包', amount: '¥ 198', state: 'paid', time: '06-16 09:58' },
  { id: 'SF-2026-0616-003', item: '专业版 月卡', amount: '¥ 299', state: 'pending', time: '06-16 09:12' },
  { id: 'SF-2026-0616-004', item: '体验版 → 专业版 升级', amount: '¥ 299', state: 'refunded', time: '06-16 08:46' },
  { id: 'SF-2026-0615-007', item: '500 币 充值包', amount: '¥ 89', state: 'paid', time: '06-15 22:01' },
]

function stateBadge(s) {
  if (s === 'paid') return <Badge tone="success">已支付</Badge>
  if (s === 'pending') return <Badge tone="warning">待支付</Badge>
  if (s === 'refunded') return <Badge tone="danger">已退款</Badge>
  return <Badge>{s}</Badge>
}

const cols = [
  { key: 'id', header: '订单号', render: (r) => <b className="text-white">{r.id}</b> },
  { key: 'item', header: '套餐 / 商品' },
  { key: 'amount', header: '金额', align: 'right' },
  { key: 'state', header: '状态', render: stateBadge },
  { key: 'time', header: '时间' },
  {
    key: 'actions',
    header: '操作',
    align: 'right',
    render: (r) => (
      <div className="flex justify-end gap-1.5 text-xs">
        <button className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-gold-400/40 hover:text-white">
          详情
        </button>
        {r.state === 'paid' && (
          <>
            <button className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-gold-400/40 hover:text-white">
              <Receipt className={ICON.xs} /> 发票
            </button>
            <button className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-danger-500/40 hover:text-danger-300">
              <RotateCcw className={ICON.xs} /> 退款
            </button>
          </>
        )}
        {r.state === 'refunded' && (
          <button className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-gold-400/40 hover:text-white">
            <Download className={ICON.xs} /> 凭证
          </button>
        )}
      </div>
    ),
  },
]

export default function Orders() {
  const [filter, setFilter] = useState('全部')
  return (
    <motion.div {...pageEnter} className="mx-auto max-w-7xl space-y-5 px-6 py-10">
      <PageHeader
        crumbs={[{ label: '首页', href: '/preview/home' }, { label: '我的订单' }]}
        title="我的订单"
        subtitle="支持状态过滤、退款、发票申请"
        toolbar={
          <>
            <div className="flex gap-1.5 rounded-full border border-white/10 bg-white/5 p-1">
              {FILTERS.map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setFilter(f)}
                  className={cn(
                    'rounded-full px-3 py-1.5 text-xs transition-colors',
                    filter === f ? 'bg-gold-400/15 text-white' : 'text-slate-300 hover:text-white',
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
            <ToolbarSearch placeholder="按订单号 / 商品筛选" />
            <Button variant="secondary" size="md" iconLeft={<FileText className={ICON.md} />}>
              导出
            </Button>
          </>
        }
      />

      <Panel>
        <DataTable columns={cols} rows={ORDERS} />
      </Panel>
    </motion.div>
  )
}
