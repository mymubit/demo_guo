export default function PolishLogPanel({ payload }) {
  if (!payload) {
    return <p className="text-sm text-navy-400">暂无润色记录。</p>
  }

  const suggestions = payload.suggestions || []

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 text-sm text-navy-300">
        {payload.mode && <span>模式：{payload.mode}</span>}
        {payload.applied != null && (
          <span>{payload.applied ? '已应用建议' : '仅生成建议'}</span>
        )}
      </div>

      {suggestions.length > 0 ? (
        <ul className="space-y-2">
          {suggestions.map((item, index) => (
            <li
              key={`suggestion-${index}`}
              className="rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm text-navy-100"
            >
              {item.type && (
                <span className="mr-2 rounded bg-white/10 px-1.5 py-0.5 text-xs text-navy-400">
                  {item.type}
                </span>
              )}
              {item.text || item.advice || JSON.stringify(item)}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-navy-400">暂无润色建议。</p>
      )}

      {payload.applyError && (
        <p className="text-xs text-red-300">应用失败：{payload.applyError}</p>
      )}
    </div>
  )
}
