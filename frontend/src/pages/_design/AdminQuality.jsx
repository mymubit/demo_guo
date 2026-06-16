/**
 * AdminQuality.jsx — 剧本质量缺陷
 *
 * 对应后端：console/creation/quality_defect_views.py
 */
import { motion } from 'framer-motion'
import { AlertTriangle, ShieldAlert, RefreshCcw, FileBarChart2 } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, Panel, DataTable } from './components'

const DEFECTS = [
  { id: 'D-202', lvl: 'P1', skill: 'script.scene', kind: '情绪曲线塌陷', count: 3, last: '2 小时前', owner: '陈老师' },
  { id: 'D-198', lvl: 'P2', skill: 'outline.episode', kind: '反转密度不足', count: 12, last: '昨天', owner: '林编剧' },
  { id: 'D-194', lvl: 'P2', skill: 'brief.collect', kind: '受众画像缺失', count: 9, last: '2 天前', owner: '王老师' },
  { id: 'D-188', lvl: 'P3', skill: 'review.gate', kind: '台词模板过期', count: 22, last: '1 周前', owner: '—' },
  { id: 'D-180', lvl: 'P3', skill: 'structure.beat', kind: '节拍分布偏移', count: 5, last: '1 周前', owner: '李总' },
]

const tone = { P1: 'danger', P2: 'warning', P3: 'info' }
const cols = [
  { key: 'id', header: '编号', render: (r) => <b className="text-white">{r.id}</b> },
  { key: 'lvl', header: '等级', render: (r) => <Badge tone={tone[r.lvl]}>{r.lvl}</Badge> },
  { key: 'skill', header: '所属技能' },
  { key: 'kind', header: '缺陷描述' },
  { key: 'count', header: '近 7 天', align: 'right' },
  { key: 'last', header: '最近发生' },
  { key: 'owner', header: '处理人' },
  {
    key: 'actions', header: '操作', align: 'right', render: (r) => (
      <span className="flex justify-end gap-1.5 text-xs">
        <button className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:border-gold-400/40 hover:text-white">详情</button>
        {r.lvl === 'P1' && (
          <button className="inline-flex items-center gap-1 rounded-md border border-gold-400/40 bg-gold-400/10 px-2 py-1 text-gold-300 hover:bg-gold-400/20">
            <RefreshCcw className={ICON.xs} /> 立即修复
          </button>
        )}
      </span>
    ),
  },
]

export default function AdminQuality() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '剧本质量缺陷' }]}
        title="质量缺陷池"
        subtitle="Agent 评审 + 人工复核双源 · 按 P1/P2/P3 分级"
        toolbar={
          <Button variant="primary" size="md" iconLeft={<FileBarChart2 className={ICON.md} />}>导出</Button>
        }
      />

      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-3">
        <div className="rounded-2xl border border-danger-500/30 bg-danger-500/[0.08] p-4.5">
          <div className="flex items-center justify-between">
            <div className="text-xs text-danger-300">P1 · 严重</div>
            <ShieldAlert className={ICON.md + ' text-danger-400'} />
          </div>
          <div className="mt-1 text-2xl font-bold text-white">3</div>
          <div className="mt-1 text-xs text-slate-400">近 7 天 · 需立即修复</div>
        </div>
        <div className="rounded-2xl border border-warning-500/30 bg-warning-500/[0.08] p-4.5">
          <div className="flex items-center justify-between">
            <div className="text-xs text-warning-300">P2 · 一般</div>
            <AlertTriangle className={ICON.md + ' text-warning-400'} />
          </div>
          <div className="mt-1 text-2xl font-bold text-white">21</div>
          <div className="mt-1 text-xs text-slate-400">本周内迭代</div>
        </div>
        <div className="rounded-2xl border border-info-500/30 bg-info-500/[0.08] p-4.5">
          <div className="flex items-center justify-between">
            <div className="text-xs text-info-300">P3 · 提示</div>
          </div>
          <div className="mt-1 text-2xl font-bold text-white">27</div>
          <div className="mt-1 text-xs text-slate-400">纳入下次发版</div>
        </div>
      </div>

      <Panel>
        <DataTable columns={cols} rows={DEFECTS} />
      </Panel>
    </motion.div>
  )
}
