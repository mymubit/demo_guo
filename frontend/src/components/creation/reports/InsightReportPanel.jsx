function LayerBlock({ title, data }) {
  if (!data || typeof data !== 'object') {
    return null
  }
  const entries = Object.entries(data).filter(([, value]) => value != null && value !== '')
  if (!entries.length) {
    return null
  }
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <p className="mb-3 text-sm font-medium text-gold-300">{title}</p>
      <dl className="space-y-2 text-sm">
        {entries.slice(0, 8).map(([key, value]) => (
          <div key={key}>
            <dt className="text-xs text-navy-400">{key}</dt>
            <dd className="mt-0.5 text-navy-100">
              {typeof value === 'object' ? JSON.stringify(value).slice(0, 200) : String(value)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export default function InsightReportPanel({ payload }) {
  if (!payload) {
    return <p className="text-sm text-navy-400">暂无洞察报告。</p>
  }

  return (
    <div className="space-y-4">
      {payload.methodology && (
        <p className="text-sm text-navy-300">{payload.methodology}</p>
      )}
      <LayerBlock title="第一层 · 剥离" data={payload.layer1_peel} />
      <LayerBlock title="第二层 · 观照" data={payload.layer2_mirror} />
      <LayerBlock title="第三层 · 颠倒" data={payload.layer3_invert} />
      {payload.analysis?.hookPoints?.length > 0 && (
        <div>
          <p className="mb-2 text-xs uppercase tracking-wide text-navy-400">钩子要点</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-navy-200">
            {payload.analysis.hookPoints.filter(Boolean).slice(0, 6).map((hook, index) => (
              <li key={`hook-${index}`}>{hook}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
