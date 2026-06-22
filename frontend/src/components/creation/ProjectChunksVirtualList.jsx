import { useMemo } from 'react'

/**
 * 流式分片虚拟列表（skill-agent/40 §7）
 */
export default function ProjectChunksVirtualList({ items = [], rowHeight = 120, height = 480 }) {
  const rows = useMemo(
    () =>
      (items || [])
        .filter(Boolean)
        .map((row, idx) => ({
          key: row.effectiveIndex ?? row.index ?? idx,
          effectiveIndex: row.effectiveIndex ?? row.index,
          data: row.data ?? row,
        })),
    [items],
  )

  if (!rows.length) {
    return <div className="rounded-xl border border-white/10 bg-black/10 p-4 text-sm text-navy-300">暂无分片数据</div>
  }

  return (
    <div
      className="overflow-y-auto rounded-xl border border-white/10 bg-black/10"
      style={{ maxHeight: height }}
    >
      {rows.map((row) => (
        <div
          key={row.key}
          className="border-b border-white/5 px-4 py-3"
          style={{ minHeight: rowHeight }}
        >
          <div className="mb-1 text-xs font-medium text-gold-300">第 {row.effectiveIndex} 集</div>
          <pre className="max-h-24 overflow-hidden text-xs text-navy-200 whitespace-pre-wrap">
            {JSON.stringify(row.data, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  )
}
