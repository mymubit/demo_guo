/**
 * pages/Admin/operations/DailyChecklistPage.jsx
 *
 * 【运营 F7】日常 5 分钟 Checklist：5 个核心动作 + 跳转链接
 */
import { useCallback, useEffect, useState } from 'react'
import {
  Activity,
  Check,
  ChevronRight,
  ClipboardCheck,
  Coins,
  Gauge,
  RefreshCw,
  ShieldAlert,
  Users,
} from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell'
import { Button, EmptyState, Skeleton } from '@/components/ui'
import { adminOperations } from '@/services/admin'

const STORAGE_KEY = 'ops:checklist:done'

function loadChecked() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    return JSON.parse(raw) || {}
  } catch {
    return {}
  }
}
function saveChecked(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (_) {
    /* ignore */
  }
}

const CHECKLIST = [
  {
    key: 'alerts',
    label: '查看今日告警',
    description: '打开监控中心，处置 0 优先级以上的告警',
    icon: ShieldAlert,
    link: '/admin/monitoring',
    sla: '5 min',
  },
  {
    key: 'slo',
    label: '扫一眼 5 个 SLO 卡片',
    description: '5xx 突增、僵尸工作流、LLM 失败率、币扣费异常、缓存耗时',
    icon: Activity,
    link: '/admin/operations/dashboard',
    sla: '1 min',
  },
  {
    key: 'feedback',
    label: '处理 P0 反馈',
    description: 'P0 未关闭 = 0 才是合格',
    icon: Users,
    link: '/admin/operations/feedback?p0_only=1',
    sla: '5 min',
  },
  {
    key: 'stuck',
    label: '关注卡点项目',
    description: '≥3 天未完成 + 未弃用 + 有过编辑的项目',
    icon: ClipboardCheck,
    link: '/admin/operations/content-quality',
    sla: '2 min',
  },
  {
    key: 'config',
    label: '看一遍死代码候选',
    description: '没有命中 = 0 才说明配置没冗余',
    icon: Gauge,
    link: '/admin/operations/config-hit',
    sla: '1 min',
  },
]

export default function DailyChecklistPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [checked, setChecked] = useState({})

  useEffect(() => {
    setChecked(loadChecked())
  }, [])

  const persist = (next) => {
    setChecked(next)
    saveChecked(next)
  }

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await adminOperations.dashboard({ days: 7 })
      setData(res?.data || res)
    } catch (e) {
      setError(e?.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const slo = data?.slo?.slo_cards || []
  const openAlerts = data?.slo?.open_alerts ?? 0
  const totalDone = Object.values(checked).filter(Boolean).length

  return (
    <AdminShell
      title="日常 Checklist"
      description="5 分钟巡检：5 步全做 = 今日无恙"
      actions={
        <div className="flex items-center gap-2">
          <span className="text-xs text-navy-400">
            今日完成 <b className="mx-1 text-gold-300">{totalDone}</b>/ {CHECKLIST.length}
          </span>
          <Button variant="secondary" onClick={load} icon={<RefreshCw className="h-4 w-4" />}>
            刷新 SLO
          </Button>
        </div>
      }
    >
      {error ? <EmptyState title="加载失败" description={error} actionLabel="重试" onAction={load} /> : null}
      {loading && !data ? (
        <Skeleton className="h-72" />
      ) : (
        <>
          {/* 顶部提示 */}
          {openAlerts > 0 ? (
            <div className="mb-4 rounded-2xl border border-danger-500/30 bg-danger-500/5 p-3 text-sm text-danger-200">
              当前有 <b className="mx-1 text-base">{openAlerts}</b> 条未处理告警。
            </div>
          ) : (
            <div className="mb-4 rounded-2xl border border-success-500/30 bg-success-500/5 p-3 text-sm text-success-200">
              告警 0 条。Nice.
            </div>
          )}

          {/* 5 步 Checklist */}
          <section className="space-y-3">
            {CHECKLIST.map((item) => {
              const Icon = item.icon
              const done = !!checked[item.key]
              return (
                <a
                  key={item.key}
                  href={item.link}
                  className={`flex items-center gap-4 rounded-2xl border p-4 transition-all ${
                    done
                      ? 'border-success-500/30 bg-success-500/5'
                      : 'border-white/10 bg-slate-900/60 hover:border-gold-400/40'
                  }`}
                >
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      persist({ ...checked, [item.key]: !done })
                    }}
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 ${
                      done
                        ? 'border-success-500 bg-success-500/20 text-success-300'
                        : 'border-white/20 text-navy-500 hover:border-gold-400'
                    }`}
                  >
                    {done ? <Check className="h-4 w-4" /> : <span className="text-xs">{item.sla}</span>}
                  </button>
                  <Icon className={`h-5 w-5 ${done ? 'text-success-300' : 'text-gold-400'}`} />
                  <div className="flex-1">
                    <p className={`text-sm font-semibold ${done ? 'text-success-200 line-through' : 'text-white'}`}>
                      {item.label}
                    </p>
                    <p className="text-xs text-navy-400">{item.description}</p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-navy-500" />
                </a>
              )
            })}
          </section>

          {/* SLO 摘要（辅助判断） */}
          <section className="mt-5 rounded-2xl border border-white/10 bg-slate-900/60 p-5">
            <h2 className="mb-3 text-sm font-semibold text-white">SLO 摘要</h2>
            <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
              {slo.map((c) => (
                <div
                  key={c.key}
                  className={`rounded-xl border p-3 text-center ${
                    c.ok ? 'border-white/10' : 'border-danger-500/30 bg-danger-500/5'
                  }`}
                >
                  <p className="text-[10px] uppercase tracking-wider text-navy-400">{c.level}</p>
                  <p className="mt-1 text-xs text-navy-200">{c.label}</p>
                  <p className={`mt-1 text-lg font-bold ${c.ok ? 'text-white' : 'text-danger-300'}`}>
                    {c.value}
                    {c.unit || ''}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </AdminShell>
  )
}
