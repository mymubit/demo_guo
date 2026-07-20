import type { ReactNode } from 'react'
import { Badge } from '@/components/ui/Badge'
import {
  complianceRiskTypeLabelZh,
  formatComplianceIssueZh,
  qualityDimensionLabelZh,
} from '@/utils/reportLabels'
import {
  axisFieldLabelZh,
  complianceRiskLabelZh,
  resolveThemeOptionLabel,
} from '@/utils/themeLabels'
import { asDisplayText, isPlaceholder, pickMeaningfulText } from '@/utils/artifactDisplay'

function text(value: unknown): string {
  return pickMeaningfulText(value) || asDisplayText(value)
}

function hasText(value: unknown): boolean {
  const t = text(value)
  return Boolean(t) && !isPlaceholder(t)
}

function Field({ label, value, note }: { label: string; value: unknown; note?: string }) {
  if (!hasText(value) && !(Array.isArray(value) && value.length > 0)) return null
  const body = Array.isArray(value)
    ? value
        .map((item) => (typeof item === 'string' ? item : JSON.stringify(item)))
        .filter(Boolean)
        .join('、')
    : text(value)
  if (!body) return null
  return (
    <div className="sf-panel p-3 text-sm">
      <dt className="text-xs text-ink-faint">
        {label}
        {note ? <span className="font-normal text-ink-faint/80"> · {note}</span> : null}
      </dt>
      <dd className="mt-1 whitespace-pre-wrap text-ink">{body}</dd>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-3">
      <h4 className="text-sm font-semibold text-ink">{title}</h4>
      {children}
    </section>
  )
}

function StringList({ items, empty }: { items: unknown; empty?: string }) {
  const list = Array.isArray(items)
    ? items.map((item) => text(item)).filter((item) => item && !isPlaceholder(item))
    : []
  if (list.length === 0) {
    return empty ? <p className="text-sm text-ink-muted">{empty}</p> : null
  }
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm text-ink">
      {list.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  )
}

function formatEmotionNode(node: unknown): string {
  if (!node || typeof node !== 'object') return text(node)
  const row = node as Record<string, unknown>
  const bits = [
    hasText(row.content) ? text(row.content) : '',
    row.value != null ? `强度 ${String(row.value)}` : '',
    hasText(row.label) ? text(row.label) : '',
    hasText(row.description) ? text(row.description) : '',
  ].filter(Boolean)
  return bits.join(' · ') || JSON.stringify(row)
}

function formatObjectRows(items: unknown): Array<{ title: string; detail: string }> {
  if (!Array.isArray(items)) return []
  return items
    .map((item, idx) => {
      if (typeof item === 'string') {
        const t = item.trim()
        return t ? { title: t, detail: '' } : null
      }
      if (!item || typeof item !== 'object') return null
      const row = item as Record<string, unknown>
      const title =
        text(row.name) ||
        text(row.title) ||
        text(row.character) ||
        text(row.clue) ||
        text(row.prop) ||
        `条目 ${idx + 1}`
      const detail = Object.entries(row)
        .filter(([k]) => !['name', 'title', 'character', 'clue', 'prop'].includes(k))
        .map(([k, v]) => {
          const body = text(v) || (typeof v === 'object' ? JSON.stringify(v) : '')
          return body ? `${k}：${body}` : ''
        })
        .filter(Boolean)
        .join('；')
      return { title, detail }
    })
    .filter((row): row is { title: string; detail: string } => row != null)
}

const DEFECT_SEVERITY_ZH: Record<string, string> = {
  critical: '严重',
  major: '重要',
  minor: '轻微',
  info: '提示',
}

function formatDefectItem(
  item: unknown,
  idx: number,
): { title: string; description: string; suggestion: string; meta: string[] } {
  if (typeof item === 'string') {
    return { title: item || `缺陷 ${idx + 1}`, description: '', suggestion: '', meta: [] }
  }
  if (!item || typeof item !== 'object') {
    return { title: `缺陷 ${idx + 1}`, description: '', suggestion: '', meta: [] }
  }
  const row = item as Record<string, unknown>
  const description = text(row.description) || text(row.detail) || text(row.summary)
  const suggestion = text(row.suggestion) || text(row.fix)
  const location = text(row.location) || text(row.episode) || text(row.position)
  const severityRaw = text(row.severity) || text(row.level)
  const severity = DEFECT_SEVERITY_ZH[severityRaw.toLowerCase()] || severityRaw
  const title =
    text(row.title) ||
    text(row.name) ||
    (description ? description.slice(0, 36) + (description.length > 36 ? '…' : '') : `缺陷 ${idx + 1}`)
  const meta: string[] = []
  if (location) meta.push(`位置 ${location}`)
  if (severity) meta.push(`级别 ${severity}`)
  return { title, description, suggestion, meta }
}

