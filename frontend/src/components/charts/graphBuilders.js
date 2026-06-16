import { chartColors, chartPalette } from './theme'
import { resolveRelationTypeLabel } from '@/utils/displayLabels'

const ROLE_CATEGORY = {
  protagonist: '主角',
  antagonist: '反派',
  supporting: '配角',
}

function roleCategoryIndex(roleType) {
  const r = String(roleType || '')
  if (r.startsWith('protagonist')) return 0
  if (r.startsWith('antagonist')) return 1
  return 2
}

function blockEpisodeRange(block) {
  if (!block || typeof block !== 'object') return null
  const from = block.from_episode ?? block.fromEpisode
  const to = block.to_episode ?? block.toEpisode
  if (from == null || to == null) return null
  return { from: Number(from), to: Number(to) }
}

function findStageKeyForEpisode(stageBlocks, episodeNumber) {
  const num = Number(episodeNumber)
  if (!Number.isFinite(num)) return null
  for (const block of stageBlocks) {
    const range = blockEpisodeRange(block)
    if (range && num >= range.from && num <= range.to) {
      return block.key ?? block.stageIndex ?? block.label
    }
  }
  return null
}

const PLACEHOLDER_ENDPOINTS = new Set(['', 'a-unknown', 'b-unknown', 'unknown'])

function isPlaceholderEndpoint(value) {
  const s = String(value || '').trim().toLowerCase()
  if (!s || PLACEHOLDER_ENDPOINTS.has(s)) return true
  return /-(unknown)$/.test(s)
}

function escapeTooltipHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function formatRhythmEventTooltipItem(event, index) {
  const text = String(event || '').trim()
  const matched = text.match(/^(Ep\d+|第\s*\d+\s*集)[:：\s-]+(.+)$/i)
  const label = matched ? matched[1].replace(/\s+/g, '') : String(index + 1).padStart(2, '0')
  const content = matched ? matched[2].trim() : text

  return `
    <div style="display:flex;gap:8px;margin-top:6px;line-height:1.45;">
      <span style="flex:0 0 auto;min-width:28px;padding:1px 6px;border-radius:6px;background:rgba(244,183,25,.14);border:1px solid rgba(244,183,25,.28);color:#f4c95d;font-size:10px;font-weight:600;text-align:center;">
        ${escapeTooltipHtml(label)}
      </span>
      <span style="color:#d9e6ff;white-space:normal;word-break:break-word;">
        ${escapeTooltipHtml(content)}
      </span>
    </div>
  `
}

function namesMentionedInText(text, nodes) {
  if (!text) return []
  const hits = []
  for (const node of nodes) {
    const name = (node.name || '').trim()
    if (!name || !text.includes(name)) continue
    hits.push({ pos: text.indexOf(name), name, id: node.id })
  }
  hits.sort((a, b) => a.pos - b.pos)
  return hits
}

function findNodeByName(name, nodes) {
  const s = String(name || '').trim()
  if (!s) return null
  const exact = nodes.find((n) => (n.name || '').trim() === s)
  if (exact) return exact.id
  if (s.length < 2) return null
  const fuzzy = nodes.filter((n) => {
    const nn = (n.name || '').trim()
    if (!nn || nn.length < 2) return false
    return nn.includes(s) || s.includes(nn) || nn.startsWith(s) || s.startsWith(nn)
  })
  if (fuzzy.length === 1) return fuzzy[0].id
  return null
}

function resolveNodeId(id, name, nodeIndex, nodes) {
  if (id && !isPlaceholderEndpoint(id) && nodeIndex.has(String(id))) return String(id)
  if (name && nodeIndex.has(name)) return nodeIndex.get(name)
  const byName = findNodeByName(name, nodes)
  if (byName) return byName
  return null
}

