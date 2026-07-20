import { useState, type ReactNode } from 'react'
import { Badge } from '@/components/ui/Badge'
import {
  asDisplayText,
  formatArcParts,
  formatConflictItem,
  formatRootRule,
  isPlaceholder,
  pickMeaningfulText,
} from '@/utils/artifactDisplay'

const ROLE_TYPE_ZH: Record<string, string> = {
  protagonist: '主角',
  antagonist: '对手',
  supporting: '配角',
  cameo: '客串',
}

const ROLE_TONE: Record<string, 'action' | 'danger' | 'info' | 'default'> = {
  protagonist: 'action',
  antagonist: 'danger',
  supporting: 'info',
  cameo: 'default',
}

function Section({ ask, children }: { ask: string; children: ReactNode }) {
  return (
    <section className="space-y-4">
      <h4 className="text-sm font-semibold text-ink">{ask}</h4>
      {children}
    </section>
  )
}

function QuietField({
  label,
  note,
  text,
}: {
  label: string
  /** 术语备注，帮助非编剧用户理解 */
  note?: string
  text: string
}) {
  return (
    <div className="space-y-1">
      <div className="text-[11px] font-medium text-ink-faint">
        {label}
        {note ? <span className="font-normal text-ink-faint/80"> · {note}</span> : null}
      </div>
      <p className="text-[14px] leading-7 text-ink">{text}</p>
    </div>
  )
}

/** 人物术语备注 */
const CHAR_FIELD_NOTES = {
  desire: '表面追逐的目标，观众最先看见的动机',
  need: '内心真正该学会的课题，往往与「想要」冲突',
  ghost: '过去放不下的旧伤/心结，持续影响当下选择',
  lie: '因旧伤形成的错误信念，角色信以为真',
  flaw: '性格或行为上的弱点，常导致失误与代价',
  voice: '说话习惯与语气特征，方便后文统一对白风格',
  visual: '一眼能认出的外形符号，便于镜头记忆',
  arc: '角色从故事开始到结束的变化轨迹',
} as const

const ARC_PART_NOTES: Record<string, string> = {
  起点: '开场时的状态与信念',
  转折一: '中段第一次重大改变',
  转折二: '最低谷或信念崩塌处',
  终局: '结局时成为什么样的人',
}

const STAGE_FIELD_NOTES = {
  target: '本幕剧情要达成的叙事任务',
  escalation: '冲突从轻到重的推进方向',
  turn: '发生后无法回头的关键事件',
} as const

