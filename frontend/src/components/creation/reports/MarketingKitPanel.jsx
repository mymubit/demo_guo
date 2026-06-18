export default function MarketingKitPanel({ payload }) {
  if (!payload) {
    return <p className="text-sm text-navy-400">暂无宣发物料。</p>
  }

  const sections = [
    { key: 'titles', label: '标题候选', items: payload.titles },
    { key: 'clipHooks', label: '切片钩子', items: payload.clipHooks },
    { key: 'posterSlogans', label: '海报 Slogan', items: payload.posterSlogans },
  ]

  return (
    <div className="space-y-5">
      {sections.map(({ key, label, items }) => (
        <div key={key}>
          <p className="mb-2 text-xs uppercase tracking-wide text-navy-400">{label}</p>
          {Array.isArray(items) && items.length > 0 ? (
            <ul className="space-y-1.5 text-sm text-navy-100">
              {items.map((item, index) => (
                <li key={`${key}-${index}`} className="rounded-lg bg-white/[0.04] px-3 py-2">
                  {String(item)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-navy-500">暂无</p>
          )}
        </div>
      ))}

      {payload.titleRiskReview && (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm">
          <p className="mb-1 text-navy-300">标题风险审查</p>
          <p className={payload.titleRiskReview.passed ? 'text-green-400' : 'text-gold-400'}>
            {payload.titleRiskReview.passed ? '通过' : '需关注'}
          </p>
        </div>
      )}
    </div>
  )
}
