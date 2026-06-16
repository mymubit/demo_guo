/**
 * AdminAgent.jsx — Agent 注册表 + LLM 路由 + 评审评分
 *
 * 对应后端：console/agent/views.py
 * 视觉：3 个 Tab 切换
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Cpu, Route, Award, Plus } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'
import { PageHeader, Panel, DataTable } from './components'

const AGENTS = [
  { k: 'planner', n: '剧情策划', n2: 'planner', state: 'live', v: 'v3', calls: 8420, success: 98.2 },
  { k: 'writer', n: '剧本主笔', n2: 'writer', state: 'live', v: 'v5', calls: 6210, success: 96.4 },
  { k: 'reviewer', n: '质量评审', n2: 'reviewer', state: 'live', v: 'v2', calls: 4880, success: 92.1 },
  { k: 'editor', n: '节奏剪辑', n2: 'editor', state: 'draft', v: 'v1', calls: 0, success: 0 },
  { k: 'casting', n: '人设匹配', n2: 'casting', state: 'live', v: 'v2', calls: 2322, success: 97.6 },
]

const ROUTES = [
  { from: 'planner', to: 'doubao-pro-32k', pri: 'primary', w: 70 },
  { from: 'planner', to: 'deepseek-v3', pri: 'fallback', w: 30 },
  { from: 'writer', to: 'doubao-pro-128k', pri: 'primary', w: 80 },
  { from: 'writer', to: 'gpt-4o-mini', pri: 'fallback', w: 20 },
  { from: 'reviewer', to: 'qwen-long', pri: 'primary', w: 60 },
  { from: 'reviewer', to: 'glm-4-plus', pri: 'fallback', w: 40 },
]

const REVIEWS = [
  { node: 'script.scene', user: '陈老师', score: 92, hint: '结构清晰、节奏合理', time: '2 小时前' },
  { node: 'outline.episode', user: '林老师', score: 86, hint: '第 22 集反转可加强', time: '5 小时前' },
  { node: 'brief.collect', user: '王老师', score: 78, hint: '受众画像可补充', time: '昨天' },
  { node: 'character.profile', user: '李老师', score: 88, hint: '主角弧线完整', time: '2 天前' },
]

const TABS = [
  { k: 'registry', n: '注册表', icon: Cpu },
  { k: 'route', n: 'LLM 路由', icon: Route },
  { k: 'review', n: '评审评分', icon: Award },
]

const aCols = [
  { key: 'k', header: 'Agent', render: (r) => <span><b className="text-white">{r.n}</b> <span className="text-slate-500">· {r.n2}</span></span> },
  { key: 'v', header: '版本', render: (r) => <Badge tone="default">{r.v}</Badge> },
  { key: 'state', header: '状态', render: (r) => <Badge tone={r.state === 'live' ? 'success' : 'warning'}>{r.state === 'live' ? '在线' : '草稿'}</Badge> },
  { key: 'calls', header: '24h 调用', align: 'right' },
  { key: 'success', header: '成功率', align: 'right', render: (r) => <span className={r.success > 95 ? 'text-success-300' : 'text-warning-300'}>{r.success}%</span> },
]
const rCols = [
  { key: 'from', header: 'Agent', render: (r) => <b className="text-white">{r.from}</b> },
  { key: 'to', header: '目标模型' },
  { key: 'pri', header: '类型', render: (r) => <Badge tone={r.pri === 'primary' ? 'gold' : 'default'}>{r.pri === 'primary' ? '主' : '备'}</Badge> },
  { key: 'w', header: '权重', align: 'right', render: (r) => `${r.w}%` },
]
const rvCols = [
  { key: 'node', header: '节点' },
  { key: 'user', header: '评审人' },
  { key: 'score', header: '分数', align: 'right', render: (r) => <b className="text-white">{r.score}</b> },
  { key: 'hint', header: '建议' },
  { key: 'time', header: '时间' },
]

export default function AdminAgent() {
  const [tab, setTab] = useState('registry')
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: 'Agent 中心' }]}
        title="Agent 注册表 · LLM 路由 · 评审评分"
        subtitle="5 个 Agent · 6 条路由 · 4 条评审记录"
        toolbar={<Button variant="primary" size="md" iconLeft={<Plus className={ICON.md} />}>注册 Agent</Button>}
      />

      <div className="flex gap-1 rounded-full border border-white/10 bg-white/5 p-1 text-sm">
        {TABS.map((t) => (
          <button
            key={t.k}
            type="button"
            onClick={() => setTab(t.k)}
            className={cn('inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 font-medium transition-colors', tab === t.k ? 'bg-white/10 text-white' : 'text-slate-300 hover:text-white')}
          >
            <t.icon className={ICON.sm} /> {t.n}
          </button>
        ))}
      </div>

      <Panel>
        <DataTable columns={tab === 'registry' ? aCols : tab === 'route' ? rCols : rvCols} rows={tab === 'registry' ? AGENTS : tab === 'route' ? ROUTES : REVIEWS} />
      </Panel>
    </motion.div>
  )
}
