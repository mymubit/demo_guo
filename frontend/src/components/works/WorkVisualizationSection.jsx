import { useEffect, useMemo, useState } from 'react'
import { ChevronDown, ChevronUp, GitBranch, Network, Layers } from 'lucide-react'
import { toast } from 'sonner'
import { creation } from '@/services/api'
import { EChart, buildStructureSankeyOption } from '@/components/charts'
import CharacterRelationshipGraph from '@/components/creation/workspace/CharacterRelationshipGraph'
import PlotFlowChart from '@/components/creation/workspace/PlotFlowChart'
import RhythmCurveChart from '@/components/creation/workspace/RhythmCurveChart'
import EmptyState from '@/components/ui/EmptyState'
import { ErrorState } from '@/components/ui/AsyncState'
import { ICON } from '@/constants/iconSizes'

const TABS = [
  { id: 'plot', label: '剧情脉络', icon: GitBranch },
  { id: 'characters', label: '人物关系', icon: Network },
  { id: 'structure', label: '结构节奏', icon: Layers },
]

function pickDefaultTab(payload) {
  if (payload?.hasPlot) return 'plot'
  if (payload?.hasCharacters) return 'characters'
  if (payload?.hasStructure) return 'structure'
  return 'plot'
}

function extractChartPayload(workspace) {
  const skills = workspace?.skills || []
  const byIndex = Object.fromEntries(skills.map((s) => [s.index, s]))

  const charEditor = byIndex[3]?.editor
  const structEditor = byIndex[2]?.editor
  const outlineEditor = byIndex[4]?.editor

  const characters = charEditor?.characterBible?.characters || charEditor?.characters || []
  const relationships = charEditor?.characterBible?.relationships || []
  const structurePlan = structEditor?.structurePlan || {}
  const stageBlocks = outlineEditor?.stageBlocks || outlineEditor?.navigation || []
  const episodes = (outlineEditor?.episodes || []).filter((e) => e?.filled)

  const hasCharacters = characters.length > 0
  const hasPlot = stageBlocks.length > 0 || episodes.length > 0
  const hasStructure =
    (structurePlan.sixStagePlan || []).length > 0 || (structurePlan.rhythmCurve || []).length > 0

  return {
    characters,
    relationships,
    structurePlan,
    stageBlocks,
    episodes,
    hasCharacters,
    hasPlot,
    hasStructure,
    hasAny: hasCharacters || hasPlot || hasStructure,
  }
}

export default function WorkVisualizationSection({ projectId }) {
  const [loading, setLoading] = useState(true)
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('plot')
  const [expanded, setExpanded] = useState(true)

  useEffect(() => {
    if (!projectId) {
      setPayload(null)
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError('')
    creation
      .workspace(projectId)
      .then((ws) => {
        if (cancelled) return
        const data = extractChartPayload(ws)
        setPayload(data)
        setActiveTab(pickDefaultTab(data))
      })
      .catch((err) => {
        if (!cancelled) {
          const message = err.message || '可视化加载失败'
          setPayload(null)
          setError(message)
          toast.error(message)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  const availableTabs = useMemo(() => {
    if (!payload) return []
    return TABS.filter((t) => {
      if (t.id === 'characters') return payload.hasCharacters
      if (t.id === 'plot') return payload.hasPlot
      if (t.id === 'structure') return payload.hasStructure
      return false
    })
  }, [payload])

  const structureSankey = useMemo(() => {
    const raw = payload?.structurePlan
      ? buildStructureSankeyOption({ structurePlan: payload.structurePlan })
      : null
    if (!raw) return { option: null, height: 320 }
    const { _chartHeight, ...option } = raw
    return { option, height: _chartHeight || 320 }
  }, [payload?.structurePlan])

  useEffect(() => {
    if (!availableTabs.length) return
    if (!availableTabs.some((t) => t.id === activeTab)) {
      setActiveTab(availableTabs[0].id)
    }
  }, [availableTabs, activeTab])

  if (loading) {
    return (
      <div className="mb-8 animate-pulse rounded-2xl border border-white/5 bg-slate-900/60 p-8">
        <div className="h-6 w-40 bg-slate-700/50 rounded mb-4" />
        <div className="h-64 rounded-xl bg-white/10" />
      </div>
    )
  }

  if (error) {
    return (
      <ErrorState
        title="创作可视化加载失败"
        description={error}
        className="mb-8"
      />
    )
  }

  if (!payload?.hasAny) {
    return (
      <EmptyState
        compact
        title="暂无创作可视化数据"
        description="当前作品还没有可展示的剧情脉络、人物关系或结构节奏数据。"
        className="mb-8"
      />
    )
  }

  return (
    <div className="mb-8 rounded-2xl border border-white/5 bg-slate-900/60 p-8">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center gap-2 text-2xl font-bold text-white hover:text-gold-300 transition-colors"
        >
          <GitBranch className={`${ICON.lg} text-gold-400`} />
          创作可视化
          {expanded ? <ChevronUp className={ICON.md} /> : <ChevronDown className={ICON.md} />}
        </button>
        {expanded ? (
          <div className="flex flex-wrap gap-2">
            {availableTabs.map((tab) => {
              const Icon = tab.icon
              const active = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium flex items-center gap-2 transition-colors border ${
                    active
                      ? 'bg-gold-400/15 text-gold-400 border-gold-400/30'
                      : 'border border-white/10 bg-white/[0.03] text-navy-300 hover:text-white'
                  }`}
                >
                  <Icon className={ICON.md} />
                  {tab.label}
                </button>
              )
            })}
          </div>
        ) : null}
      </div>

      {expanded ? (
        <>
          {activeTab === 'characters' && payload.hasCharacters ? (
            <CharacterRelationshipGraph
              characters={payload.characters}
              relationships={payload.relationships}
            />
          ) : null}

          {activeTab === 'plot' && payload.hasPlot ? (
            <PlotFlowChart
              stageBlocks={payload.stageBlocks}
              episodes={payload.episodes}
              height={400}
            />
          ) : null}

          {activeTab === 'structure' && payload.hasStructure ? (
            <div className="space-y-4">
              {structureSankey.option ? (
                <div className="rounded-xl border border-white/5 bg-slate-900/40 p-3">
                  <div className="text-xs text-navy-400 mb-2">结构流向 · 阶段 → 节奏段 → 反转点</div>
                  <EChart option={structureSankey.option} height={structureSankey.height} />
                </div>
              ) : null}
              {(payload.structurePlan.rhythmCurve || []).length > 0 ? (
                <RhythmCurveChart curve={payload.structurePlan.rhythmCurve} />
              ) : null}
              {!structureSankey.option && !(payload.structurePlan.rhythmCurve || []).length ? (
                <p className="text-sm text-navy-400 text-center py-8">结构数据不足以生成图表</p>
              ) : null}
            </div>
          ) : null}
        </>
      ) : (
        <p className="text-sm text-navy-400">点击标题展开人物关系、剧情脉络与结构节奏图表</p>
      )}
    </div>
  )
}