function resolveRelationshipEndpoints(rel, nodes, nodeIndex) {
  const mentioned = namesMentionedInText(rel.description || '', nodes)
  let aName = isPlaceholderEndpoint(rel.characterAName) ? '' : (rel.characterAName || rel.displayA || '').trim()
  let bName = isPlaceholderEndpoint(rel.characterBName) ? '' : (rel.characterBName || rel.displayB || '').trim()
  let aId = isPlaceholderEndpoint(rel.characterAId) ? '' : rel.characterAId || rel.charAId
  let bId = isPlaceholderEndpoint(rel.characterBId) ? '' : rel.characterBId || rel.charBId

  if (mentioned.length >= 2 && (!aName || !bName)) {
    if (!aName) aName = mentioned[0].name
    if (!bName) bName = mentioned.find((m) => m.name !== aName)?.name || mentioned[1]?.name
  } else if (mentioned.length === 1) {
    if (!aName) aName = mentioned[0].name
    else if (!bName && mentioned[0].name !== aName) bName = mentioned[0].name
  }

  return {
    from: resolveNodeId(aId || rel.from || rel.source || rel.fromId, aName, nodeIndex, nodes),
    to: resolveNodeId(bId || rel.to || rel.target || rel.toId, bName, nodeIndex, nodes),
    aName,
    bName,
  }
}

function truncateText(text, max = 120) {
  const s = String(text || '').trim()
  if (!s) return ''
  return s.length > max ? `${s.slice(0, max)}…` : s
}

function relationshipEdgeLabel(rel) {
  return resolveRelationTypeLabel(rel) || '关联'
}

function formatRelationshipEdgeTooltip(rel) {
  if (!rel || typeof rel !== 'object') return '关联'
  const parts = []
  const a = rel.characterAName || 'A'
  const b = rel.characterBName || 'B'
  const typeLabel = rel.relationTypeLabel || rel.relationType
  if (typeLabel) parts.push(`<b>${a} ↔ ${b}</b> · ${typeLabel}`)
  else parts.push(`<b>${a} ↔ ${b}</b>`)
  if (rel.description) parts.push(truncateText(rel.description, 160))
  if (rel.perspectiveA) parts.push(`<span style="opacity:0.85">${a} → ${b}：${truncateText(rel.perspectiveA, 100)}</span>`)
  if (rel.perspectiveB) parts.push(`<span style="opacity:0.85">${b} → ${a}：${truncateText(rel.perspectiveB, 100)}</span>`)
  if (rel.coreConflict) parts.push(`核心冲突：${truncateText(rel.coreConflict, 80)}`)
  if (rel.hiddenTension) parts.push(`潜在矛盾：${truncateText(rel.hiddenTension, 80)}`)
  if (rel.evolutionPath) parts.push(`演化：${truncateText(rel.evolutionPath, 80)}`)
  return parts.join('<br/><br/>') || '关联'
}

function pushRelationshipLink(rel, from, to, links) {
  const persA = (rel.perspectiveA || '').trim()
  const persB = (rel.perspectiveB || '').trim()
  const meta = { ...rel, characterAName: rel.characterAName, characterBName: rel.characterBName }
  const label = relationshipEdgeLabel(rel)
  const bidirectional = Boolean(persA && persB)

  links.push({
    source: from,
    target: to,
    value: label,
    relMeta: meta,
    lineStyle: { curveness: bidirectional ? 0.18 : 0.12, width: bidirectional ? 2 : 1.6 },
    symbol: bidirectional ? ['arrow', 'arrow'] : ['none', 'arrow'],
    symbolSize: bidirectional ? 6 : 7,
  })
}

/**
 * 人物关系图 — 支持 workspace view（characters + relationships）与 Fusion 分组 schema。
 */
