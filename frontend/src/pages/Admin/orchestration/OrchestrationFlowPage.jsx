import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { RefreshCw, Rocket, RotateCcw, Undo2, Settings } from 'lucide-react'
import { Badge } from '@/components/ui'
import { AdminEmpty, AdminLoading, AdminPanel } from '@/components/admin/AdminUI'
import { ICON } from '@/constants/iconSizes'
import { cn } from '@/utils/cn'
import { resolveNodeRunState } from '@/utils/orchestrationNodeStates'
import OrchestrationNodeStateBadge from '@/components/admin/OrchestrationNodeStateBadge'
import { admin } from '@/services/api'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import MainChainStepInspector from '../mainChain/MainChainStepInspector'
import MainChainExecutionModesCard from '../mainChain/MainChainExecutionModesCard'
import OrchestrationPipelineRail from './OrchestrationPipelineRail'
import OrchestrationPostScriptPanel from './OrchestrationPostScriptPanel'
import OrchestrationFlowGraphPanel from './OrchestrationFlowGraphPanel'
import OrchestrationStepSearch from '@/components/admin/OrchestrationStepSearch'
import OrchestrationFlowGraphCanvas from '@/components/admin/OrchestrationFlowGraphCanvas'
import { useAdminSelection } from '@/components/admin/AdminMasterDetail'
import { useOrchestrationHubContext } from './OrchestrationHubContext'
import OrchestrationPipelineBar from './OrchestrationPipelineBar'
import GrayScaleControlPanel from './GrayScaleControlPanel'
import { resolveFlowSelectionNodeId } from '@/utils/orchestrationFlowSteps'

function pickSavePayload(step) {
  return {
    display_name: step.display_name,
    coin_cost: step.coin_cost,
    enabled: step.enabled,
    requires_confirm: step.requires_confirm,
    portal_visible: step.portal_visible,
    max_tokens: step.max_tokens,
    llm_provider_id: step.llm_provider_id,
    tier1_sections: step.tier1_sections,
    system_prompt: step.system_prompt,
    user_prompt_tpl: step.user_prompt_tpl,
    constraints: step.constraints,
    prompt_enabled: step.prompt_enabled,
    sub_skills: step.sub_skills,
  }
}

function sortStepsByChainOrder(steps) {
  return [...steps].sort((a, b) => (a.chain_order || 0) - (b.chain_order || 0))
}

function MainChainBlueprintGrid({
  steps = [],
  selectedNodeId,
  nodeStates = {},
  llmProviders = [],
  dirtyNodeId,
  onSelectStep,
}) {
  const providerLabelById = useMemo(
    () =>
      Object.fromEntries(
        llmProviders.map((p) => [p.id, p.display_name || p.model_name || p.provider_key || String(p.id)]),
      ),
    [llmProviders],
  )

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
      {steps.map((step, index) => {
        const active = step.node_id === selectedNodeId
        const runState = resolveNodeRunState(nodeStates, step.node_id)
        const isDirty = dirtyNodeId === step.node_id
        const skillId = step.sub_skills?.[0]?.skill_id || step.node_id
        const modelLabel = step.llm_provider_id
          ? providerLabelById[step.llm_provider_id] || `模型 #${step.llm_provider_id}`
          : '—'

        return (
          <button
            key={step.node_id}
            type="button"
            onClick={() => onSelectStep?.(step)}
            className={cn(
              'flex flex-col items-start gap-1.5 rounded-2xl border p-3 text-left transition-colors',
              active
                ? 'border-gold-400/40 bg-gold-400/10 text-white'
                : 'border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20',
              step.enabled === false && 'opacity-50',
            )}
          >
            <div className="flex w-full items-center justify-between gap-1">
              <span className="text-[10px] text-slate-500">STEP {step.node_index ?? index + 1}</span>
              {isDirty ? (
                <Badge tone="warning" size="sm">
                  未保存
                </Badge>
              ) : runState !== 'idle' ? (
                <OrchestrationNodeStateBadge state={runState} />
              ) : step.enabled === false ? (
                <Badge tone="default" size="sm">
                  停用
                </Badge>
              ) : null}
            </div>
            <div className="text-sm font-semibold text-white line-clamp-2">
              {step.agent_name_zh || step.display_name || step.node_id}
            </div>
            <div className="text-[10px] text-slate-400 font-mono truncate w-full">{skillId}</div>
            <div className="mt-1 text-[10px] text-slate-500 truncate w-full">{modelLabel}</div>
            <div className="mt-1 flex w-full items-center justify-end">
              <Settings className={cn(ICON.xs, 'text-slate-500')} />
            </div>
          </button>
        )
      })}
    </div>
  )
}

