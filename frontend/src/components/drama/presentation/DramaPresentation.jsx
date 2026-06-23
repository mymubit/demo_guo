import { useState } from 'react'
import { CheckCircle2, ChevronDown, ChevronUp, XCircle } from 'lucide-react'

function MetricsBlock({ block }) {
  return (
    <section>
      {block.title ? <h5 className="text-xs font-semibold text-gray-500 mb-2">{block.title}</h5> : null}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {(block.items || []).map((item, index) => (
          <div key={`${item.label}-${index}`} className="rounded-lg bg-indigo-50 border border-indigo-100 px-3 py-2">
            <p className="text-[10px] text-indigo-600">{item.label}</p>
            <p className="text-lg font-semibold text-gray-900 mt-0.5">{item.value}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

function HeroBlock({ block }) {
  return (
    <div className="rounded-lg bg-indigo-50 border border-indigo-100 px-4 py-3">
      {block.title ? <p className="text-xs font-medium text-indigo-600 mb-1">{block.title}</p> : null}
      {block.subtitle ? (
        <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">{block.subtitle}</p>
      ) : null}
    </div>
  )
}

function KvBlock({ block }) {
  return (
    <section>
      {block.title ? <h5 className="text-xs font-semibold text-gray-500 mb-2">{block.title}</h5> : null}
      <dl className="space-y-2">
        {(block.rows || []).map((row, index) => (
          <div key={`${block.title || 'kv'}-${row.key}-${index}`} className="grid grid-cols-[minmax(5rem,28%)_1fr] gap-2 text-sm">
            <dt className="text-gray-500">{row.key}</dt>
            <dd className="text-gray-800 whitespace-pre-wrap">{row.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

function ParagraphBlock({ block }) {
  return (
    <section>
      {block.title ? <h5 className="text-xs font-semibold text-gray-500 mb-2">{block.title}</h5> : null}
      <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{block.text}</p>
    </section>
  )
}

function ListBlock({ block }) {
  return (
    <section>
      {block.title ? <h5 className="text-xs font-semibold text-gray-500 mb-2">{block.title}</h5> : null}
      <ul className="list-disc pl-5 space-y-1.5 text-sm text-gray-800">
        {(block.items || []).map((item, index) => (
          <li key={`${block.title}-${index}`} className="leading-relaxed">
            {item}
          </li>
        ))}
      </ul>
    </section>
  )
}

function CardsBlock({ block }) {
  return (
    <section>
      {block.title ? <h5 className="text-xs font-semibold text-gray-500 mb-2">{block.title}</h5> : null}
      <div className="space-y-2">
        {(block.items || []).map((item, index) => (
          <div key={`${item.title}-${index}`} className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-medium text-gray-900">{item.title}</p>
              {item.subtitle ? <span className="text-xs text-gray-500">{item.subtitle}</span> : null}
            </div>
            {(item.tags || []).filter(Boolean).length > 0 ? (
              <div className="mt-1 flex flex-wrap gap-1">
                {item.tags.filter(Boolean).map((tag, tagIndex) => (
                  <span key={`${item.title}-${tag}-${tagIndex}`} className="rounded-full bg-white px-2 py-0.5 text-[10px] text-gray-600 border border-gray-200">
                    {tag}
                  </span>
                ))}
              </div>
            ) : null}
            {item.body ? (
              <p className="mt-2 text-xs text-gray-600 leading-relaxed whitespace-pre-wrap">{item.body}</p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  )
}

function VerdictBlock({ block }) {
  return (
    <section className="rounded-lg border border-gray-100 p-4">
      <div className="flex items-center gap-2 mb-2">
        {block.passed ? (
          <CheckCircle2 className="h-5 w-5 text-green-600" />
        ) : (
          <XCircle className="h-5 w-5 text-red-500" />
        )}
        <span className={`text-sm font-semibold ${block.passed ? 'text-green-700' : 'text-red-700'}`}>
          {block.detail || (block.passed ? '通过' : '未通过')}
        </span>
      </div>
      {(block.issues || []).length > 0 ? (
        <ul className="mt-2 space-y-1.5 text-xs text-gray-700">
          {block.issues.map((issue, index) => (
            <li key={`issue-${index}`} className="rounded bg-gray-50 px-2 py-1.5 leading-relaxed">
              {issue}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}

function ScoreBoardBlock({ block }) {
  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end gap-3">
        {block.grade ? (
          <span className="text-2xl font-bold text-indigo-600">{block.grade}</span>
        ) : null}
        {block.total != null ? (
          <span className="text-sm text-gray-600">总分 {block.total}</span>
        ) : null}
      </div>
      {block.summary ? (
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{block.summary}</p>
      ) : null}
      {(block.dimensions || []).length > 0 ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {block.dimensions.map((row, index) => (
            <div key={`${row.name}-${index}`} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm">
              <span className="text-gray-600">{row.name}</span>
              <span className="font-medium text-gray-900">{row.score}</span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  )
}

function ChecksBlock({ block }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        {block.passed ? (
          <CheckCircle2 className="h-5 w-5 text-green-600" />
        ) : (
          <XCircle className="h-5 w-5 text-red-500" />
        )}
        <span className="text-sm font-medium text-gray-900">{block.verdict || '—'}</span>
      </div>
      <div className="space-y-2">
        {(block.items || []).map((row, index) => (
          <div key={`${row.level}-${index}`} className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
            <div className="flex items-center justify-between gap-2 text-sm">
              <span className="font-medium text-gray-800">{row.level}</span>
              <span className="text-xs text-gray-500">{row.status}</span>
            </div>
            {row.detail ? (
              <p className="mt-1 text-xs text-gray-600 leading-relaxed whitespace-pre-wrap">{row.detail}</p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  )
}

function ScriptEpisodesBlock({ block }) {
  return (
    <section className="space-y-4">
      {(block.episodes || []).map((episode) => (
        <div key={episode.episodeNumber} className="rounded-xl border border-gray-200 overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 border-b border-gray-100">
            <p className="text-sm font-medium text-gray-900">
              第{episode.episodeNumber}集 {episode.title !== `第${episode.episodeNumber}集` ? `· ${episode.title}` : ''}
            </p>
            {episode.memoryCheckPoint ? (
              <p className="mt-1 text-xs text-gray-500">检查点：{episode.memoryCheckPoint}</p>
            ) : null}
          </div>
          <div className="divide-y divide-gray-100">
            {(episode.beats || []).map((beat, index) => (
              <div key={`${episode.episodeNumber}-beat-${index}`} className="px-4 py-3 text-sm space-y-1.5">
                {beat.sceneHeader ? (
                  <p className="text-xs font-semibold text-indigo-700">{beat.sceneHeader}</p>
                ) : null}
                {beat.action ? (
                  <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{beat.action}</p>
                ) : null}
                {beat.dialogue ? (
                  <p className="text-gray-900 font-medium leading-relaxed whitespace-pre-wrap">{beat.dialogue}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ))}
    </section>
  )
}

export function PresentationBlock({ block }) {
  if (!block) return null
  switch (block.type) {
    case 'hero':
      return <HeroBlock block={block} />
    case 'metrics':
      return <MetricsBlock block={block} />
    case 'kv':
      return <KvBlock block={block} />
    case 'paragraph':
      return <ParagraphBlock block={block} />
    case 'list':
      return <ListBlock block={block} />
    case 'cards':
      return <CardsBlock block={block} />
    case 'verdict':
      return <VerdictBlock block={block} />
    case 'score_board':
      return <ScoreBoardBlock block={block} />
    case 'checks':
      return <ChecksBlock block={block} />
    case 'script_episodes':
      return <ScriptEpisodesBlock block={block} />
    default:
      return null
  }
}

export function DramaPresentationCard({ view, raw }) {
  const [showRaw, setShowRaw] = useState(false)
  if (!view) return null

  return (
    <article className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      <header className="flex items-start justify-between gap-3 border-b border-gray-100 px-4 py-3 bg-gray-50/80">
        <div>
          <h4 className="text-sm font-medium text-gray-900">{view.label || view.artifact_key}</h4>
          {view.summary ? <p className="mt-1 text-xs text-gray-500 line-clamp-2">{view.summary}</p> : null}
        </div>
        <button
          type="button"
          onClick={() => setShowRaw((value) => !value)}
          className="inline-flex items-center gap-1 shrink-0 text-xs text-gray-500 hover:text-gray-700"
        >
          {showRaw ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          {showRaw ? '收起 JSON' : 'JSON'}
        </button>
      </header>
      <div className="p-4 space-y-4">
        {(view.blocks || []).map((block, index) => (
          <PresentationBlock key={`${view.artifact_key}-${block.type}-${index}`} block={block} />
        ))}
        {!view.blocks?.length ? (
          <p className="text-sm text-gray-400">暂无可读内容</p>
        ) : null}
        {showRaw && raw != null ? (
          <pre className="text-xs bg-gray-50 border border-gray-100 rounded-lg p-4 overflow-auto max-h-80 text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(raw, null, 2)}
          </pre>
        ) : null}
      </div>
    </article>
  )
}

export default function DramaPresentation({ views = {}, rawArtifacts = {} }) {
  const keys = Object.keys(views)
  if (!keys.length) {
    return <div className="text-center py-8 text-gray-400 text-sm">执行已完成，暂无展示内容</div>
  }
  return (
    <div className="space-y-4">
      {keys.map((key) => (
        <DramaPresentationCard key={key} view={views[key]} raw={rawArtifacts[key]} />
      ))}
    </div>
  )
}