export function buildCharacterRelationGraphOption({
  characterBible = {},
  characters: charactersProp,
  relationships: relationshipsProp,
  title = '',
}) {
  const nodes = []
  const links = []
  const nodeIndex = new Map()
  const categories = [
    { name: ROLE_CATEGORY.protagonist },
    { name: ROLE_CATEGORY.antagonist },
    { name: ROLE_CATEGORY.supporting },
  ]

  const pushChar = (char, roleHint) => {
    if (!char || typeof char !== 'object') return
    const id = char.id || char.characterId || char.name
    if (!id) return
    const sid = String(id)
    if (nodeIndex.has(sid)) return
    const name = (char.name || id).trim()
    const category = roleHint != null ? roleCategoryIndex(roleHint) : roleCategoryIndex(char.roleType)
    nodeIndex.set(sid, true)
    nodeIndex.set(name, sid)
    nodes.push({
      id: sid,
      name,
      value: truncateText(char.oneLineSummary || char.coreMotivation || '', 48),
      symbolSize: category === 0 ? 52 : category === 1 ? 44 : 36,
      category,
      label: { show: true, fontSize: 11 },
    })
  }

  const flatChars = charactersProp || characterBible.characters
  if (Array.isArray(flatChars) && flatChars.length) {
    for (const c of flatChars) pushChar(c)
  } else {
    for (const c of characterBible.protagonists || []) pushChar(c, 'protagonist')
    for (const c of characterBible.antagonists || []) pushChar(c, 'antagonist')
    for (const c of characterBible.supportingRoles || []) pushChar(c, 'supporting')
  }

  const relList = relationshipsProp || characterBible.relationships || characterBible.relationshipMap || []
  if (Array.isArray(relList) && relList.length) {
    for (const rel of relList) {
      if (!rel || typeof rel !== 'object') continue
      const { from, to } = resolveRelationshipEndpoints(rel, nodes, nodeIndex)
      if (!from || !to || from === to) continue
      pushRelationshipLink(
        {
          ...rel,
          characterAName: rel.characterAName || nodes.find((n) => n.id === from)?.name,
          characterBName: rel.characterBName || nodes.find((n) => n.id === to)?.name,
        },
        from,
        to,
        links,
      )
    }
  }

  const relText = (characterBible.relationshipSummary || '').trim()
  if (!links.length && nodes.length >= 2 && relText) {
    const hero = nodes[0]
    for (let i = 1; i < Math.min(nodes.length, 6); i += 1) {
      links.push({
        source: hero.id,
        target: nodes[i].id,
        value: '关系网',
        lineStyle: { type: 'dashed', opacity: 0.5 },
      })
    }
  }

  if (!nodes.length) return null

  return {
    title: title ? { text: title, left: 'center', top: 4, textStyle: { fontSize: 14 } } : undefined,
    tooltip: {
      confine: true,
      appendToBody: true,
      extraCssText: 'max-width:360px;white-space:normal;word-break:break-word;line-height:1.45;',
      formatter: (p) => {
        if (p.dataType === 'edge') {
          return formatRelationshipEdgeTooltip(p.data.relMeta) || p.data.value || '关联'
        }
        const summary = p.data.value ? `<br/><span style="opacity:0.8">${p.data.value}</span>` : ''
        return `${p.data.name}${summary}`
      },
    },
    legend: [{ data: categories.map((c) => c.name), bottom: 0, itemGap: 12, textStyle: { fontSize: 11 } }],
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        focusNodeAdjacency: true,
        categories,
        data: nodes,
        links,
        edgeLabel: { show: false },
        label: { position: 'right', color: chartColors.text },
        force: {
          repulsion: 320,
          edgeLength: [100, 180],
          gravity: 0.06,
        },
        lineStyle: { color: '#475569', curveness: 0.15 },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 3 },
          label: { show: true },
        },
      },
    ],
  }
}

/**
 * 剧情脉络图 — stageBlocks / sixStagePlan → 分集，支持工作台 series_outline 结构。
 */
