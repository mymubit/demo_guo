import { Save } from 'lucide-react'

export function MetaChip({ children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs bg-navy-900/50 border border-navy-600/25 text-navy-100 ${className}`}
    >
      {children}
    </span>
  )
}

export function ContentSection({ title, subtitle, children, id, headerExtra }) {
  if (!children) return null
  return (
    <section id={id} className="px-5 py-5 border-b border-navy-700/30 last:border-b-0">
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <h4 className="text-sm font-semibold text-white">{title}</h4>
        {subtitle && <span className="text-xs text-navy-500">{subtitle}</span>}
        {headerExtra}
      </div>
      {children}
    </section>
  )
}

export function AllContentShell({ meta, children, editMode, saving, onSave, showSave = true }) {
  return (
    <div className="space-y-4">
      {meta && <div className="flex flex-wrap items-center gap-2">{meta}</div>}
      <div className="rounded-2xl border border-navy-700/30 bg-navy-800/20 overflow-hidden">
        <div className="px-5 py-3 border-b border-navy-700/30 bg-navy-800/30 flex items-center justify-between gap-3">
          <h4 className="text-sm font-semibold text-white">全部内容</h4>
          {editMode && showSave && onSave && (
            <button
              type="button"
              disabled={saving}
              onClick={onSave}
              className="shrink-0 px-3 py-1.5 rounded-lg bg-navy-700/60 hover:bg-navy-600/60 border border-navy-500/30 text-white text-xs inline-flex items-center gap-1.5 disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? '保存中…' : '保存'}
            </button>
          )}
        </div>
        <div className="max-h-[70vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  )
}

export function PickerTile({ active, onClick, children, subtitle, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`aspect-square rounded-2xl border text-sm font-medium transition-all flex flex-col items-center justify-center gap-1 px-2 disabled:opacity-40 disabled:cursor-not-allowed ${
        active
          ? 'border-white/80 bg-navy-700/50 text-white shadow-lg shadow-gold-400/5'
          : 'border-navy-600/30 bg-navy-900/40 text-navy-300 hover:border-navy-500/50 hover:text-white'
      }`}
    >
      <span className="text-center leading-snug line-clamp-3 w-full">{children}</span>
      {subtitle && (
        <span className="text-[10px] text-navy-500 font-normal line-clamp-1 w-full text-center">
          {subtitle}
        </span>
      )}
    </button>
  )
}

export default function MasterDetailLayout({
  meta,
  detailTitle,
  detailExtra,
  detail,
  pickerLabel = '目录',
  picker,
  editMode,
  saving,
  onSave,
  showSave = true,
  emptyHint = '从右侧选择条目查看详情',
}) {
  return (
    <div className="space-y-4">
      {meta && <div className="flex flex-wrap items-center gap-2">{meta}</div>}

      <div className="flex flex-col-reverse lg:flex-row gap-5 lg:gap-6">
        <div className="flex-1 min-w-0 rounded-2xl border border-navy-700/30 bg-navy-800/20 overflow-hidden">
          <div className="px-5 py-3 border-b border-navy-700/30 bg-navy-800/30 flex items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2 min-w-0">
              <h4 className="text-sm font-semibold text-white truncate">
                {detailTitle || '选择条目'}
              </h4>
              {detailExtra}
            </div>
            {editMode && showSave && onSave && (
              <button
                type="button"
                disabled={saving}
                onClick={onSave}
                className="shrink-0 px-3 py-1.5 rounded-lg bg-navy-700/60 hover:bg-navy-600/60 border border-navy-500/30 text-white text-xs inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                {saving ? '保存中…' : '保存'}
              </button>
            )}
          </div>
          <div className="px-5 py-5 max-h-[70vh] overflow-y-auto">
            {detail || (
              <p className="text-sm text-navy-400 py-8 text-center">{emptyHint}</p>
            )}
          </div>
        </div>

        <div className="w-full lg:w-64 xl:w-72 shrink-0">
          <div className="text-xs text-navy-500 mb-2 px-1">{pickerLabel}</div>
          {picker}
        </div>
      </div>
    </div>
  )
}
