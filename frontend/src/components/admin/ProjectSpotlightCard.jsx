import { Eye, Wrench, Download } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import PipelineStageBar from '@/components/shared/PipelineStageBar'

function stateTone(status) {
  if (status === 'completed') return 'success'
  if (status === 'running') return 'info'
  if (status === 'review' || status === 'awaiting') return 'warning'
  if (status === 'failed') return 'danger'
  return 'default'
}

function stateText(status, statusText) {
  if (statusText) return statusText
  if (status === 'completed') return '已完成'
  if (status === 'running') return '运行中'
  if (status === 'awaiting') return '待确认'
  if (status === 'failed') return '失败'
  return status || '—'
}

function mapBarState(status) {
  if (status === 'completed') return 'completed'
  if (status === 'failed') return 'failed'
  if (status === 'running') return 'running'
  return 'idle'
}

export default function ProjectSpotlightCard({
  project,
  onTrace,
  onFullTrace,
  onIntervene,
  onDownload,
}) {
  const {
    project_id: id,
    title,
    user_phone: userPhone,
    user_id: userId,
    theme,
    episodes,
    current_node: currentNode = 1,
    status,
    status_text: statusText,
    overall_score: score,
    elapsed,
    remain,
    cover_url: coverUrl,
  } = project

  const user = userPhone || userId || '—'
  const isCompleted = status === 'completed'
  const barState = mapBarState(status)

  return (
    <article className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
      <div className="flex items-center gap-3">
        <div
          className="h-14 w-14 flex-none rounded-xl bg-cover bg-center bg-slate-800/80"
          style={coverUrl ? { backgroundImage: `url(${coverUrl})` } : undefined}
          aria-label={title}
        />
        <div className="min-w-0 flex-1">
          <h3 className="m-0 truncate text-[15px] font-semibold text-white">
            {title || '未命名'} · {id}
          </h3>
          <div className="mt-0.5 text-xs text-slate-500">
            用户 {user} · {theme || '—'} · {episodes ?? '—'} 集 · 第 {currentNode} 节点
          </div>
        </div>
        <Badge tone={stateTone(status)} size="md">
          {stateText(status, statusText)}
        </Badge>
      </div>

      <div className="mt-3.5">
        <PipelineStageBar currentNode={currentNode} state={barState} />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {isCompleted ? (
          <>
            <span>
              评分 <b className="text-white">{score ?? '—'}</b>
              {elapsed ? ` · ${elapsed}` : ''}
            </span>
            <span className="ml-auto" />
            {onDownload ? (
              <Button variant="secondary" size="sm" iconLeft={<Download className={ICON.sm} />} onClick={onDownload}>
                下载剧本
              </Button>
            ) : null}
            <Button variant="primary" size="sm" iconLeft={<Eye className={ICON.sm} />} onClick={onTrace}>
              回看 Trace
            </Button>
          </>
        ) : (
          <>
            <span>
              {elapsed ? `耗时 ${elapsed}` : '进行中'}
              {remain ? ` · 剩余 ${remain}` : ''}
            </span>
            <span className="ml-auto" />
            <Button variant="secondary" size="sm" iconLeft={<Eye className={ICON.sm} />} onClick={onTrace}>
              查看 Trace
            </Button>
            {onIntervene ? (
              <Button variant="primary" size="sm" iconLeft={<Wrench className={ICON.sm} />} onClick={onIntervene}>
                手动介入
              </Button>
            ) : (
              onFullTrace && (
                <Button variant="primary" size="sm" iconLeft={<Eye className={ICON.sm} />} onClick={onFullTrace}>
                  完整监察
                </Button>
              )
            )}
          </>
        )}
      </div>
    </article>
  )
}