function parsePowerBlocks(powerText: string): { summary: string; actors: string[] } {
  const marker = '关键人物：'
  const idx = powerText.indexOf(marker)
  if (idx < 0) return { summary: powerText.trim(), actors: [] }
  const summary = powerText.slice(0, idx).trim()
  const actorsRaw = powerText.slice(idx + marker.length).trim()
  const actors = actorsRaw
    .split('；')
    .map((item) => item.trim())
    .filter(Boolean)
  return { summary, actors }
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
  const [synopsisOpen, setSynopsisOpen] = useState(false)
  const [openChars, setOpenChars] = useState<Record<string, boolean>>({})

  const synopsis = data.synopsis as { short?: string; full?: string } | undefined
  const characters = (data.characters as Array<Record<string, unknown>> | undefined) ?? []
  const world = data.world_rules as Record<string, unknown> | undefined
  const rootRules = (Array.isArray(world?.root_rules) ? world.root_rules : [])
    .map((item) => formatRootRule(item))
    .filter((item): item is NonNullable<typeof item> => item != null)

  const powerText = (() => {
    const raw = world?.power_structure
    if (typeof raw === 'string') return isPlaceholder(raw) ? '' : raw.trim()
    if (raw && typeof raw === 'object') {
      const obj = raw as Record<string, unknown>
      const chunks: string[] = []
      const desc = pickMeaningfulText(obj.description, obj.summary)
      if (desc) chunks.push(desc)
      const actors = Array.isArray(obj.key_actors) ? obj.key_actors : []
      const actorLines: string[] = []
      for (const actor of actors) {
        if (!actor || typeof actor !== 'object') continue
        const row = actor as Record<string, unknown>
        const name = pickMeaningfulText(row.name)
        if (!name) continue
        const bits = [
          pickMeaningfulText(row.position),
          pickMeaningfulText(row.resources) && `资源：${pickMeaningfulText(row.resources)}`,
          pickMeaningfulText(row.motivation) && `动机：${pickMeaningfulText(row.motivation)}`,
        ].filter(Boolean)
        actorLines.push(bits.length ? `${name}（${bits.join('；')}）` : name)
      }
      if (actorLines.length) chunks.push(`关键人物：${actorLines.join('；')}`)
      return chunks.join('\n')
    }
    return ''
  })()
  const powerBlocks = powerText ? parsePowerBlocks(powerText) : null

  const relationships =
    (data.relationship_map as Array<Record<string, unknown>> | undefined) ?? []
  const series = data.series_structure as Record<string, unknown> | undefined
  const stages = (
    (series?.six_stage_structure as Array<Record<string, unknown>> | undefined) ?? []
  ).filter((stage) => {
    const name = pickMeaningfulText(stage.name)
    const body = pickMeaningfulText(
      stage.target,
      stage.summary,
      stage.conflict_escalation_direction,
      stage.irreversible_turn,
    )
    return Boolean(name || body)
  })

  const emotionRaw = series?.series_emotion_curve
  const emotionPoints: Array<Record<string, unknown>> = Array.isArray(emotionRaw)
    ? emotionRaw.filter(
        (item): item is Record<string, unknown> => !!item && typeof item === 'object',
      )
    : emotionRaw && typeof emotionRaw === 'object'
      ? (
          ((emotionRaw as { key_points?: Array<Record<string, unknown>> }).key_points) ?? []
        ).filter(
          (item): item is Record<string, unknown> => !!item && typeof item === 'object',
        )
      : []
  const emotionSummary =
    emotionRaw && typeof emotionRaw === 'object' && !Array.isArray(emotionRaw)
      ? pickMeaningfulText((emotionRaw as { description?: unknown }).description)
      : pickMeaningfulText(emotionPoints[0]?.curve_summary)

  const conflictChain = (
    Array.isArray(series?.conflict_escalation_chain) ? series.conflict_escalation_chain : []
  )
    .map((item) => formatConflictItem(item))
    .filter((text) => text && !isPlaceholder(text))

  const reversals =
    (series?.major_reversal_positions as Array<Record<string, unknown>> | undefined) ?? []
  const foreshadows =
    (series?.foreshadowing_table as Array<Record<string, unknown>> | undefined) ?? []
  const adapt = data.adapt_source as { mode?: string } | undefined
  const mainStoryline = pickMeaningfulText(series?.main_storyline)
  const title = pickMeaningfulText(data.drama_title) || '剧本蓝图'
  const logline = pickMeaningfulText(data.logline)
  const shortSyn = pickMeaningfulText(synopsis?.short)
  const fullSyn = pickMeaningfulText(synopsis?.full)
  const setting = pickMeaningfulText(world?.setting_summary)

  const metaPills = [
    adapt?.mode === 'original' ? '原创' : adapt?.mode === 'adapt' ? '改编' : '',
    characters.length > 0 ? `${characters.length} 名角色` : '',
    stages.length > 0 ? `${stages.length} 幕结构` : '',
    foreshadows.length > 0 ? `${foreshadows.length} 条伏笔` : '',
  ].filter(Boolean)

  return (
    <div className="w-full space-y-9">
      <header className="rounded-xl border border-border bg-surface px-5 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-[11px] font-medium tracking-wide text-ink-faint">剧本蓝图</p>
            <h3 className="mt-1 text-2xl font-semibold tracking-tight text-ink">{title}</h3>
            {logline ? (
              <p className="mt-3 text-base leading-8 text-ink">{logline}</p>
            ) : null}
            {metaPills.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {metaPills.map((pill) => (
                  <Badge key={pill} tone="info">
                    {pill}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
          {waitingApproval ? (
            <div className="flex shrink-0 gap-2">
              <button
                type="button"
                disabled={approvalPending}
                onClick={onReject}
                className="rounded-lg border border-border bg-surface px-3 py-2 text-sm"
              >
                驳回
              </button>
              <button
                type="button"
                disabled={approvalPending}
                onClick={onApprove}
                className="rounded-lg bg-action px-3 py-2 text-sm font-medium text-white hover:bg-action-hover"
              >
                批准蓝图
              </button>
            </div>
          ) : null}
        </div>
      </header>

      {(shortSyn || fullSyn) && (
        <Section ask="故事讲什么？">
          {shortSyn ? (
            <p className="text-[15px] font-medium leading-7 text-ink">{shortSyn}</p>
          ) : null}
          {fullSyn && fullSyn !== shortSyn ? (
            <div className="mt-1">
              {synopsisOpen ? (
                <p className="whitespace-pre-wrap text-[14px] leading-7 text-ink-muted">
                  {fullSyn}
                </p>
              ) : null}
              <button
                type="button"
                onClick={() => setSynopsisOpen((v) => !v)}
                className="mt-2 text-sm text-action hover:text-action-hover"
              >
                {synopsisOpen ? '收起全文' : '展开全文梗概'}
              </button>
            </div>
          ) : null}
        </Section>
      )}

      {(setting || rootRules.length > 0 || powerBlocks) && (
        <Section ask="世界怎么运转？">
          {setting ? (
            <p className="text-[14px] leading-7 text-ink">{setting}</p>
          ) : null}

          {powerBlocks?.summary ? (
            <QuietField
              label="权力怎么分配"
              note="谁掌握稀缺资源，谁就能制造主线冲突"
              text={powerBlocks.summary}
            />
          ) : null}

          {powerBlocks && powerBlocks.actors.length > 0 ? (
            <div className="space-y-2">
              <div className="text-[11px] font-medium text-ink-faint">关键势力</div>
              <ul className="space-y-2">
                {powerBlocks.actors.map((actor) => (
                  <li
                    key={actor}
                    className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-[14px] leading-6 text-ink"
                  >
                    {actor}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {rootRules.length > 0 ? (
            <div className="space-y-2">
              <div className="text-[11px] font-medium text-ink-faint">不可破的规矩</div>
              <ol className="space-y-3">
                {rootRules.map((rule, idx) => (
                  <li key={`rule-${idx}`} className="flex gap-3">
                    <span className="mt-0.5 w-6 shrink-0 text-sm font-semibold text-ink-faint">
                      {idx + 1}.
                    </span>
                    <div className="min-w-0">
                      <p className="text-[14px] font-medium leading-6 text-ink">{rule.title}</p>
                      {rule.details.length > 0 ? (
                        <p className="mt-1 text-[13px] leading-6 text-ink-muted">
                          {rule.details.map((d) => `${d.label}：${d.text}`).join(' · ')}
                        </p>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          ) : null}
        </Section>
      )}

      {characters.length > 0 ? (
        <Section ask="谁在推动故事？">
          <div className="grid gap-4 lg:grid-cols-2">
            {characters.map((c, idx) => {
              const key = `${pickMeaningfulText(c.name) || 'char'}-${idx}`
              const roleKey = String(c.role_type ?? '')
              const roleZh = ROLE_TYPE_ZH[roleKey] || roleKey
              const desire = pickMeaningfulText(c.surface_desire ?? c.want)
              const need = pickMeaningfulText(c.deep_need ?? c.need)
              const background = pickMeaningfulText(
                c.audience_identification ?? c.background,
              )
              const ghost = pickMeaningfulText(c.ghost)
              const lie = pickMeaningfulText(c.lie)
              const flaw = pickMeaningfulText(c.flaw)
              const voice = pickMeaningfulText(c.voice_tag)
              const visual = pickMeaningfulText(c.visual_anchor)
              const arcParts = formatArcParts(c.arc)
              const open = Boolean(openChars[key])
              const hasMore = Boolean(
                ghost || lie || flaw || voice || visual || arcParts.length > 0,
              )

              return (
                <article
                  key={key}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-lg font-semibold text-ink">
                        {pickMeaningfulText(c.name) || '未命名角色'}
                        {c.age != null && !isPlaceholder(c.age) ? (
                          <span className="ml-2 text-sm font-normal text-ink-faint">
                            {String(c.age)} 岁
                          </span>
                        ) : null}
                      </div>
                    </div>
                    {roleZh ? (
                      <Badge tone={ROLE_TONE[roleKey] || 'default'}>{roleZh}</Badge>
                    ) : null}
                  </div>

                  {background ? (
                    <p className="mt-3 text-[14px] leading-7 text-ink-muted">{background}</p>
                  ) : null}

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {desire ? (
                      <QuietField
                        label="想要"
                        note={CHAR_FIELD_NOTES.desire}
                        text={desire}
                      />
                    ) : null}
                    {need ? (
                      <QuietField label="需要" note={CHAR_FIELD_NOTES.need} text={need} />
                    ) : null}
                  </div>

                  {hasMore ? (
                    <div className="mt-3">
                      {open ? (
                        <div className="space-y-3 border-t border-slate-100 pt-3">
                          {ghost ? (
                            <QuietField
                              label="幽灵（心结）"
                              note={CHAR_FIELD_NOTES.ghost}
                              text={ghost}
                            />
                          ) : null}
                          {lie ? (
                            <QuietField
                              label="谎言（错误信念）"
                              note={CHAR_FIELD_NOTES.lie}
                              text={lie}
                            />
                          ) : null}
                          {flaw ? (
                            <QuietField
                              label="缺陷"
                              note={CHAR_FIELD_NOTES.flaw}
                              text={flaw}
                            />
                          ) : null}
                          {voice ? (
                            <QuietField
                              label="声线"
                              note={CHAR_FIELD_NOTES.voice}
                              text={voice}
                            />
                          ) : null}
                          {visual ? (
                            <QuietField
                              label="视觉锚点"
                              note={CHAR_FIELD_NOTES.visual}
                              text={visual}
                            />
                          ) : null}
                          {arcParts.length > 0 ? (
                            <div className="space-y-2">
                              <div className="text-[11px] font-medium text-ink-faint">
                                弧光
                                <span className="font-normal text-ink-faint/80">
                                  {' '}
                                  · {CHAR_FIELD_NOTES.arc}
                                </span>
                              </div>
                              <ol className="space-y-3">
                                {arcParts.map((part) => (
                                  <li key={part.label} className="text-[13px] leading-6">
                                    <div className="text-ink-faint">
                                      {part.label}
                                      {ARC_PART_NOTES[part.label] ? (
                                        <span className="font-normal text-ink-faint/80">
                                          {' '}
                                          · {ARC_PART_NOTES[part.label]}
                                        </span>
                                      ) : null}
                                    </div>
                                    <p className="mt-0.5 text-ink-muted">{part.text}</p>
                                  </li>
                                ))}
                              </ol>
                            </div>
                          ) : null}
                        </div>
                      ) : null}
                      <button
                        type="button"
                        onClick={() =>
                          setOpenChars((prev) => ({ ...prev, [key]: !prev[key] }))
                        }
                        className="mt-2 text-sm text-action hover:text-action-hover"
                      >
                        {open ? '收起细节' : '查看弧光与细节'}
                      </button>
                    </div>
                  ) : null}
                </article>
              )
            })}
          </div>
        </Section>
      ) : null}

      {relationships.length > 0 ? (
        <Section ask="关系怎么缠？">
          <ul className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white">
            {relationships.map((rel, idx) => {
              const from = pickMeaningfulText(rel.from)
              const to = pickMeaningfulText(rel.to)
              const type = pickMeaningfulText(rel.type)
              const description = pickMeaningfulText(rel.description)
              if (!from && !to && !description) return null
              return (
                <li key={`rel-${idx}`} className="px-4 py-3.5">
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span className="text-[14px] font-medium text-ink">
                      {from || '？'}
                      <span className="mx-1.5 text-ink-faint">→</span>
                      {to || '？'}
                    </span>
                    {type ? <Badge>{type}</Badge> : null}
                  </div>
                  {description ? (
                    <p className="mt-1.5 text-[13px] leading-6 text-ink-muted">{description}</p>
                  ) : null}
                </li>
              )
            })}
          </ul>
        </Section>
      ) : null}

      {(mainStoryline || stages.length > 0) && (
        <Section ask="剧情怎么走？">
          {mainStoryline ? (
            <p className="text-[14px] leading-7 text-ink">{mainStoryline}</p>
          ) : null}
          {emotionSummary ? (
            <p className="text-[13px] leading-6 text-ink-faint">情绪走向：{emotionSummary}</p>
          ) : null}

          {stages.length > 0 ? (
            <ol className="relative space-y-0 border-l border-slate-200 pl-5">
              {stages.map((stage, idx) => {
                const name = pickMeaningfulText(stage.name)
                const range = pickMeaningfulText(stage.episode_range)
                const target = pickMeaningfulText(stage.target ?? stage.summary)
                const escalation = pickMeaningfulText(stage.conflict_escalation_direction)
                const turn = pickMeaningfulText(stage.irreversible_turn)
                return (
                  <li key={`stage-${idx}`} className="relative pb-6 last:pb-0">
                    <span className="absolute -left-[1.4rem] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-action bg-surface" />
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="text-[15px] font-semibold text-ink">
                        第 {asDisplayText(stage.stage) || idx + 1} 幕
                        {name ? ` · ${name}` : ''}
                      </span>
                      {range ? (
                        <span className="text-xs text-ink-faint">EP {range}</span>
                      ) : null}
                    </div>
                    <div className="mt-2 space-y-2">
                      {target ? (
                        <QuietField
                          label="这一幕要完成"
                          note={STAGE_FIELD_NOTES.target}
                          text={target}
                        />
                      ) : null}
                      {escalation ? (
                        <QuietField
                          label="冲突怎么升"
                          note={STAGE_FIELD_NOTES.escalation}
                          text={escalation}
                        />
                      ) : null}
                      {turn ? (
                        <QuietField
                          label="不可逆转折"
                          note={STAGE_FIELD_NOTES.turn}
                          text={turn}
                        />
                      ) : null}
                    </div>
                  </li>
                )
              })}
            </ol>
          ) : null}
        </Section>
      )}

      {(emotionPoints.length > 0 ||
        conflictChain.length > 0 ||
        reversals.length > 0 ||
        foreshadows.length > 0) && (
        <Section ask="节奏与埋线">
          <div className="grid gap-6 lg:grid-cols-2">
            {emotionPoints.length > 0 ? (
              <div className="space-y-3">
                <div className="text-[11px] font-medium text-ink-faint">
                  情绪关键点
                  <span className="font-normal text-ink-faint/80">
                    {' '}
                    · 全剧情绪起伏的标志性集数
                  </span>
                </div>
                <ul className="space-y-2.5">
                  {emotionPoints.map((pt, idx) => {
                    const emotion = pickMeaningfulText(pt.emotion)
                    const event = pickMeaningfulText(pt.event, pt.description)
                    if (!emotion && !event) return null
                    return (
                      <li key={`emo-${idx}`} className="text-[13px] leading-6">
                        <span className="font-medium text-ink">
                          {pt.episode != null ? `EP${String(pt.episode)}` : '节点'}
                          {emotion ? ` · ${emotion}` : ''}
                        </span>
                        {event ? (
                          <span className="mt-0.5 block text-ink-muted">{event}</span>
                        ) : null}
                      </li>
                    )
                  })}
                </ul>
              </div>
            ) : null}

            {conflictChain.length > 0 ? (
              <div className="space-y-3">
                <div className="text-[11px] font-medium text-ink-faint">
                  冲突升级
                  <span className="font-normal text-ink-faint/80">
                    {' '}
                    · 从外部规则到内心/命运的层层加压
                  </span>
                </div>
                <ol className="space-y-2.5">
                  {conflictChain.map((item, idx) => (
                    <li key={`cf-${idx}`} className="flex gap-2 text-[13px] leading-6">
                      <span className="shrink-0 text-ink-faint">{idx + 1}.</span>
                      <span className="text-ink-muted">{item}</span>
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}

            {reversals.length > 0 ? (
              <div className="space-y-3">
                <div className="text-[11px] font-medium text-ink-faint">
                  重大反转
                  <span className="font-normal text-ink-faint/80">
                    {' '}
                    · 颠覆观众预期或改变角色立场的节点
                  </span>
                </div>
                <ul className="space-y-2.5">
                  {reversals.map((item, idx) => {
                    const description = pickMeaningfulText(item.description)
                    if (!description && item.episode == null) return null
                    return (
                      <li key={`rev-${idx}`} className="text-[13px] leading-6">
                        <span className="font-medium text-ink">
                          {item.episode != null ? `EP${String(item.episode)}` : '反转'}
                          {pickMeaningfulText(item.type)
                            ? ` · ${pickMeaningfulText(item.type)}`
                            : ''}
                        </span>
                        {description ? (
                          <span className="mt-0.5 block text-ink-muted">{description}</span>
                        ) : null}
                      </li>
                    )
                  })}
                </ul>
              </div>
            ) : null}

            {foreshadows.length > 0 ? (
              <div className="space-y-3">
                <div className="text-[11px] font-medium text-ink-faint">
                  伏笔
                  <span className="font-normal text-ink-faint/80">
                    {' '}
                    · 前期埋下、后期揭晓的线索
                  </span>
                </div>
                <ul className="space-y-2.5">
                  {foreshadows.map((item, idx) => {
                    const description = pickMeaningfulText(item.description)
                    if (!description) return null
                    const setup = Array.isArray(item.setup_episodes)
                      ? item.setup_episodes.join('、')
                      : pickMeaningfulText(item.setup_episodes)
                    return (
                      <li key={`fs-${idx}`} className="text-[13px] leading-6">
                        <span className="font-medium text-ink">
                          {pickMeaningfulText(item.id) || `伏笔 ${idx + 1}`}
                        </span>
                        <span className="mt-0.5 block text-ink-muted">{description}</span>
                        <span className="mt-0.5 block text-[12px] text-ink-faint">
                          埋设 EP{setup || '—'} · 回收{' '}
                          {item.payoff_episode != null
                            ? `EP${String(item.payoff_episode)}`
                            : '—'}
                        </span>
                      </li>
                    )
                  })}
                </ul>
              </div>
            ) : null}
          </div>
        </Section>
      )}
    </div>
  )
}
