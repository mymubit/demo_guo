import { Badge } from '@/components/ui/Badge'

const GENRE_AXIS_LABELS: Record<string, string> = {
  emotion: '情绪卖点',
  identity: '身份设定',
  conflict: '冲突类型',
  world: '世界观',
  audience: '受众',
  tone: '调性',
}

export function ProjectBriefView({ data }: { data: Record<string, unknown> }) {
  const genre = data.genre_matrix as Record<string, string> | undefined
  return (
    <div className="space-y-4">
      <header>
        <h3 className="text-xl font-semibold text-ink">{String(data.title ?? '项目简报')}</h3>
        <p className="mt-2 text-sm text-ink-muted">{String(data.core_idea ?? '')}</p>
      </header>
      <div className="flex flex-wrap gap-2">
        {genre
          ? Object.entries(genre).map(([k, v]) => (
              <Badge key={k} tone="brand">
                {GENRE_AXIS_LABELS[k] ?? k}：{v}
              </Badge>
            ))
          : null}
        {data.compliance_risk ? <Badge tone="warning">风险 {String(data.compliance_risk)}</Badge> : null}
      </div>
      <dl className="grid grid-cols-2 gap-4 text-sm">
        {(
          [
            ['目标受众', data.target_audience],
            ['核心冲突', data.core_conflict],
            ['钩子概念', data.hook_concept],
            ['商业钩子', data.commercial_hook],
            ['首集钩子', data.first_episode_hook],
            ['集数', data.episode_count],
          ] as Array<[string, unknown]>
        ).map(([label, value]) =>
          value != null && value !== '' ? (
            <div key={label} className="sf-panel p-3">
              <dt className="text-xs text-ink-faint">{label}</dt>
              <dd className="mt-1 text-ink">{String(value)}</dd>
            </div>
          ) : null,
        )}
      </dl>
    </div>
  )
}

