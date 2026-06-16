import { LayoutList } from 'lucide-react'

export default function EpisodeNav({
  navigation = [],
  episodes = [],
  activeEpisode,
  onSelectEpisode,
  onSelectRange,
}) {
  if (!navigation?.length && !episodes?.length) return null

  return (
    <aside className="w-full lg:w-44 shrink-0 space-y-4">
      {navigation?.length > 0 && (
        <div>
          <p className="text-[11px] text-navy-400 mb-2 uppercase tracking-wide">结构导航</p>
          <div className="space-y-1">
            {navigation.map((block) => (
              <button
                key={`${block.label}-${block.from_episode}`}
                type="button"
                onClick={() => onSelectRange?.(block)}
                className="w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-left text-xs text-navy-300 transition-colors hover:border-gold-400/30 hover:text-white"
              >
                <span className="font-semibold text-navy-100">{block.label}</span>
                <span className="block text-navy-400 mt-0.5">
                  第{block.from_episode}–{block.to_episode}集
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {episodes?.length > 0 && (
        <div>
          <p className="text-[11px] text-navy-400 mb-2 uppercase tracking-wide flex items-center gap-1">
            <LayoutList className="w-3 h-3" />
            分集
          </p>
          <div className="max-h-64 overflow-y-auto space-y-1 pr-1">
            {episodes.map((ep) => {
              const num = ep.episodeNumber
              const active = activeEpisode === num
              return (
                <button
                  key={num}
                  type="button"
                  onClick={() => onSelectEpisode?.(num)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
                    active
                      ? 'bg-gold-400/15 border border-gold-400/40 text-gold-200'
                      : 'border border-transparent text-navy-400 hover:bg-white/[0.05] hover:text-navy-200'
                  }`}
                >
                  第{num}集 {ep.title ? `· ${ep.title.slice(0, 10)}` : ''}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </aside>
  )
}
