import { useCallback, useEffect, useRef, useState } from 'react'
import { creation } from '@/services/api'
import { PIPELINE_NODE_ICONS } from '@/config/fusion'
import { filterCreationPipelineNodes } from '@/utils/pipelineNodes'
import { resolveSkillId } from '@/utils/skillTerm'

const DEFAULT_CATALOG = {
  themes: [],
  platforms: [],
  formatVariants: [],
  budgetLevels: [],
  creationEntries: [],
  episodeSettings: {},
  sections: {},
  creationEntryProfiles: {},
  mainChain: [],
  publishedPipelines: [],
  defaultPipelinePackId: '',
}

function mapPipelineNodes(mainChain) {
  return filterCreationPipelineNodes(mainChain || []).map((n, idx) => ({
    step: n.index || idx + 1,
    index: n.index || idx + 1,
    name: n.agent_name_zh || n.name,
    agentId: resolveSkillId(n),
    agentName: n.agent_name || n.agentName || '',
    agentNameZh: n.agent_name_zh || n.agent_name_zh || n.name,
    desc: n.description || '',
    description: n.description || '',
    outputKey: n.output_key || n.outputKey || '',
    subSkillCount: n.sub_skill_count ?? n.subSkillCount ?? 0,
    fusion_node_id: n.fusion_node_id,
    coinCost: n.coin_cost ?? n.coinCost,
    coin_cost: n.coin_cost ?? n.coinCost,
    requires_confirm: n.requires_confirm,
    orchestrationStageType: n.orchestration_stage_type,
    orchestrationStageLabel: n.orchestration_stage_label,
    orchestrationParallelPeers: n.orchestration_parallel_peers || [],
    orchestrationHasBranch: Boolean(n.orchestration_has_branch),
    icon: PIPELINE_NODE_ICONS[(n.index || idx + 1) - 1] || PIPELINE_NODE_ICONS[0],
  }))
}

export function useFusionCatalog() {
  const [catalog, setCatalog] = useState(DEFAULT_CATALOG)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedPipelineId, setSelectedPipelineId] = useState('')
  const [pipelineNodes, setPipelineNodes] = useState([])
  const [executionPlan, setExecutionPlan] = useState(null)
  const [pipelineLoading, setPipelineLoading] = useState(false)
  const previewSeqRef = useRef(0)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await creation.fusionCatalog()
        if (!cancelled && data) {
          const merged = { ...DEFAULT_CATALOG, ...data }
          setCatalog(merged)
          setSelectedPipelineId(
            merged.defaultPipelinePackId || merged.publishedPipelines?.[0]?.id || '',
          )
          setPipelineNodes(mapPipelineNodes(merged.mainChain))
          setExecutionPlan(merged.executionPlan || null)
          setError(null)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message || '融合技能目录加载失败')
          console.warn('融合 catalog 加载失败', e)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const loadPipelinePreview = useCallback(async (packId) => {
    if (!packId) return
    const seq = ++previewSeqRef.current
    setPipelineLoading(true)
    try {
      const data = await creation.fusionNodes(packId)
      if (seq !== previewSeqRef.current) return
      setPipelineNodes(mapPipelineNodes(data?.mainChain || []))
    } catch (e) {
      if (seq === previewSeqRef.current) {
        console.warn('流水线预览加载失败', e)
      }
    } finally {
      if (seq === previewSeqRef.current) {
        setPipelineLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    if (!selectedPipelineId || loading) return
    if (selectedPipelineId === catalog.defaultPipelinePackId) {
      setPipelineNodes(mapPipelineNodes(catalog.mainChain))
      setExecutionPlan(catalog.executionPlan || null)
      return
    }
    loadPipelinePreview(selectedPipelineId)
  }, [selectedPipelineId, loading, catalog, loadPipelinePreview])

  const agentCatalog = catalog.agentCatalog || null
  const publishedPipelines = catalog.publishedPipelines || []

  return {
    catalog,
    loading,
    error,
    pipelineNodes,
    agentCatalog,
    executionPlan,
    publishedPipelines,
    selectedPipelineId,
    setSelectedPipelineId,
    pipelineLoading,
  }
}
