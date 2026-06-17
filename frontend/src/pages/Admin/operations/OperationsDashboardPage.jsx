/**
 * pages/Admin/operations/OperationsDashboardPage.jsx
 *
 * 【运营 F3】运营 Dashboard 主页面
 *
 * 5 个核心 SLO 卡片 + 概要（今日创作数/运行中/失败）+ 跳转到子页面入口。
 * 子页面：内容质量、反馈、配置命中率、抽样回访、日常 Checklist。
 */
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Bug,
  CheckCircle2,
  ChevronRight,
  Coins,
  Gauge,
  RefreshCw,
  Sparkles,
  TrendingUp,
  XCircle,
} from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell'
import { Button, EmptyState, Skeleton } from '@/components/ui'
import { adminOperations } from '@/services/admin'

const SLO_ICONS = {
  submit_5xx: AlertCircle,
  zombie_workflow: Bug,
  llm_error_rate: Activity,
  coin_spend_anomaly: Coins,
  dashboard_cache: Gauge,
}

const SLO_DESCRIPTIONS = {
  submit_5xx: '5 分钟内创作提交接口 5xx 数量；超过 5 即 P0 告警',
  zombie_workflow: '15 分钟前启动仍未结束的 workflow 实例（堆积排查）',
  llm_error_rate: '5 分钟内 LLM 业务错误率；≥15% 视为 P0',
  coin_spend_anomaly: '与昨日同时段扣费差异；波动 50% 触发 P1 告警',
  dashboard_cache: '5 分钟内 Dashboard 平均耗时；≥800ms 视为 P2',
}

const SUBPAGE_LINKS = [
  { key: 'content-quality', label: '内容质量', description: '保存率/导出率/弃用率/卡点人群', icon: TrendingUp, path: '/admin/operations/content-quality' },
  { key: 'feedback', label: '用户反馈', description: 'P0 优先 + 抽样回访', icon: CheckCircle2, path: '/admin/operations/feedback' },
  { key: 'config-hit', label: '配置命中率', description: '找死代码 & 热点', icon: Gauge, path: '/admin/operations/config-hit' },
  { key: 'samples', label: '抽样回访', description: '一键标记已抽样', icon: Sparkles, path: '/admin/operations/feedback?from=samples' },
  { key: 'checklist', label: '日常 Checklist', description: '5 分钟巡检', icon: ChevronRight, path: '/admin/operations/checklist' },
]

function formatValue(card) {
  if (card.value == null) return '—'
  return `${card.value}${card.unit || ''}`
}

function SloCard({ card }) {
  const Icon = SLO_ICONS[card.key] || Activity
  const ok = card.ok !== false
  return (
    <div
      className={`relative rounded-2xl border p-5 ${
        ok
          ? 'border-white/10 bg-slate-900/60'
          : 'border-danger-500/40 bg-danger-500/5'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-navy-400">
          <Icon className="h-4 w-4" />
          <span>{card.level}</span>
        </div>
        <span
          className={`text-[10px] rounded-full px-2 py-0.5 font-semibold ${
            ok ? 'bg-success-500/20 text-success-300' : 'bg-danger-500/20 text-danger-300'
          }`}
        >
          {ok ? 'OK' : 'ALERT'}
        </span>
      </div>
      <p className="mt-3 text-sm text-navy-300">{card.label}</p>
      <p className={`mt-1 text-3xl font-bold ${ok ? 'text-white' : 'text-danger-300'}`}>
        {formatValue(card)}
      </p>
      <p className="mt-1 text-[11px] text-navy-500">{SLO_DESCRIPTIONS[card.key] || ''}</p>
      <p className="mt-2 text-[11px] text-navy-500">窗口：{card.window || '实时'}</p>
    </div>
  )
}

export default function OperationsDashboardPage() {
  const navigate = useNavigate()
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await adminOperations.dashboard({ days })
      setData(res?.data || res)
    } catch (e) {
      setError(e?.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    load()
  }, [load])

  const slo = data?.slo?.slo_cards || []
  const snapshot = data?.slo?.snapshot || {}
  const openAlerts = data?.slo?.open_alerts ?? 0

  return (
    <AdminShell
      title="运营 Dashboard"
      description="一人运营 5 个核心 SLO 卡片 + 子页面入口"
      actions={
        <div className="flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="sf-control w-32"
          >
            <option value={7}>最近 7 天</option>
            <option value={30}>最近 30 天</option>
            <option value={60}>最近 60 天</option>
            <option value={90}>最近 90 天</option>
          </select>
          <Button variant="secondary" onClick={load} icon={<RefreshCw className="h-4 w-4" />}>
            刷新
          </Button>
        </div>
      }
    >
      {error ? (
        <EmptyState
          icon={<XCircle className="h-6 w-6" />}
          title="加载失败"
          description={error}
          actionLabel="重试"
          onAction={load}
        />
      ) : null}

      {loading && !data ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : (
        <>
          {/* 5 个核心 SLO 卡片 */}
          <section>
            <h2 className="mb-3 text-sm font-semibold text-white">核心 SLO</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
              {slo.map((card) => (
                <SloCard key={card.key} card={card} />
              ))}
            </div>
          </section>

          {/* 快照 + 告警 */}
          <section className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
              <p className="text-xs text-navy-400">今日新增创作</p>
              <p className="mt-1 text-2xl font-bold text-white">{snapshot.today_projects ?? 0}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
              <p className="text-xs text-navy-400">运行中</p>
              <p className="mt-1 text-2xl font-bold text-gold-300">{snapshot.running_projects ?? 0}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5">
              <p className="text-xs text-navy-400">失败（待处理）</p>
              <p className="mt-1 text-2xl font-bold text-danger-300">{snapshot.failed_projects ?? 0}</p>
            </div>
          </section>

          {/* 子页面入口 */}
          <section className="mt-5">
            <h2 className="mb-3 text-sm font-semibold text-white">子页面入口</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {SUBPAGE_LINKS.map((link) => {
                const Icon = link.icon
                return (
                  <button
                    key={link.key}
                    type="button"
                    onClick={() => navigate(link.path)}
                    className="group rounded-2xl border border-white/10 bg-slate-900/60 p-5 text-left transition-all hover:border-gold-400/40 hover:bg-slate-900/80"
                  >
                    <div className="flex items-center justify-between">
                      <Icon className="h-5 w-5 text-gold-400" />
                      <ArrowRight className="h-4 w-4 text-navy-400 transition-transform group-hover:translate-x-1 group-hover:text-gold-400" />
                    </div>
                    <p className="mt-3 text-base font-semibold text-white">{link.label}</p>
                    <p className="mt-1 text-xs text-navy-400">{link.description}</p>
                  </button>
                )
              })}
            </div>
          </section>

          {openAlerts > 0 ? (
            <section className="mt-5 rounded-2xl border border-warning-500/30 bg-warning-500/5 p-4 text-sm text-warning-200">
              当前有 <b className="mx-1 text-base">{openAlerts}</b>
              条待处理告警，请到 <a
                href="/admin/monitoring"
                className="ml-1 underline"
              >告警监控</a> 查看。
            </section>
          ) : null}
        </>
      )}
    </AdminShell>
  )
}
