import { ArrowRight } from 'lucide-react'
import { getEntryMeta } from '@/utils/creationEntryMeta'
import { cn } from '@/utils/cn'

/** 首屏主推：原创 / 大纲扩写 */
const PRIMARY_ENTRY_KEYS = ['from-scratch', 'from-outline']

function EntryCard({ entry, catalog, onSelectEntry }) {
  const meta = getEntryMeta(entry.key, entry, catalog)
  const Icon = meta.icon
  return (
    <button
      type="button"
      onClick={() => onSelectEntry(entry.key)}
      className={cn(
        'group rounded-2xl border border-white/10 bg-white/[0.03] p-6 text-left transition-all',
        'hover:border-gold-400/40 hover:bg-gold-400/10',
      )}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gold-400/20 to-purple-500/20 flex items-center justify-center border border-gold-500/20">
            <Icon className="w-6 h-6 text-gold-400" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider text-purple-300 font-semibold">
              {meta.tag}
            </span>
            <h3 className="text-lg font-bold text-white group-hover:text-gold-300 transition-colors">
              {meta.name}
            </h3>
          </div>
        </div>
        <ArrowRight className="w-5 h-5 text-navy-400 group-hover:text-gold-400 group-hover:translate-x-0.5 transition-all shrink-0 mt-2" />
      </div>
      <p className="text-sm text-navy-300 leading-relaxed">{meta.description}</p>
    </button>
  )
}

export default function CreationEntryHub({ catalog, onSelectEntry }) {
  const all = catalog.creationEntries || []
  const primary = PRIMARY_ENTRY_KEYS
    .map((key) => all.find((e) => e.key === key))
    .filter(Boolean)
  const secondary = all.filter((e) => !PRIMARY_ENTRY_KEYS.includes(e.key))

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {primary.map((entry) => (
          <EntryCard key={entry.key} entry={entry} catalog={catalog} onSelectEntry={onSelectEntry} />
        ))}
      </div>
      {secondary.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {secondary.map((entry) => (
            <EntryCard key={entry.key} entry={entry} catalog={catalog} onSelectEntry={onSelectEntry} />
          ))}
        </div>
      ) : null}
    </div>
  )
}
