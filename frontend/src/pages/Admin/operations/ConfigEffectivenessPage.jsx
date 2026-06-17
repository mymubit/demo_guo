/**
 * pages/Admin/operations/ConfigEffectivenessPage.jsx
 *
 * 【运营 F6】配置命中率：找死代码 + 24h 热点
 */
import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw, TrendingUp, Skull } from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell'
import { Button, EmptyState, Skeleton } from '@/components/ui'
import { adminOperations } from '@/services/admin'

function pct(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString()
}

export default function ConfigEffectivenessPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await adminOperations.configHit({ limit: 30 })
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

  return (
    <AdminShell
      title="配置命中率"
      description="找死代码（hit_count<10 + 7d 没人用）+ 24h 热点"
      actions={
        <Button variant="secondary" onClick={load} icon={<RefreshCw className="h-4 w-4" />}>
          刷新
        </Button>
      }
    >
      {error ? <EmptyState title="加载失败" description={error} actionLabel="重试" onAction={load} /> : null}
      {loading && !data ? (
        <Skeleton className="h-72" />
      ) : data ? (
        <>
          <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
              <p className="text-xs text-navy-400">有效配置项</p>
              <p className="mt-1 text-2xl font-bold text-white">{pct(data.total_active)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
              <p className="text-xs text-navy-400">24h 有命中</p>
              <p className="mt-1 text-2xl font-bold text-success-300">{pct(data.touched_24h)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
              <p className="text-xs text-navy-400">覆盖率</p>
              <p className="mt-1 text-2xl font-bold text-gold-300">
                {data.total_active
                  ? ((data.touched_24h / data.total_active) * 100).toFixed(1)
                  : 0}
                %
              </p>
            </div>
          </section>

          {/* 24h 热点 */}
          <section className="mt-5 rounded-2xl border border-white/10 bg-slate-900/60 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
              <TrendingUp className="h-4 w-4 text-gold-400" />
              24h 热点
            </h2>
            {(data.top_24h || []).length === 0 ? (
              <EmptyState title="暂无 24h 命中" description="还没有任何配置在 24h 内被读取" />
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="border-b border-white/5 text-left text-navy-400">
                      <th className="py-2 pr-3">配置键</th>
                      <th className="py-2 pr-3">配置名</th>
                      <th className="py-2 pr-3 text-right">24h</th>
                      <th className="py-2 pr-3 text-right">累计</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_24h.map((c) => (
                      <tr key={c.config_key} className="border-b border-white/5">
                        <td className="py-2 pr-3 font-mono text-navy-200">{c.config_key}</td>
                        <td className="py-2 pr-3 text-navy-100">{c.config_name}</td>
                        <td className="py-2 pr-3 text-right text-success-300">{c.hit_24h}</td>
                        <td className="py-2 pr-3 text-right text-navy-200">{c.hit_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* 累计 Top */}
          <section className="mt-5 rounded-2xl border border-white/10 bg-slate-900/60 p-5">
            <h2 className="mb-3 text-sm font-semibold text-white">累计 Top 30</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="border-b border-white/5 text-left text-navy-400">
                    <th className="py-2 pr-3">配置键</th>
                    <th className="py-2 pr-3">分类</th>
                    <th className="py-2 pr-3 text-right">累计</th>
                    <th className="py-2 pr-3 text-right">24h</th>
                    <th className="py-2 pr-3">最近命中</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.top_total || []).map((c) => (
                    <tr key={c.config_key} className="border-b border-white/5">
                      <td className="py-2 pr-3 font-mono text-navy-200">{c.config_key}</td>
                      <td className="py-2 pr-3 text-navy-300">
                        {c.category_name || c.category_code}
                        {c.is_sensitive ? <span className="ml-1 text-warning-300">· 敏感</span> : null}
                      </td>
                      <td className="py-2 pr-3 text-right text-navy-100">{c.hit_count}</td>
                      <td className="py-2 pr-3 text-right text-navy-300">{c.hit_24h}</td>
                      <td className="py-2 pr-3 text-navy-400">
                        {c.last_hit_at ? new Date(c.last_hit_at).toLocaleString('zh-CN', { hour12: false }) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* 死代码候选 */}
          <section className="mt-5 rounded-2xl border border-warning-500/30 bg-warning-500/5 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-warning-200">
              <Skull className="h-4 w-4" />
              死代码候选
              <span className="ml-2 text-xs text-warning-300">hit_count &lt; 10 + 创建 &gt; 7 天</span>
            </h2>
            {(data.dead_candidates || []).length === 0 ? (
              <EmptyState
                title="没有死代码"
                description="所有配置项都被读过了"
                icon={<AlertTriangle className="h-5 w-5" />}
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-xs">
                  <thead>
                    <tr className="border-b border-white/5 text-left text-warning-300">
                      <th className="py-2 pr-3">配置键</th>
                      <th className="py-2 pr-3">配置名</th>
                      <th className="py-2 pr-3 text-right">累计</th>
                      <th className="py-2 pr-3">最近命中</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.dead_candidates.map((c) => (
                      <tr key={c.config_key} className="border-b border-white/5">
                        <td className="py-2 pr-3 font-mono text-warning-100">{c.config_key}</td>
                        <td className="py-2 pr-3 text-warning-200">{c.config_name}</td>
                        <td className="py-2 pr-3 text-right text-warning-100">{c.hit_count}</td>
                        <td className="py-2 pr-3 text-warning-300">
                          {c.last_hit_at ? new Date(c.last_hit_at).toLocaleDateString('zh-CN') : '从未'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      ) : null}
    </AdminShell>
  )
}
