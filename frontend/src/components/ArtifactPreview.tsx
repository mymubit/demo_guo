import { useMemo, useState } from 'react'
import { cn } from '@/utils/cn'
import {
  buildArtifactSections,
  formatArtifactJson,
  type ArtifactDisplaySection,
} from '@/utils/artifactDisplay'

type PreviewMode = 'readable' | 'json'

interface ArtifactPreviewProps {
  payload: unknown
  className?: string
  /** 面板标题；默认「产物预览」 */
  title?: string
  'data-testid'?: string
  /**
   * @deprecated 可读预览为主内容，始终展示；保留参数以免旧调用报错。
   */
  defaultOpen?: boolean
  /** @deprecated 使用 title */
  summaryLabel?: string
}

function SectionBody({ section }: { section: ArtifactDisplaySection }) {
  if (section.variant === 'cards' && section.cards && section.cards.length > 0) {
    return (
      <div className="mt-2 space-y-2.5">
        {section.cards.map((card) => (
          <article
            key={`${section.id}-${card.title}`}
            className="rounded-md border border-border/60 bg-surface px-3 py-2.5"
          >
            <h5 className="text-sm font-medium text-ink">{card.title}</h5>
            <dl className="mt-2 space-y-2">
              {card.rows.map((row) => (
                <div key={`${card.title}-${row.label}`}>
                  <dt className="text-[11px] font-medium uppercase tracking-wide text-ink-faint">
                    {row.label}
                  </dt>
                  <dd className="mt-0.5 whitespace-pre-wrap break-words text-sm leading-relaxed text-ink">
                    {row.value}
                  </dd>
                </div>
              ))}
            </dl>
          </article>
        ))}
      </div>
    )
  }

  return (
    <dl className="mt-2 divide-y divide-border/50">
      {section.rows.map((row) => (
        <div
          key={`${section.id}-${row.label}-${row.value.slice(0, 24)}`}
          className="grid gap-1 py-2 first:pt-0 last:pb-0 sm:grid-cols-[9.5rem_minmax(0,1fr)] sm:gap-3"
        >
          <dt className="shrink-0 text-xs text-ink-faint">{row.label}</dt>
          <dd className="min-w-0 whitespace-pre-wrap break-words text-sm leading-relaxed text-ink">
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function ArtifactPreview({
  payload,
  className,
  title,
  summaryLabel,
  'data-testid': testId = 'artifact-preview',
}: ArtifactPreviewProps) {
  const [mode, setMode] = useState<PreviewMode>('readable')
  const sections = useMemo(() => buildArtifactSections(payload), [payload])
  const jsonText = useMemo(() => formatArtifactJson(payload), [payload])
  const heading = title || summaryLabel || '产物预览'

  return (
    <section
      className={cn('rounded-lg border border-border bg-surface', className)}
      data-testid={testId}
    >
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-3 py-2.5">
        <h3 className="text-sm font-semibold text-ink">{heading}</h3>
        <div className="flex gap-1 text-xs" role="group" aria-label="产物预览模式">
          <button
            type="button"
            className={cn(
              'rounded-md px-2.5 py-1 transition',
              mode === 'readable'
                ? 'bg-action/10 font-medium text-action'
                : 'text-ink-muted hover:bg-canvas-muted hover:text-ink',
            )}
            aria-pressed={mode === 'readable'}
            onClick={() => setMode('readable')}
          >
            可读预览
          </button>
          <button
            type="button"
            className={cn(
              'rounded-md px-2.5 py-1 transition',
              mode === 'json'
                ? 'bg-action/10 font-medium text-action'
                : 'text-ink-muted hover:bg-canvas-muted hover:text-ink',
            )}
            aria-pressed={mode === 'json'}
            onClick={() => setMode('json')}
          >
            原始 JSON
          </button>
        </div>
      </header>

      <div className="p-3">
        {mode === 'readable' ? (
          sections.length === 0 ? (
            <p className="text-xs text-ink-faint">暂无可读字段，可切换到原始 JSON。</p>
          ) : (
            <div data-testid="artifact-preview-readable" className="space-y-3">
              {sections.map((section) => (
                <section
                  key={section.id}
                  className="rounded-md border border-border/70 bg-canvas-muted/40 px-3 py-2.5"
                >
                  <h4 className="text-xs font-semibold tracking-wide text-ink">
                    {section.title}
                  </h4>
                  {section.hint ? (
                    <p className="mt-1 text-xs leading-relaxed text-ink-faint">{section.hint}</p>
                  ) : null}
                  <SectionBody section={section} />
                </section>
              ))}
            </div>
          )
        ) : (
          <pre
            data-testid="artifact-preview-json"
            className="overflow-x-auto whitespace-pre-wrap break-words rounded-md border border-border bg-canvas-muted/40 px-3 py-2 font-mono text-xs leading-relaxed text-ink"
          >
            {jsonText}
          </pre>
        )}
      </div>
    </section>
  )
}
