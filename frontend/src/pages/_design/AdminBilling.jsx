/**
 * AdminBilling.jsx — 充值包 / 创作币定价 / AI 字段扣费
 *
 * 对应后端：console/commerce/billing_views.py
 */
import { motion } from 'framer-motion'
import { Plus, Edit3, Coins, FileBarChart2 } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, Panel, DataTable, KpiTile } from './components'

const PACKAGES = [
  { k: 100, p: 19, off: 0, tag: '体验' },
  { k: 500, p: 89, off: 6, tag: '热门' },
  { k: 1000, p: 168, off: 12, tag: '推荐' },
  { k: 3000, p: 478, off: 16, tag: '专业' },
  { k: 10000, p: 1498, off: 22, tag: '旗舰' },
]

const AI_FIELD_RULES = [
  { node: '信息收集', unit: 30, unitName: '币 / 次', trigger: '每次创作', volume: '12,840' },
  { node: '结构规划', unit: 60, unitName: '币 / 次', trigger: '自动触发', volume: '6,210' },
  { node: '人设开发', unit: 80, unitName: '币 / 次', trigger: '自动触发', volume: '4,880' },
  { node: '大纲撰写', unit: 120, unitName: '币 / 集', trigger: '按集数计', volume: '3,201' },
  { node: '剧本创作', unit: 380, unitName: '币 / 集', trigger: '按集数计', volume: '2,322' },
  { node: '质量审查', unit: 60, unitName: '币 / 次', trigger: '自动触发', volume: '1,902' },
  { node: '输出交付', unit: 30, unitName: '币 / 次', trigger: '自动触发', volume: '1,860' },
]

const pkgCols = [
  { key: 'k', header: '创作币', render: (r) => <b className="text-white">{r.k.toLocaleString()}</b> },
  { key: 'p', header: '售价', align: 'right', render: (r) => `¥ ${r.p}` },
  { key: 'off', header: '折扣', align: 'right', render: (r) => r.off ? <Badge tone="success">-{r.off}%</Badge> : '—' },
  { key: 'tag', header: '标签', render: (r) => <Badge tone="gold">{r.tag}</Badge> },
  { key: 'actions', header: '操作', align: 'right', render: () => (
    <button className="inline-flex items-center gap-1 text-xs text-slate-300 hover:text-white">
      <Edit3 className={ICON.xs} /> 编辑
    </button>
  )},
]

const ruleCols = [
  { key: 'node', header: '主链节点', render: (r) => <b className="text-white">{r.node}</b> },
  { key: 'unit', header: '单价', render: (r) => <span><b className="text-white">{r.unit}</b> {r.unitName}</span> },
  { key: 'trigger', header: '触发方式' },
  { key: 'volume', header: '本月调用', align: 'right' },
  { key: 'actions', header: '操作', align: 'right', render: () => (
    <button className="inline-flex items-center gap-1 text-xs text-slate-300 hover:text-white">
      <Edit3 className={ICON.xs} /> 编辑
    </button>
  )},
]

export default function AdminBilling() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '充值 / 创作币' }]}
        title="充值与创作币定价"
        subtitle="充值包 · 创作币 · AI 字段扣费规则"
        toolbar={
          <Button variant="primary" size="md" iconLeft={<Plus className={ICON.md} />}>新建充值包</Button>
        }
      />

      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-3">
        <KpiTile label="今日充值订单" value="284" delta="+14.2%" up />
        <KpiTile label="创作币消费" value="¥ 8,420" delta="+2.4%" up gold />
        <KpiTile label="待结算金额" value="¥ 1,234" delta="—" />
      </div>

      <Panel title="充值包" sub="5 档 · 会员 9 折 · 旗舰版 +5%">
        <DataTable columns={pkgCols} rows={PACKAGES} />
      </Panel>

      <Panel
        title="AI 字段扣费规则"
        sub="按主链节点 × 触发方式定价 · 与 billing/ai_field_prompt_service.py 同源"
        action={<Button variant="secondary" size="sm" iconLeft={<FileBarChart2 className={ICON.sm} />}>同步到生产</Button>}
      >
        <DataTable columns={ruleCols} rows={AI_FIELD_RULES} />
      </Panel>
    </motion.div>
  )
}
