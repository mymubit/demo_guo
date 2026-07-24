import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { formatApiError } from '@/services/errors'
import { listScriptReviews } from '@/services/v3/reviews'

const LIST_KEY = ['v3', 'reviews', 'list'] as const

const SOURCE_LABEL: Record<string, string> = {
  paste: '粘贴',
  upload: '上传',
}

export function ScriptReviewsPage() {
  const navigate = useNavigate()
  const listQuery = useQuery({
    queryKey: LIST_KEY,
    queryFn: () => listScriptReviews(),
  })
  const items = listQuery.data?.items ?? []

  return (
    <PageShell
      title="剧本评审"
      description="粘贴或上传外界剧本，进行质量评分与合规审查，并保留历史对比。"
      actions={
        <Button type="button" onClick={() => navigate('/reviews/new')}>
          新建评审
        </Button>
      }
    >
      {listQuery.isLoading ? <p className="text-sm text-ink-muted">正在加载…</p> : null}
      {listQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(listQuery.error)}</p>
      ) : null}

      {listQuery.isSuccess && items.length === 0 ? (
        <div className="sf-panel p-8 text-center" data-testid="reviews-empty">
          <p className="text-ink">还没有评审件</p>
          <p className="mt-2 text-sm text-ink-muted">
            粘贴或上传 .txt / .md 剧本，即可独立评分，不影响项目交付门禁。
          </p>
          <Button type="button" className="mt-4" onClick={() => navigate('/reviews/new')}>
            去新建
          </Button>
        </div>
      ) : null}

      {items.length > 0 ? (
        <div className="sf-panel overflow-x-auto">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead className="border-b border-line text-ink-muted">
              <tr>
                <th className="px-4 py-3 font-medium">标题</th>
                <th className="px-4 py-3 font-medium">来源</th>
                <th className="px-4 py-3 font-medium">关联项目</th>
                <th className="px-4 py-3 font-medium">质量分</th>
                <th className="px-4 py-3 font-medium">合规</th>
                <th className="px-4 py-3 font-medium">更新</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-line/60 last:border-0">
                  <td className="px-4 py-3">
                    <Link
                      to={`/reviews/${item.id}`}
                      className="font-medium text-action hover:underline"
                      data-testid={`review-row-${item.id}`}
                    >
                      {item.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-ink-muted">
                    {SOURCE_LABEL[item.source_type] ?? item.source_type}
                  </td>
                  <td className="px-4 py-3 text-ink-muted">{item.project_title ?? '—'}</td>
                  <td className="px-4 py-3 tabular-nums">
                    {item.latest_quality_score != null
                      ? `${item.latest_quality_score}${item.latest_quality_grade ? ` (${item.latest_quality_grade})` : ''}`
                      : '—'}
                  </td>
                  <td className="px-4 py-3">{item.latest_compliance_result ?? '—'}</td>
                  <td className="px-4 py-3 text-ink-muted">
                    {item.updated_at ? new Date(item.updated_at).toLocaleString('zh-CN') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </PageShell>
  )
}
