import { Link } from 'react-router-dom'
import { AdminBadge, formatDateTime } from '@/components/admin/AdminUI'

export function CreationVerifyBadge({ summary }) {
  if (!summary?.hasReports) {
    return <span className="text-navy-400 text-xs">无复核报告</span>
  }
  if (summary.allPassed) {
    return <AdminBadge tone="success">复核通过</AdminBadge>
  }
  const failed = (summary.stages || []).filter((s) => s.passed === false && !s.skipped)
  return (
    <span title={failed.map((s) => s.label).join('、')}>
      <AdminBadge tone="danger">复核 {failed.length} 项未过</AdminBadge>
    </span>
  )
}

const STATUS_TONE = {
  ready: 'success',
  completed: 'success',
  blocked: 'danger',
  failed: 'danger',
  writing: 'warning',
  running: 'warning',
  reviewing: 'warning',
  scoring: 'warning',
  awaiting: 'warning',
  planning: 'default',
  draft: 'default',
  pending: 'default',
}

/** 创作项目运营摘要卡 — 用于轨迹页顶栏 */
export default function ProjectOpsSummary({ data, compact = false, onTabChange, onInspectRun }) {
  if (!data) return null

  const score =
    data.overall_score != null
      ? `${data.overall_score}${data.grade ? ` · ${data.grade}` : ''}`
      : '—'

  return (
    <div
      className={`sf-console-panel border border-white/5 ${
        compact ? 'p-4 space-y-3' : 'p-5 space-y-4'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className={`font-bold text-white ${compact ? 'text-base' : 'text-lg'}`}>
            {data.title || '未命名'}
          </h2>
          <p className="text-xs text-navy-300 font-mono mt-1 break-all">{data.project_id}</p>
          {data.drama_trace ? (
            <p className="text-xs text-indigo-300/90 mt-1">
              {data.drama_trace.track_mode_display || data.drama_trace.track_mode}
              {' · '}
              {data.drama_trace.current_stage_display || data.drama_trace.current_stage}
              {' · '}
              完成 {data.drama_trace.completion_rate ?? 0}%
            </p>
          ) : null}
        </div>
        <AdminBadge tone={STATUS_TONE[data.status] || 'default'}>
          {data.status_text || data.status}
        </AdminBadge>
      </div>

      {data.user_id ? (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <Link
            to={`/admin/users?q=${encodeURIComponent(data.user_phone || data.user_id)}`}
            className="text-gold-400 hover:text-gold-300 underline-offset-2 hover:underline"
          >
            查看用户 {data.user_phone || data.user_id}
          </Link>
        </div>
      ) : null}

      {(data.execution_failed_count ?? 0) > 0 && !compact ? (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-red-300/90">
            最近有 {data.execution_failed_count} 次失败 run
          </span>
          {onTabChange ? (
            <button
              type="button"
              onClick={() => onTabChange('runs')}
              className="text-xs text-gold-400 hover:text-gold-300 underline"
            >
              查看执行记录 →
            </button>
          ) : null}
          {data.latest_failed_run?.id && onInspectRun ? (
            <button
              type="button"
              onClick={() => onInspectRun(data.latest_failed_run.id)}
              className="text-xs text-red-300 hover:text-red-200 underline"
            >
              打开最近失败 run
            </button>
          ) : null}
        </div>
      ) : null}

      <div className={`grid gap-3 ${compact ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-4'}`}>
        {[
          { label: '用户', value: data.user_phone || data.user_id || '—' },
          { label: '创作入口', value: data.creation_entry || '—' },
          { label: '模式', value: data.pipeline_mode || '—' },
          { label: '题材', value: data.theme || '—' },
          { label: '集数', value: data.episode_count ?? '—' },
          { label: '进度', value: data.drama_trace?.completion_rate != null
              ? `${data.drama_trace.completion_rate}%`
              : data.progress_percent != null
                ? `${data.progress_percent}%`
                : '—' },
          { label: 'Drama 阶段', value: data.drama_trace?.current_stage_display || '—' },
          { label: '评分', value: score },
          {
            label: 'Agent 执行',
            value: `${data.execution_run_count ?? 0} 次`,
            hint:
              (data.execution_failed_count ?? 0) > 0
                ? `失败 ${data.execution_failed_count} 次`
                : undefined,
          },
        ]
          .filter((_, i) => !compact || i < 4)
          .map((item) => (
            <div key={item.label} className="rounded-xl border border-white/5 bg-slate-900/40 px-3 py-2">
              <p className="text-[10px] text-navy-400">{item.label}</p>
              <p className="text-sm text-white font-medium mt-0.5 truncate">{item.value}</p>
              {item.hint ? <p className="text-[10px] text-red-400/90 mt-0.5">{item.hint}</p> : null}
            </div>
          ))}
      </div>

      {!compact && (
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <CreationVerifyBadge summary={data.verify_summary} />
          {data.updated_at ? (
            <span className="text-navy-400">更新 {formatDateTime(data.updated_at)}</span>
          ) : null}
        </div>
      )}
    </div>
  )
}

export function ProjectFusionNodesPanel({ nodes = [] }) {
  if (!nodes.length) {
    return <p className="text-sm text-navy-400 py-6 text-center">暂无融合节点记录</p>
  }
  return (
    <div className="sf-console-panel overflow-hidden border border-white/5">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/5 text-navy-400 text-left">
            <th className="px-4 py-3 font-medium">步骤</th>
            <th className="px-4 py-3 font-medium">节点</th>
            <th className="px-4 py-3 font-medium">状态</th>
            <th className="px-4 py-3 font-medium hidden md:table-cell">摘要</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((n) => (
            <tr key={n.node_index} className="border-b border-white/10 text-navy-200">
              <td className="px-4 py-3 text-gold-400/90">{n.node_index}</td>
              <td className="px-4 py-3">
                <span className="text-white">{n.name || n.fusion_node_id}</span>
                <span className="text-navy-300 text-xs block font-mono">{n.fusion_node_id}</span>
              </td>
              <td className="px-4 py-3">
                <AdminBadge tone={STATUS_TONE[n.status] || 'default'}>{n.status}</AdminBadge>
              </td>
              <td className="px-4 py-3 text-xs text-navy-400 hidden md:table-cell max-w-xs truncate">
                {n.summary || '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function ProjectVerifyPanel({ summary }) {
  if (!summary?.hasReports) {
    return <p className="text-sm text-navy-400 py-6 text-center">该项目尚无原创复核报告</p>
  }
  const stages = summary.stages || []
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <CreationVerifyBadge summary={summary} />
        <span className="text-xs text-navy-400">
          {summary.allPassed ? '全部阶段通过' : '以下阶段需运营关注'}
        </span>
      </div>
      <ul className="space-y-2">
        {stages.map((stage) => (
          <li
            key={stage.key || stage.label}
            className="rounded-xl border border-white/5 bg-slate-900/40 px-4 py-3 flex flex-wrap items-center justify-between gap-2"
          >
            <span className="text-sm text-white">{stage.label || stage.key}</span>
            {stage.skipped ? (
              <AdminBadge tone="default">已跳过</AdminBadge>
            ) : stage.passed ? (
              <AdminBadge tone="success">通过</AdminBadge>
            ) : (
              <AdminBadge tone="danger">未通过</AdminBadge>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
