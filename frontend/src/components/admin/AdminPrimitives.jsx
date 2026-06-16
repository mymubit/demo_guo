/**
 * 后台设计 primitive — 对齐 _design/components.jsx
 * PageHeader / KpiTile / Panel / DataTable / ToolbarSearch / Sparkline
 */
import { Search } from 'lucide-react'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'

export function AdminPageHeader({
  crumbs,
  title,
  subtitle,
  description,
  toolbar,
  actions,
}) {
  const sub = subtitle || description
  return (
    <div className="mb-5 flex flex-wrap items-center gap-4">
      <div className="min-w-0">
        {crumbs?.length ? (
          <div className="text-xs text-slate-500">
            {crumbs.map((c, i) => (
              <span key={`${c.label}-${i}`}>
                {i > 0 ? ' / ' : ''}
                {c.href ? (
                  <a href={c.href} className="hover:text-white">
                    {c.label}
                  </a>
                ) : i === crumbs.length - 1 ? (
                  <b className="text-white">{c.label}</b>
                ) : (
                  c.label
                )}
              </span>
            ))}
          </div>
        ) : null}
        <h1 className="mt-1 text-xl font-bold tracking-tight text-white">{title}</h1>
        {sub ? <p className="mt-1 text-sm text-slate-500">{sub}</p> : null}
      </div>
      {(toolbar || actions) && (
        <div className="ml-auto flex flex-wrap items-center gap-2">{toolbar || actions}</div>
      )}
    </div>
  )
}

export function ToolbarSearch({ placeholder, width = 240, className, ...props }) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300',
        className,
      )}
    >
      <Search className={ICON.md} />
      <input
        placeholder={placeholder}
        className="bg-transparent placeholder:text-slate-500 focus:outline-none"
        style={{ width }}
        {...props}
      />
    </div>
  )
}

export function Sparkline({ points, stroke = '#667eea', className }) {
  return (
    <svg className={cn('mt-2 h-9 w-full', className)} viewBox="0 0 120 36" preserveAspectRatio="none">
      <polyline points={points} fill="none" strokeWidth="1.5" stroke={stroke} />
    </svg>
  )
}

export function KpiTile({ label, value, delta, up, danger, gold, spark, hint }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="mt-1 text-[28px] font-bold leading-tight tracking-tight text-white">{value}</div>
      {delta ? (
        <div className={cn('mt-1 flex items-center gap-1 text-xs', up ? 'text-success-300' : 'text-danger-300')}>
          {delta}
        </div>
      ) : null}
      {hint ? <div className="mt-1 text-xs text-slate-500">{hint}</div> : null}
      {spark ? (
        <Sparkline points={spark} stroke={gold ? '#f6d365' : danger ? '#f87171' : '#667eea'} />
      ) : null}
    </div>
  )
}

export function AdminPanel({ title, sub, action, children, className }) {
  return (
    <div className={cn('rounded-2xl border border-white/5 bg-slate-900/60 p-4.5', className)}>
      {(title || action) && (
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            {title ? <h3 className="m-0 text-sm font-semibold text-white">{title}</h3> : null}
            {sub ? <div className="mt-1 text-xs text-slate-500">{sub}</div> : null}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  )
}

/**
 * columns: [{ key, header, align?: 'left'|'right', render?, className? }]
 */
export function AdminDataTable({ columns, rows, rowKey = 'id', empty = '暂无数据' }) {
  return (
    <table className="w-full border-collapse text-[13px]">
      <thead>
        <tr className="text-[11px] uppercase tracking-wider text-slate-500">
          {columns.map((c) => (
            <th
              key={c.key}
              className={cn(
                'border-b border-white/5 py-2 first:pl-0 last:pr-0',
                c.align === 'right' ? 'text-right' : 'text-left',
                c.className,
              )}
            >
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {!rows?.length ? (
          <tr>
            <td colSpan={columns.length} className="py-8 text-center text-slate-500">
              {empty}
            </td>
          </tr>
        ) : (
          rows.map((r, idx) => (
            <tr
              key={typeof rowKey === 'function' ? rowKey(r, idx) : r[rowKey] ?? idx}
              className="border-t border-white/5 hover:bg-indigo-500/[0.06]"
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={cn(
                    'py-3 text-slate-300',
                    c.align === 'right' ? 'text-right tabular-nums' : 'text-left',
                    c.className,
                  )}
                >
                  {c.render ? c.render(r) : r[c.key]}
                </td>
              ))}
            </tr>
          ))
        )}
      </tbody>
    </table>
  )
}

export function AdminPillTabs({ tabs, active, onChange, className }) {
  if (!tabs?.length) return null
  return (
    <div
      className={cn(
        'flex flex-wrap gap-1 rounded-full border border-white/10 bg-white/5 p-1 text-sm',
        className,
      )}
    >
      {tabs.map((t) => {
        const Icon = t.icon
        const isActive = active === t.key
        return (
          <button
            key={t.key}
            type="button"
            onClick={() => onChange(t.key)}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 font-medium transition-colors',
              isActive ? 'bg-white/10 text-white' : 'text-slate-300 hover:text-white',
            )}
          >
            {Icon ? <Icon className={ICON.sm} /> : null}
            {t.label}
          </button>
        )
      })}
    </div>
  )
}

export function AdminDonutChart({ data, className }) {
  const C = 2 * Math.PI * 60
  let offset = 0
  return (
    <div className={cn('relative grid h-[220px] place-items-center', className)}>
      <svg width="160" height="160" viewBox="0 0 160 160" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="80" cy="80" r="60" fill="none" stroke="rgba(255,255,255,.05)" strokeWidth="18" />
        {data.map((d) => {
          const len = (d.pct / 100) * C
          const seg = (
            <circle
              key={d.lbl}
              cx="80"
              cy="80"
              r="60"
              fill="none"
              stroke={d.color}
              strokeWidth="18"
              strokeDasharray={`${len} ${C}`}
              strokeDashoffset={-offset}
            />
          )
          offset += len
          return seg
        })}
      </svg>
      <div className="pointer-events-none absolute bottom-1.5 left-3.5 right-3.5 flex flex-wrap justify-center gap-3.5 text-[11px] text-slate-400">
        {data.map((d) => (
          <span key={d.lbl}>
            <i className="mr-1 inline-block h-2 w-2 rounded-sm align-middle" style={{ background: d.color }} />
            {d.lbl} {d.pct}%
          </span>
        ))}
      </div>
    </div>
  )
}
