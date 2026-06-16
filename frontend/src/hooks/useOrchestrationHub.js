import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { agentIdToNodeId } from '@/utils/orchestrationNodeStates'

/**
 * 调度中心共享 URL 状态：编排 ↔ 监察联动、回放、高亮。
 * ?tab=flow|monitor &step=node_id &agent=agent_id &run=uuid &replay=1
 */
export function useOrchestrationHub(steps = []) {
  const [searchParams, setSearchParams] = useSearchParams()

  const tab = searchParams.get('tab') || 'flow'
  const highlightStepId = searchParams.get('step') || ''
  const highlightAgentId = searchParams.get('agent') || ''
  const replayRunId = searchParams.get('run') || ''
  const isReplayOpen = searchParams.get('replay') === '1' || Boolean(replayRunId)

  const resolvedHighlightStepId = useMemo(() => {
    if (highlightStepId) return highlightStepId
    if (highlightAgentId) return agentIdToNodeId(steps, highlightAgentId)
    return ''
  }, [highlightStepId, highlightAgentId, steps])

  const patchParams = useCallback(
    (patch, { replace = false } = {}) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          Object.entries(patch).forEach(([key, value]) => {
            if (value == null || value === '') next.delete(key)
            else next.set(key, String(value))
          })
          return next
        },
        { replace },
      )
    },
    [setSearchParams],
  )

  const setTab = useCallback(
    (nextTab) => patchParams({ tab: nextTab || 'flow' }),
    [patchParams],
  )

  const highlightAgent = useCallback(
    (agentId) => {
      const nodeId = agentIdToNodeId(steps, agentId)
      patchParams({
        tab: 'flow',
        agent: agentId || undefined,
        step: nodeId || undefined,
      })
    },
    [patchParams, steps],
  )

  const highlightStep = useCallback(
    (nodeId) => patchParams({ tab: 'flow', step: nodeId || undefined, agent: undefined }),
    [patchParams],
  )

  const openReplay = useCallback(
    (runId) => patchParams({ tab: 'monitor', run: runId || undefined, replay: runId ? '1' : undefined }),
    [patchParams],
  )

  const closeReplay = useCallback(
    () => patchParams({ run: undefined, replay: undefined }),
    [patchParams],
  )

  return {
    tab,
    highlightStepId: resolvedHighlightStepId,
    highlightAgentId,
    replayRunId,
    isReplayOpen,
    setTab,
    highlightAgent,
    highlightStep,
    openReplay,
    closeReplay,
    patchParams,
  }
}
