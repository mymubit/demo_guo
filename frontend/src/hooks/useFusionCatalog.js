import { useEffect, useState } from 'react'
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
}

export function useFusionCatalog() {
  const [catalog, setCatalog] = useState(DEFAULT_CATALOG)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await creation.fusionCatalog()
        if (!cancelled && data) {
          setCatalog({ ...DEFAULT_CATALOG, ...data })
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

  const pipelineNodes = filterCreationPipelineNodes(catalog.mainChain || []).map((n, idx) => ({
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
    icon: PIPELINE_NODE_ICONS[(n.index || idx + 1) - 1] || PIPELINE_NODE_ICONS[0],
  }))

  const agentCatalog = catalog.agentCatalog || null

  return { catalog, loading, error, pipelineNodes, agentCatalog }
}
