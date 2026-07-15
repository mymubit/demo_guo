import { Badge } from '@/components/ui/Badge'

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
                {k}: {v}
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
