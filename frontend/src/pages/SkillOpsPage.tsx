import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, Download, Link2, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { FilterEmptyState } from '@/components/layout/FilterEmptyState'
import { ListPageToolbar } from '@/components/layout/ListPageToolbar'
import { OpsPageShell } from '@/components/ops/OpsPageShell'
import { OpsStatusStrip } from '@/components/ops/OpsStatusStrip'
import { adminApi, type SkillFailureItem, type SkillOpsOverview } from '@/services/admin'
import { formatApiError } from '@/services/errors'
import { formatRoleLabel } from '@/utils/roleLabels'

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

function failureTypeLabel(item: SkillFailureItem): string {
  const msg = (item.error_message || '').toLowerCase()
  if (/schema|不合规|required property|校验失败|is not of type/.test(msg)) return 'Schema 未通过'
  if (/json|parse|decode|unexpected token|expecting property/.test(msg)) return 'JSON 非法'
  if (/repair|纠错/.test(msg)) return '纠错失败'
  return '结构化失败'
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
    <OpsPageShell
      title="技能运维"
      description={
        data?.purpose ??
        '收集 JSON/Schema 翻车样本，用来改技能反例；超时和模型参数问题请去 LLM 调用或模型管理。'
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
            variant="secondary"
            size="sm"
            iconLeft={<Download className="h-3.5 w-3.5" />}
            onClick={() => exportMutation.mutate()}
            disabled={exportMutation.isPending || (data?.failure_count ?? 0) === 0}
          >
            导出失败样本
          </Button>
        </>
      }
      status={
        message ? (
          <div className="rounded-lg border border-border bg-canvas-muted px-3 py-2 text-sm text-ink-muted">
            {message}
          </div>
        ) : null
      }
      toolbar={
        data ? (
          <ListPageToolbar
            count={data.failures.length}
            countLabel="条"
            filters={[
              {
                id: 'role',
                label: '角色',
                value: roleFilter,
                onChange: setRoleFilter,
                options: [
                  { value: '', label: '全部' },
                  ...roleOptions.map((role) => ({
                    value: role,
                    label: formatRoleLabel(role),
                  })),
                ],
              },
            ]}
          />
        ) : undefined
      }
    >
      {overviewQuery.isError ? <ErrorBanner message={formatApiError(overviewQuery.error)} /> : null}
      {overviewQuery.isLoading ? <LoadingBlock label="加载技能运维数据…" /> : null}

      {data ? (
        <div className="space-y-5">
          <section className="grid gap-3 sm:grid-cols-3">
            <StatCard
              label="可回流失败"
              value={String(data.failure_count)}
              hint="含 json_repair / Schema / 非法 JSON"
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
              label="纠错成功率"
              value={
                repair?.repair_success_rate != null
                  ? `${Math.round(Number(repair.repair_success_rate) * 100)}%`
                  : '—'
              }
              hint={
                repair && repair.repair_calls > 0
                  ? `${repair.repair_success}/${repair.repair_calls} 次 json_repair 成功`
                  : '尚无纠错调用'
              }
            />
          </section>

          {noise?.infra || noise?.provider_config ? (
            <OpsStatusStrip
              tone="warning"
              summary={`已过滤噪音：超时/基建 ${noise?.infra ?? 0} · 模型参数 ${noise?.provider_config ?? 0}`}
            >
              <p>
                这些样本不写进技能反例。请到
                <Link className="mx-1 font-medium underline" to="/admin/llm/logs">
                  LLM 调用
                </Link>
                或
                <Link className="mx-1 font-medium underline" to="/admin/model">
                  模型管理
                </Link>
                处理。
              </p>
            </OpsStatusStrip>
          ) : null}

          {data.failures.length === 0 ? (
            <FilterEmptyState
              title="暂无可回流失败"
              description="生成任务出现 JSON/Schema 不合规时，会显示在这里，便于改 anti-examples。"
              variant="inbox"
            />
          ) : (
            <div className="sf-panel overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="w-36">角色</TableHead>
                    <TableHead className="w-32">失败类型</TableHead>
                    <TableHead className="w-36">时间</TableHead>
                    <TableHead className="w-28 text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.failures.map((item) => (
                    <FailureRow key={item.id} item={item} />
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      ) : null}
    </OpsPageShell>
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
      <div className="mt-1 text-xs text-ink-faint">{hint}</div>
    </div>
  )
}

function FailureRow({ item }: { item: SkillFailureItem }) {
  const [previewOpen, setPreviewOpen] = useState(false)
  const roleLabel = formatRoleLabel(item.role)
  const typeLabel = failureTypeLabel(item)

  return (
    <TableRow className="hover:bg-canvas-muted/60">
      <TableCell>
        <div className="text-sm font-medium text-ink">{roleLabel}</div>
        {item.role ? (
          <div className="mt-0.5 font-mono text-[11px] text-ink-faint">{item.role}</div>
        ) : null}
      </TableCell>
      <TableCell>
        <div className="text-sm text-ink">{typeLabel}</div>
        {item.error_message ? (
          <p className="mt-0.5 line-clamp-2 text-[11px] text-ink-muted">{item.error_message}</p>
        ) : null}
        {item.response_preview ? (
          <div className="mt-1">
            <button
              type="button"
              className="inline-flex items-center gap-1 text-[11px] text-ink-faint hover:text-ink-muted"
              onClick={() => setPreviewOpen((v) => !v)}
            >
              {previewOpen ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              {previewOpen ? '收起预览' : '展开预览'}
            </button>
            {previewOpen ? (
              <pre className="mt-1 max-h-24 overflow-auto rounded-lg bg-canvas-muted p-2 text-[11px] text-ink-muted">
                {item.response_preview}
              </pre>
            ) : null}
          </div>
        ) : null}
      </TableCell>
      <TableCell className="text-xs text-ink-muted">{formatTime(item.created_at)}</TableCell>
      <TableCell className="text-right">
        {item.job_id ? (
          <Link
            className="inline-flex items-center gap-1 text-xs font-medium text-action hover:underline"
            to={`/admin/llm/logs?job_id=${item.job_id}`}
          >
            <Link2 className="h-3 w-3" />
            看调用链
          </Link>
        ) : (
          <span className="text-xs text-ink-faint">—</span>
        )}
      </TableCell>
    </TableRow>
  )
}
