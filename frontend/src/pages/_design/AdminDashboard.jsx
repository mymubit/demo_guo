/**
 * AdminDashboard.jsx — 设计稿运营仪表盘
 *
 * Linear-style 克制版：先 KPI，再图表，再表格。无装饰 Hero。
 * 对应后端：console/monitor/dashboard_views.DashboardView
 */
import { motion } from 'framer-motion'
import {
  Users,
  Wallet,
  FolderKanban,
  Cpu,
  Search,
  Download,
  ArrowUpRight,
  ArrowDownRight,
  CircleAlert,
  CircleCheck,
  TriangleAlert,
} from 'lucide-react'
import { MetricCard, Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const KPIS = [
  { label: '活跃用户', value: '12,486', delta: '+8.2%', up: true, spark: 'M0,28 12,22 24,26 36,18 48,20 60,12 72,16 84,8 96,12 108,4 120,6' },
  { label: '日营收 (元)', value: '¥ 38,920', delta: '+12.4%', up: true, spark: 'M0,24 12,20 24,22 36,14 48,16 60,10 72,12 84,6 96,8 108,2 120,4', gold: true },
  { label: '创作中项目', value: '128', delta: '-3.1%', up: false, spark: 'M0,12 12,14 24,10 36,16 48,12 60,18 72,14 84,20 96,16 108,22 120,18' },
  { label: 'LLM 成本 (元)', value: '¥ 1,284', delta: '+5.6%', up: true, danger: true, spark: 'M0,22 12,18 24,20 36,12 48,16 60,10 72,14 84,8 96,12 108,4 120,8' },
]

// 7 日柱图（双系列）
const CHART_DAYS = [
  { d: '06-10', h1: 48, h2: 0, alt: false },
  { d: '06-11', h1: 62, h2: 0, alt: false },
  { d: '06-12', h1: 38, h2: 0, alt: true },
  { d: '06-13', h1: 74, h2: 0, alt: false },
  { d: '06-14', h1: 58, h2: 0, alt: false },
  { d: '06-15', h1: 82, h2: 0, alt: true },
  { d: '06-16', h1: 90, h2: 0, alt: false },
]

// 会员构成环图数据（百分比）
const MEMBER_SHARE = [
  { lbl: '专业', pct: 50, color: '#667eea' },
  { lbl: '旗舰', pct: 30, color: '#f6d365' },
  { lbl: '体验', pct: 20, color: '#34d399' },
]

const SKILL_TOP = [
  { n: 'brief.collect', c: 3201 },
  { n: 'structure.beat', c: 2884 },
  { n: 'outline.episode', c: 2610 },
  { n: 'character.profile', c: 2322 },
  { n: 'script.scene', c: 1902 },
]

const LLM_TOP = [
  { n: 'doubao-pro-32k', c: '¥ 642' },
  { n: 'deepseek-v3', c: '¥ 312' },
  { n: 'gpt-4o-mini', c: '¥ 188' },
  { n: 'qwen-long', c: '¥ 96' },
  { n: 'glm-4-plus', c: '¥ 46' },
]

const ALERTS = [
  { level: 'P2', text: 'volcengine 限流阈值达 80%', tone: 'warning' },
  { level: 'P3', text: 'script.scene 失败率 +1.2%', tone: 'info' },
  { level: 'OK', text: 'dj_queue 队列恢复', tone: 'success' },
  { level: 'P1', text: 'doubao-pro 凭证过期', tone: 'danger' },
]

export default function AdminDashboard() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      {/* 页头 */}
      <div className="flex flex-wrap items-center gap-4">
        <div>
          <div className="text-xs text-slate-500">Console / <b className="text-white">今日总览</b></div>
          <h1 className="mt-1 text-xl font-bold">运营仪表盘 · 2026-06-16</h1>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
            <Search className={ICON.md} />
            <input
              placeholder="搜索项目 / 用户 / 订单"
              className="w-60 bg-transparent placeholder:text-slate-500 focus:outline-none"
            />
          </div>
          <Button variant="primary" size="md" iconLeft={<Download className={ICON.md} />}>
            导出报表
          </Button>
        </div>
      </div>

      {/* KPI 行 */}
      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        {KPIS.map((k) => (
          <div key={k.label} className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
            <div className="text-xs text-slate-400">{k.label}</div>
            <div className="mt-1 text-[28px] font-bold leading-tight tracking-tight text-white">{k.value}</div>
            <div className={cn('mt-1 flex items-center gap-1 text-xs', k.up ? 'text-success-300' : 'text-danger-300')}>
              {k.up ? <ArrowUpRight className={ICON.xs} /> : <ArrowDownRight className={ICON.xs} />}
              {k.delta} · 较昨日
            </div>
            <svg className="mt-2 h-9 w-full" viewBox="0 0 120 36" preserveAspectRatio="none">
              <polyline points={k.spark} fill="none" strokeWidth="1.5"
                stroke={k.gold ? '#f6d365' : k.danger ? '#f87171' : '#667eea'} />
            </svg>
          </div>
        ))}
      </div>

      {/* 图表行 */}
      <div className="grid grid-cols-1 gap-3.5 lg:grid-cols-[1.6fr_1fr]">
        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
          <h3 className="m-0 text-sm font-semibold text-white">近 7 日 · 创作 & 营收</h3>
          <div className="mt-1 mb-3 text-xs text-slate-500">左轴：新增项目 · 右轴：充值金额（元）</div>
          <div className="relative h-[220px] overflow-hidden rounded-xl">
            <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/10 to-transparent" />
            <div className="absolute inset-0 grid grid-rows-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="border-b border-white/5" />
              ))}
            </div>
            <div className="absolute inset-x-0 bottom-7 top-3.5 flex items-end gap-2 px-3.5">
              {CHART_DAYS.map((c, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex-1 rounded-t',
                    c.alt
                      ? 'bg-gradient-to-t from-gold-600 to-gold-400 opacity-90'
                      : 'bg-gradient-to-t from-indigo-600 to-indigo-400 opacity-90',
                  )}
                  style={{ height: `${c.h1}%` }}
                />
              ))}
            </div>
            <div className="absolute inset-x-3.5 bottom-2 flex justify-between text-[10px] text-slate-500">
              <span>06-10</span><span>06-12</span><span>06-14</span><span>06-16</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
          <h3 className="m-0 text-sm font-semibold text-white">会员构成</h3>
          <div className="mt-1 mb-3 text-xs text-slate-500">基于 MembershipPlan 用户分布</div>
          <Donut data={MEMBER_SHARE} />
        </div>
      </div>

      {/* 表格行 */}
      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-3">
        <Panel title="技能调用 Top 5" sub="近 7 日 · 按调用次数">
          <Table
            head={['技能', '调用']}
            rows={SKILL_TOP.map((s) => [s.n, s.c.toLocaleString()])}
          />
        </Panel>
        <Panel title="LLM 用量 Top" sub="按 ¥ 消耗">
          <Table
            head={['模型', '成本']}
            rows={LLM_TOP.map((s) => [s.n, s.c])}
          />
        </Panel>
        <Panel title="系统告警" sub="监控中心 推送">
          <ul className="m-0 space-y-1.5 p-0">
            {ALERTS.map((a) => (
              <li key={a.text} className="flex items-center gap-2.5 border-b border-white/5 py-2 text-[13px] last:border-b-0">
                <Badge tone={a.tone}>{a.level}</Badge>
                <span className="text-slate-300">{a.text}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </motion.div>
  )
}

// —— 子组件 ——
function Panel({ title, sub, children }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
      <h3 className="m-0 text-sm font-semibold text-white">{title}</h3>
      <div className="mt-1 mb-3 text-xs text-slate-500">{sub}</div>
      {children}
    </div>
  )
}