export function buildPlotFlowGraphOption({
  seriesOutline = {},
  structurePlan = {},
  stageBlocks: stageBlocksProp,
  episodes: episodesProp,
  title = '',
}) {
  const nodes = []
  const links = []
  const stageBlocks =
    stageBlocksProp || seriesOutline.stageBlocks || seriesOutline.navigation || structurePlan.sixStagePlan || []
  const episodes = episodesProp || seriesOutline.episodes || []

  for (const block of stageBlocks) {
    if (!block || typeof block !== 'object') continue
    const key = block.key ?? block.stageIndex ?? block.stageName ?? block.label
    if (key == null) continue
    const range = blockEpisodeRange(block)
    const rangeLabel = range ? `E${range.from}-${range.to}` : ''
    nodes.push({
      id: `stage-${key}`,
      name: block.label || block.title || block.stageName || `阶段 ${key}`,
      value: rangeLabel,
      symbolSize: 44,
      category: 0,
      itemStyle: { color: chartColors.gold },
    })
  }

  for (const ep of episodes.slice(0, 60)) {
    if (!ep || typeof ep !== 'object') continue
    const num = ep.episodeNumber || ep.episode
    if (!num) continue
    const id = `ep-${num}`
    nodes.push({
      id,
      name: `第${num}集`,
      value: (ep.oneLineSummary || ep.title || '').slice(0, 48),
      symbolSize: ep.isKeyEpisode ? 34 : 26,
      category: 1,
      itemStyle: { color: chartPalette[(Number(num) - 1) % chartPalette.length] },
    })
    const stageKey =
      ep.stageKey ||
      ep.stageIndex ||
      ep.actIndex ||
      ep.stageInfo?.stageKey ||
      findStageKeyForEpisode(stageBlocks, num)
    if (stageKey != null) {
      links.push({
        source: `stage-${stageKey}`,
        target: id,
        value: '集纲',
      })
    }
  }

  const epNodes = nodes.filter((n) => n.id.startsWith('ep-'))
  epNodes.sort((a, b) => parseInt(a.id.replace('ep-', ''), 10) - parseInt(b.id.replace('ep-', ''), 10))
  for (let i = 0; i < epNodes.length - 1; i += 1) {
    links.push({
      source: epNodes[i].id,
      target: epNodes[i + 1].id,
      value: '接续',
      lineStyle: { type: 'dashed', opacity: 0.35 },
    })
  }

  if (!nodes.length) return null

  return {
    title: title ? { text: title, left: 'center', top: 4, textStyle: { fontSize: 14 } } : undefined,
    tooltip: {
      formatter: (p) => {
        if (p.dataType === 'edge') return p.data.value || '关联'
        const extra = p.data.value ? `<br/>${p.data.value}` : ''
        return `${p.data.name}${extra}`
      },
    },
    legend: [{ data: ['故事阶段', '分集'], bottom: 4 }],
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        categories: [{ name: '故事阶段' }, { name: '分集' }],
        data: nodes,
        links,
        force: {
          repulsion: 220,
          edgeLength: [60, 140],
          gravity: 0.1,
        },
        emphasis: { focus: 'adjacency' },
      },
    ],
  }
}

/** 全剧情绪强度曲线 */
export function buildRhythmCurveOption({ curve = [] }) {
  if (!curve.length) return null
  return {
    tooltip: {
      trigger: 'axis',
      confine: true,
      extraCssText: 'max-width:560px;white-space:normal;word-break:break-word;',
      formatter: (params) => {
        const p = params?.[0]
        if (!p) return ''
        const block = curve[p.dataIndex] || {}
        const parts = [
          `<b>${escapeTooltipHtml(formatRhythmEpisodeLabel(block))}</b>`,
          `强度 ${p.value ?? '—'}/10`,
        ]
        const hooks = (block.suggestedHooks || [])
          .map((h) => h.name || h.code)
          .filter(Boolean)
        if (hooks.length) parts.push(`推荐钩子：${hooks.map(escapeTooltipHtml).join('、')}`)
        const revs = (block.linkedReversals || [])
          .map((r) => `E${r.episodeNumber}${r.patternName ? ` · ${r.patternName}` : ''}`)
          .filter(Boolean)
        if (revs.length) parts.push(`段内反转：${revs.map(escapeTooltipHtml).join('、')}`)
        const events = (block.keyEvents || []).slice(0, 5)
        if (events.length) {
          parts.push(`
            <div style="margin-top:8px;">
              <div style="margin-bottom:2px;color:#8fa4c8;font-size:11px;">关键事件</div>
              ${events.map(formatRhythmEventTooltipItem).join('')}
            </div>
          `)
        }
        if (block.notes) parts.push(escapeTooltipHtml(String(block.notes).slice(0, 100)))
        return parts.join('<br/>')
      },
    },
    grid: { left: 44, right: 16, top: 28, bottom: 40 },
    xAxis: {
      type: 'category',
      data: curve.map((b) => formatRhythmEpisodeLabel(b).replace(/^第|集$/g, '') || '—'),
      boundaryGap: false,
      axisLabel: { fontSize: 10 },
    },
    yAxis: { type: 'value', min: 0, max: 10, splitNumber: 5, axisLabel: { formatter: '{value}' } },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: chartColors.gold },
        lineStyle: { width: 2.5, color: chartColors.gold },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(212, 168, 83, 0.35)' },
              { offset: 1, color: 'rgba(212, 168, 83, 0.02)' },
            ],
          },
        },
        data: curve.map((b) => b.intensityLevel ?? 0),
      },
    ],
  }
}

