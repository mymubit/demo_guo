import { Save } from 'lucide-react'

/**
 * 结构与世界观：左侧子级 Tab + 右侧单栏内容（预览/编辑共用）。
 */
export default function StructureSectionLayout({
  meta,
  headerExtra,
  sections = [],
  activeId,
  onSelect,
  children,
  editMode,
  saving,
  onSave,
  showSave = true,
  navLabel = '内容模块',
  fallbackTitle = '详情',
}) {
  const active = sections.find((s) => s.id === activeId)

  return (
    <div className="space-y-4">
      {meta ? <div>{meta}</div> : null}

      <div className="overflow-hidden rounded-2xl border border-white/5 bg-slate-900/40">
        <div className="flex max-h-[76vh] min-h-[420px] flex-col md:flex-row">
          <nav
            className="shrink-0 border-b border-white/5 bg-slate-900/60 md:w-40 md:border-b-0 md:border-r xl:w-44"
            aria-label={navLabel}
          >
            <div className="flex snap-x gap-1 overflow-x-auto overscroll-x-contain p-2 md:flex-col md:overflow-y-auto md:p-3 md:max-h-[76vh]">
              {sections.map((section) => {
                if (section.isGroup) {
                  return (
                    <div
                      key={section.id}
                      className="shrink-0 px-3 pt-2.5 pb-0.5 first:pt-1 md:w-full"
                    >
                      <span className="text-[10px] font-semibold tracking-wide text-navy-400">
                        {section.label}
                      </span>
                    </div>
                  )
                }
                const isActive = section.id === activeId
                return (
                  <button
                    key={section.id}
                    type="button"
                    onClick={() => onSelect(section.id)}
                    className={`shrink-0 snap-start md:shrink md:w-full text-left rounded-xl px-3 py-2.5 transition-colors border-l-2 ${
                      isActive
                        ? 'border-gold-400 bg-gold-400/10 text-white'
                        : 'border-transparent text-navy-400 hover:bg-white/[0.05] hover:text-navy-100'
                    }`}
                  >
                    <div className="text-sm font-medium leading-snug">{section.label}</div>
                    {section.subtitle ? (
                      <div className="text-[10px] text-navy-400 mt-0.5 leading-tight">
                        {section.subtitle}
                      </div>
                    ) : null}
                  </button>
                )
              })}
            </div>
          </nav>

          <div className="flex flex-1 flex-col min-w-0 min-h-0">
            <div className="flex shrink-0 items-center justify-between gap-3 border-b border-white/5 bg-slate-900/60 px-5 py-3.5 md:px-6">
              <div className="min-w-0">
                <h4 className="text-sm font-semibold text-white truncate">
                  {active?.label || fallbackTitle}
                </h4>
                {active?.subtitle ? (
                  <p className="text-[11px] text-navy-400 mt-0.5">{active.subtitle}</p>
                ) : null}
              </div>
              {editMode && showSave && onSave ? (
                <button
                  type="button"
                  disabled={saving}
                  onClick={onSave}
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white transition-colors hover:bg-white/[0.06] disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  {saving ? '保存中…' : '保存'}
                </button>
              ) : null}
            </div>
            {headerExtra ? (
              <div className="shrink-0 border-b border-white/5 bg-slate-900/35 px-5 py-4 md:px-6">
                {headerExtra}
              </div>
            ) : null}
            <div className="flex-1 overflow-y-auto px-5 py-5 md:px-6 md:py-6">{children}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