export function ProjectBriefView({ data }: { data: Record<string, unknown> }) {
  const genre = (data.genre_matrix as Record<string, unknown> | undefined) ?? {}
  const ruleParams = (data.rule_params as Record<string, unknown> | undefined) ?? {}
  const flavorTags = Array.isArray(genre.flavor_tags) ? genre.flavor_tags : []
  const competitors = Array.isArray(data.competitor_references) ? data.competitor_references : []

  return (
    <div className="space-y-6">
      <header>
        <h3 className="text-xl font-semibold text-ink">{text(data.title) || '项目简报'}</h3>
        {hasText(data.core_idea) ? (
          <p className="mt-2 text-sm leading-relaxed text-ink-muted">{text(data.core_idea)}</p>
        ) : null}
      </header>

      <div className="flex flex-wrap gap-2">
        {Object.entries(genre).map(([key, value]) => {
          if (key === 'flavor_tags') return null
          if (value == null || value === '') return null
          const label = resolveThemeOptionLabel(null, key, String(value))
          return (
            <Badge key={key} tone="action">
              {axisFieldLabelZh(key)}：{label}
            </Badge>
          )
        })}
        {flavorTags.map((tag) => (
          <Badge key={String(tag)} tone="info">
            {resolveThemeOptionLabel(null, 'flavor_tags', String(tag))}
          </Badge>
        ))}
        {data.compliance_risk ? (
          <Badge tone="warning">风险 {complianceRiskLabelZh(data.compliance_risk)}</Badge>
        ) : null}
      </div>

      <Section title="创意与卖点">
        <dl className="grid gap-3 sm:grid-cols-2">
          <Field label="目标受众" value={data.target_audience} />
          <Field label="核心冲突" value={data.core_conflict} />
          <Field label="钩子概念" value={data.hook_concept} />
          <Field label="商业钩子" value={data.commercial_hook} />
          <Field label="首集钩子" value={data.first_episode_hook} />
          <Field label="付费方向" value={data.paywall_direction} />
          <Field label="集数" value={data.episode_count} />
          <Field label="单集时长（分钟）" value={data.episode_duration} />
        </dl>
      </Section>

      <Section title="市场与差异化">
        <dl className="grid gap-3 sm:grid-cols-2">
          <Field label="市场机会" value={data.market_opportunity} />
          <Field label="差异化策略" value={data.differentiation_strategy} />
          <Field label="爆款要素" value={data.blockbuster_factors} />
          <Field label="参考作品" value={data.reference_works} />
          <Field label="矩阵键" value={data.matrix_key} />
          <Field label="预设题材码" value={data.preset_theme_code} />
        </dl>
        {competitors.length > 0 ? (
          <div className="sf-panel space-y-2 p-3 text-sm">
            <div className="text-xs text-ink-faint">竞品参考</div>
            {competitors.map((item, idx) => {
              if (!item || typeof item !== 'object') {
                return (
                  <p key={idx} className="text-ink">
                    {String(item)}
                  </p>
                )
              }
              const row = item as Record<string, unknown>
              return (
                <p key={idx} className="text-ink">
                  {text(row.title) || text(row.name) || `竞品 ${idx + 1}`}
                  {hasText(row.note) ? ` · ${text(row.note)}` : ''}
                  {hasText(row.differentiation) ? ` · ${text(row.differentiation)}` : ''}
                </p>
              )
            })}
          </div>
        ) : null}
      </Section>

      {Object.keys(ruleParams).length > 0 ? (
        <Section title="规则参数">
          <dl className="grid gap-3 sm:grid-cols-2">
            <Field label="反转密度" value={ruleParams.reversal_density} />
            <Field
              label="情绪曲线"
              value={Array.isArray(ruleParams.emotion_curve) ? ruleParams.emotion_curve.join(' → ') : null}
            />
            <Field
              label="幕比"
              value={Array.isArray(ruleParams.act_ratio) ? ruleParams.act_ratio.join(' / ') : null}
            />
            <Field label="钩子类型" value={ruleParams.hook_types} />
          </dl>
        </Section>
      ) : null}
    </div>
  )
}

