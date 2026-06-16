/**
 * 作品详情右侧 — 元信息面板
 */
import { KvRow } from '@/components/shared/ConsumerSection'
import { formatDateTime } from '@/utils/date'

export default function WorkMetaPanel({ work, themeName }) {
  if (!work) return null

  const rows = [
    { label: '题材', value: themeName || work.theme || '—' },
    { label: '集数', value: work.episode_count ? `${work.episode_count} 集` : '—' },
    {
      label: '评分',
      value: work.overall_score != null ? `${work.overall_score} / 100` : '生成中',
    },
    { label: '格式', value: work.format_variant || '通用' },
    { label: '创建', value: formatDateTime(work.created_at) },
    { label: '项目 ID', value: String(work.project_id || '').slice(0, 16) },
  ]

  return (
    <aside className="space-y-3.5">
      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
        <h3 className="m-0 mb-3 text-sm font-semibold text-white">剧本信息</h3>
        <dl className="space-y-0">
          {rows.map((row) => (
            <KvRow key={row.label} label={row.label} value={row.value} />
          ))}
        </dl>
      </div>
      {work.idea ? (
        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
          <h3 className="m-0 mb-2 text-sm font-semibold text-white">一句话创意</h3>
          <p className="m-0 text-[13px] leading-relaxed text-navy-200 line-clamp-6">{work.idea}</p>
        </div>
      ) : null}
    </aside>
  )
}
