import { useEffect } from 'react'
import { X } from 'lucide-react'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { formatApiError } from '@/services/errors'
import type { InjectionManifest, LlmCallLogDetail } from '@/services/admin'
import { cn } from '@/utils/cn'
import {
  classifyJobOutcome,
  formatClock,
  formatLatency,
  formatRoleLabel,
  JOB_STATUS_LABEL,
  PURPOSE_LABEL,
  shortId,
  type DetailTab,
} from '@/components/ops/llmLogs/llmLogUtils'

function PromptBody({ content }: { content?: string | null }) {
  const text = content || '（空）'
  const truncatedInDb = text.includes('…(已截断，原文')
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-ink-faint">
        <span>{text.length.toLocaleString()} 字符 · 原始全文</span>
        {truncatedInDb ? (
          <span className="font-medium text-amber-700">落库曾触发硬顶截断</span>
        ) : null}
      </div>
      <pre className="max-h-[min(70vh,48rem)] overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-canvas-muted p-3 text-xs leading-relaxed text-ink">
        {text}
      </pre>
    </div>
  )
}

function MetaPanel({ detail }: { detail: LlmCallLogDetail }) {
  const outcome = classifyJobOutcome(detail)
  const primary: Array<[string, string]> = [
    ['模型调用', detail.status === 'success' ? '成功' : '失败'],
    [
      '工作台任务',
      detail.job_status ? JOB_STATUS_LABEL[detail.job_status] ?? detail.job_status : '—',
    ],
    [
      '项目',
      detail.project_title?.trim() || (detail.project_id ? shortId(detail.project_id, 12) : '—'),
    ],
    ['角色', formatRoleLabel(detail.role, detail.role_label)],
    ['用途', PURPOSE_LABEL[detail.purpose] || detail.purpose],
    ['耗时', formatLatency(detail.latency_ms)],
    ['模型', detail.model_name || '—'],
  ]
  const secondary: Array<[string, string]> = [
    ['角色 ID', detail.role || '—'],
    ['任务', shortId(detail.job_id, 12)],
    ['HTTP', detail.http_status != null ? String(detail.http_status) : '—'],
    ['Prompt Tokens', detail.prompt_tokens != null ? String(detail.prompt_tokens) : '—'],
    ['Completion Tokens', detail.completion_tokens != null ? String(detail.completion_tokens) : '—'],
    ['Total Tokens', detail.total_tokens != null ? String(detail.total_tokens) : '—'],
    ['时间', formatClock(detail.created_at)],
  ]
  return (
    <div className="space-y-5">
      {outcome ? (
        <div
          className={cn(
            'rounded-lg border px-3 py-2 text-xs',
            outcome.tone === 'ok'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
              : outcome.tone === 'warn'
                ? 'border-amber-200 bg-amber-50 text-amber-900'
                : outcome.tone === 'bad'
                  ? 'border-red-200 bg-red-50 text-red-800'
                  : 'border-border bg-canvas-muted text-ink-muted',
          )}
        >
          <p className="font-medium">{outcome.label}</p>
          {detail.job_error_message ? (
            <p className="mt-1 whitespace-pre-wrap opacity-90">{detail.job_error_message}</p>
          ) : null}
        </div>
      ) : null}
      <dl className="space-y-2.5 text-sm">
        {primary.map(([k, v]) => (
          <div key={k} className="flex items-start justify-between gap-3 border-b border-border/60 pb-2">
            <dt className="shrink-0 text-ink-faint">{k}</dt>
            <dd className="min-w-0 break-all text-right font-medium text-ink">{v}</dd>
          </div>
        ))}
      </dl>
      <dl className="space-y-2 text-xs">
        {secondary.map(([k, v]) => (
          <div key={k} className="flex items-start justify-between gap-3">
            <dt className="shrink-0 text-ink-faint">{k}</dt>
            <dd className="min-w-0 break-all text-right font-mono text-ink-muted">{v}</dd>
          </div>
        ))}
      </dl>
      {detail.error_message ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">
          {detail.error_message}
        </div>
      ) : null}
    </div>
  )
}

const LAYER_LABEL: Record<string, string> = {
  header: '角色头',
  skill: 'SKILL',
  modules: '模块',
  rules: '规则',
  knowledge: '知识',
  fewshots: 'Few-shot',
  anti: '反例',
  scoring_inline: '评分内联',
  contract: '输出契约',
}

