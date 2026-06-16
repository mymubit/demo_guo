/**
 * AdminProjects.jsx — 设计稿创作项目监控
 *
 * 对应后端：console/creation/project_views.py + orchestration/execution_views.py
 * 视觉重点：项目卡 + 7 节点状态条 + 全部项目表
 */
import { motion } from 'framer-motion'
import { Search, Filter, Eye, Wrench, Download, FileText } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const STAGES = ['信息', '结构', '人设', '大纲', '剧本', '审查', '交付']

// 顶部项目卡 — 与后端 AdminCreationProjectDetailView 字段对齐
const PROJECT_CARDS = [
  {
    id: 'P-10248',
    title: '《逆光》',
    user: '138****8821',
    theme: '都市逆袭',
    episodes: 80,
    node: 4,
    state: 'running',
    elapsed: '03:12',
    remain: '04:48',
    cover:
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20shanghai%20rooftop%20at%20night%2C%20a%20woman%20in%20a%20red%20coat%2C%20neon%20reflections%2C%20anamorphic%2C%20photorealistic&image_size=square',
  },
  {
    id: 'P-10241',
    title: '《权倾长乐》',
    user: '139****0032',
    theme: '古装权谋',
    episodes: 60,
    node: 7,
    state: 'completed',
    score: 86,
    elapsed: '08:02',
    cover:
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=ancient%20chinese%20palace%20inner%20court%2C%20lanterns%2C%20silk%20robes%2C%20fog%2C%20cinematic%20golden%20light&image_size=square',
  },
]

// 全部项目表
const PROJECTS = [
  { id: 'P-10248', title: '《逆光》', user: '138****8821', theme: '都市逆袭', node: '4 / 7', elapsed: '03:12', tokens: 21440, state: 'running' },
  { id: 'P-10236', title: '《错位》', user: '139****0032', theme: '悬疑反转', node: '7 / 7', elapsed: '08:02', tokens: 182310, state: 'completed' },
  { id: 'P-10220', title: '《长夜未央》', user: '186****7741', theme: '家庭复仇', node: '5 / 7', elapsed: '05:48', tokens: 96210, state: 'review' },
  { id: 'P-10211', title: '《被校花倒追》', user: '177****2098', theme: '甜宠虐恋', node: '2 / 7', elapsed: '00:42', tokens: 8920, state: 'failed' },
]

function stateTone(state) {
  if (state === 'completed') return 'success'
  if (state === 'running') return 'info'
  if (state === 'review') return 'warning'
  if (state === 'failed') return 'danger'
  return 'default'
}
function stateText(state) {
  if (state === 'completed') return '已完成'
  if (state === 'running') return '运行中'
  if (state === 'review') return '人工复核'
  if (state === 'failed') return '失败 · 限流'
  return state
}

export default function AdminProjects() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      {/* 页头 */}
      <div className="flex flex-wrap items-center gap-4">
        <div>
          <div className="text-xs text-slate-500">Console / <b className="text-white">创作项目</b></div>
          <h1 className="mt-1 text-xl font-bold">创作项目监控 · 128 在跑</h1>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
            <Search className={ICON.md} />
            <input
              placeholder="按项目 / 用户筛选"
              className="w-60 bg-transparent placeholder:text-slate-500 focus:outline-none"
            />
          </div>
          <Button variant="secondary" size="md">全部</Button>
          <Button variant="primary" size="md" iconLeft={<Filter className={ICON.md} />}>
            筛选异常
          </Button>
        </div>
      </div>

      {/* 项目卡 — 顶部 2 张 */}
      <div className="grid grid-cols-1 gap-3.5 lg:grid-cols-2">
        {PROJECT_CARDS.map((p) => (
          <article key={p.id} className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
            <div className="flex items-center gap-3">
              <div
                className="h-14 w-14 flex-none rounded-xl bg-cover bg-center"
                style={{ backgroundImage: `url(${p.cover})` }}
                aria-label={p.title}
              />
              <div className="min-w-0 flex-1">
                <h3 className="m-0 text-[15px] font-semibold text-white">{p.title} · {p.id}</h3>
                <div className="mt-0.5 text-xs text-slate-500">
                  用户 {p.user} · {p.theme} · {p.episodes} 集 · 第 {p.node} 节点
                </div>
              </div>
              <Badge tone={stateTone(p.state)} size="md">{stateText(p.state)}</Badge>
            </div>

            <div className="mt-3.5 grid grid-cols-7 gap-1.5">
              {STAGES.map((s, i) => {
                const idx = i + 1
                const tone =
                  p.state === 'completed' ? 'done' :
                  idx < p.node ? 'done' :
                  idx === p.node && p.state === 'running' ? 'run' :
                  idx === p.node && p.state === 'failed' ? 'fail' :
                  'idle'
                return (
                  <div
                    key={s}
                    className={cn(
                      'rounded-md border py-1.5 text-center text-[10px]',
                      tone === 'done' && 'border-success-500/35 bg-success-500/12 text-success-300',
                      tone === 'run' && 'border-indigo-500/40 bg-indigo-500/15 text-indigo-300',
                      tone === 'fail' && 'border-danger-500/35 bg-danger-500/12 text-danger-300',
                      tone === 'idle' && 'border-white/5 bg-white/[0.03] text-slate-500',
                    )}
                  >
                    {s}
                  </div>
                )
              })}
            </div>

            <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
              {p.state === 'completed' ? (
                <>
                  <span>评分 <b className="text-white">{p.score}</b> · {p.elapsed}</span>
                  <span className="ml-auto" />
                  <Button variant="secondary" size="sm" iconLeft={<Download className={ICON.sm} />}>
                    下载剧本
                  </Button>
                  <Button variant="primary" size="sm" iconLeft={<Eye className={ICON.sm} />}>
                    回看 Trace
                  </Button>
                </>
              ) : (
                <>
                  <span>耗时 {p.elapsed} · 剩余 {p.remain}</span>
                  <span className="ml-auto" />
                  <Button variant="secondary" size="sm" iconLeft={<Eye className={ICON.sm} />}>
                    查看 Trace
                  </Button>
                  <Button variant="primary" size="sm" iconLeft={<Wrench className={ICON.sm} />}>
                    手动介入
                  </Button>
                </>
              )}
            </div>
          </article>
        ))}
      </div>

      {/* 全部项目表 */}
      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
        <h3 className="m-0 text-sm font-semibold text-white">全部项目</h3>
        <div className="mt-1 mb-3 text-xs text-slate-500">按开始时间倒序 · 共 128</div>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-slate-500">
              <th className="py-2 text-left">项目</th>
              <th className="py-2 text-left">用户</th>
              <th className="py-2 text-left">题材</th>
              <th className="py-2 text-left">节点</th>
              <th className="py-2 text-right">耗时</th>
              <th className="py-2 text-right">Token</th>
              <th className="py-2 text-left">状态</th>
            </tr>
          </thead>
          <tbody>
            {PROJECTS.map((p) => (
              <tr key={p.id} className="border-t border-white/5 hover:bg-indigo-500/[0.06]">
                <td className="py-3"><b className="text-white">{p.title}</b></td>
                <td className="py-3 text-slate-300">{p.user}</td>
                <td className="py-3 text-slate-300">{p.theme}</td>
                <td className="py-3 text-slate-300">{p.node}</td>
                <td className="py-3 text-right tabular-nums text-slate-300">{p.elapsed}</td>
                <td className="py-3 text-right tabular-nums text-slate-300">{p.tokens.toLocaleString()}</td>
                <td className="py-3"><Badge tone={stateTone(p.state)}>{stateText(p.state)}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
