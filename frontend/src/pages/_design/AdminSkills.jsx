/**
 * AdminSkills.jsx — 技能定义 + 配置项 + 写作规则 + 审批
 *
 * 对应后端：console/skill/skill_views.py + console/skill/writing_rule_views.py
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Plus, Edit3, Check, X, FileText } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'
import { PageHeader, Panel, DataTable } from './components'

const SKILLS = [
  { k: 'brief.collect', v: 'v3', caller: 'node 1', state: 'ok' },
  { k: 'structure.beat', v: 'v2', caller: 'node 2', state: 'ok' },
  { k: 'character.profile', v: 'v2', caller: 'node 3', state: 'draft' },
  { k: 'outline.episode', v: 'v4', caller: 'node 4', state: 'ok' },
  { k: 'script.scene', v: 'v5', caller: 'node 5', state: 'ok' },
  { k: 'review.gate', v: 'v2', caller: 'node 6', state: 'defect' },
  { k: 'final.deliver', v: 'v2', caller: 'node 7', state: 'ok' },
]
const skTone = { ok: 'success', draft: 'warning', defect: 'danger' }
const skText = { ok: '就绪', draft: '草稿', defect: '缺陷' }

const RULES = [
  { k: '禁止双主角', cat: '人物', state: 'pending', by: '林编剧', time: '2 小时前' },
  { k: '反派必须有悔意', cat: '冲突', state: 'approved', by: '王老师', time: '昨天' },
  { k: '钩子集必须含反转', cat: '节奏', state: 'approved', by: '陈导', time: '3 天前' },
  { k: '敏感词清单 v2.3', cat: '合规', state: 'approved', by: '系统', time: '1 周前' },
  { k: '单集字数 800–1500', cat: '格式', state: 'pending', by: '李总', time: '今天' },
]
const ruTone = { pending: 'warning', approved: 'success' }
const ruText = { pending: '待审批', approved: '已生效' }

const skillCols = [
  { key: 'k', header: '技能', render: (r) => <b className="text-white">{r.k}</b> },
  { key: 'v', header: '版本', render: (r) => <Badge tone="default">{r.v}</Badge> },
  { key: 'caller', header: '调用方' },
  { key: 'state', header: '状态', render: (r) => <Badge tone={skTone[r.state]}>{skText[r.state]}</Badge> },
  {
    key: 'actions', header: '操作', align: 'right', render: () => (
      <span className="flex justify-end gap-1.5 text-xs">
        <button className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-gold-400/40 hover:text-white">配置</button>
        <button className="inline-flex items-center gap-1 text-indigo-300 hover:underline">
          <FileText className={ICON.xs} /> 评审
        </button>
      </span>
    ),
  },
]
const ruleCols = [
  { key: 'k', header: '规则', render: (r) => <b className="text-white">{r.k}</b> },
  { key: 'cat', header: '分类' },
  { key: 'state', header: '状态', render: (r) => <Badge tone={ruTone[r.state]}>{ruText[r.state]}</Badge> },
  { key: 'by', header: '提交人' },
  { key: 'time', header: '提交时间' },
  {
    key: 'actions', header: '操作', align: 'right', render: (r) => r.state === 'pending' ? (
      <span className="flex justify-end gap-1 text-xs">
        <button className="inline-flex items-center gap-1 rounded-md border border-success-500/40 bg-success-500/10 px-2 py-1 text-success-300 hover:bg-success-500/20">
          <Check className={ICON.xs} /> 通过
        </button>
        <button className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-danger-500/40 hover:text-danger-300">
          <X className={ICON.xs} /> 驳回
        </button>
      </span>
    ) : null,
  },
]

export default function AdminSkills() {
  const [tab, setTab] = useState('defs')
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '技能中心' }]}
        title="技能定义 · 配置项 · 写作规则"
        subtitle="12 个技能 · 4 个有缺陷待修 · 5 条规则待审批"
        toolbar={
          <Button variant="primary" size="md" iconLeft={<Plus className={ICON.md} />}>新建技能</Button>
        }
      />

      <div className="flex gap-1 rounded-full border border-white/10 bg-white/5 p-1 text-sm">
        {[
          { k: 'defs', n: '技能定义' },
          { k: 'rules', n: '写作规则' },
        ].map((t) => (
          <button
            key={t.k}
            type="button"
            onClick={() => setTab(t.k)}
            className={cn('rounded-full px-4 py-1.5 font-medium transition-colors', tab === t.k ? 'bg-white/10 text-white' : 'text-slate-300 hover:text-white')}
          >
            {t.n}
          </button>
        ))}
      </div>

      {tab === 'defs' ? <Panel><DataTable columns={skillCols} rows={SKILLS} /></Panel> : <Panel><DataTable columns={ruleCols} rows={RULES} /></Panel>}
    </motion.div>
  )
}