/** 质检/合规/润色及通用产物的结构化展示，避免整页 JSON */
export function ReportArtifactView({
  kind,
  data,
}: {
  kind: 'quality_report' | 'compliance_report' | 'polished_script' | 'generic'
  data: Record<string, unknown>
}) {
  if (kind === 'quality_report') {
    const dimensions = (data.dimensions ?? {}) as Record<string, { score?: number; comment?: string }>
    return (
      <div className="space-y-4">
        <header className="sf-panel p-4">
          <h3 className="text-lg font-semibold text-ink">质量评分报告</h3>
          <div className="mt-2 flex flex-wrap gap-3 text-sm text-ink">
            <span>
              总分：<strong>{String(data.overall_score ?? '—')}</strong>
            </span>
            <span>
              等级：<strong>{String(data.grade ?? '—')}</strong>
            </span>
            <span>
              结论：<strong>{String(data.verdict ?? '—')}</strong>
            </span>
            {data.needs_revision != null ? (
              <Badge tone={data.needs_revision ? 'warning' : 'success'}>
                {data.needs_revision ? '建议修订' : '可放行'}
              </Badge>
            ) : null}
          </div>
        </header>
        {Object.keys(dimensions).length > 0 ? (
          <ul className="grid gap-2 sm:grid-cols-2">
            {Object.entries(dimensions).map(([key, dim]) => (
              <li key={key} className="sf-panel p-3 text-sm">
                <div className="font-medium text-ink">{key}</div>
                <div className="mt-1 text-ink-muted">得分 {dim.score ?? '—'}</div>
                {dim.comment ? <p className="mt-1 text-xs text-ink-muted">{dim.comment}</p> : null}
              </li>
            ))}
          </ul>
        ) : (
          <KeyValueFallback data={data} omit={['dimensions']} />
        )}
      </div>
    )
  }

  if (kind === 'compliance_report') {
    const risks = Array.isArray(data.risk_items) ? data.risk_items : []
    const blocking = Array.isArray(data.blocking_issues) ? data.blocking_issues : []
    return (
      <div className="space-y-4">
        <header className="sf-panel p-4">
          <h3 className="text-lg font-semibold text-ink">合规审查报告</h3>
          <p className="mt-2 text-sm text-ink">
            总评：<strong>{String(data.overall_result ?? '—')}</strong>
          </p>
        </header>
        {blocking.length > 0 ? (
          <section className="sf-panel space-y-2 p-4">
            <h4 className="text-sm font-medium text-red-700">阻断项</h4>
            <ul className="list-disc space-y-1 pl-5 text-sm text-ink">
              {blocking.map((item, idx) => (
                <li key={idx}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>
              ))}
            </ul>
          </section>
        ) : null}
        {risks.length > 0 ? (
          <section className="space-y-2">
            <h4 className="text-sm font-medium text-ink">风险项</h4>
            {risks.map((item, idx) => {
              const row = item as { type?: string; description?: string; suggestion?: string }
              return (
                <div key={idx} className="sf-panel p-3 text-sm">
                  <div className="font-medium text-ink">{row.type || `风险 ${idx + 1}`}</div>
                  {row.description ? <p className="mt-1 text-ink-muted">{row.description}</p> : null}
                  {row.suggestion ? <p className="mt-1 text-xs text-brand-700">建议：{row.suggestion}</p> : null}
                </div>
              )
            })}
          </section>
        ) : (
          <p className="text-sm text-ink-muted">暂无风险项明细。</p>
        )}
      </div>
    )
  }

  if (kind === 'polished_script') {
    const content =
      (typeof data.content === 'string' && data.content) ||
      (typeof data.script_content === 'string' && data.script_content) ||
      (typeof data.polished_text === 'string' && data.polished_text) ||
      ''
    return (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-ink">修复稿 / 润色稿</h3>
        {content ? (
          <pre className="sf-panel max-h-[70vh] overflow-auto whitespace-pre-wrap p-4 text-sm leading-relaxed text-ink">
            {content}
          </pre>
        ) : (
          <KeyValueFallback data={data} />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-ink">阶段产物</h3>
      <KeyValueFallback data={data} />
    </div>
  )
}

function KeyValueFallback({
  data,
  omit = [],
}: {
  data: Record<string, unknown>
  omit?: string[]
}) {
  const entries = Object.entries(data).filter(([k]) => !omit.includes(k))
  if (entries.length === 0) {
    return <p className="text-sm text-ink-muted">暂无结构化字段。</p>
  }
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div key={key} className="sf-panel p-3 text-sm">
          <dt className="text-xs text-ink-faint">{key}</dt>
          <dd className="mt-1 whitespace-pre-wrap text-ink">
            {typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
              ? String(value)
              : Array.isArray(value)
                ? value.length === 0
                  ? '—'
                  : value.map((v) => (typeof v === 'string' ? v : JSON.stringify(v))).join('；')
                : value && typeof value === 'object'
                  ? JSON.stringify(value, null, 2)
                  : '—'}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function StoryBibleView({
  data,
  onApprove,
  onReject,
  approvalPending,
  waitingApproval,
}: {
  data: Record<string, unknown>
  onApprove?: () => void
  onReject?: () => void
  approvalPending?: boolean
  waitingApproval?: boolean
}) {
  const synopsis = data.synopsis as { short?: string; full?: string } | undefined
  const characters = (data.characters as Array<Record<string, unknown>> | undefined) ?? []
  const world = data.world_rules as Record<string, unknown> | undefined

  return (
    <div className="space-y-5">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold text-ink">{String(data.drama_title ?? '剧本蓝图')}</h3>
          <p className="mt-2 text-sm text-ink-muted">{String(data.logline ?? '')}</p>
        </div>
        {waitingApproval ? (
          <div className="flex gap-2">
            <button
              type="button"
              disabled={approvalPending}
              onClick={onReject}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
            >
              驳回
            </button>
            <button
              type="button"
              disabled={approvalPending}
              onClick={onApprove}
              className="rounded-lg bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-600"
            >
              批准蓝图
            </button>
          </div>
        ) : null}
      </header>

      <section className="sf-panel p-4">
        <h4 className="text-sm font-semibold">梗概</h4>
        <p className="mt-2 text-sm text-ink">{synopsis?.short}</p>
        {synopsis?.full ? <p className="mt-2 whitespace-pre-wrap text-sm text-ink-muted">{synopsis.full}</p> : null}
      </section>

      {world ? (
        <section className="sf-panel p-4">
          <h4 className="text-sm font-semibold">世界规则</h4>
          <p className="mt-2 text-sm text-ink-muted">{String(world.setting_summary ?? '')}</p>
        </section>
      ) : null}

      <section>
        <h4 className="mb-2 text-sm font-semibold">人物</h4>
        <div className="grid grid-cols-2 gap-3">
          {characters.map((c, idx) => (
            <div key={`${String(c.name)}-${idx}`} className="sf-panel p-3">
              <div className="flex items-center justify-between">
                <span className="font-medium text-ink">{String(c.name)}</span>
                <Badge>{String(c.role_type)}</Badge>
              </div>
              <p className="mt-2 text-xs text-ink-muted">{String(c.arc ?? '')}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export function NarrativePlanView({ data }: { data: Record<string, unknown> }) {
  const cards =
    (data.episode_narrative_designs as Array<Record<string, unknown>> | undefined) ?? []
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-ink">分集叙事计划</h3>
      <div className="grid grid-cols-1 gap-3">
        {cards.map((card) => (
          <article key={String(card.episode)} className="sf-panel p-4">
            <div className="flex items-center justify-between gap-3">
              <h4 className="font-medium text-ink">
                EP{String(card.episode)} · {String(card.title)}
              </h4>
              <Badge tone="brand">{String(card.hook_grade ?? '')}</Badge>
            </div>
            <p className="mt-2 text-sm text-ink-muted">{String(card.core_event ?? '')}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-ink-muted">
              <div>开场钩子：{String(card.opening_hook ?? '—')}</div>
              <div>结尾钩子：{String(card.ending_hook ?? '—')}</div>
              <div>情绪强度：{String(card.emotion_intensity ?? '—')}</div>
              <div>付费卡点：{String(card.paywall_hook ?? '—')}</div>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}

export function EpisodeScriptsView({ data }: { data: Record<string, unknown> }) {
  const episodes = (data.episodes as Array<Record<string, unknown>> | undefined) ?? []
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-ink">分集正文</h3>
      {episodes.map((ep) => {
        const production = ep.production_notes as Record<string, unknown> | undefined
        return (
          <article key={String(ep.episode_number)} className="sf-panel overflow-hidden">
            <header className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
              <div>
                <h4 className="font-medium text-ink">
                  第 {String(ep.episode_number)} 集 · {String(ep.title)}
                </h4>
                <p className="mt-1 text-xs text-ink-muted">
                  字数 {String(ep.word_count)} · 对白比{' '}
                  {typeof ep.dialogue_ratio === 'number'
                    ? `${Math.round(ep.dialogue_ratio * 100)}%`
                    : '—'}{' '}
                  · 场景 {String(ep.scene_count)}
                </p>
              </div>
              {production ? (
                <Badge tone="info">{String(production.complexity_band)}</Badge>
              ) : null}
            </header>
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap bg-canvas px-4 py-3 text-sm leading-relaxed text-ink">
              {String(ep.script ?? '')}
            </pre>
            {production ? (
              <footer className="border-t border-slate-100 px-4 py-3 text-xs text-ink-muted">
                制片标签：{Array.isArray(production.tags) ? production.tags.join('、') : '—'}
                {Array.isArray(production.high_cost_scenes) && production.high_cost_scenes.length > 0
                  ? ` · 高成本场景：${production.high_cost_scenes.join('、')}`
                  : ''}
              </footer>
            ) : null}
          </article>
        )
      })}
    </div>
  )
}
