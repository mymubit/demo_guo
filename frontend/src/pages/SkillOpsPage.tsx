import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Download, Link2, RefreshCw, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyState, ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { PageShell } from '@/components/layout/PageShell'
import { adminApi, type SkillFailureItem, type SkillOpsOverview } from '@/services/admin'
import { formatApiError } from '@/services/errors'

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return iso
  }
}

function shortId(id: string | null | undefined, len = 8): string {
  if (!id) return '—'
  return id.length <= len ? id : `${id.slice(0, len)}…`
}

function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function SkillOpsPage() {
  const [roleFilter, setRoleFilter] = useState('')
  const [message, setMessage] = useState<string | null>(null)

  const overviewQuery = useQuery({
    queryKey: ['skill-ops', roleFilter],
    queryFn: () =>
      adminApi.getSkillOpsOverview({
        limit: 40,
        role: roleFilter.trim() || undefined,
      }),
  })

  const exportMutation = useMutation({
    mutationFn: () =>
      adminApi.exportSkillFailures({
        limit: 50,
        role: roleFilter.trim() || undefined,
      }),
    onSuccess: (data) => {
      downloadJson(`skill_failure_export_${Date.now()}.json`, data)
      setMessage(`已导出 ${data.count} 条（仅结构化失败，可回流 anti-examples）`)
    },
    onError: (err) => {
      setMessage(formatApiError(err))
    },
  })

  const data: SkillOpsOverview | undefined = overviewQuery.data
  const evalSummary = data?.eval_summary
  const repair = data?.repair_stats
  const noise = data?.noise_counts

  const roleOptions = useMemo(() => {
    const set = new Set<string>()
    for (const item of data?.failures ?? []) {
      if (item.role) set.add(item.role)
    }
    return [...set].sort()
  }, [data?.failures])

  return (
    <PageShell
      title="技能运维"
      description={
        data?.purpose ??
        '只收集「JSON/Schema 翻车」样本，用来改技能反例；超时和模型参数问题不在这里处理。'
      }
      actions={
        <>
          <Button
            variant="secondary"
            size="sm"
            iconLeft={<RefreshCw className="h-3.5 w-3.5" />}
            onClick={() => void overviewQuery.refetch()}
            disabled={overviewQuery.isFetching}
          >
            刷新
          </Button>
          <Button
            size="sm"
            iconLeft={<Download className="h-3.5 w-3.5" />}
            onClick={() => exportMutation.mutate()}
            disabled={exportMutation.isPending || (data?.failure_count ?? 0) === 0}
          >
            导出反例草稿
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-5">
        {message ? (
          <div className="rounded-lg border border-border bg-canvas-muted px-3 py-2 text-sm text-ink-muted">
            {message}
          </div>
        ) : null}

        {overviewQuery.isError ? <ErrorBanner message={formatApiError(overviewQuery.error)} /> : null}
        {overviewQuery.isLoading ? <LoadingBlock label="加载技能运维数据…" /> : null}

        {data ? (
          <>
            <section className="grid gap-3 sm:grid-cols-3">
              <StatCard
                label="可回流的结构化失败"
                value={String(data.failure_count)}
                hint="json_repair / Schema / 非法 JSON"
              />
              <StatCard
                label="离线评测通过率"
                value={
                  evalSummary?.pass_rate != null
                    ? `${Math.round(Number(evalSummary.pass_rate) * 100)}%`
                    : '—'
                }
                hint={
                  evalSummary
                    ? `${evalSummary.passed}/${evalSummary.total} 通过`
                    : '尚无 summary.json'
                }
              />
              <StatCard
                label="纠错调用成功率"
                value={
                  repair?.repair_success_rate != null
                    ? `${Math.round(Number(repair.repair_success_rate) * 100)}%`
                    : '—'
                }
                hint={
                  repair && repair.repair_calls > 0
                    ? `${repair.repair_success}/${repair.repair_calls} 次纠错成功`
                    : '尚无 json_repair 调用'
                }
              />
            </section>

            {noise?.infra || noise?.provider_config ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                已过滤噪音：基础设施/超时 {noise?.infra ?? 0} 条，模型参数（如不支持 json_object）
                {noise?.provider_config ?? 0} 条。这些请去
                <Link className="mx-1 font-medium underline" to="/admin/llm/logs">
                  LLM 调用
                </Link>
                或
                <Link className="mx-1 font-medium underline" to="/admin/model">
                  模型管理
                </Link>
                处理，不用写进技能反例。
              </div>
            ) : null}

            <section className="sf-panel overflow-hidden">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-amber-600" />
                  <h2 className="text-sm font-semibold text-ink">结构化失败（可改技能）</h2>
                </div>
                <label className="flex items-center gap-2 text-xs text-ink-muted">
                  角色
                  <select
                    className="sf-control w-auto py-1"
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value)}
                  >
                    <option value="">全部</option>
                    {roleOptions.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {data.failures.length === 0 ? (
                <EmptyState
                  title="暂无可回流失败"
                  description="生成任务出现 JSON/Schema 不合规时，会显示在这里，便于改 anti-examples。"
                />
              ) : (
                <ul className="divide-y divide-border">
                  {data.failures.map((item) => (
                    <FailureRow key={item.id} item={item} />
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : null}
      </div>
    </PageShell>
  )
}

function StatCard({
  label,
  value,
  hint,
}: {
  label: string
  value: string
  hint: string
}) {
  return (
    <div className="sf-panel px-4 py-3">
      <div className="text-xs font-medium text-ink-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold tracking-tight text-ink">{value}</div>
      <div className="mt-1 text-xs text-ink-muted">{hint}</div>
    </div>
  )
}

function FailureRow({ item }: { item: SkillFailureItem }) {
  return (
    <li className="px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-ink-muted">{shortId(item.id)}</span>
            <Badge tone="warning">结构化</Badge>
            <span className="text-sm font-medium text-ink">{item.role || '—'}</span>
            <span className="text-xs text-ink-muted">{item.purpose}</span>
          </div>
          <p className="mt-1 text-sm text-ink">{item.error_message || '结构化输出失败'}</p>
          {item.response_preview ? (
            <pre className="mt-2 max-h-24 overflow-auto rounded-lg bg-canvas-muted p-2 text-[11px] text-ink-muted">
              {item.response_preview}
            </pre>
          ) : null}
        </div>
        <div className="shrink-0 text-right text-xs text-ink-muted">
          <div>{formatTime(item.created_at)}</div>
          {item.job_id ? (
            <Link
              className="mt-1 inline-flex items-center gap-1 text-action hover:underline"
              to={`/admin/llm/chains?job_id=${item.job_id}`}
            >
              <Link2 className="h-3 w-3" />
              调用链
            </Link>
          ) : null}
        </div>
      </div>
    </li>
  )
}
