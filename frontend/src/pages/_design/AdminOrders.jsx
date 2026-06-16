/**
 * AdminOrders.jsx — 后台订单管理
 *
 * 对应后端：console/commerce/order_views.py
 */
import { motion } from 'framer-motion'
import { RefreshCcw, Download, FileText, Check } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, ToolbarSearch, Panel, DataTable } from './components'

const ORDERS = [
  { id: 'SF-2026-0616-001', user: '陈导', plan: '旗舰版续费', amount: 2880, state: 'paid', time: '06-16 10:24' },
  { id: 'SF-2026-0616-002', user: '林编剧', plan: '1000 币 充值包', amount: 198, state: 'paid', time: '06-16 09:58' },
  { id: 'SF-2026-0616-003', user: '匿名', plan: '专业版 月卡', amount: 299, state: 'pending', time: '06-16 09:12' },
  { id: 'SF-2026-0616-004', user: '王老师', plan: '体验版 → 专业版 升级', amount: 299, state: 'refunded', time: '06-16 08:46' },
  { id: 'SF-2026-0615-021', user: '李总', plan: '创作币 10000', amount: 1498, state: 'paid', time: '06-15 21:18' },
  { id: 'SF-2026-0615-018', user: '张同学', plan: '专业版 续费', amount: 299, state: 'paid', time: '06-15 17:02' },
]

const tone = { paid: 'success', pending: 'warning', refunded: 'danger' }
const text = { paid: '已支付', pending: '待支付', refunded: '已退款' }

const cols = [
  { key: 'id', header: '订单号', render: (r) => <b className="text-white">{r.id}</b> },
  { key: 'user', header: '用户' },
  { key: 'plan', header: '套餐' },
  { key: 'amount', header: '金额', align: 'right', render: (r) => `¥ ${r.amount.toLocaleString()}` },
  { key: 'state', header: '状态', render: (r) => <Badge tone={tone[r.state]}>{text[r.state]}</Badge> },
  { key: 'time', header: '时间' },
  {
    key: 'actions',
    header: '操作',
    align: 'right',
    render: (r) => (
      <span className="flex justify-end gap-1.5 text-xs">
        <button className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-gold-400/40 hover:text-white">详情</button>
        {r.state === 'paid' && (
          <>
            <button className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-gold-400/40 hover:text-white">
              <FileText className={ICON.xs} /> 发票
            </button>
            <button className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-danger-500/40 hover:text-danger-300">
              <RefreshCcw className={ICON.xs} /> 退款
            </button>
          </>
        )}
        {r.state === 'pending' && (
          <button className="inline-flex items-center gap-1 rounded-md border border-gold-400/40 bg-gold-400/10 px-2 py-1 text-gold-300 hover:bg-gold-400/20">
            <Check className={ICON.xs} /> 标记已支付
          </button>
        )}
      </span>
    ),
  },
]

export default function AdminOrders() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '订单 / 退款' }]}
        title="订单管理"
        subtitle="支持状态过滤、批量退款、发票申请"
        toolbar={
          <>
            <ToolbarSearch placeholder="按订单号 / 用户筛选" />
            <Button variant="secondary" size="md" iconLeft={<Download className={ICON.md} />}>导出</Button>
          </>
        }
      />
      <Panel>
        <DataTable columns={cols} rows={ORDERS} />
      </Panel>
    </motion.div>
  )
}
