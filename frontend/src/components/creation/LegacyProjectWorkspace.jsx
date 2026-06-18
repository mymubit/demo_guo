import { useCallback, useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Sparkles,
  Check,
  Download,
  Share2,
  ArrowLeft,
  Loader2,
  AlertCircle,
  Pencil,
  Eye,
  LayoutList,
  FileText,
} from 'lucide-react'
import ReadableMarkdownPanel from './workspace/ReadableMarkdownPanel'
import PostScriptPanel from './workspace/PostScriptPanel'
import WorkspaceModuleSidebar from './workspace/WorkspaceModuleSidebar'
import WorkspaceStatsPanel from './workspace/WorkspaceStatsPanel'
import { ExecutionDurationLabel } from '@/components/shared/ExecutionRunPanel'
import { toast } from 'sonner'
import { creation } from '@/services/api'
import { displayPipelineStepName } from '@/utils/pipelineNodes'
import { resolveSkillId } from '@/utils/skillTerm'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import SkillEditorPanel from './workspace/SkillEditorPanel'
import StepStatusMark from '@/components/ui/StepStatusMark'
import { ErrorState } from '@/components/ui/AsyncState'
import { GateLogBadge } from './workspace/GateLogSection'
import { cn } from '@/utils/cn'
import { useSubmitGuard } from '@/hooks/useSubmitGuard'

function agentTabName(module) {
  if (module?.agent_name_zh) return module.agent_name_zh
  if (module?.index === 1) return '立项整理'
  return displayPipelineStepName(module?.name || '')
}

function isSkillPassed(skill) {
  if (!skill || skill.status === 'failed') return false
  if (skill.index === 1) {
    return skill.has_content && skill.content_kind === 'user_confirmed'
  }
  return skill.content_kind === 'agent_generated'
}