export default function OrchestrationFlowPage() {
  const hub = useOrchestrationHubContext()
  const {
    highlightStepId,
    highlightAgent,
    highlightStep,
    setSteps: setHubSteps,
  } = hub || {}

  const { showMessage, MessageBanner } = useAdminPanelMessage()
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [metaSaving, setMetaSaving] = useState(false)
  const [reordering, setReordering] = useState(false)
  const [blueprint, setBlueprint] = useState(null)
  const [llmProviders, setLlmProviders] = useState([])
  const [dirtyNodeId, setDirtyNodeId] = useState(null)
  const [draftByNode, setDraftByNode] = useState({})
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showCanvas, setShowCanvas] = useState(true)
  const [searchOpen, setSearchOpen] = useState(false)
  const [nodeStates, setNodeStates] = useState({})
  const [fusionPacks, setFusionPacks] = useState([])
  const [packsLoading, setPacksLoading] = useState(true)
  const [packBusy, setPackBusy] = useState(false)
  const [grayScaleMessage, setGrayScaleMessage] = useState(null)
  const reorderHistoryRef = useRef([])

  const steps = blueprint?.steps || []
  const agentsById = blueprint?.agents || {}
  const [selectedNodeId, setSelectedNodeId] = useAdminSelection(steps, (s) => s.node_id)

  const selectedStep = useMemo(() => {
    if (!selectedNodeId) return null
    return draftByNode[selectedNodeId] || steps.find((s) => s.node_id === selectedNodeId) || null
  }, [selectedNodeId, draftByNode, steps])

  const loadRecentRuns = useCallback(async () => {
    try {
      const res = await admin.orchestrationRecentRuns(50)
      setNodeStates(res?.node_states || {})
    } catch {
      setNodeStates({})
    }
  }, [])

  const loadPacks = useCallback(async () => {
    setPacksLoading(true)
    try {
      const res = await admin.listFusionPacks()
      setFusionPacks(res?.items || [])
    } catch {
      setFusionPacks([])
    } finally {
      setPacksLoading(false)
    }
  }, [])

  const load = useCallback(async () => {
    setLoadError(null)
    setLoading(true)
    let blueprintOk = false
    try {
      const bp = await admin.getOrchestrationFlowBlueprint()
      setBlueprint(bp)
      setHubSteps?.(bp?.steps || [])
      setDraftByNode({})
      setDirtyNodeId(null)
      reorderHistoryRef.current = []
      blueprintOk = true
    } catch (err) {
      setLoadError(err)
      showMessage(err.message || '加载流程蓝图失败', 'error')
    }
    try {
      const llmRes = await admin.getLlmConfig()
      setLlmProviders(Array.isArray(llmRes?.providers) ? llmRes.providers : [])
    } catch {
      if (blueprintOk) {
        showMessage('模型列表加载失败，步骤仍可编辑', 'error')
      }
    }
    await loadRecentRuns()
    await loadPacks()
    setLoading(false)
  }, [showMessage, setHubSteps, loadRecentRuns, loadPacks])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (highlightStepId) setSelectedNodeId(highlightStepId)
  }, [highlightStepId, setSelectedNodeId])

  function handlePatch(nextStep) {
    if (!nextStep?.node_id) return
    setDraftByNode((prev) => ({ ...prev, [nextStep.node_id]: nextStep }))
    setDirtyNodeId(nextStep.node_id)
  }

  async function handleSave(step) {
    if (!step?.id) return
    setSaving(true)
    try {
      const saved = await admin.patchOrchestrationFlowStep(step.id, pickSavePayload(step))
      showMessage('步骤已保存')
      setBlueprint((prev) => {
        if (!prev) return prev
        const nextSteps = (prev.steps || []).map((row) =>
          row.id === saved.id ? { ...row, ...saved } : row,
        )
        setHubSteps?.(nextSteps)
        return {
          ...prev,
          steps: nextSteps,
          workspace_steps: nextSteps.filter((s) => (s.node_index || 0) <= 5),
          pipeline_tail_steps: nextSteps.filter((s) => (s.node_index || 0) > 5),
          publish_state: {
            ...(prev.publish_state || {}),
            is_dirty: true,
          },
        }
      })
      setDraftByNode((prev) => {
        const next = { ...prev }
        delete next[step.node_id]
        return next
      })
      if (dirtyNodeId === step.node_id) setDirtyNodeId(null)
    } catch (err) {
      showMessage(err.message || '保存失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function saveFlowGraph(payload) {
    setMetaSaving(true)
    try {
      await admin.patchOrchestrationFlowRegistryMeta(payload)
      showMessage('流程图已保存')
      const bp = await admin.getOrchestrationFlowBlueprint()
      setBlueprint(bp)
      setHubSteps?.(bp?.steps || [])
    } catch (err) {
      showMessage(err.message || '保存失败', 'error')
    } finally {
      setMetaSaving(false)
    }
  }

  async function saveRegistryMeta(payload) {
    setMetaSaving(true)
    try {
      const meta = await admin.patchOrchestrationFlowRegistryMeta(payload)
      showMessage('后处理链已保存')
      setBlueprint((prev) =>
        prev
          ? {
              ...prev,
              polish_max_rounds: meta.polish_max_rounds ?? prev.polish_max_rounds,
              flow_graph: meta.flow_graph || prev.flow_graph,
              publish_state: { ...(prev.publish_state || {}), is_dirty: true },
            }
          : prev,
      )
    } catch (err) {
      showMessage(err.message || '保存失败', 'error')
    } finally {
      setMetaSaving(false)
    }
  }

  async function applyReorder(orderedUuids, { recordHistory = true } = {}) {
    if (recordHistory) {
      const prevOrder = sortStepsByChainOrder(steps).map((s) => s.id)
      reorderHistoryRef.current.push(prevOrder)
      if (reorderHistoryRef.current.length > 20) reorderHistoryRef.current.shift()
    }

    setReordering(true)
    try {
      const res = await admin.reorderOrchestrationFlowSteps(orderedUuids)
      const nextSteps = res?.steps || []
      setBlueprint((prev) =>
        prev
          ? {
              ...prev,
              steps: nextSteps,
              workspace_steps: nextSteps.filter((s) => (s.node_index || 0) <= 5),
              pipeline_tail_steps: nextSteps.filter((s) => (s.node_index || 0) > 5),
              publish_state: { ...(prev.publish_state || {}), is_dirty: true },
            }
          : prev,
      )
      setHubSteps?.(nextSteps)
      if (recordHistory) showMessage('顺序已更新')
    } catch (err) {
      if (recordHistory) {
        showMessage(err.message || '重排失败', 'error')
        reorderHistoryRef.current.pop()
      }
      await load()
    } finally {
      setReordering(false)
    }
  }

  async function handleReorderSteps(orderedUuids) {
    await applyReorder(orderedUuids, { recordHistory: true })
  }

  async function handleUndoReorder() {
    const prev = reorderHistoryRef.current.pop()
    if (!prev?.length) {
      showMessage('没有可撤销的排序操作', 'error')
      return
    }
    await applyReorder(prev, { recordHistory: false })
    showMessage('已撤销排序')
  }

  async function handlePublish() {
    setPublishing(true)
    try {
      const res = await admin.publishOrchestrationFlowBlueprint()
      showMessage(`已发布 v${res?.version || ''}`)
      await load()
    } catch (err) {
      showMessage(err.message || '发布失败', 'error')
    } finally {
      setPublishing(false)
    }
  }

  async function syncFromSsot() {
    setSyncing(true)
    try {
      await admin.syncPipelineSteps()
      showMessage('已从 SSOT 同步')
      await load()
    } catch (err) {
      showMessage(err.message || '同步失败', 'error')
    } finally {
      setSyncing(false)
    }
  }

  const meta = blueprint?.meta || {}
  const publishState = blueprint?.publish_state || {}
  const version = blueprint?.version || meta.db_version || '—'
  const sortedSteps = sortStepsByChainOrder(steps)
  const hasAdvanced =
    (blueprint?.execution_plan?.edges?.length || 0) > 0 ||
    (blueprint?.explicit_post_agents?.length || blueprint?.catalog?.explicitPostAgents?.length || 0) > 0 ||
    (blueprint?.flow_graph?.parallel_groups?.length || 0) > 0
  const activePackId = blueprint?.pipeline_pack?.id || fusionPacks.find((p) => p.is_active)?.id || ''

  async function handleSelectPack(packId) {
    if (!packId || packId === activePackId) return
    setPackBusy(true)
    try {
      await admin.activateFusionPack(packId)
      showMessage('已切换编辑流水线')
      await load()
    } catch (err) {
      showMessage(err.message || '切换失败', 'error')
    } finally {
      setPackBusy(false)
    }
  }

  async function handleDuplicatePack(sourceId, displayName) {
    setPackBusy(true)
    try {
      await admin.duplicateFusionPack(sourceId, displayName, { activate: true })
      showMessage('流水线已复制并切换')
      await load()
    } catch (err) {
      showMessage(err.message || '复制失败', 'error')
    } finally {
      setPackBusy(false)
    }
  }

  async function handleUpdatePackMeta(packId, data) {
    setPackBusy(true)
    try {
      await admin.updateFusionPack(packId, data)
      await loadPacks()
      showMessage('流水线信息已更新')
    } catch (err) {
      showMessage(err.message || '更新失败', 'error')
    } finally {
      setPackBusy(false)
    }
  }

  async function handleSetDefaultPack(packId) {
    setPackBusy(true)
    try {
      await admin.setDefaultFusionPack(packId)
      showMessage('已设为创作默认流水线')
      await loadPacks()
    } catch (err) {
      showMessage(err.message || '设置失败', 'error')
    } finally {
      setPackBusy(false)
    }
  }

  async function handleTogglePublish(packId, published) {
    setPackBusy(true)
    try {
      await admin.publishFusionPack(packId, { published, publish_blueprint: published })
      showMessage(published ? '已发布到创作入口' : '已从创作入口下架')
      await loadPacks()
    } catch (err) {
      showMessage(err.message || '操作失败', 'error')
    } finally {
      setPackBusy(false)
    }
  }

  // 获取当前活跃的 pack 用于灰度控制
  const activePack = fusionPacks.find((p) => p.is_active)

  async function handleGraySwitch({ gray_weight }) {
    if (!activePack) return
    setPackBusy(true)
    setGrayScaleMessage(null)
    try {
      await admin.workflowGraySwitch({
        pack_id: activePack.id,
        gray_weight,
      })
      setGrayScaleMessage({ type: 'success', text: `灰度权重已更新为 ${gray_weight}%` })
      await loadPacks()
    } catch (err) {
      setGrayScaleMessage({ type: 'error', text: err.message || '灰度切换失败' })
    } finally {
      setPackBusy(false)
    }
  }

  async function handleRollback() {
    if (!activePack) return
    setPackBusy(true)
    setGrayScaleMessage(null)
    try {
      await admin.workflowRollback({ pack_id: activePack.id })
      setGrayScaleMessage({ type: 'success', text: '已回滚到上一版本' })
      await loadPacks()
    } catch (err) {
      setGrayScaleMessage({ type: 'error', text: err.message || '回滚失败' })
    } finally {
      setPackBusy(false)
    }
  }

  function handleShowHistory() {
    // TODO: 显示历史版本弹窗
    showMessage('历史版本功能开发中', 'info')
  }

  function handlePreview() {
    // TODO: 灰度预览功能
    showMessage('灰度预览功能开发中', 'info')
  }

  if (loading && !blueprint) {
    return <AdminLoading label="加载流程蓝图…" />
  }

  if (loadError && !blueprint) {
    return (
      <div className="space-y-4">
        <MessageBanner />
        <AdminEmpty title="加载失败" description={loadError.message || '请稍后重试'} />
        <div className="flex justify-center">
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            重试
          </button>
        </div>
      </div>
    )
  }

  if (!blueprint) return null

  return (
    <div className="space-y-4">
      <MessageBanner />
      <AdminPanel
        title="Fusion 节点包"
        sub="按题材封装的流水线参数包 · 选择后编辑主链步骤"
      >
        <OrchestrationPipelineBar
          embedded
          packs={fusionPacks}
          activePackId={activePackId}
          loading={packsLoading}
          busy={packBusy || loading}
          onSelectPack={handleSelectPack}
          onDuplicate={handleDuplicatePack}
          onUpdateMeta={handleUpdatePackMeta}
          onSetDefault={handleSetDefaultPack}
          onTogglePublish={handleTogglePublish}
        />
      </AdminPanel>

      <GrayScaleControlPanel
        pack={activePack}
        loading={packsLoading}
        onGraySwitch={handleGraySwitch}
        onRollback={handleRollback}
        onShowHistory={handleShowHistory}
        onPreview={handlePreview}
        message={grayScaleMessage}
      />

      <OrchestrationStepSearch
        steps={sortedSteps}
        open={searchOpen}
        onOpenChange={setSearchOpen}
        selectedNodeId={selectedNodeId}
        onSelect={(step) => {
          setSelectedNodeId(step.node_id)
          highlightStep?.(step.node_id)
        }}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-navy-200">
            蓝图 <span className="font-mono text-gold-300">{version}</span>
          </span>
          {publishState.is_dirty ? (
            <span className="px-3 py-1.5 rounded-lg text-xs text-amber-300/90 border border-amber-500/25 bg-amber-500/10">
              有未发布变更
            </span>
          ) : publishState.has_published ? (
            <span className="px-3 py-1.5 rounded-lg text-xs text-green-300/90 border border-green-500/25 bg-green-500/10">
              已发布
            </span>
          ) : null}
          {meta.enabled_count != null ? (
            <span className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-400">
              {meta.enabled_count}/{meta.node_count} 启用 · 约 {meta.estimated_auto_cost ?? 0} 币/轮
            </span>
          ) : null}
          {dirtyNodeId ? (
            <span className="px-3 py-1.5 rounded-lg text-xs text-amber-300/90 border border-amber-500/25 bg-amber-500/10">
              步骤未保存
            </span>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setSearchOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-300 hover:bg-white/[0.06]"
          >
            搜索步骤
            <kbd className="hidden rounded border border-white/10 px-1 text-[10px] text-navy-500 sm:inline">/</kbd>
          </button>
          <button
            type="button"
            onClick={handleUndoReorder}
            disabled={reordering || reorderHistoryRef.current.length === 0}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-200 hover:bg-white/[0.06] disabled:opacity-40"
            title="撤销排序"
          >
            <Undo2 className="w-3.5 h-3.5" />
            撤销排序
          </button>
          <button
            type="button"
            onClick={() => setShowCanvas((v) => !v)}
            className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-300 hover:bg-white/[0.06]"
          >
            {showCanvas ? '隐藏画布' : '显示画布'}
          </button>
          {hasAdvanced ? (
            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-300 hover:bg-white/[0.06]"
            >
              {showAdvanced ? '收起高级' : '并行 / 后处理'}
            </button>
          ) : null}
          <button
            type="button"
            onClick={handlePublish}
            disabled={publishing || (!publishState.is_dirty && publishState.has_published)}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-navy-950 font-medium bg-gradient-to-r from-gold-400 to-gold-600 disabled:opacity-50"
          >
            <Rocket className={`w-3.5 h-3.5 ${publishing ? 'animate-pulse' : ''}`} />
            {publishing ? '发布中…' : '发布到 C 端'}
          </button>
          <button
            type="button"
            onClick={syncFromSsot}
            disabled={syncing || loading}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-200 hover:bg-white/[0.06] disabled:opacity-60"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing || loading ? 'animate-spin' : ''}`} />
            同步 SSOT
          </button>
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-navy-200 hover:bg-white/[0.06] disabled:opacity-60"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            刷新状态
          </button>
        </div>
      </div>

      <AdminPanel title="主链蓝图" sub="点击节点可编辑技能 / 模型 / 提示词">
        <MainChainBlueprintGrid
          steps={sortedSteps}
          selectedNodeId={selectedNodeId}
          nodeStates={nodeStates}
          llmProviders={llmProviders}
          dirtyNodeId={dirtyNodeId}
          onSelectStep={(step) => {
            setSelectedNodeId(step.node_id)
            highlightStep?.(step.node_id)
          }}
        />
      </AdminPanel>

      {showCanvas ? (
        <OrchestrationFlowGraphCanvas
          steps={sortedSteps}
          flowGraph={blueprint.flow_graph}
          executionPlan={blueprint.execution_plan}
          nodeStates={nodeStates}
          highlightNodeId={highlightStepId}
          selectedNodeId={selectedNodeId}
          onSelectNode={(nodeId) => {
            const targetId = resolveFlowSelectionNodeId(nodeId, sortedSteps)
            setSelectedNodeId(targetId)
            highlightStep?.(targetId)
          }}
          height={320}
        />
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(260px,300px)_minmax(0,1fr)] gap-4 items-start">
        <OrchestrationPipelineRail
          steps={sortedSteps}
          explicitPostAgents={blueprint.explicit_post_agents || blueprint?.catalog?.explicitPostAgents || []}
          agentsById={agentsById}
          executionPlan={blueprint?.execution_plan}
          selectedNodeId={selectedNodeId}
          highlightNodeId={highlightStepId}
          nodeStates={nodeStates}
          onSelectStep={(step) => {
            setSelectedNodeId(step.node_id)
            highlightStep?.(step.node_id)
          }}
          onReorderSteps={handleReorderSteps}
          reordering={reordering}
        />

        <div className="sf-console-panel min-h-[520px] lg:max-h-[calc(100vh-240px)] overflow-y-auto p-4 md:p-5">
          <MainChainStepInspector
            step={selectedStep}
            tier1Catalog={blueprint?.tier1_section_catalog_detail || []}
            llmProviders={llmProviders}
            onPatch={handlePatch}
            onSave={handleSave}
            saving={saving}
            dirty={dirtyNodeId === selectedStep?.node_id}
          />
        </div>
      </div>

      {showAdvanced ? (
        <div className="space-y-4 pt-2 border-t border-white/10">
          <OrchestrationFlowGraphPanel
            blueprint={blueprint}
            onSave={saveFlowGraph}
            saving={metaSaving}
            steps={sortedSteps}
            nodeStates={nodeStates}
            selectedNodeId={selectedNodeId}
            onSelectNode={(nodeId) => setSelectedNodeId(nodeId)}
          />
          <OrchestrationPostScriptPanel
            blueprint={blueprint}
            onSave={saveRegistryMeta}
            saving={metaSaving}
          />
          <MainChainExecutionModesCard blueprint={blueprint} />
        </div>
      ) : null}
    </div>
  )
}
