/**
 * AdminOrchestration.jsx — 调度监控
 *
 * 对应后端：console/orchestration/views.py
 * 视觉：实时队列 + 执行链路 + 失败重试
 */
import { motion } from 'framer-motion'
import { Activity, RefreshCcw, AlertCircle, ChevronRight } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, Panel, DataTable, KpiTile } from './components'

const QUEUES = [
  { k: 'dj_create', n: '创作主队列', running: 18, pending: 6, done: 1284, fail: 4 },
  { k: 'dj_evaluate', n: '评估队列', running: 4, pending: 12, done: 320, fail: 1 },
  { k: 'dj_render', n: '渲染队列', running: 0, pending: 2, done: 86, fail: 0 },
  { k: 'dj_share', n: '分享生成', running: 1, pending: 0, done: 12, fail: 0 },
]

const RUNS = [
  { id: 'R-2048', task: 'script.scene · 《逆光》第 17 集', state: 'running', step: '3/5', elapsed: '02:14', worker: 'W-12' },
  { id: 'R-2046', task: 'review.gate · 《错位》第 22 集', state: 'failed', step: '2/4', elapsed: '00:18', worker: 'W-08' },
  { id: 'R-2040', task: 'brief.collect · 新项目', state: 'success', step: '1/1', elapsed: '00:08', worker: 'W-03' },
  { id: 'R-2038', task: 'outline.episode · 《长夜》第 5 集', state: 'running', step: '2/3', elapsed: '00:42', worker: 'W-11' },
]

const stateTone = { running: 'info', failed: 'danger', success: 'success' }
const stateText = { running: '执行中', failed: '失败', success: '完成' }

const cols = [
  { key: 'id', header: '执行 ID', render: (r) => <b className="text-white">{r.id}</b> },
  { key: 'task', header: '任务' },
  { key: 'state', header: '状态', render: (r) => <Badge tone={stateTone[r.state]}>{stateText[r.state]}</Badge> },
  { key: 'step', header: '步骤' },
  { key: 'elapsed', header: '耗时', align: 'right' },
  { key: 'worker', header: 'Worker' },
  {
    key: 'actions', header: '操作', align: 'right', render: (r) => (
      <span className="flex justify-end gap-1.5 text-xs">
        <button className="text-indigo-300 hover:underline">Trace</button>
        {r.state === 'failed' && (
          <>
            <span className="text-slate-600">·</span>
            <button className="inline-flex items-center gap-1 text-warning-300 hover:underline">
              <RefreshCcw className={ICON.xs} /> 重试
            </button>
          </>
        )}
      </span>
    ),
  },
]

export default function AdminOrchestration() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '调度监控' }]}
        title="调度执行监控"
        subtitle="4 个队列 · 23 个正在运行 · 1 个失败待重试"
      />

      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="正在运行" value="23" delta="+5" up />
        <KpiTile label="待处理" value="20" delta="+12" up />
        <KpiTile label="今日完成" value="1,702" delta="+8.2%" up gold />
        <KpiTile label="失败率" value="1.4%" delta="-0.2%" up />
      </div>

      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2 lg:grid-cols-4">
        {QUEUES.map((q) => (
          <div key={q.k} className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
            <div className="flex items-center justify-between">
              <div className="text-xs text-slate-400">{q.n}</div>
              <Activity className={ICON.md + ' text-indigo-400'} />
            </div>
            <div className="mt-1.5 font-mono text-[10px] text-slate-500">{q.k}</div>
            <div className="mt-3 grid grid-cols-2 gap-1.5 text-xs">
              <Stat k="运行中" v={q.running} tone="info" />
              <Stat k="待处理" v={q.pending} tone="default" />
              <Stat k="完成" v={q.done} tone="success" />
              <Stat k="失败" v={q.fail} tone={q.fail > 2 ? 'danger' : 'warning'} />
            </div>
          </div>
        ))}
      </div>

      <Panel title="最近执行" sub="按时间倒序 · 支持 Trace 回看 / 失败重试">
        <DataTable columns={cols} rows={RUNS} />
      </Panel>
    </motion.div>
  )
}

function Stat({ k, v, tone }) {
  const c = tone === 'success' ? 'text-success-300' : tone === 'danger' ? 'text-danger-300' : tone === 'info' ? 'text-info-300' : tone === 'warning' ? 'text-warning-300' : 'text-white'
  return (
    <div className="rounded-md border border-white/5 bg-white/[0.02] px-2 py-1.5">
      <div className="text-[10px] text-slate-500">{k}</div>
      <div className={`text-sm font-bold ${c}`}>{v}</div>
    </div>
  )
}
