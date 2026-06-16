import { useCallback, useEffect, useMemo } from 'react'
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  MarkerType,
  Position,
  useEdgesState,
  useNodesState,
} from '@xyflow/react'
import dagre from '@dagrejs/dagre'
import '@xyflow/react/dist/style.css'
import { cn } from '@/utils/cn'
import OrchestrationNodeStateBadge from '@/components/admin/OrchestrationNodeStateBadge'
import { resolveNodeRunState } from '@/utils/orchestrationNodeStates'
import { expandFlowSteps } from '@/utils/orchestrationFlowSteps'

const NODE_WIDTH = 200
const NODE_HEIGHT = 72

function stepLabel(step) {
  return step.agent_name_zh || step.display_name || step.node_id
}

function layoutGraph(nodes, edges) {
  const graph = new dagre.graphlib.Graph()
  graph.setDefaultEdgeLabel(() => ({}))
  graph.setGraph({ rankdir: 'LR', nodesep: 48, ranksep: 64, marginx: 24, marginy: 24 })
  nodes.forEach((node) => graph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT }))
  edges.forEach((edge) => graph.setEdge(edge.source, edge.target))
  dagre.layout(graph)
  return nodes.map((node) => {
    const pos = graph.node(node.id)
    return {
      ...node,
      position: { x: (pos?.x || 0) - NODE_WIDTH / 2, y: (pos?.y || 0) - NODE_HEIGHT / 2 },
      targetPosition: Position.Left,
      sourcePosition: Position.Right,
    }
  })
}

function FlowStepNode({ data, selected }) {
  return (
    <div
      className={cn(
        'rounded-xl border px-3 py-2 w-[200px] bg-slate-900/90 backdrop-blur-sm transition-shadow',
        selected ? 'border-gold-500/50 shadow-[0_0_16px_rgba(244,183,25,0.15)]' : 'border-white/10',
        data.isPlaceholder && 'border-dashed opacity-75',
        data.isSubFlow && !data.isPlaceholder && 'border-purple-500/35',
        data.runState === 'running' && 'border-cyan-400/45',
        data.runState === 'failed' && 'border-red-500/40',
        data.runState === 'completed' && 'border-green-500/35',
        data.highlighted && 'ring-2 ring-gold-400/40',
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-[10px] text-navy-400">#{data.order}</span>
        <OrchestrationNodeStateBadge state={data.runState} compact />
      </div>
      <div className="text-xs font-medium text-white truncate">{data.label}</div>
      <div className="text-[10px] font-mono text-navy-300 truncate mt-0.5">{data.nodeId}</div>
      {data.isPlaceholder ? (
        <span className="text-[10px] text-amber-400/90 mt-1 inline-block">待同步 SSOT</span>
      ) : null}
      {data.parallel ? (
        <span className="text-[10px] text-cyan-400/90 mt-1 inline-block">并行</span>
      ) : null}
    </div>
  )
}

const nodeTypes = { flowStep: FlowStepNode }

function buildGraphModel({ steps, flowGraph, executionPlan, nodeStates, highlightNodeId, selectedNodeId }) {
  const expanded = expandFlowSteps(steps)
  const ordered = [...expanded].sort(
    (a, b) => (a.flow_order ?? a.chain_order ?? 0) - (b.flow_order ?? b.chain_order ?? 0),
  )
  const parallelByNode = {}
  for (const stage of executionPlan?.stages || []) {
    if (stage.type !== 'parallel') continue
    for (const idx of stage.indices || []) {
      const step = ordered.find((s) => s.node_index === idx && !s.is_sub_flow)
      if (step) parallelByNode[step.node_id] = stage
    }
  }

  const baseNodes = ordered.map((step) => ({
    id: step.node_id,
    type: 'flowStep',
    data: {
      label: stepLabel(step),
      nodeId: step.is_sub_flow ? step.sub_skill_id || step.sub_flow_key : step.node_id,
      order: step.flow_order ?? step.chain_order,
      parallel: Boolean(!step.is_sub_flow && parallelByNode[step.node_id]),
      runState: resolveNodeRunState(
        nodeStates,
        step.is_sub_flow ? step.parent_node_id || step.node_id : step.node_id,
      ),
      highlighted: step.node_id === highlightNodeId,
      selected: step.node_id === selectedNodeId,
      isSubFlow: Boolean(step.is_sub_flow),
      isPlaceholder: Boolean(step.flow_placeholder),
      subSkillId: step.sub_skill_id || '',
    },
    draggable: false,
    selectable: true,
  }))

  const edgeSet = new Map()
  const pushEdge = (from, to, meta = {}) => {
    const source = String(from || '').trim()
    const target = String(to || '').trim()
    if (!source || !target || source === target) return
    const key = `${source}->${target}:${meta.type || 'seq'}`
    if (edgeSet.has(key)) return
    edgeSet.set(key, {
      id: key,
      source,
      target,
      type: 'smoothstep',
      animated: meta.type === 'branch',
      label: meta.label || undefined,
      labelStyle: { fill: '#94a3b8', fontSize: 10 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#64748b' },
      style: {
        stroke: meta.type === 'branch' ? '#f4b719' : '#64748b',
        strokeWidth: meta.type === 'branch' ? 2 : 1.5,
      },
    })
  }

  const customEdges = flowGraph?.edges || []
  const nodeIdSet = new Set(ordered.map((step) => step.node_id))
  if (customEdges.length) {
    customEdges.forEach((edge) => {
      const from = String(edge.from || edge.source || '').trim()
      const to = String(edge.to || edge.target || '').trim()
      if (!nodeIdSet.has(from) || !nodeIdSet.has(to)) return
      pushEdge(from, to, { type: edge.type, label: edge.label || edge.type })
    })
  }
  if (edgeSet.size === 0) {
    for (let i = 0; i < ordered.length - 1; i += 1) {
      pushEdge(ordered[i].node_id, ordered[i + 1].node_id)
    }
  }

  const nodes = layoutGraph(baseNodes, [...edgeSet.values()])
  return { nodes, edges: [...edgeSet.values()] }
}

/** React Flow + Dagre 自动布局的流程图画布 */
export default function OrchestrationFlowGraphCanvas({
  steps = [],
  flowGraph = null,
  executionPlan = null,
  nodeStates = null,
  highlightNodeId = '',
  selectedNodeId = '',
  onSelectNode,
  className,
  height = 360,
}) {
  const model = useMemo(
    () =>
      buildGraphModel({
        steps,
        flowGraph,
        executionPlan,
        nodeStates,
        highlightNodeId,
        selectedNodeId,
      }),
    [steps, flowGraph, executionPlan, nodeStates, highlightNodeId, selectedNodeId],
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(model.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(model.edges)

  useEffect(() => {
    setNodes(model.nodes)
    setEdges(model.edges)
  }, [model, setNodes, setEdges])

  const onNodeClick = useCallback(
    (_, node) => onSelectNode?.(node.id),
    [onSelectNode],
  )

  return (
    <div className={cn('rounded-xl border border-white/5 bg-slate-900/40 overflow-hidden', className)} style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        panOnScroll
        zoomOnScroll
        minZoom={0.35}
        maxZoom={1.4}
      >
        <Background gap={18} size={1} color="#1e3a5f" />
        <MiniMap
          nodeColor="#334155"
          maskColor="rgba(3,13,36,0.75)"
          className="!bg-slate-900/80 !border-white/10"
        />
        <Controls className="!bg-slate-900/90 !border-white/10 !shadow-none [&>button]:!bg-slate-800 [&>button]:!border-white/10 [&>button]:!text-navy-200" />
      </ReactFlow>
    </div>
  )
}
