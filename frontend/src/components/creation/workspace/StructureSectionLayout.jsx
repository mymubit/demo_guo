import { Save } from 'lucide-react'

/**
 * 结构与世界观：左侧子级 Tab + 右侧单栏内容（预览/编辑共用）。
 */
export default function StructureSectionLayout({
  meta,
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

      <div className="rounded-2xl border border-navy-700/30 bg-navy-800/20 overflow-hidden">
        <div className="flex flex-col md:flex-row max-h-[72vh] min-h-[360px]">
          <nav
            className="shrink-0 md:w-36 lg:w-40 border-b md:border-b-0 md:border-r border-navy-700/30 bg-navy-900/35"
            aria-label={navLabel}
          >
            <div className="flex snap-x gap-1 overflow-x-auto overscroll-x-contain p-2 md:flex-col md:overflow-y-auto md:p-3 md:max-h-[72vh]">
              {sections.map((section) => {
                if (section.isGroup) {
                  return (
                    <div
                      key={section.id}
                      className="shrink-0 px-3 pt-2.5 pb-0.5 first:pt-1 md:w-full"
                    >
                      <span className="text-[10px] font-semibold tracking-wide text-navy-500">
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
                        : 'border-transparent text-navy-400 hover:text-navy-100 hover:bg-navy-800/45'
                    }`}
                  >
                    <div className="text-sm font-medium leading-snug">{section.label}</div>
                    {section.subtitle ? (
                      <div className="text-[10px] text-navy-500 mt-0.5 leading-tight">
                        {section.subtitle}
                      </div>
                    ) : null}
                  </button>
                )
              })}
            </div>
          </nav>

          <div className="flex flex-1 flex-col min-w-0 min-h-0">
            <div className="shrink-0 px-5 py-3 border-b border-navy-700/30 bg-navy-800/25 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <h4 className="text-sm font-semibold text-white truncate">
                  {active?.label || fallbackTitle}
                </h4>
                {active?.subtitle ? (
                  <p className="text-[11px] text-navy-500 mt-0.5">{active.subtitle}</p>
                ) : null}
              </div>
              {editMode && showSave && onSave ? (
                <button
                  type="button"
                  disabled={saving}
                  onClick={onSave}
                  className="shrink-0 px-3 py-1.5 rounded-lg bg-navy-700/60 hover:bg-navy-600/60 border border-navy-500/30 text-white text-xs inline-flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  {saving ? '保存中…' : '保存'}
                </button>
              ) : null}
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-5">{children}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