function QualityAlertBanner({ alerts, onAcknowledge, acknowledgingCode }) {
  const visible = (alerts || []).filter((alert) => alert.code !== 'brief-incomplete')
  if (!visible.length) return null
  return (
    <div className="mb-6 space-y-3">
      {visible.map((alert) => (
        <div
          key={alert.code}
          className={`px-4 py-3 rounded-xl text-sm border ${
            alert.level === 'error'
              ? 'bg-red-500/10 border-red-500/30 text-red-200'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-200'
          }`}
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="font-medium">{alert.title}</p>
              {alert.message && <p className="mt-1 text-xs opacity-90">{alert.message}</p>}
            </div>
            {alert.acknowledgable && onAcknowledge ? (
              <button
                type="button"
                disabled={acknowledgingCode === alert.code}
                onClick={() => onAcknowledge(alert.code)}
                className="shrink-0 rounded-lg border border-gold-400/40 bg-gold-400/10 px-3 py-1.5 text-xs font-medium text-gold-200 hover:bg-gold-400/20 disabled:opacity-50"
              >
                {acknowledgingCode === alert.code ? '确认中…' : '我已确认，继续'}
              </button>
            ) : null}
          </div>
          {alert.details?.length > 0 && (
            <div className="mt-3 space-y-2">
              {alert.details.map((detail, i) => (
                <div
                  key={`${alert.code}-detail-${i}`}
                  className="rounded-lg border border-white/10 bg-black/10 px-3 py-2 text-xs leading-relaxed"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-white/90">{detail.category || '风险项'}</span>
                    {detail.matched_text ? (
                      <span className="rounded-full bg-white/10 px-2 py-0.5 text-[11px]">
                        命中：{detail.matched_text}
                      </span>
                    ) : null}
                  </div>
                  {detail.excerpt ? (
                    <p className="mt-1 text-white/80">片段：{detail.excerpt}</p>
                  ) : null}
                  {detail.constraint ? (
                    <p className="mt-1 opacity-90">规则：{detail.constraint}</p>
                  ) : null}
                  {detail.suggestion ? (
                    <p className="mt-1 opacity-90">建议：{detail.suggestion}</p>
                  ) : null}
                </div>
              ))}
            </div>
          )}
          {alert.issues?.length > 0 && (
            <ul className={`text-xs space-y-1 list-disc list-inside opacity-90 ${alert.details?.length > 0 ? 'mt-3' : 'mt-2'}`}>
              {alert.issues.map((issue, i) => (
                <li key={`${alert.code}-${i}`}>{issue}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  )
}

function SkillStatusBadge({ skill }) {
  const { status, content_kind: kind, has_content: hasContent, index } = skill || {}

  if (status === 'running') {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gold-400/15 text-gold-400 animate-pulse">
        <Loader2 className="w-3 h-3 animate-spin" />
        生成中
      </span>
    )
  }
  if (status === 'failed') {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-400/15 text-red-400">
        <AlertCircle className="w-3 h-3" />
        失败
      </span>
    )
  }
  if (isSkillPassed(skill)) {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-400/15 text-green-400">
        <Check className="w-3 h-3" />
        {index === 1 ? '已通过' : '已生成'}
      </span>
    )
  }
  if (kind === 'user_confirmed' || (index === 1 && hasContent)) {
    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gold-400/15 text-gold-300">
        <Check className="w-3 h-3" />
        已确认
      </span>
    )
  }
  if (kind === 'skeleton') {
    return (
      <span className="text-xs px-2 py-0.5 rounded-full bg-white/[0.05] text-navy-300">骨架就绪</span>
    )
  }
  if (hasContent) {
    return (
      <span className="text-xs px-2 py-0.5 rounded-full bg-white/[0.05] text-navy-300">草稿</span>
    )
  }
  return (
    <span className="text-xs px-2 py-0.5 rounded-full bg-white/[0.05] text-slate-400">待生成</span>
  )
}

function LegacyProjectWorkspace({
  projectId,
  currencyName = '创作币',
  onBack,
  onRestart,
}) {
  const [workspace, setWorkspace] = useState(null)
  const [activeIndex, setActiveIndex] = useState(1)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [downloadingFormat, setDownloadingFormat] = useState('')
  const [sharing, setSharing] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [contentViewMode, setContentViewMode] = useState('structured')
  const [acknowledgingCode, setAcknowledgingCode] = useState('')
  const [error, setError] = useState('')
  const pollCountRef = useRef(0)
  const requestSeqRef = useRef(0)
  const { isSubmitting: isGenerateLocked, runSubmit: runGenerateSubmit } = useSubmitGuard({
    minInterval: 1000,
    onError: () => {},
    shouldThrow: true,
  })

  const loadWorkspace = useCallback(async () => {
    if (!projectId) return
    const requestSeq = requestSeqRef.current + 1
    requestSeqRef.current = requestSeq
    try {
      const data = await creation.workspace(projectId)
      if (requestSeqRef.current !== requestSeq) return
      setWorkspace(data)
      setError(data?.error_message || '')
      if (data?.running_skill_index) {
        setActiveIndex(data.running_skill_index)
      }
    } catch (e) {
      if (requestSeqRef.current !== requestSeq) return
      setError(e.message || '加载工作台失败')
    } finally {
      if (requestSeqRef.current === requestSeq) {
        setLoading(false)
      }
    }
  }, [projectId])

  useEffect(() => {
    setLoading(true)
    loadWorkspace()
  }, [loadWorkspace])

  useEffect(() => {
    setEditMode(false)
    setContentViewMode('structured')
    window.setTimeout(() => window.dispatchEvent(new Event('resize')), 0)
  }, [activeIndex])

  const modules = workspace?.skills || []
  const executionPlan = workspace?.execution_plan
  const hasOrchestrationHints =
    Boolean(executionPlan?.has_parallel) || Boolean(executionPlan?.has_branches)

  const isBusy =
    workspace?.status === 'running' ||
    (workspace?.status !== 'failed' &&
      (workspace?.running_skill_index || modules.some((s) => s.status === 'running')))

  const runningSkill =
    workspace?.status !== 'failed' ? modules.find((s) => s.status === 'running') : null
  const runningBlocker = workspace?.running_blocker
  const activeSkill = modules.find((s) => s.index === activeIndex)
  const activeSkillGenerating =
    activeSkill?.status === 'running' && workspace?.status !== 'failed'
  const contextualError =
    activeSkill?.error_message ||
    (workspace?.status === 'failed' &&
    (workspace?.failed_node_index == null || workspace.failed_node_index === activeIndex)
      ? error
      : '')

  useEffect(() => {
    if (!projectId || !isBusy) return
    pollCountRef.current = 0
    let timer = null
    const pollDelay = () => {
      if (pollCountRef.current < 8) return 2500
      if (pollCountRef.current < 20) return 5000
      return 8000
    }
    const tick = () => {
      if (document.hidden) return
      pollCountRef.current += 1
      loadWorkspace()
    }
    const schedule = (immediate = false) => {
      if (timer) window.clearTimeout(timer)
      if (document.hidden) return
      if (immediate) tick()
      timer = window.setTimeout(() => {
        tick()
        schedule()
      }, pollDelay())
    }
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        pollCountRef.current = 0
        schedule(true)
        return
      }
      if (timer) window.clearTimeout(timer)
    }

    schedule(true)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      if (timer) window.clearTimeout(timer)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [projectId, isBusy, loadWorkspace])

  const hasModuleStats = modules.length > 0
  const generatedCount = hasModuleStats
    ? modules.filter((skill) => skill.status !== 'failed' && skill.content_kind === 'agent_generated').length
    : workspace?.completed_agent_count ?? workspace?.completed_skill_count ?? 0
  const confirmedCount = hasModuleStats
    ? modules.filter((skill) => skill.status !== 'failed' && skill.has_content).length
    : workspace?.confirmed_skill_count ?? generatedCount
  const completedCount = hasModuleStats
    ? modules.filter((skill) => isSkillPassed(skill)).length
    : generatedCount
  const totalSkills = workspace?.total_agents ?? workspace?.total_skills ?? 5
  const nextBatch = activeSkill?.editor?.nextBatch
  const outlineCoinCost =
    activeSkill?.index === 4
      ? activeSkill?.editor?.frameworkCoinCost || activeSkill?.coin_cost || 0
      : 0

  async function handleOutlineGenerate(options = {}) {
    await handleGenerate(4, options)
  }

  async function handleGenerate(nodeIndex, options = {}) {
    if (!projectId || generating || isGenerateLocked) return
    setGenerating(true)
    try {
      await runGenerateSubmit(async () => {
        await creation.generateAgent(projectId, nodeIndex, options)
        toast.success(options.regenerate ? '已提交重新生成' : '已提交生成任务')
        setActiveIndex(nodeIndex)
        await loadWorkspace()
      })
    } catch (e) {
      toast.error(e.message || '生成失败')
      await loadWorkspace()
    } finally {
      setGenerating(false)
    }
  }

  async function handleBatchScripts() {
    if (!nextBatch?.count) {
      toast.error('全部集数已生成完毕')
      return
    }
    await handleGenerate(5, {
      from_episode: nextBatch.from_episode,
      to_episode: nextBatch.to_episode,
    })
  }

  async function handleSaveContent(data) {
    if (!projectId || saving) return
    setSaving(true)
    try {
      await creation.saveAgentContent(projectId, activeIndex, data)
      // 【运营 F1】埋点：编辑节点
      try {
        const { trackNodeEdited } = await import('@/utils/behaviorTracker')
        trackNodeEdited({
          projectId,
          nodeIndex: activeIndex,
          nodeName: nodeMeta?.name || '',
        })
      } catch (_) {
        /* ignore */
      }
      toast.success('已保存')
      setEditMode(false)
      await loadWorkspace()
    } catch (e) {
      toast.error(e.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  async function handleAcknowledgeQualityAlert(alertCode) {
    if (!projectId || acknowledgingCode) return
    setAcknowledgingCode(alertCode)
    try {
      await creation.acknowledgeQualityAlert(projectId, activeIndex, alertCode)
      toast.success('已确认，可继续后续创作')
      await loadWorkspace()
    } catch (e) {
      toast.error(e.message || '确认失败')
    } finally {
      setAcknowledgingCode('')
    }
  }

  async function handleDownload(format) {
    if (downloadingFormat) {
      toast.message('下载处理中，请稍候')
      return
    }
    setDownloadingFormat(format)
    try {
      const blob = await creation.download(projectId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const ext = format === 'zip' ? 'zip' : format === 'html' ? 'html' : 'md'
      a.download = `${workspace?.title || '剧本'}.${ext}`
      a.click()
      URL.revokeObjectURL(url)
      // 【运营 F1】埋点：剧本导出
      try {
        const { trackScriptExported } = await import('@/utils/behaviorTracker')
        trackScriptExported({ projectId, fileFormat: ext })
      } catch (_) {
        /* ignore */
      }
    } catch (e) {
      toast.error(e.message || '下载失败')
    } finally {
      setDownloadingFormat('')
    }
  }

  async function handleShare() {
    if (sharing) {
      toast.message('分享链接生成中，请稍候')
      return
    }
    setSharing(true)
    try {
      const res = await creation.share(projectId, { allow_download: true })
      const url = res?.share_url || `${window.location.origin}/share/${res?.share_token || ''}`
      if (!navigator.clipboard?.writeText) {
        throw new Error('当前浏览器不支持自动复制，请手动复制分享链接')
      }
      await navigator.clipboard.writeText(url)
      // 【运营 F1】埋点：生成分享链接
      try {
        const { trackShareLinkGenerated } = await import('@/utils/behaviorTracker')
        trackShareLinkGenerated({ projectId, validDays: 7 })
      } catch (_) {
        /* ignore */
      }
      toast.success('分享链接已复制')
    } catch (e) {
      toast.error(e.message || '分享失败')
    } finally {
      setSharing(false)
    }
  }

  async function handleRefresh() {
    if (refreshing) return
    setRefreshing(true)
    try {
      await loadWorkspace()
    } finally {
      setRefreshing(false)
    }
  }

  const hasEditorContent =
    activeSkill?.editor &&
    (activeSkill.editor.structurePlan ||
      activeSkill.editor.characterBible ||
      activeSkill.editor.fields?.length ||
      activeSkill.editor.characters?.length ||
      activeSkill.editor.skeletonReady ||
      activeSkill.editor.episodes?.some((e) => e.filled) ||
      activeSkill.editor.episodes?.length)

  if (loading && !workspace) {
    return (
      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-12 text-center">
        <Loader2 className="w-8 h-8 text-gold-400 animate-spin mx-auto mb-4" />
        <p className="text-navy-300">加载 Agent 工作台…</p>
      </div>
    )
  }

  if (!loading && !workspace) {
    return (
      <ErrorState
        title="加载 Agent 工作台失败"
        description={error || '工作台数据暂时不可用，请稍后重试'}
        onRetry={loadWorkspace}
        className="rounded-2xl border border-white/5 bg-slate-900/60"
      />
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="overflow-hidden rounded-2xl border border-white/5 bg-slate-900/60"
    >
      <div className="px-6 py-5 border-b border-white/5 flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-navy-300">
              Agent 工作台
            </span>
            <span className="rounded-full border border-green-400/20 bg-green-500/10 px-2 py-0.5 text-green-300">
              已完成 {completedCount}/{totalSkills}
            </span>
            {generatedCount > 0 && generatedCount < completedCount ? (
              <span className="rounded-full border border-gold-400/20 bg-gold-400/10 px-2 py-0.5 text-gold-300">
                AI 已生成 {generatedCount} 步
              </span>
            ) : null}
            {hasOrchestrationHints ? (
              <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-2 py-0.5 text-cyan-300">
                {executionPlan?.has_parallel && executionPlan?.has_branches
                  ? '并行组 + 条件分支'
                  : executionPlan?.has_parallel
                    ? '含并行组'
                    : '含条件分支'}
              </span>
            ) : null}
          </div>
          <h2 className="text-xl font-bold text-white truncate">{workspace?.title || '创作项目'}</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {(workspace?.can_export_zip || workspace?.can_download) && (
            <>
              <button
                type="button"
                onClick={() => handleDownload('md')}
                disabled={Boolean(downloadingFormat)}
                className="px-3 py-2 rounded-xl text-sm border border-white/10 bg-white/[0.03] text-navy-100 hover:bg-white/[0.06] inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                {downloadingFormat === 'md' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                Markdown
              </button>
              <button
                type="button"
                onClick={() => handleDownload('html')}
                disabled={Boolean(downloadingFormat)}
                className="px-3 py-2 rounded-xl text-sm border border-white/10 bg-white/[0.03] text-navy-100 hover:bg-white/[0.06] inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                {downloadingFormat === 'html' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                HTML
              </button>
              {workspace?.can_export_zip && (
                <button
                  type="button"
                  onClick={() => handleDownload('zip')}
                  disabled={Boolean(downloadingFormat)}
                  className="px-3 py-2 rounded-xl text-sm border border-white/10 bg-white/[0.03] text-navy-100 hover:bg-white/[0.06] inline-flex items-center gap-1.5 disabled:opacity-50"
                >
                  {downloadingFormat === 'zip' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  ZIP 全量
                </button>
              )}
            </>
          )}
          {workspace?.can_share && (
            <button
              type="button"
              onClick={handleShare}
              disabled={sharing}
              className="px-3 py-2 rounded-xl text-sm border border-white/10 bg-white/[0.03] text-navy-100 hover:bg-white/[0.06] inline-flex items-center gap-1.5 disabled:opacity-50"
            >
              {sharing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Share2 className="w-4 h-4" />}
              {sharing ? '分享中' : '分享'}
            </button>
          )}
          <button
            type="button"
            onClick={onBack}
            className="px-3 py-2 rounded-xl text-sm border border-white/10 bg-white/[0.03] text-navy-200 hover:bg-white/[0.06] inline-flex items-center gap-1.5"
          >
            <ArrowLeft className="w-4 h-4" />
            返回
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[220px_minmax(0,1fr)] 2xl:grid-cols-[220px_minmax(0,1fr)_280px]">
        <aside className="border-b border-white/5 bg-slate-900/40 p-4 lg:border-b-0 lg:border-r">
          <WorkspaceModuleSidebar
            modules={modules}
            activeIndex={activeIndex}
            onSelect={setActiveIndex}
            agentTabName={agentTabName}
          />
        </aside>

        <main className="min-w-0 p-6 md:p-8 xl:p-10">
        {contextualError && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
            <p className="font-medium">{contextualError}</p>
            {contextualError.includes('角色设计') && activeSkill?.index === 4 && (
              <p className="text-xs mt-1 text-red-200/80">
                请先切换到「角色设计」完成 AI 生成，再回来生成大纲。
              </p>
            )}
          </div>
        )}

        {workspace?.adaptation?.meta?.creationEntry && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-200 text-sm space-y-2">
            <p>
              AdaptAgent · {workspace.adaptation.meta.creationEntry}
              {workspace.adaptation.meta.referenceWork
                ? ` · 参考「${workspace.adaptation.meta.referenceWork}」`
                : ''}
              {workspace.adaptation.meta.originalityMode ? ' · 结构指纹原创模式' : ''}
            </p>
            {workspace.adaptation.verify_summary?.hasReports && (
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-purple-300/80">原创复核：</span>
                {(workspace.adaptation.verify_summary.stages || []).map((stage) => (
                  <span
                    key={stage.key}
                    title={(stage.issues || []).join(' · ') || stage.label}
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${
                      stage.skipped
                        ? 'bg-white/[0.05] text-slate-400'
                        : stage.passed
                          ? 'bg-green-500/15 text-green-400'
                          : 'bg-red-500/15 text-red-300'
                    }`}
                  >
                    {stage.label}
                    <StepStatusMark skipped={stage.skipped} passed={stage.passed} className="w-3 h-3" />
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {workspace?.adaptation?.verify_summary?.hasReports &&
          workspace.adaptation.verify_summary.allPassed === false && (
            <div className="mb-6 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-sm">
              <p className="font-medium">参考创作原创复核存在未通过项</p>
              <p className="text-xs mt-1 text-red-200/80">
                请查看下方各 Agent 节点的质检提示，修订后重新生成对应阶段。
              </p>
            </div>
          )}

        <QualityAlertBanner
          alerts={activeSkill?.quality_alerts}
          onAcknowledge={handleAcknowledgeQualityAlert}
          acknowledgingCode={acknowledgingCode}
        />

        {isBusy && activeSkill?.status !== 'running' && (
          <div className="mb-4 px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-100 text-sm">
            <p className="font-medium">
              {runningSkill
                ? `「${agentTabName(runningSkill)}」正在生成，请稍候…`
                : runningBlocker?.node_name
                  ? `「${runningBlocker.node_name}」正在执行，请稍候…`
                  : '有技能正在执行，请稍候'}
            </p>
            <p className="text-xs mt-1 text-amber-200/80">
              页面将自动刷新；若长时间无响应，请点击下方「刷新」后重试。
            </p>
          </div>
        )}

        {!modules.length && (
          <div className="py-16 text-center">
            <p className="text-navy-300 mb-2">暂无可用 Agent 模块</p>
            <p className="text-xs text-navy-400">请稍后刷新，或联系管理员检查创作流水线配置。</p>
          </div>
        )}

        {activeSkill && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h3 className="text-2xl font-bold text-white">{agentTabName(activeSkill)}</h3>
                  {resolveSkillId(activeSkill) && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300">
                      {resolveSkillId(activeSkill)}
                    </span>
                  )}
                  <SkillStatusBadge skill={activeSkill} />
                  {isSkillPassed(activeSkill) && activeSkill.index === 1 && (
                    <GateLogBadge passed label="立项" />
                  )}
                  {activeSkill.index === 2 &&
                    activeSkill.editor?.structurePlan?.worldValidationLog &&
                    !activeSkill.editor.structurePlan.worldValidationLog.skipped && (
                      <GateLogBadge
                        passed={activeSkill.editor.structurePlan.worldValidationLog.passed}
                        label="世界观校验"
                      />
                    )}
                  {activeSkill.index === 3 &&
                    activeSkill.editor?.characterGateLog &&
                    !activeSkill.editor.characterGateLog.skipped && (
                      <GateLogBadge
                        passed={activeSkill.editor.characterGateLog.passed}
                        acknowledged={Boolean(activeSkill.editor.characterGateLog.userAcknowledgedAt)}
                        label="人设"
                      />
                    )}
                  {activeSkill.index === 4 &&
                    activeSkill.editor?.planValidationLog &&
                    !activeSkill.editor.planValidationLog.skipped &&
                    activeSkill.editor.planValidationLog.passed && (
                      <GateLogBadge
                        passed={activeSkill.editor.planValidationLog.passed}
                        label="大纲校验"
                      />
                    )}
                  {activeSkill.execution_run?.duration_ms != null &&
                    activeSkill.status !== 'running' && (
                      <ExecutionDurationLabel durationMs={activeSkill.execution_run.duration_ms} />
                    )}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {hasEditorContent && activeSkill.status !== 'running' && !editMode && (
                  <div className="inline-flex overflow-hidden rounded-xl border border-white/10">
                    <button
                      type="button"
                      onClick={() => setContentViewMode('structured')}
                      className={`px-3 py-2.5 text-sm inline-flex items-center gap-1.5 ${
                        contentViewMode === 'structured'
                          ? 'bg-gold-400/10 text-gold-300'
                          : 'border border-white/10 bg-white/[0.03] text-navy-300 hover:bg-white/[0.06]'
                      }`}
                    >
                      <LayoutList className="w-4 h-4" />
                      结构化
                    </button>
                    <button
                      type="button"
                      onClick={() => setContentViewMode('markdown')}
                      disabled={!activeSkill.readable_markdown}
                      className={`px-3 py-2.5 text-sm inline-flex items-center gap-1.5 border-l border-white/10 disabled:opacity-40 ${
                        contentViewMode === 'markdown'
                          ? 'bg-gold-400/10 text-gold-300'
                          : 'border border-white/10 bg-white/[0.03] text-navy-300 hover:bg-white/[0.06]'
                      }`}
                    >
                      <FileText className="w-4 h-4" />
                      可读预览
                    </button>
                  </div>
                )}

                {hasEditorContent && activeSkill.status !== 'running' && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditMode((v) => !v)
                      if (!editMode) setContentViewMode('structured')
                    }}
                    className={`px-4 py-2.5 rounded-xl text-sm border inline-flex items-center gap-2 ${
                      editMode
                        ? 'border-gold-400/40 bg-gold-400/10 text-gold-300'
                        : 'border border-white/10 bg-white/[0.03] text-navy-200 hover:bg-white/[0.06]'
                    }`}
                  >
                    {editMode ? <Eye className="w-4 h-4" /> : <Pencil className="w-4 h-4" />}
                    {editMode ? '预览' : '编辑'}
                  </button>
                )}

                {activeSkill.index === 5 && nextBatch?.count > 0 && (
                  <button
                    type="button"
                    disabled={generating || isBusy}
                    onClick={handleBatchScripts}
                    className="px-5 py-3 rounded-xl btn-gold font-semibold inline-flex items-center gap-2 disabled:opacity-50"
                  >
                    {generating || activeSkill.status === 'running' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Sparkles className="w-4 h-4" />
                    )}
                    批量生成 {nextBatch.count} 集
                    <span className="text-xs opacity-80">
                      {nextBatch.coin_cost} {currencyName}
                    </span>
                  </button>
                )}

                {activeSkill.can_generate && activeSkill.index !== 5 && activeSkill.index !== 4 && (
                  <button
                    type="button"
                    disabled={generating || isBusy}
                    onClick={() =>
                      handleGenerate(activeSkill.index, {
                        regenerate: activeSkill.content_kind === 'agent_generated',
                      })
                    }
                    className="px-5 py-3 rounded-xl btn-gold font-semibold inline-flex items-center gap-2 disabled:opacity-50"
                  >
                    {generating || activeSkill.status === 'running' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Sparkles className="w-4 h-4" />
                    )}
                    {activeSkill.content_kind === 'agent_generated'
                      ? '重新生成'
                      : 'AI 生成'}
                    <span className="text-xs opacity-80">
                      {activeSkill.coin_cost} {currencyName}
                    </span>
                  </button>
                )}

                {activeSkill.index === 5 && activeSkill.has_content && (
                  <button
                    type="button"
                    disabled={generating || isBusy}
                    onClick={() => handleGenerate(5, { regenerate: true })}
                    className="px-4 py-3 rounded-xl text-sm border border-white/10 text-navy-300 hover:bg-white/[0.05] disabled:opacity-50"
                  >
                    清空并重生成首批
                  </button>
                )}
              </div>
            </div>

            <div className="min-h-[280px]">
              {activeSkillGenerating ? (
                <div className="py-12 text-center">
                  <Loader2 className="w-10 h-10 text-gold-400 animate-spin mx-auto mb-4" />
                  <p className="text-navy-200">正在生成{agentTabName(activeSkill)}…</p>
                  <p className="text-xs text-navy-400 mt-2">可切换 Tab，完成后自动刷新</p>
                </div>
            ) : activeSkill.status === 'failed' && (activeSkill.error_message || contextualError) ? (
                <div className="py-12 text-center px-4">
                  <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-4" />
                  <p className="text-red-200 text-sm">
                    {activeSkill.error_message || contextualError}
                  </p>
                  {(activeSkill.error_message || contextualError || '').includes('立项策划') ||
                  (activeSkill.error_message || contextualError || '').includes('立项整理') ? (
                    <p className="text-xs text-navy-300 mt-2">
                      立项策划在创建项目时已确认，无需 AI 生成。请刷新工作台后重试；若仍失败请重启后端服务。
                    </p>
                  ) : (
                    <p className="text-xs text-navy-400 mt-2">请根据提示处理后重新点击 AI 生成</p>
                  )}
                </div>
              ) : hasEditorContent && contentViewMode === 'markdown' && !editMode ? (
                <ReadableMarkdownPanel
                  markdown={activeSkill.readable_markdown}
                  title={`${agentTabName(activeSkill)} · 可读预览`}
                />
              ) : hasEditorContent ? (
                <SkillEditorPanel
                  skill={activeSkill}
                  editor={activeSkill.editor}
                  editMode={editMode}
                  saving={saving}
                  onSave={handleSaveContent}
                  onOutlineGenerate={activeSkill.index === 4 ? handleOutlineGenerate : undefined}
                  outlineGenerating={generating}
                  skillBusy={isBusy || activeSkillGenerating}
                  coinCost={outlineCoinCost}
                  currencyName={currencyName}
                />
              ) : activeSkill.readable_markdown && !editMode ? (
                <ReadableMarkdownPanel
                  markdown={activeSkill.readable_markdown}
                  title={`${agentTabName(activeSkill)} · 可读预览`}
                />
              ) : activeSkill.preview_html ? (
                <div
                  className="text-sm text-navy-100 prose prose-invert max-w-none node-preview-content"
                  dangerouslySetInnerHTML={{ __html: sanitizeHtml(activeSkill.preview_html) }}
                />
              ) : (
                <div className="py-12 text-center">
                  <p className="text-navy-400 mb-2">暂无内容</p>
                  <p className="text-xs text-navy-400">{activeSkill.hint}</p>
                </div>
              )}
            </div>

            {activeSkill.index === 5 && (
              <PostScriptPanel
                projectId={projectId}
                postScript={workspace?.post_script}
                onRefresh={loadWorkspace}
              />
            )}

          </>
        )}

        {onRestart && (
          <div className="mt-8 flex justify-end border-t border-white/5 pt-6">
            <button
              type="button"
              onClick={onRestart}
              className="inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm text-navy-400 hover:text-navy-200"
            >
              新建项目
            </button>
          </div>
        )}
        </main>

        <aside className="border-t border-white/5 bg-slate-900/40 p-4 lg:col-span-2 2xl:col-span-1 2xl:border-l 2xl:border-t-0">
          <WorkspaceStatsPanel
            workspace={workspace}
            activeSkill={activeSkill}
            completedCount={completedCount}
            confirmedCount={confirmedCount}
            totalSkills={totalSkills}
            currencyName={currencyName}
            refreshing={refreshing}
            onRefresh={handleRefresh}
            agentTabName={agentTabName}
          />
        </aside>
      </div>
    </motion.div>
  )
}

export default LegacyProjectWorkspace
