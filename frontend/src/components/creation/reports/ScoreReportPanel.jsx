import ScoreReport from '../ScoreReport'

export default function ScoreReportPanel({ payload }) {
  if (!payload) {
    return <p className="text-sm text-navy-400">暂无评分报告。</p>
  }

  const report = {
    ...payload,
    dimensions: payload.dimensions || payload.scorePayload?.dimensions || [],
    overallScore: payload.overallScore ?? payload.scorePayload?.overallScore,
    grade: payload.grade ?? payload.scorePayload?.grade,
    releasePassScore: payload.releasePassScore ?? payload.scorePayload?.releasePassScore,
  }

  return (
    <div className="space-y-3">
      <ScoreReport report={report} />
      {payload.ready === false && (
        <p className="text-xs text-navy-400">剧本尚未就绪，评分为预估值。</p>
      )}
      {payload.source && (
        <p className="text-xs text-navy-500">来源：{payload.source}</p>
      )}
    </div>
  )
}