/** 质检/合规/润色及通用产物的结构化展示 */
export function ReportArtifactView({
  kind,
  data,
}: {
  kind: 'quality_report' | 'compliance_report' | 'polished_script' | 'generic'
  data: Record<string, unknown>
}) {
  if (kind === 'quality_report') {
    const dimensions = (data.dimensions ?? {}) as Record<
      string,
      { score?: number; weight?: number; comment?: string; evidence?: string[]; deductions?: string[] }
    >
    const defects = Array.isArray(data.defects) ? data.defects : []
    const priorities = Array.isArray(data.revision_priorities) ? data.revision_priorities : []
    const continuity = (data.continuity_summary as Record<string, unknown> | undefined) ?? {}
    const continuityIssues = Array.isArray(continuity.issues) ? continuity.issues : []
    const continuitySummary = pickMeaningfulText(continuity.summary, continuity.description)
    const verdictDetail = pickMeaningfulText(data.verdict_detail)

    return (
      <div className="space-y-5">
        <header className="sf-panel p-4">
          <h3 className="text-lg font-semibold text-ink">
            {text(data.drama_title) ? `${text(data.drama_title)} · 质量评分` : '质量评分报告'}
          </h3>
          <div className="mt-3 flex flex-wrap gap-3 text-sm text-ink">
            <span>
              总分：<strong>{String(data.overall_score ?? '—')}</strong>
            </span>
            <span>
              等级：<strong>{String(data.grade ?? '—')}</strong>
            </span>
            <span>
              结论：<strong>{String(data.verdict ?? '—')}</strong>
            </span>
            <span>阈值 {String(data.pass_threshold ?? '—')}</span>
            <span>预设 {String(data.scoring_preset ?? '—')}</span>
            <span>脚本源 {String(data.resolved_script_key ?? '—')}</span>
            {data.needs_revision != null ? (
              <Badge tone={data.needs_revision ? 'warning' : 'success'}>
                {data.needs_revision ? '建议修订' : '可放行'}
              </Badge>
            ) : null}
            {data.can_continue_next_batch != null ? (
              <Badge tone={data.can_continue_next_batch ? 'success' : 'warning'}>
                {data.can_continue_next_batch ? '可进下一批' : '暂缓下一批'}
              </Badge>
            ) : null}
          </div>
          {verdictDetail ? (
            <p className="mt-3 text-sm leading-relaxed text-ink-muted">{verdictDetail}</p>
          ) : null}
        </header>

        {Object.keys(dimensions).length > 0 ? (
          <ul className="grid gap-3 sm:grid-cols-2">
            {Object.entries(dimensions).map(([key, dim]) => (
              <li key={key} className="sf-panel space-y-2 p-3 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-medium text-ink">{qualityDimensionLabelZh(key)}</div>
                  <div className="text-ink-muted">
                    {dim.score ?? '—'}
                    {dim.weight != null ? ` · 权重 ${dim.weight}` : ''}
                  </div>
                </div>
                {hasText(dim.comment) ? <p className="text-xs text-ink-muted">{text(dim.comment)}</p> : null}
                {Array.isArray(dim.evidence) && dim.evidence.length > 0 ? (
                  <ul className="list-disc space-y-1 pl-4 text-xs text-ink-muted">
                    {dim.evidence.map((line) => (
                      <li key={line}>证据：{line}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-amber-700">缺少维度证据（仅有分数）</p>
                )}
                {Array.isArray(dim.deductions) && dim.deductions.length > 0 ? (
                  <ul className="list-disc space-y-1 pl-4 text-xs text-amber-800">
                    {dim.deductions.map((line) => (
                      <li key={line}>扣分：{line}</li>
                    ))}
                  </ul>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <KeyValueFallback data={data} omit={['dimensions']} />
        )}

        <Section title="连贯性">
          <p className="text-sm text-ink">结果：{String(continuity.result ?? '—')}</p>
          {continuitySummary ? (
            <p className="mt-2 text-sm leading-relaxed text-ink-muted">{continuitySummary}</p>
          ) : null}
          {continuityIssues.length > 0 ? (
            <ul className="mt-2 space-y-2">
              {formatObjectRows(continuityIssues).map((row) => (
                <li key={row.title} className="sf-panel p-3 text-sm">
                  <div className="font-medium text-ink">{row.title}</div>
                  {row.detail ? <p className="mt-1 text-ink-muted">{row.detail}</p> : null}
                </li>
              ))}
            </ul>
          ) : !continuitySummary ? (
            <p className="mt-1 text-sm text-ink-muted">无连贯性问题。</p>
          ) : null}
        </Section>

        {defects.length > 0 ? (
          <Section title="缺陷清单">
            <ul className="space-y-2">
              {defects.map((item, idx) => {
                const row = formatDefectItem(item, idx)
                return (
                  <li key={row.title} className="sf-panel space-y-1.5 p-3 text-sm">
                    <div className="font-medium text-ink">{row.title}</div>
                    {row.description ? (
                      <p className="text-ink-muted">{row.description}</p>
                    ) : null}
                    {row.meta.length > 0 ? (
                      <p className="text-xs text-ink-faint">{row.meta.join(' · ')}</p>
                    ) : null}
                    {row.suggestion ? (
                      <p className="text-xs text-action">建议：{row.suggestion}</p>
                    ) : null}
                  </li>
                )
              })}
            </ul>
          </Section>
        ) : null}

        {priorities.length > 0 ? (
          <Section title="修订优先级">
            <ul className="space-y-2">
              {formatObjectRows(priorities).map((row) => (
                <li key={row.title} className="sf-panel p-3 text-sm">
                  <div className="font-medium text-ink">{row.title}</div>
                  {row.detail ? <p className="mt-1 text-ink-muted">{row.detail}</p> : null}
                </li>
              ))}
            </ul>
          </Section>
        ) : null}

        {data.evolution_proposal && typeof data.evolution_proposal === 'object' ? (
          <Section title="进化建议">
            <KeyValueFallback data={data.evolution_proposal as Record<string, unknown>} />
          </Section>
        ) : null}
      </div>
    )
  }

  if (kind === 'compliance_report') {
    const risks = Array.isArray(data.risk_items) ? data.risk_items : []
    const blocking = Array.isArray(data.blocking_issues) ? data.blocking_issues : []
    return (
      <div className="space-y-5">
        <header className="sf-panel p-4">
          <h3 className="text-lg font-semibold text-ink">
            {text(data.drama_title) ? `${text(data.drama_title)} · 合规审查` : '合规审查报告'}
          </h3>
          <div className="mt-2 flex flex-wrap gap-3 text-sm text-ink">
            <span>
              总评：<strong>{String(data.overall_result ?? '—')}</strong>
            </span>
            <span>模式 {String(data.check_mode ?? '—')}</span>
            <span>平台 {String(data.target_platform ?? '—')}</span>
            <span>脚本源 {String(data.resolved_script_key ?? '—')}</span>
            {hasText(data.platform_policy_version) ? (
              <span>政策版 {text(data.platform_policy_version)}</span>
            ) : null}
          </div>
        </header>
        {blocking.length > 0 ? (
          <section className="sf-panel space-y-2 p-4">
            <h4 className="text-sm font-medium text-red-700">阻断项</h4>
            <ul className="space-y-2">
              {blocking.map((item, idx) => {
                const row = formatComplianceIssueZh(item)
                return (
                  <li key={`${row.title}-${idx}`} className="rounded-lg bg-red-50 px-3 py-2 text-sm">
                    <div className="font-medium text-red-900">{row.title}</div>
                    {row.detail ? <p className="mt-1 text-red-800">{row.detail}</p> : null}
                    {row.meta.length > 0 ? (
                      <p className="mt-1 text-xs text-red-700">{row.meta.join(' · ')}</p>
                    ) : null}
                  </li>
                )
              })}
            </ul>
          </section>
        ) : (
          <p className="text-sm text-ink-muted">无阻断项。</p>
        )}
        {risks.length > 0 ? (
          <section className="space-y-2">
            <h4 className="text-sm font-medium text-ink">风险项</h4>
            {risks.map((item, idx) => {
              const row = item as { type?: string; description?: string; suggestion?: string }
              return (
                <div key={idx} className="sf-panel p-3 text-sm">
                  <div className="font-medium text-ink">{complianceRiskTypeLabelZh(row.type)}</div>
                  {row.description ? <p className="mt-1 text-ink-muted">{row.description}</p> : null}
                  {row.suggestion ? (
                    <p className="mt-1 text-xs text-action">建议：{row.suggestion}</p>
                  ) : null}
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
    const episodes = (data.episodes as Array<Record<string, unknown>> | undefined) ?? []
    const legacyContent =
      (typeof data.content === 'string' && data.content) ||
      (typeof data.script_content === 'string' && data.script_content) ||
      (typeof data.polished_text === 'string' && data.polished_text) ||
      ''
    const resolved = Array.isArray(data.resolved_issues) ? data.resolved_issues : []
    const remaining = Array.isArray(data.remaining_issues) ? data.remaining_issues : []
    const summary = Array.isArray(data.revision_summary) ? data.revision_summary : []

    return (
      <div className="space-y-5">
        <h3 className="text-lg font-semibold text-ink">修复稿 / 润色稿</h3>
        {(resolved.length > 0 || remaining.length > 0 || summary.length > 0) && (
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="sf-panel space-y-2 p-3">
              <h4 className="text-sm font-medium text-ink">已解决问题</h4>
              <StringList items={resolved} empty="无" />
            </div>
            <div className="sf-panel space-y-2 p-3">
              <h4 className="text-sm font-medium text-ink">遗留问题</h4>
              <StringList items={remaining} empty="无" />
            </div>
            {summary.length > 0 ? (
              <div className="sf-panel space-y-2 p-3 sm:col-span-2">
                <h4 className="text-sm font-medium text-ink">修订摘要</h4>
                <ul className="space-y-2">
                  {formatObjectRows(summary).map((row) => (
                    <li key={row.title} className="text-sm">
                      <div className="font-medium text-ink">{row.title}</div>
                      {row.detail ? <p className="text-ink-muted">{row.detail}</p> : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        )}
        {episodes.length > 0 ? (
          <EpisodeScriptsView data={{ episodes }} heading="修复后分集正文" />
        ) : legacyContent ? (
          <pre className="sf-panel max-h-[70vh] overflow-auto whitespace-pre-wrap p-4 text-sm leading-relaxed text-ink">
            {legacyContent}
          </pre>
        ) : (
          <KeyValueFallback data={data} omit={['episodes', 'revision_summary', 'resolved_issues', 'remaining_issues']} />
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

export function NarrativePlanView({ data }: { data: Record<string, unknown> }) {
  const cards =
    (data.episode_narrative_designs as Array<Record<string, unknown>> | undefined) ?? []
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-ink">分集叙事计划</h3>
      <div className="grid grid-cols-1 gap-4">
        {cards.map((card) => {
          const foreshadow = (card.foreshadowing as Record<string, unknown> | undefined) ?? {}
          const emotionNodes = (card.emotion_nodes as Record<string, unknown> | undefined) ?? {}
          return (
            <article key={String(card.episode)} className="sf-panel space-y-3 p-4">
              <div className="flex items-center justify-between gap-3">
                <h4 className="font-medium text-ink">
                  EP{String(card.episode)} · {text(card.title) || '未命名'}
                </h4>
                {card.hook_grade ? <Badge tone="action">{String(card.hook_grade)}</Badge> : null}
              </div>
              {hasText(card.core_event) ? (
                <p className="text-sm text-ink-muted">{text(card.core_event)}</p>
              ) : null}
              <dl className="grid gap-3 sm:grid-cols-2">
                <Field label="目标冲突" value={card.goal_conflict} />
                <Field label="反转" value={card.reversal} />
                <Field label="开场钩子" value={card.opening_hook} />
                <Field label="结尾钩子" value={card.ending_hook} />
                <Field label="付费卡点" value={card.paywall_hook} />
                <Field label="情绪强度" value={card.emotion_intensity} />
                <Field label="节奏标签" value={card.rhythm_tag} />
                <Field label="出场角色" value={card.characters} />
                <Field label="爽点" value={card.satisfaction_points} />
              </dl>
              {(Array.isArray(foreshadow.setup) && foreshadow.setup.length > 0) ||
              (Array.isArray(foreshadow.payoff) && foreshadow.payoff.length > 0) ? (
                <div className="grid gap-3 sm:grid-cols-2 text-sm">
                  <div>
                    <div className="text-xs text-ink-faint">伏笔埋设</div>
                    <StringList items={foreshadow.setup} empty="—" />
                  </div>
                  <div>
                    <div className="text-xs text-ink-faint">伏笔回收</div>
                    <StringList items={foreshadow.payoff} empty="—" />
                  </div>
                </div>
              ) : null}
              {Object.keys(emotionNodes).length > 0 ? (
                <div className="grid gap-2 sm:grid-cols-3 text-xs text-ink-muted">
                  {(['EV', 'ET', 'TP'] as const).map((key) => {
                    const label = key === 'EV' ? '情绪值' : key === 'ET' ? '情绪类型' : '转折点'
                    const body = formatEmotionNode(emotionNodes[key])
                    return body ? (
                      <div key={key} className="rounded-lg bg-canvas px-2 py-1.5">
                        {label}：{body}
                      </div>
                    ) : null
                  })}
                </div>
              ) : null}
            </article>
          )
        })}
      </div>
    </div>
  )
}

export function EpisodeScriptsView({
  data,
  heading = '分集正文',
}: {
  data: Record<string, unknown>
  heading?: string
}) {
  const episodes = (data.episodes as Array<Record<string, unknown>> | undefined) ?? []
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-ink">{heading}</h3>
      {episodes.map((ep) => {
        const production = ep.production_notes as Record<string, unknown> | undefined
        const memory = ep.memory_checkpoint as Record<string, unknown> | undefined
        const rhythm = (memory?.rhythm_state as Record<string, unknown> | undefined) ?? {}
        const golden = Array.isArray(ep.golden_lines) ? ep.golden_lines : []
        return (
          <article key={String(ep.episode_number)} className="sf-panel overflow-hidden">
            <header className="flex items-center justify-between border-b border-border px-4 py-3">
              <div>
                <h4 className="font-medium text-ink">
                  第 {String(ep.episode_number)} 集 · {text(ep.title) || '未命名'}
                </h4>
                <p className="mt-1 text-xs text-ink-muted">
                  字数 {String(ep.word_count ?? '—')} · 对白比{' '}
                  {typeof ep.dialogue_ratio === 'number'
                    ? `${Math.round(ep.dialogue_ratio * 100)}%`
                    : '—'}{' '}
                  · 场景 {String(ep.scene_count ?? '—')}
                </p>
              </div>
              {production?.complexity_band ? (
                <Badge tone="info">{String(production.complexity_band)}</Badge>
              ) : null}
            </header>
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap bg-canvas px-4 py-3 text-sm leading-relaxed text-ink">
              {String(ep.script ?? '')}
            </pre>
            {golden.length > 0 ? (
              <div className="border-t border-border px-4 py-3 text-sm">
                <div className="text-xs text-ink-faint">金句</div>
                <StringList items={golden} />
              </div>
            ) : null}
            {production ? (
              <footer className="space-y-1 border-t border-border px-4 py-3 text-xs text-ink-muted">
                <div>
                  制片标签：
                  {Array.isArray(production.tags) && production.tags.length > 0
                    ? production.tags.join('、')
                    : '—'}
                  {production.complexity_score != null
                    ? ` · 复杂度 ${String(production.complexity_score)}`
                    : ''}
                </div>
                {Array.isArray(production.high_cost_scenes) && production.high_cost_scenes.length > 0 ? (
                  <div>高成本场景：{production.high_cost_scenes.join('、')}</div>
                ) : null}
                {Array.isArray(production.lower_cost_alternatives) &&
                production.lower_cost_alternatives.length > 0 ? (
                  <div>低成本替代：{production.lower_cost_alternatives.join('、')}</div>
                ) : null}
              </footer>
            ) : null}
            {memory ? (
              <div className="space-y-2 border-t border-border px-4 py-3 text-xs text-ink-muted">
                <div className="font-medium text-ink">记忆检查点</div>
                <div>
                  节奏：情节 {String(rhythm.plot_pace ?? '—')} · 情绪{' '}
                  {String(rhythm.emotion_pace ?? '—')} · EV {String(rhythm.episode_ev ?? '—')}
                  {rhythm.episode_et != null ? ` · ET ${String(rhythm.episode_et)}` : ''}
                  {hasText(rhythm.episode_tp) ? ` · TP ${text(rhythm.episode_tp)}` : ''}
                </div>
                <div>
                  下集约束：
                  <StringList items={memory.next_episode_constraints} empty="无" />
                </div>
                {formatObjectRows(memory.active_clues).length > 0 ? (
                  <div>
                    活跃线索：
                    {formatObjectRows(memory.active_clues)
                      .map((row) => row.title)
                      .join('、')}
                  </div>
                ) : null}
                {formatObjectRows(memory.foreshadowing).length > 0 ? (
                  <div>
                    伏笔：
                    {formatObjectRows(memory.foreshadowing)
                      .map((row) => row.title)
                      .join('、')}
                  </div>
                ) : null}
              </div>
            ) : null}
          </article>
        )
      })}
    </div>
  )
}