function parseNumericRange(text, fallbackStart, fallbackEnd) {
  if (fallbackStart != null && fallbackEnd != null) {
    return { start: Number(fallbackStart), end: Number(fallbackEnd) }
  }
  const raw = String(text || '').trim()
  const span = raw.match(/(\d+)\s*[-–~至]\s*(\d+)/i)
  if (span) return { start: Number(span[1]), end: Number(span[2]) }
  const single = raw.match(/(\d+)/)
  if (single) {
    const n = Number(single[1])
    return { start: n, end: n }
  }
  return null
}

/** 节奏曲线块 →「第1集」或「第1-10集」 */
export function formatRhythmEpisodeLabel(block = {}) {
  const direct = String(block.episodeRange || block.episodeGroup || '').trim()
  const parsed = parseNumericRange(direct, block.episodeStart, block.episodeEnd)
  if (parsed) {
    return parsed.start === parsed.end
      ? `第${parsed.start}集`
      : `第${parsed.start}-${parsed.end}集`
  }
  if (direct) {
    const cleaned = direct.replace(/^ep\s*/i, '').trim()
    return cleaned.includes('-') ? `第${cleaned}集` : `第${cleaned}集`
  }
  return '—'
}

function stageEpisodeRange(stage) {
  if (!stage || typeof stage !== 'object') return null
  return parseNumericRange(stage.episodeRange, stage.startEpisode, stage.endEpisode)
}

function rhythmEpisodeRange(block) {
  if (!block || typeof block !== 'object') return null
  return parseNumericRange(block.episodeRange)
}

function episodeInRange(episode, range) {
  const ep = Number(episode)
  if (!Number.isFinite(ep) || !range) return false
  return ep >= range.start && ep <= range.end
}

function rangesOverlap(a, b) {
  if (!a || !b) return false
  return a.start <= b.end && b.start <= a.end
}

/**
 * 六阶段 → 节奏段 → 反转点：按集数范围分层桑基，避免全连接导致标签堆叠。
 */
