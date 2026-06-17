/**
 * pages/Admin/operations/ContentQualityPage.jsx
 *
 * 【运营 F4】内容质量看板：保存率/导出率/弃用率 + 用户漏斗 + 卡点人群
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { ArrowDown, ChevronRight, RefreshCw } from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell'
import { Button, EmptyState, Skeleton } from '@/components/ui'
import { EChart } from '@/components/charts'
import { adminOperations } from '@/services/admin'

function pct(v) {
  if (v == null) return '—'
  return `${v.toFixed ? v.toFixed(2) : v}%`
}

function MetricBox({ label, value, hint, tone = 'text-white' }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
      <p className="text-xs text-navy-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${tone}`}>{value}</p>
      {hint ? <p className="mt-1 text-[11px] text-navy-500">{hint}</p> : null}
    </div>
  )
}

export default function ContentQualityPage() {
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await adminOperations.contentQuality({ days })
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

  const summary = data?.summary || {}
  const funnel = data?.funnel || {}
  const stuck = data?.stuck_projects || []

  const funnelChartOption = useMemo(() => {
    const stages = funnel.stages || []
    return {
      grid: { top: 20, right: 16, bottom: 30, left: 48 },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: stages.map((s) => s.label),
        axisLabel: { color: '#94a3b8' },
      },
      yAxis: { type: 'value', axisLabel: { color: '#94a3b8' } },
      series: [
        {
          type: 'bar',
          data: stages.map((s) => s.count),
          itemStyle: { color: '#fbbf24', borderRadius: [6, 6, 0, 0] },
          label: { show: true, position: 'top', color: '#fff' },
        },
      ],
    }
  }, [funnel])

  return (
    <AdminShell
      title="内容质量"
      description="保存率 / 导出率 / 弃用率 / 卡点人群（一项都没人看 = 内容质量出了问题）"
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
      {error ? <EmptyState title="加载失败" description={error} actionLabel="重试" onAction={load} /> : null}

      {loading && !data ? (
        <Skeleton className="h-72" />
      ) : (
        <>
          {/* 4 个核心率 */}
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricBox
              label="保存率"
              value={pct(summary.save_rate)}
              hint="有过编辑的项目 / 总项目"
              tone={summary.save_rate < 30 ? 'text-danger-300' : 'text-success-300'}
            />
            <MetricBox
              label="导出率"
              value={pct(summary.export_rate)}
              hint="至少导出 1 次的项目 / 总项目"
              tone={summary.export_rate < 10 ? 'text-danger-300' : 'text-success-300'}
            />
            <MetricBox
              label="完成率"
              value={pct(summary.complete_rate)}
              hint="状态=completed / 总项目"
            />
            <MetricBox
              label="弃用率"
              value={pct(summary.abandon_rate)}
              hint="abandoned_at 非空 / 总项目"
              tone={summary.abandon_rate > 30 ? 'text-danger-300' : 'text-warning-300'}
            />
          </section>

          {/* 漏斗 */}
          <section className="mt-5 rounded-2xl border border-white/10 bg-slate-900/60 p-5">
            <h2 className="mb-3 text-sm font-semibold text-white">用户漏斗</h2>
            <EChart option={funnelChartOption} style={{ height: 260 }} />
            <div className="mt-3 space-y-1 text-xs text-navy-300">
              {(funnel.stages || []).map((s) => (
                <div key={s.key} className="flex items-center gap-2">
                  <ChevronRight className="h-3 w-3 text-navy-500" />
                  <span className="flex-1">{s.label}</span>
                  <span className="text-navy-100">{s.count}</span>
                  <span className="ml-2 w-16 text-right text-navy-500">{pct(s.rate)}</span>
                </div>
              ))}
            </div>
          </section>

          {/* 卡点人群 */}
          <section className="mt-5 rounded-2xl border border-white/10 bg-slate-900/60 p-5">
            <h2 className="mb-3 text-sm font-semibold text-white">
              卡点人群 <span className="ml-2 text-xs text-navy-400">≥3 天未完成 + 未弃用 + 有过编辑</span>
            </h2>
            {stuck.length === 0 ? (
              <EmptyState
                title="没有卡点项目"
                description="所有进行中的项目都在 3 天内有动静"
                icon={<ArrowDown className="h-5 w-5" />}
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="border-b border-white/5 text-left text-navy-400">
                      <th className="py-2 pr-3">项目</th>
                      <th className="py-2 pr-3">状态</th>
                      <th className="py-2 pr-3">编辑</th>
                      <th className="py-2 pr-3">停留</th>
                      <th className="py-2 pr-3">最近编辑</th>
                      <th className="py-2 pr-3">用户</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stuck.map((p) => (
                      <tr key={p.project_id} className="border-b border-white/5">
                        <td className="py-2 pr-3 text-navy-100">
                          <a
                            href={`/admin/creation/projects/${p.project_id}`}
                            className="hover:text-gold-300"
                          >
                            {p.title}
                          </a>
                          <p className="text-[10px] text-navy-500">{p.theme}</p>
                        </td>
                        <td className="py-2 pr-3 text-navy-200">{p.status_text}</td>
                        <td className="py-2 pr-3 text-navy-200">{p.user_edit_count}</td>
                        <td className="py-2 pr-3 text-navy-200">{p.days_since_create}d</td>
                        <td className="py-2 pr-3 text-navy-400">
                          {p.last_edited_at ? new Date(p.last_edited_at).toLocaleDateString('zh-CN') : '从未编辑'}
                        </td>
                        <td className="py-2 pr-3 text-navy-400">{p.user_phone || p.user_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </AdminShell>
  )
}