function Table({ head, rows }) {
  return (
    <table className="w-full border-collapse text-[13px]">
      <thead>
        <tr className="text-[11px] uppercase tracking-wider text-slate-500">
          {head.map((h) => (
            <th key={h} className="border-b border-white/5 py-2 text-left first:pl-0 last:pr-0 last:text-right">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r[0]} className="border-b border-white/5 last:border-b-0">
            <td className="py-2.5 text-white">{r[0]}</td>
            <td className="py-2.5 text-right text-slate-300 tabular-nums">{r[1]}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function Donut({ data }) {
  // 总周长 = 2πr = 2*π*60 ≈ 377
  const C = 2 * Math.PI * 60
  let offset = 0
  return (
    <div className="relative grid h-[220px] place-items-center">
      <svg width="160" height="160" viewBox="0 0 160 160" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="80" cy="80" r="60" fill="none" stroke="rgba(255,255,255,.05)" strokeWidth="18" />
        {data.map((d) => {
          const len = (d.pct / 100) * C
          const seg = (
            <circle
              key={d.lbl}
              cx="80"
              cy="80"
              r="60"
              fill="none"
              stroke={d.color}
              strokeWidth="18"
              strokeDasharray={`${len} ${C}`}
              strokeDashoffset={-offset}
            />
          )
          offset += len
          return seg
        })}
      </svg>
      <div className="pointer-events-none absolute bottom-1.5 left-3.5 right-3.5 flex justify-center gap-3.5 text-[11px] text-slate-400">
        {data.map((d) => (
          <span key={d.lbl}>
            <i className="mr-1 inline-block h-2 w-2 rounded-sm align-middle" style={{ background: d.color }} />
            {d.lbl} {d.pct}%
          </span>
        ))}
      </div>
    </div>
  )
}
