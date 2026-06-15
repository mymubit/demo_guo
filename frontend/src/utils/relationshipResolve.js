const PLACEHOLDER_ENDPOINTS = new Set(['', 'a-unknown', 'b-unknown', 'unknown', '—'])

export function isPlaceholderEndpoint(value) {
  const s = String(value || '').trim().toLowerCase()
  if (!s || PLACEHOLDER_ENDPOINTS.has(s) || s === '—') return true
  return /-(unknown)$/.test(s)
}

function roleGender(roleType) {
  const rt = String(roleType || '').toLowerCase()
  if (rt.includes('female')) return 'female'
  if (rt.includes('male')) return 'male'
  return ''
}

function extractEndpointName(value) {
  if (!value) return ''
  if (typeof value === 'string') return value.trim()
  if (typeof value === 'object') return (value.name || value.characterName || '').trim()
  return ''
}

function findCharacterId(name, characters) {
  const n = String(name || '').trim()
  if (!n) return ''
  const exact = (characters || []).find((c) => (c.name || '').trim() === n)
  if (exact?.id) return exact.id
  if (n.length < 2) return ''
  const fuzzy = (characters || []).filter((c) => {
    const cn = (c.name || '').trim()
    if (!cn || !c.id || cn.length < 2) return false
    return cn.includes(n) || n.includes(cn) || cn.startsWith(n) || n.startsWith(cn)
  })
  if (fuzzy.length === 1) return fuzzy[0].id
  return ''
}

function pickProtagonist(characters, gender) {
  const prots = (characters || []).filter((c) => String(c.roleType || '').startsWith('protagonist'))
  if (gender === 'female') {
    return prots.find((c) => roleGender(c.roleType) === 'female') || prots[0]
  }
  if (gender === 'male') {
    return prots.find((c) => roleGender(c.roleType) === 'male') || prots[1] || prots[0]
  }
  return prots[0]
}

function pickAntagonist(characters) {
  return (characters || []).find((c) => String(c.roleType || '').startsWith('antagonist'))
}

function namesMentionedInText(text, characters) {
  if (!text) return []
  const hits = []
  const seen = new Set()
  const sorted = [...(characters || [])]
    .map((c) => ({ name: (c.name || '').trim(), id: c.id }))
    .filter((c) => c.name)
    .sort((a, b) => b.name.length - a.name.length)

  for (const { name, id } of sorted) {
    if (seen.has(name)) continue
    const pos = text.indexOf(name)
    if (pos >= 0) {
      hits.push({ pos, name, id })
      seen.add(name)
    }
  }
  hits.sort((a, b) => a.pos - b.pos)
  return hits
}

function inferMissingEndpoints(aName, bName, rel, characters) {
  const desc = rel.description || ''
  const ctx = `${rel.relationTypeLabel || ''} ${rel.relationType || ''} ${desc}`
  let left = aName
  let right = bName

  const loverHints = ['恋人', '情侣', '宠物', '主人', 'romantic', 'lover', '陌生人']
  const friendHints = ['闺蜜', '挚友', '朋友', 'friend', 'confidant']
  const enemyHints = ['仇敌', '敌对', 'enemy', '势不两立']

  if (!left && !right) {
    if (loverHints.some((h) => ctx.includes(h))) {
      const pf = pickProtagonist(characters, 'female')
      const pm = pickProtagonist(characters, 'male')
      if (pf?.name && pm?.name) return [pf.name, pm.name]
    }
    if (enemyHints.some((h) => ctx.includes(h))) {
      const ant = pickAntagonist(characters)
      const prot = pickProtagonist(characters)
      if (ant?.name && prot?.name) return [ant.name, prot.name]
    }
  }

  if (left && !right) {
    if (friendHints.some((h) => ctx.includes(h)) || ctx.includes('女主')) {
      const pf = pickProtagonist(characters, 'female')
      if (pf?.name && pf.name !== left) right = pf.name
    }
    if (!right && loverHints.some((h) => ctx.includes(h))) {
      const pm = pickProtagonist(characters, 'male')
      if (pm?.name && pm.name !== left) right = pm.name
    }
    if (!right && enemyHints.some((h) => ctx.includes(h))) {
      const ant = pickAntagonist(characters)
      if (ant?.name && ant.name !== left) right = ant.name
      else {
        const prot = pickProtagonist(characters)
        if (prot?.name && prot.name !== left) right = prot.name
      }
    }
  }

  if (!left && right) {
    if (friendHints.some((h) => ctx.includes(h)) || ctx.includes('女主')) {
      const pf = pickProtagonist(characters, 'female')
      if (pf?.name && pf.name !== right) left = pf.name
    }
    if (!left && loverHints.some((h) => ctx.includes(h))) {
      const pf = pickProtagonist(characters, 'female')
      if (pf?.name && pf.name !== right) left = pf.name
    }
  }

  return [left, right]
}

export function resolveRelationshipRow(rel, characters = []) {
  let aName = isPlaceholderEndpoint(rel.characterAName) ? '' : (rel.characterAName || '').trim()
  let bName = isPlaceholderEndpoint(rel.characterBName) ? '' : (rel.characterBName || '').trim()
  if (!aName) aName = extractEndpointName(rel.characterA) || extractEndpointName(rel.aCharacter)
  if (!bName) bName = extractEndpointName(rel.characterB) || extractEndpointName(rel.bCharacter)

  const mentioned = namesMentionedInText(rel.description || '', characters)
  if (mentioned.length) {
    if (!aName) aName = mentioned[0].name
    if (!bName) bName = mentioned.find((m) => m.name !== aName)?.name || ''
  }

  ;[aName, bName] = inferMissingEndpoints(aName, bName, rel, characters)

  const findId = (name) => findCharacterId(name, characters)

  return {
    ...rel,
    characterAName: aName,
    characterBName: bName,
    characterAId:
      findId(aName) || (isPlaceholderEndpoint(rel.characterAId) ? '' : rel.characterAId) || '',
    characterBId:
      findId(bName) || (isPlaceholderEndpoint(rel.characterBId) ? '' : rel.characterBId) || '',
    displayA: aName || '—',
    displayB: bName || '—',
    charAId: findId(aName),
    charBId: findId(bName),
  }
}

export function resolveRelationshipList(relationships, characters) {
  return (relationships || []).map((rel) => resolveRelationshipRow(rel, characters))
}
