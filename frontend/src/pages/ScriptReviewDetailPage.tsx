import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { DimensionBars } from '@/components/quality/DimensionBars'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { formatApiError } from '@/services/errors'
import {
  checkScriptReviewCompliance,
  getScriptReview,
  scoreScriptReview,
} from '@/services/v3/reviews'
import type { ScriptReviewRun, ScriptReviewRunKind } from '@/types/v3/domain'
import { cn } from '@/utils/cn'

const KIND_LABEL: Record<ScriptReviewRunKind, string> = {
  quality: '质量评分',
  compliance: '合规审查',
}

const STATUS_LABEL: Record<string, string> = {
  queued: '排队',
  running: '执行中',
  succeeded: '成功',
  failed: '失败',
}

function isInProgress(run: ScriptReviewRun | undefined): boolean {
  return Boolean(run && (run.status === 'queued' || run.status === 'running'))
}

export function ScriptReviewDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selected, setSelected] = useState<string[]>([])
  const [actionError, setActionError] = useState<string | null>(null)
  const [previewOpen, setPreviewOpen] = useState(true)

  const detailQuery = useQuery({
    queryKey: ['v3', 'reviews', 'detail', id],
    queryFn: () => getScriptReview(id),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const runs = query.state.data?.runs ?? []
      return runs.some((run) => isInProgress(run)) ? 2000 : false
    },
  })

  const scoreMutation = useMutation({
    mutationFn: () => scoreScriptReview(id),
    onSuccess: async () => {
      setActionError(null)
      await queryClient.invalidateQueries({ queryKey: ['v3', 'reviews', 'detail', id] })
    },
    onError: (err) => setActionError(formatApiError(err)),
  })

  const complianceMutation = useMutation({
    mutationFn: () => checkScriptReviewCompliance(id),
    onSuccess: async () => {
      setActionError(null)
      await queryClient.invalidateQueries({ queryKey: ['v3', 'reviews', 'detail', id] })
    },
    onError: (err) => setActionError(formatApiError(err)),
  })

  const review = detailQuery.data
  const runs = review?.runs ?? []
  const busy =
    scoreMutation.isPending ||
    complianceMutation.isPending ||
    runs.some((run) => isInProgress(run))

  const selectedRuns = useMemo(
    () => runs.filter((run) => selected.includes(run.id)),
    [runs, selected],
  )

  const canCompare =
    selectedRuns.length === 2 &&
    selectedRuns.every((run) => run.status === 'succeeded') &&
    selectedRuns[0]?.kind === selectedRuns[1]?.kind

  const latestSucceeded = useMemo(() => {
    return runs.find((run) => run.status === 'succeeded') ?? null
  }, [runs])

  const toggleSelect = (run: ScriptReviewRun) => {
    setSelected((prev) => {
      if (prev.includes(run.id)) return prev.filter((item) => item !== run.id)
      if (prev.length >= 2) return [prev[1], run.id]
      return [...prev, run.id]
    })
  }

  const handleCompare = () => {
    if (!canCompare || selectedRuns.length !== 2) return
    const [a, b] = selectedRuns
    navigate(`/reviews/${id}/compare?a=${a.id}&b=${b.id}`)
  }

  return (
    <PageShell
      title={review?.title ?? '评审详情'}
      description="触发质量评分 / 合规审查，查看历史记录并对比。"
      actions={
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={() => navigate('/reviews')}>
            返回列表
          </Button>
          <Button
            type="button"
            disabled={busy}
            onClick={() => scoreMutation.mutate()}
            data-testid="score-review"
          >
            质量评分
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={busy}
            onClick={() => complianceMutation.mutate()}
            data-testid="compliance-review"
          >
            合规审查
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={!canCompare}
            onClick={handleCompare}
            data-testid="compare-runs"
          >
            对比所选
          </Button>
        </div>
      }
    >
      {detailQuery.isLoading ? <p className="text-sm text-ink-muted">正在加载…</p> : null}
      {detailQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(detailQuery.error)}</p>
      ) : null}
      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}

      {review ? (
        <div className="space-y-4">
          <div className="sf-panel p-4 text-sm text-ink-muted">
            <p>
              来源：{review.source_type === 'upload' ? '上传' : '粘贴'}
              {review.source_filename ? ` · ${review.source_filename}` : ''}
              {review.project_title
                ? ` · 关联项目 ${review.project_title}`
                : ' · 未关联项目'}
            </p>
          </div>

          <section className="sf-panel p-4">
            <button
              type="button"
              className="mb-2 text-sm font-medium text-action"
              onClick={() => setPreviewOpen((v) => !v)}
            >
              {previewOpen ? '收起原文' : '展开原文'}
            </button>
            {previewOpen ? (
              <pre
                className="max-h-[24rem] overflow-auto whitespace-pre-wrap rounded-md bg-canvas-muted p-3 text-sm text-ink"
                data-testid="script-preview"
              >
                {review.script_text}
              </pre>
            ) : null}
          </section>

          {latestSucceeded?.kind === 'quality' ? (
            <section className="sf-panel p-4">
              <h2 className="mb-3 text-sm font-semibold text-ink">最近质量报告</h2>
              <p className="mb-3 text-sm text-ink">
                总分{' '}
                <span className="tabular-nums font-medium">
                  {String(latestSucceeded.report_payload.overall_score ?? '—')}
                </span>
                {latestSucceeded.report_payload.grade
                  ? ` · 等级 ${String(latestSucceeded.report_payload.grade)}`
                  : ''}
              </p>
              <DimensionBars dimensions={latestSucceeded.report_payload.dimensions} />
            </section>
          ) : null}

          <section className="sf-panel overflow-x-auto">
            <table className="w-full min-w-[36rem] text-left text-sm">
              <thead className="border-b border-line text-ink-muted">
                <tr>
                  <th className="px-3 py-2 font-medium">选</th>
                  <th className="px-3 py-2 font-medium">类型</th>
                  <th className="px-3 py-2 font-medium">状态</th>
                  <th className="px-3 py-2 font-medium">摘要</th>
                  <th className="px-3 py-2 font-medium">时间</th>
                </tr>
              </thead>
              <tbody>
                {runs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-ink-muted">
                      尚无评审记录，点击上方按钮开始。
                    </td>
                  </tr>
                ) : (
                  runs.map((run) => {
                    const summary =
                      run.kind === 'quality'
                        ? run.report_payload.overall_score != null
                          ? `总分 ${String(run.report_payload.overall_score)}`
                          : run.error_message || '—'
                        : run.report_payload.overall_result
                          ? String(run.report_payload.overall_result)
                          : run.error_message || '—'
                    return (
                      <tr key={run.id} className="border-b border-line/60 last:border-0">
                        <td className="px-3 py-2">
                          <input
                            type="checkbox"
                            checked={selected.includes(run.id)}
                            onChange={() => toggleSelect(run)}
                            disabled={run.status !== 'succeeded'}
                            aria-label={`选择 ${run.id}`}
                            data-testid={`select-run-${run.id}`}
                          />
                        </td>
                        <td className="px-3 py-2">{KIND_LABEL[run.kind]}</td>
                        <td className="px-3 py-2">
                          <span
                            className={cn(
                              run.status === 'failed' && 'text-danger',
                              run.status === 'succeeded' && 'text-ink',
                            )}
                          >
                            {STATUS_LABEL[run.status] ?? run.status}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-ink-muted">{summary}</td>
                        <td className="px-3 py-2 text-ink-muted">
                          {run.created_at
                            ? new Date(run.created_at).toLocaleString('zh-CN')
                            : '—'}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </section>
        </div>
      ) : null}
    </PageShell>
  )
}
