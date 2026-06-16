import { useEffect, useState } from 'react'
import {
  Loader2,
  ShieldCheck,
  Sparkles,
  Star,
  Megaphone,
  Clapperboard,
  Check,
} from 'lucide-react'
import { toast } from 'sonner'
import { works as worksApi } from '@/services/api'
import { ExecutionDurationLabel } from '@/components/shared/ExecutionRunPanel'

function AgentCard({ title, icon: Icon, children, action, durationMs }) {
  return (
    <div className="flex min-h-[140px] flex-col rounded-xl border border-white/5 bg-slate-900/40 p-4">
      <div className="flex items-center justify-between gap-2 mb-2">
        <p className="text-xs text-gold-400/90 flex items-center gap-1">
          {Icon && <Icon className="w-3.5 h-3.5" />}
          {title}
        </p>
        <ExecutionDurationLabel durationMs={durationMs} className="text-[10px] shrink-0" />
      </div>
      <div className="flex-1 text-sm">{children}</div>
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}

function ReviewSubReport({ label, passed, skipped, issues = [], extra }) {
  if (skipped) return null
  const visibleIssues = (issues || []).filter(Boolean)
  if (passed == null && !visibleIssues.length && !extra) return null
  const ok = passed !== false
  return (
    <div className="mt-2 rounded-lg border border-white/5 bg-slate-900/40 px-2.5 py-2">
      <p className={`text-[11px] font-medium ${ok ? 'text-green-400/90' : 'text-amber-400/90'}`}>
        {label}
        {passed != null ? (ok ? ' · 通过' : ' · 待优化') : ''}
        {extra ? ` · ${extra}` : ''}
      </p>
      {visibleIssues.slice(0, 2).map((line, i) => (
        <p key={i} className="text-[10px] text-navy-400 mt-0.5 line-clamp-2">
          · {line}
        </p>
      ))}
    </div>
  )
}

export default function PostScriptPanel({ projectId, postScript, onRefresh }) {
  const [running, setRunning] = useState(null)
  const [polishApplying, setPolishApplying] = useState(false)
  const [selectedPolish, setSelectedPolish] = useState(new Set())
  const [showAllPolish, setShowAllPolish] = useState(false)

  const suggestions = postScript?.polish?.suggestions || []

  useEffect(() => {
    setSelectedPolish(new Set())
  }, [suggestions.length, postScript?.polish?.applied])

  if (!postScript?.scriptsReady) return null

  const {
    status,
    review,
    score,
    polish,
    insight,
    insightStatus = 'not_run',
    insightCanGenerate = true,
    marketing,
    marketingStatus = 'not_run',
    marketingCanGenerate = true,
  } = postScript

  async function runAgent(agentId) {
    if (running) {
      toast.message('已有 Agent 正在执行，请稍候')
      return
    }
    setRunning(agentId)
    try {
      const res = await worksApi.runAgent(projectId, agentId)
      if (res?.status === 'error') {
        throw new Error((res.errors || []).join('；') || 'Agent 执行失败')
      }
      toast.success(
        agentId === 'insight'
          ? '拉片分析完成'
          : agentId === 'marketing'
            ? '宣发物料已生成'
            : '已提交，请稍后刷新'
      )
      await onRefresh?.()
    } catch (e) {
      toast.error(e.message || '执行失败')
    } finally {
      setRunning(null)
    }
  }

  function togglePolishIndex(index) {
    setSelectedPolish((prev) => {
      const next = new Set(prev)
      if (next.has(index)) next.delete(index)
      else next.add(index)
      return next
    })
  }

  async function handleApplyPolish(applyAll = false) {
    if (polishApplying) return
    setPolishApplying(true)
    try {
      await worksApi.applyPolish(projectId, {
        apply_all: applyAll,
        indices: applyAll ? undefined : Array.from(selectedPolish),
      })
      toast.success('润色建议已写入剧本备注')
      setSelectedPolish(new Set())
      await onRefresh?.()
    } catch (e) {
      toast.error(e.message || '应用失败')
    } finally {
      setPolishApplying(false)
    }
  }

  const visiblePolish = showAllPolish ? suggestions : suggestions.slice(0, 4)

  return (
    <div className="mt-6 rounded-2xl border border-white/5 bg-slate-900/60 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-gold-400/90" />
          <h3 className="text-sm font-semibold text-white">后处理与增值 Agent</h3>
        </div>
        {status === 'running' && (
          <span className="text-xs text-gold-400 inline-flex items-center gap-1.5">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            自动后处理中…
          </span>
        )}
        {status === 'pending' && (
          <span className="text-xs text-navy-400">全剧剧本已齐，等待后处理</span>
        )}
        {status === 'done' && (
          <span className="text-xs text-green-400/90 inline-flex items-center gap-1">
            <Check className="w-3.5 h-3.5" />
            后处理已完成
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 mb-4">
        <AgentCard
          title="质检"
          icon={ShieldCheck}
          durationMs={review?.durationMs ?? review?.executionRun?.duration_ms}
          action={
            <button
              type="button"
              disabled={!!running}
              onClick={() => runAgent('review')}
              className="text-xs text-gold-400 hover:text-gold-300 disabled:opacity-50"
            >
              {running === 'review' ? '提交中…' : '重新质检'}
            </button>
          }
        >
          {review ? (
            <>
              <p className="text-navy-100">
                {review.passed ? '通过' : '待优化'}
                {review.pacingPassed === false && ' · 节奏需调整'}
                {review.gatePassed === false && ' · Gate 未过'}
              </p>
              <ReviewSubReport
                label="结构质检"
                passed={review.plotStructure?.passed}
                issues={review.plotStructure?.issues}
              />
              <ReviewSubReport
                label="质量校验"
                passed={review.qualityGuard?.passed}
                skipped={review.qualityGuard?.skipped}
                issues={review.qualityGuard?.issues}
              />
              {review.scoreQuick && !review.scoreQuick.skipped && review.scoreQuick.overallScore != null && (
                <ReviewSubReport
                  label="快评"
                  passed
                  extra={`${review.scoreQuick.overallScore} 分${review.scoreQuick.grade ? ` · ${review.scoreQuick.grade}` : ''}`}
                />
              )}
              {review.scoreQuick?.skipped && review.scoreQuick.reason && (
                <p className="text-[10px] text-navy-400 mt-1">快评跳过：{review.scoreQuick.reason}</p>
              )}
              {review.complianceFuse?.triggered && (
                <ReviewSubReport
                  label="合规熔断"
                  passed={false}
                  issues={(review.complianceFuse.categories || []).map(
                    (c) => c.label || c.code || '红线'
                  )}
                />
              )}
              {review.complianceContent && review.complianceContent.passed === false && (
                <ReviewSubReport
                  label="内容合规"
                  passed={false}
                  issues={review.complianceContent.issues}
                  extra={
                    review.complianceContent.highRiskCount != null
                      ? `高危 ${review.complianceContent.highRiskCount} 项`
                      : undefined
                  }
                />
              )}
              {(review.issues || []).slice(0, 3).map((issue, i) => (
                <p key={i} className="text-xs text-navy-400 mt-1">
                  · {issue}
                </p>
              ))}
            </>
          ) : (
            <p className="text-xs text-navy-400">暂无报告</p>
          )}
        </AgentCard>

        <AgentCard
          title="深度评分"
          icon={Star}
          durationMs={score?.durationMs ?? score?.executionRun?.duration_ms}
          action={
            <button
              type="button"
              disabled={!!running}
              onClick={() => runAgent('score')}
              className="text-xs text-gold-400 hover:text-gold-300 disabled:opacity-50"
            >
              {running === 'score' ? '评分中…' : '重新评分'}
            </button>
          }
        >
          {score?.overallScore != null ? (
            <>
              <p className="text-navy-100">
                {score.overallScore} 分
                {score.grade ? ` · ${score.grade} 级` : ''}
              </p>
            </>
          ) : (
            <p className="text-xs text-navy-400">暂无评分</p>
          )}
        </AgentCard>

        <AgentCard
          title="拉片分析"
          icon={Clapperboard}
          durationMs={insight?.durationMs ?? insight?.executionRun?.duration_ms}
          action={
            <button
              type="button"
              disabled={!!running || !insightCanGenerate}
              onClick={() => runAgent('insight')}
              className="text-xs text-gold-400 hover:text-gold-300 disabled:opacity-50"
            >
              {running === 'insight' ? '分析中…' : insight?.lineCount ? '重新拉片' : '开始拉片'}
            </button>
          }
        >
          {insightStatus === 'running' && (
            <p className="text-xs text-gold-400 inline-flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />拉片分析中…
            </p>
          )}
          {insightStatus === 'failed' && (
            <p className="text-xs text-red-400">执行失败，可重新触发</p>
          )}
          {insight?.lineCount ? (
            <>
              <p className="text-navy-100 text-xs">
                {insight.lineCount} 行 · {insight.episodeHeadings} 集标题
              </p>
              {insight.rhythmNotes && (
                <p className="text-xs text-navy-400 mt-1 line-clamp-2">{insight.rhythmNotes}</p>
              )}
            </>
          ) : insightStatus === 'not_run' ? (
            <p className="text-xs text-navy-400">拆解钩子、节奏与 CP 线</p>
          ) : null}
        </AgentCard>

        <AgentCard
          title="宣发物料"
          icon={Megaphone}
          durationMs={marketing?.durationMs ?? marketing?.executionRun?.duration_ms}
          action={
            <button
              type="button"
              disabled={!!running || !marketingCanGenerate}
              onClick={() => runAgent('marketing')}
              className="text-xs text-gold-400 hover:text-gold-300 disabled:opacity-50"
            >
              {running === 'marketing' ? '生成中…' : marketing?.titles?.length ? '重新生成' : '生成宣发'}
            </button>
          }
        >
          {marketingStatus === 'running' && (
            <p className="text-xs text-gold-400 inline-flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />物料生成中…
            </p>
          )}
          {marketingStatus === 'failed' && (
            <p className="text-xs text-red-400">执行失败，可重新触发</p>
          )}
          {marketing?.titles?.length ? (
            <>
              <p className="text-xs text-navy-300">剧名：{marketing.titles[0]}</p>
              {marketing.clipHooks?.[0] && (
                <p className="text-xs text-navy-400 mt-1 line-clamp-2">
                  切片：{marketing.clipHooks[0]}
                </p>
              )}
            </>
          ) : marketingStatus === 'not_run' ? (
            <p className="text-xs text-navy-400">投流标题、切片钩子、海报 Slogan</p>
          ) : null}
        </AgentCard>
      </div>

      <div className="rounded-xl border border-white/5 bg-slate-900/40 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <p className="text-xs text-gold-400/90 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5" />
            润色建议
            {polish?.applied && (
              <span className="text-green-400/90 ml-2">已应用部分</span>
            )}
          </p>
          <div className="flex items-center gap-3">
            <ExecutionDurationLabel
              durationMs={polish?.durationMs ?? polish?.executionRun?.duration_ms}
              className="text-[10px]"
            />
          <button
            type="button"
            disabled={!!running}
            onClick={() => runAgent('polish')}
            className="text-xs text-gold-400 hover:text-gold-300 disabled:opacity-50"
          >
            {running === 'polish' ? '分析中…' : suggestions.length ? '刷新建议' : '生成润色建议'}
          </button>
          </div>
        </div>

        {suggestions.length > 0 ? (
          <>
            <ul className="space-y-2 max-h-[240px] overflow-y-auto pr-1">
              {visiblePolish.map((s) => (
                <li
                  key={s.index}
                  className="flex items-start gap-3 rounded-lg border border-white/5 bg-slate-900/40 p-3 text-sm"
                >
                  <input
                    type="checkbox"
                    checked={selectedPolish.has(s.index)}
                    onChange={() => togglePolishIndex(s.index)}
                    className="mt-1 rounded border-white/20"
                  />
                  <div className="min-w-0 flex-1">
                    {s.episodeNumber != null && (
                      <span className="text-xs text-gold-400/90 mr-2">第{s.episodeNumber}集</span>
                    )}
                    {s.field && <span className="text-xs text-navy-400 mr-2">{s.field}</span>}
                    <p className="text-navy-200 text-xs whitespace-pre-wrap leading-relaxed">
                      {s.advice}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
            {suggestions.length > 4 && (
              <button
                type="button"
                onClick={() => setShowAllPolish((v) => !v)}
                className="mt-2 text-xs text-navy-400 hover:text-navy-200"
              >
                {showAllPolish ? '收起' : `展开全部 ${suggestions.length} 条`}
              </button>
            )}
            <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/5">
              <button
                type="button"
                disabled={polishApplying || selectedPolish.size === 0}
                onClick={() => handleApplyPolish(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium btn-gold disabled:opacity-50"
              >
                {polishApplying ? '写入中…' : `应用选中（${selectedPolish.size}）`}
              </button>
              <button
                type="button"
                disabled={polishApplying}
                onClick={() => handleApplyPolish(true)}
                className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-200 transition-colors hover:bg-white/[0.05] disabled:opacity-50"
              >
                应用全部
              </button>
            </div>
          </>
        ) : (
          <p className="text-xs text-navy-400">生成后可将建议写入对应集的润色备注（polishRevisionNotes）</p>
        )}
      </div>

      <p className="text-[10px] text-navy-400 mt-3">
        全剧剧本齐后自动执行 review → polish → review → score；应用润色后请刷新剧本 Tab 查看各集备注。
      </p>
    </div>
  )
}
