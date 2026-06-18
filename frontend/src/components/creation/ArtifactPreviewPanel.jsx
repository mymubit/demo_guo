import SkillEditorPanel from './workspace/SkillEditorPanel'
import ReviewReportPanel from './reports/ReviewReportPanel'
import ScoreReportPanel from './reports/ScoreReportPanel'
import MarketingKitPanel from './reports/MarketingKitPanel'
import InsightReportPanel from './reports/InsightReportPanel'
import PolishLogPanel from './reports/PolishLogPanel'

const REPORT_PANELS = {
  review_report: ReviewReportPanel,
  score_report: ScoreReportPanel,
  marketing_kit: MarketingKitPanel,
  insight_report: InsightReportPanel,
  polish_log: PolishLogPanel,
}

export default function ArtifactPreviewPanel({ editorView }) {
  if (!editorView) {
    return <p className="text-sm text-navy-400">暂无预览内容。</p>
  }

  const ReportPanel = REPORT_PANELS[editorView.mode]
  if (ReportPanel) {
    return (
      <div className="max-h-[520px] overflow-auto">
        <ReportPanel payload={editorView.payload} />
      </div>
    )
  }

  if (editorView.mode === 'json') {
    return (
      <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap text-xs leading-relaxed text-navy-100">
        {JSON.stringify(editorView.payload, null, 2)}
      </pre>
    )
  }

  return (
    <div className="max-h-[520px] overflow-auto">
      <SkillEditorPanel
        skill={{ index: 0 }}
        editor={editorView}
        editMode={false}
      />
    </div>
  )
}
