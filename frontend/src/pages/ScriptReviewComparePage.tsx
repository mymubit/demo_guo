import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { DimensionBars } from '@/components/quality/DimensionBars'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { formatApiError } from '@/services/errors'
import { compareScriptReviewRuns } from '@/services/v3/reviews'
import type { ScriptReviewCompareSide } from '@/types/v3/domain'

function SidePanel({
  title,
  side,
  kind,
}: {
  title: string
  side: ScriptReviewCompareSide
  kind: string
}) {
  const dimsRecord = Object.fromEntries(
    (side.dimensions ?? []).map((item) => [
      item.key,
      { score: item.score, weight: item.weight },
    ]),
  )

  return (
    <section className="sf-panel space-y-3 p-4" data-testid={`compare-${title}`}>
      <h2 className="text-sm font-semibold text-ink">{title}</h2>
      <p className="text-xs text-ink-muted">
        {side.created_at ? new Date(side.created_at).toLocaleString('zh-CN') : '—'}
      </p>
      {kind === 'quality' ? (
        <>
          <p className="text-sm text-ink">
            总分{' '}
            <span className="tabular-nums font-medium">
              {String(side.summary.overall_score ?? '—')}
            </span>
            {side.summary.grade ? ` · ${String(side.summary.grade)}` : ''}
          </p>
          <DimensionBars dimensions={dimsRecord} />
        </>
      ) : (
        <p className="text-sm text-ink">
          结论 {String(side.summary.overall_result ?? '—')}
          {' · '}阻断 {String(side.summary.blocking_count ?? 0)}
          {' · '}风险 {String(side.summary.risk_count ?? 0)}
        </p>
      )}
      {side.top_defects.length > 0 ? (
        <ul className="list-disc space-y-1 pl-5 text-sm text-ink-muted">
          {side.top_defects.slice(0, 5).map((item, index) => (
            <li key={index}>
              {typeof item === 'string'
                ? item
                : item && typeof item === 'object'
                  ? String(
                      (item as Record<string, unknown>).title ??
                        (item as Record<string, unknown>).finding_key ??
                        JSON.stringify(item).slice(0, 80),
                    )
                  : String(item)}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-ink-muted">无关键缺陷摘要</p>
      )}
    </section>
  )
}

export function ScriptReviewComparePage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const a = (params.get('a') || '').trim()
  const b = (params.get('b') || '').trim()

  const compareQuery = useQuery({
    queryKey: ['v3', 'reviews', 'compare', id, a, b],
    queryFn: () => compareScriptReviewRuns(id, a, b),
    enabled: Boolean(id && a && b),
  })

  const data = compareQuery.data

  return (
    <PageShell
      title="评审对比"
      description="同类型两条成功记录的指标并排对比（不做正文 diff）。"
      actions={
        <Button type="button" variant="secondary" onClick={() => navigate(`/reviews/${id}`)}>
          返回详情
        </Button>
      }
    >
      {!a || !b ? (
        <p className="text-sm text-danger">缺少对比参数 a / b</p>
      ) : null}
      {compareQuery.isLoading ? <p className="text-sm text-ink-muted">正在加载对比…</p> : null}
      {compareQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(compareQuery.error)}</p>
      ) : null}

      {data ? (
        <div className="space-y-4">
          <p className="text-sm text-ink-muted" data-testid="compare-delta">
            类型：{data.kind === 'quality' ? '质量评分' : '合规审查'}
            {data.deltas.overall_score != null
              ? ` · 总分差（右−左） ${data.deltas.overall_score}`
              : ''}
            {data.deltas.blocking_count != null
              ? ` · 阻断项差（右−左） ${data.deltas.blocking_count}`
              : ''}
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            <SidePanel title="左侧" side={data.left} kind={data.kind} />
            <SidePanel title="右侧" side={data.right} kind={data.kind} />
          </div>
        </div>
      ) : null}
    </PageShell>
  )
}