function InjectionPanel({ detail }: { detail: LlmCallLogDetail }) {
  const manifest = detail.injection_manifest as InjectionManifest | null | undefined
  if (!manifest) {
    return (
      <p className="text-sm text-ink-muted">无注入清单（历史记录）。新调用生成后会在此展示分层与跳过原因。</p>
    )
  }
  const layers = Object.entries(manifest.layers || {}).filter(([, v]) => (v?.chars || 0) > 0)
  const included = manifest.modules?.included || []
  const skipped = manifest.modules?.skipped || []
  const knowledgeIncluded = manifest.knowledge?.included || []
  const knowledgeSkipped = manifest.knowledge?.skipped || []
  return (
    <div className="space-y-5 text-sm">
      <div className="rounded-lg border border-border bg-canvas-muted/40 px-3 py-2 text-xs text-ink-muted">
        <div>System {Number(manifest.system_chars || 0).toLocaleString()} 字</div>
        {manifest.checksum ? (
          <div className="mt-1 font-mono">checksum {manifest.checksum}</div>
        ) : null}
        {detail.injection_truncated ? (
          <div className="mt-1 font-medium text-amber-700">存在预算截断</div>
        ) : null}
      </div>
      <section className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">分层</h3>
        <ul className="space-y-1.5">
          {layers.map(([key, stat]) => (
            <li key={key} className="flex items-center justify-between gap-2 text-xs">
              <span className="text-ink-muted">
                {LAYER_LABEL[key] || key}
                {stat.truncated ? <span className="ml-1 text-amber-700">截断</span> : null}
              </span>
              <span className="font-mono text-ink">{Number(stat.chars).toLocaleString()}</span>
            </li>
          ))}
        </ul>
      </section>
      <section className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
          模块 · 已注入 {included.length}
        </h3>
        {included.length === 0 ? (
          <p className="text-xs text-ink-faint">无</p>
        ) : (
          <ul className="space-y-1 text-xs">
            {included.map((m) => (
              <li key={m.id} className="flex justify-between gap-2">
                <span>{m.label_zh || m.id}</span>
                <span className="font-mono text-ink-muted">
                  {m.mode || 'full'} · {Number(m.chars || 0).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}
        {skipped.length > 0 ? (
          <>
            <h4 className="pt-2 text-xs font-medium text-ink-muted">已跳过 {skipped.length}</h4>
            <ul className="space-y-1 text-xs text-ink-muted">
              {skipped.map((m) => (
                <li key={m.id}>
                  {m.label_zh || m.id}
                  {m.reason ? ` · ${m.reason}` : ''}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>
      <section className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
          知识 · 已注入 {knowledgeIncluded.length}
        </h3>
        {knowledgeIncluded.length === 0 ? (
          <p className="text-xs text-ink-faint">无</p>
        ) : (
          <ul className="space-y-1 text-xs">
            {knowledgeIncluded.map((k) => (
              <li key={k.path} className="flex justify-between gap-2">
                <span className="min-w-0 truncate">{k.path.split('/').pop()}</span>
                <span className="shrink-0 font-mono text-ink-muted">
                  {Number(k.chars || 0).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}
        {knowledgeSkipped.length > 0 ? (
          <p className="text-xs text-ink-faint">跳过 {knowledgeSkipped.length} 个（预算/条件）</p>
        ) : null}
      </section>
      {manifest.rules ? (
        <section className="space-y-1 text-xs text-ink-muted">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">规则</h3>
          <p>
            {manifest.rules.item_count ?? 0} 条 · sections{' '}
            {(manifest.rules.sections_included || []).join('、') || '—'}
            {manifest.rules.truncated ? ' · 已截断' : ''}
          </p>
        </section>
      ) : null}
      {manifest.policies ? (
        <section className="space-y-1 text-xs text-ink-muted">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">策略快照</h3>
          <p>
            evaluate_enable_when=
            {String(Boolean(manifest.policies.evaluate_enable_when))} · as_index=
            {String(Boolean(manifest.policies.module_as_index))}
            {manifest.policies.knowledge_mode
              ? ` · knowledge_mode=${manifest.policies.knowledge_mode}`
              : ''}
            {manifest.policies.policy_enforced === false ? ' · 预算未强制' : ''}
          </p>
          <p>
            max_chars modules/rules/knowledge=
            {manifest.policies.module_max_chars ?? 0}/
            {manifest.policies.rule_max_chars ?? 0}/
            {manifest.policies.knowledge_max_chars ?? 0}
          </p>
        </section>
      ) : null}
    </div>
  )
}

export function CallDetailDrawer({
  detail,
  loading,
  error,
  tab,
  onTabChange,
  onClose,
}: {
  detail?: LlmCallLogDetail
  loading: boolean
  error: unknown
  tab: DetailTab
  onTabChange: (tab: DetailTab) => void
  onClose: () => void
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <button
        type="button"
        className="absolute inset-0 bg-ink/30"
        aria-label="关闭详情"
        onClick={onClose}
      />
      <aside className="relative flex h-full w-full max-w-[28rem] flex-col border-l border-border bg-surface shadow-panel">
        <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-ink">调用详情</h2>
            {detail ? (
              <p className="mt-1 truncate text-xs text-ink-muted">
                {formatRoleLabel(detail.role, detail.role_label)} ·{' '}
                {PURPOSE_LABEL[detail.purpose] || detail.purpose}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            className="rounded-lg p-1.5 text-ink-muted hover:bg-canvas-muted hover:text-ink"
            onClick={onClose}
            aria-label="关闭"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {loading ? (
          <div className="p-5">
            <LoadingBlock label="加载详情…" />
          </div>
        ) : error ? (
          <div className="p-5">
            <ErrorBanner message={formatApiError(error)} />
          </div>
        ) : detail ? (
          <>
            <div className="flex gap-1 border-b border-border px-3 pt-2">
              {(
                [
                  { id: 'meta' as const, label: '概要' },
                  { id: 'injection' as const, label: '注入' },
                  { id: 'system' as const, label: 'System' },
                  { id: 'user' as const, label: 'User' },
                  { id: 'response' as const, label: '回复' },
                ] as const
              ).map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => onTabChange(t.id)}
                  className={cn(
                    'rounded-t-md px-3 py-2 text-xs font-medium transition',
                    tab === t.id
                      ? 'bg-surface text-action shadow-[0_-1px_0_0_var(--border)_inset]'
                      : 'text-ink-muted hover:text-ink',
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-5">
              {tab === 'meta' ? <MetaPanel detail={detail} /> : null}
              {tab === 'injection' ? <InjectionPanel detail={detail} /> : null}
              {tab === 'system' ? <PromptBody content={detail.system_prompt} /> : null}
              {tab === 'user' ? <PromptBody content={detail.user_prompt} /> : null}
              {tab === 'response' ? (
                <div className="space-y-3">
                  {detail.error_message ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">
                      {detail.error_message}
                    </div>
                  ) : null}
                  <PromptBody content={detail.response_text} />
                </div>
              ) : null}
            </div>
          </>
        ) : null}
      </aside>
    </div>
  )
}
