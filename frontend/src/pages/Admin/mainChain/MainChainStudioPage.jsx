import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { RefreshCw, Upload } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import AdminMasterDetail, {
  AdminMasterDetailListButton,
  useAdminSelection,
} from '@/components/admin/AdminMasterDetail'
import { formatSkillRootDisplay } from '@/utils/adminAgentLabels'
import { admin } from '@/services/api'
import { useAdminPanelMessage } from '@/hooks/useAdminPanelMessage'
import MainChainBlueprintStrip from './MainChainBlueprintStrip'
import MainChainStepInspector from './MainChainStepInspector'
import MainChainPostScriptPanel from './MainChainPostScriptPanel'
import MainChainExecutionModesCard from './MainChainExecutionModesCard'

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

export default function MainChainStudioPage() {
  const { showMessage, MessageBanner } = useAdminPanelMessage()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [metaSaving, setMetaSaving] = useState(false)
  const [blueprint, setBlueprint] = useState(null)
  const [llmProviders, setLlmProviders] = useState([])
  const [dirtyNodeId, setDirtyNodeId] = useState(null)
  const [draftByNode, setDraftByNode] = useState({})

  const steps = blueprint?.steps || []
  const [selectedNodeId, setSelectedNodeId] = useAdminSelection(steps, (s) => s.node_id)

  const selectedStep = useMemo(() => {
    if (!selectedNodeId) return null
    return draftByNode[selectedNodeId] || steps.find((s) => s.node_id === selectedNodeId) || null
  }, [selectedNodeId, draftByNode, steps])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [bp, llmRes] = await Promise.all([
        admin.getMainChainBlueprint(),
        admin.getLlmConfig(),
      ])
      setBlueprint(bp)
      setLlmProviders(Array.isArray(llmRes?.providers) ? llmRes.providers : [])
      setDraftByNode({})
      setDirtyNodeId(null)
    } catch (err) {
      showMessage(err.message || '加载主链蓝图失败', 'error')
    } finally {
      setLoading(false)
    }
  }, [showMessage])

  useEffect(() => {
    load()
  }, [load])

  function handlePatch(nextStep) {
    if (!nextStep?.node_id) return
    setDraftByNode((prev) => ({ ...prev, [nextStep.node_id]: nextStep }))
    setDirtyNodeId(nextStep.node_id)
  }

  async function handleSave(step) {
    if (!step?.id) return
    setSaving(true)
    try {
      const saved = await admin.patchMainChainStep(step.id, pickSavePayload(step))
      showMessage('步骤已保存')
      setBlueprint((prev) => {
        if (!prev) return prev
        const nextSteps = (prev.steps || []).map((row) =>
          row.id === saved.id ? { ...row, ...saved } : row
        )
        return {
          ...prev,
          steps: nextSteps,
          workspace_steps: nextSteps.filter((s) => (s.node_index || 0) <= 5),
          pipeline_tail_steps: nextSteps.filter((s) => (s.node_index || 0) > 5),
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

  async function saveRegistryMeta(payload) {
    setMetaSaving(true)
    try {
      const meta = await admin.patchMainChainRegistryMeta(payload)
      showMessage('后处理链已保存')
      setBlueprint((prev) =>
        prev
          ? {
              ...prev,
              post_script_chain: meta.post_script_chain || prev.post_script_chain,
              post_script_append_agents: meta.post_script_append_agents || prev.post_script_append_agents,
              polish_max_rounds: meta.polish_max_rounds ?? prev.polish_max_rounds,
            }
          : prev
      )
    } catch (err) {
      showMessage(err.message || '保存失败', 'error')
    } finally {
      setMetaSaving(false)
    }
  }

  async function syncFromSsot() {
    setSyncing(true)
    try {
      await admin.syncPipelineSteps()
      showMessage('已从 SSOT 同步主链')
      await load()
    } catch (err) {
      showMessage(err.message || '同步失败', 'error')
    } finally {
      setSyncing(false)
    }
  }

  const meta = blueprint?.meta || {}
  const version = blueprint?.version || meta.db_version || '—'

  return (
    <AdminShell
      title="主链工作室"
      description="主链蓝图：步骤编排、Agent 绑定、模型路由与运营配置统一在此维护"
    >
      <MessageBanner />

      <div className="glass-card rounded-2xl p-4 border border-gold-500/15 bg-gold-500/5 flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-navy-200 space-y-1">
          <div>
            <span className="text-white font-medium">蓝图版本</span>
            <span className="ml-2 font-mono text-gold-300">{version}</span>
            {meta.enabled_count != null ? (
              <span className="ml-3 text-navy-500">
                {meta.enabled_count}/{meta.node_count} 步启用 · 约 {meta.estimated_auto_cost ?? 0} 币/轮
              </span>
            ) : null}
          </div>
          {meta.skill_root ? (
            <p className="text-[11px] font-mono text-navy-500" title={meta.skill_root}>
              SSOT：{formatSkillRootDisplay(meta.skill_root_display || meta.skill_root)}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={syncFromSsot}
            disabled={syncing}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-navy-100 border border-navy-600/40 hover:bg-navy-800/60 disabled:opacity-60"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? '同步中…' : '从 SSOT 同步'}
          </button>
          <Link
            to="/admin/agent?tab=rules"
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-navy-300 border border-navy-700/40 hover:bg-navy-800/40"
          >
            写作规则 →
          </Link>
          <Link
            to="/admin/agent?tab=registry"
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-navy-300 border border-navy-700/40 hover:bg-navy-800/40"
          >
            Agent 注册表 →
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-navy-400">加载主链蓝图…</div>
      ) : (
        <>
          <MainChainExecutionModesCard blueprint={blueprint} />

          <MainChainBlueprintStrip
            blueprint={blueprint}
            selectedNodeId={selectedNodeId}
            onSelectStep={(step) => setSelectedNodeId(step.node_id)}
          />

          <MainChainPostScriptPanel
            blueprint={blueprint}
            onSave={saveRegistryMeta}
            saving={metaSaving}
          />

          <AdminMasterDetail
            listTitle="主链步骤"
            listHint="选中后在右侧编辑"
            detailTitle="步骤 Inspector"
            items={steps}
            selectedId={selectedNodeId}
            onSelect={setSelectedNodeId}
            getId={(row) => row.node_id}
            sidebarWidthClass="lg:grid-cols-[280px_minmax(0,1fr)]"
            renderListItem={(row, { active, index, onSelect }) => (
              <AdminMasterDetailListButton
                key={row.node_id}
                active={active}
                onClick={onSelect}
                index={row.node_index ?? index + 1}
                title={row.agent_name_zh || row.display_name || row.node_id}
                subtitle={row.agent_id || row.node_id}
                meta={row.enabled !== false ? `${row.coin_cost ?? 0} 币` : '停用'}
                dirty={dirtyNodeId === row.node_id}
              />
            )}
            renderDetail={() => (
              <MainChainStepInspector
                step={selectedStep}
                tier1Catalog={blueprint?.tier1_section_catalog_detail || []}
                llmProviders={llmProviders}
                onPatch={handlePatch}
                onSave={handleSave}
                saving={saving}
                dirty={dirtyNodeId === selectedStep?.node_id}
              />
            )}
          />
        </>
      )}

    </AdminShell>
  )
}