export function buildStructureSankeyOption({ structurePlan = {} }) {
  const stages = (structurePlan.sixStagePlan || []).filter((s) => s && (s.stageName || s.stageIndex))
  const rhythm = structurePlan.rhythmCurve || []
  const reversals = [...(structurePlan.keyReversalPoints || [])]
    .filter((r) => r && r.episodeNumber != null)
    .sort((a, b) => Number(a.episodeNumber) - Number(b.episodeNumber))
    .slice(0, 12)

  if (!stages.length) return null

  const nodes = []
  const links = []
  const linkSet = new Set()
  const nodeSet = new Set()

  const addLink = (source, target, value = 1) => {
    if (!source || !target) return
    const key = `${source}>>${target}`
    if (linkSet.has(key)) return
    linkSet.add(key)
    links.push({ source, target, value })
  }

  const addNode = (name, depth, color) => {
    if (!name || nodeSet.has(name)) return name
    nodeSet.add(name)
    nodes.push({
      name,
      depth,
      itemStyle: color ? { color } : undefined,
      label: {
        color: chartColors.text,
        fontSize: depth === 0 ? 12 : 11,
        formatter: ({ name: n }) => n.replace(/^[SRV]·/, ''),
      },
    })
    return name
  }

  const stageNodes = []
  for (const s of stages) {
    const label = s.stageName || `阶段${s.stageIndex}`
    const id = addNode(`S·${label}`, 0, chartColors.gold)
    if (id) stageNodes.push({ id, range: stageEpisodeRange(s), label })
  }

  const rhythmNodes = []
  for (const r of rhythm) {
    const range = rhythmEpisodeRange(r)
    if (!range) continue
    const label = `第${r.episodeRange}集`
    const intensity = r.intensityLevel != null ? ` · ${r.intensityLevel}/10` : ''
    const id = addNode(`R·${label}${intensity}`, 1, chartPalette[2])
    if (id) rhythmNodes.push({ id, range })
  }

  for (const { id: stageId, range: stageRange } of stageNodes) {
    let linkedRhythm = false
    for (const { id: rhythmId, range: rhythmRange } of rhythmNodes) {
      if (!rangesOverlap(stageRange, rhythmRange)) continue
      addLink(stageId, rhythmId, 2)
      linkedRhythm = true
    }
    if (!linkedRhythm && stageRange) {
      for (const rev of reversals) {
        if (episodeInRange(rev.episodeNumber, stageRange)) {
          const revId = addNode(`V·第${rev.episodeNumber}集反转`, 2, chartPalette[4])
          if (revId) addLink(stageId, revId, 1)
        }
      }
    }
  }

  for (const rev of reversals) {
    const ep = Number(rev.episodeNumber)
    const revId = addNode(`V·第${ep}集反转`, 2, chartPalette[4])
    if (!revId) continue

    let linked = false
    for (const { id: rhythmId, range: rhythmRange } of rhythmNodes) {
      if (episodeInRange(ep, rhythmRange)) {
        addLink(rhythmId, revId, 1)
        linked = true
      }
    }
    if (!linked) {
      for (const { id: stageId, range: stageRange } of stageNodes) {
        if (episodeInRange(ep, stageRange)) {
          addLink(stageId, revId, 1)
          linked = true
          break
        }
      }
    }
    if (!linked && stageNodes[0]) {
      addLink(stageNodes[0].id, revId, 1)
    }
  }

  if (!links.length) return null

  const layerCount = Math.max(
    stageNodes.length,
    rhythmNodes.length,
    reversals.length,
    3,
  )

  return {
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove',
      formatter: (params) => {
        if (params.dataType === 'edge') {
          return `${params.data.source.replace(/^[SRV]·/, '')} → ${params.data.target.replace(/^[SRV]·/, '')}`
        }
        return params.name.replace(/^[SRV]·/, '')
      },
    },
    series: [
      {
        type: 'sankey',
        left: '4%',
        right: '14%',
        top: 16,
        bottom: 16,
        nodeAlign: 'justify',
        nodeGap: 14,
        layoutIterations: 48,
        emphasis: { focus: 'adjacency' },
        data: nodes,
        links,
        lineStyle: { color: 'gradient', curveness: 0.45, opacity: 0.45 },
        label: {
          color: chartColors.text,
          fontSize: 11,
          overflow: 'truncate',
          width: 96,
        },
        levels: [
          { depth: 0, itemStyle: { color: chartColors.gold }, label: { position: 'right' } },
          { depth: 1, itemStyle: { color: chartPalette[2] }, label: { position: 'right' } },
          { depth: 2, itemStyle: { color: chartPalette[4] }, label: { position: 'left' } },
        ],
      },
    ],
    _chartHeight: Math.max(300, Math.min(480, layerCount * 36 + 80)),
  }
}
