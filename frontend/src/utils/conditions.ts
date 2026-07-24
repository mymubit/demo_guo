/**
 * Minimal condition evaluator for workbench visible_when / enable_when / required_when.
 * Supports:
 *   field == 'value'
 *   field == true | false
 *   field != …
 *   field contains 'value'
 *   field is not empty
 *   and / or combinations (left-associative)
 */

export type ConditionContext = Record<string, unknown>

function resolveField(ctx: ConditionContext, field: string): unknown {
  if (Object.prototype.hasOwnProperty.call(ctx, field)) return ctx[field]
  const parts = field.split('.')
  let cur: unknown = ctx
  for (const p of parts) {
    if (cur == null || typeof cur !== 'object') return undefined
    cur = (cur as Record<string, unknown>)[p]
  }
  return cur
}

function parseLiteral(raw: string): unknown {
  const t = raw.trim()
  if (t === 'true') return true
  if (t === 'false') return false
  if (/^-?\d+(\.\d+)?$/.test(t)) return Number(t)
  if (
    (t.startsWith("'") && t.endsWith("'")) ||
    (t.startsWith('"') && t.endsWith('"'))
  ) {
    return t.slice(1, -1)
  }
  return t
}

function isNonEmpty(value: unknown): boolean {
  if (value == null) return false
  if (typeof value === 'string' || Array.isArray(value)) return value.length > 0
  if (typeof value === 'object') return Object.keys(value as object).length > 0
  return true
}

function evalAtomic(expr: string, ctx: ConditionContext): boolean {
  const notEmptyMatch = expr.match(/^([a-zA-Z_][\w.]*)\s+is\s+not\s+empty$/i)
  if (notEmptyMatch) {
    return isNonEmpty(resolveField(ctx, notEmptyMatch[1]))
  }

  const containsMatch = expr.match(/^([a-zA-Z_][\w.]*)\s+contains\s+(.+)$/)
  if (containsMatch) {
    const left = resolveField(ctx, containsMatch[1])
    const right = parseLiteral(containsMatch[2])
    if (Array.isArray(left)) return left.includes(right)
    if (typeof left === 'string') return left.includes(String(right))
    return false
  }

  const eqMatch = expr.match(/^([a-zA-Z_][\w.]*)\s*==\s*(.+)$/)
  if (eqMatch) {
    const left = resolveField(ctx, eqMatch[1])
    const right = parseLiteral(eqMatch[2])
    return left === right
  }

  const neMatch = expr.match(/^([a-zA-Z_][\w.]*)\s*!=\s*(.+)$/)
  if (neMatch) {
    const left = resolveField(ctx, neMatch[1])
    const right = parseLiteral(neMatch[2])
    return left !== right
  }

  throw new Error(`Unsupported condition expression: ${expr}`)
}

function splitTopLevel(expr: string, op: 'and' | 'or'): string[] | null {
  const needle = ` ${op} `
  const parts: string[] = []
  let depth = 0
  let buf = ''
  for (let i = 0; i < expr.length; ) {
    if (expr[i] === '(') {
      depth += 1
      buf += expr[i]
      i += 1
      continue
    }
    if (expr[i] === ')') {
      depth -= 1
      buf += expr[i]
      i += 1
      continue
    }
    if (depth === 0 && expr.slice(i, i + needle.length).toLowerCase() === needle) {
      parts.push(buf.trim())
      buf = ''
      i += needle.length
      continue
    }
    buf += expr[i]
    i += 1
  }
  if (parts.length === 0) return null
  parts.push(buf.trim())
  return parts
}

export function evaluateCondition(expression: string | undefined | null, ctx: ConditionContext): boolean {
  if (!expression || !expression.trim()) return true
  const expr = expression.trim()

  if (expr.startsWith('(') && expr.endsWith(')')) {
    let depth = 0
    let wrapped = true
    for (let i = 0; i < expr.length; i += 1) {
      if (expr[i] === '(') depth += 1
      if (expr[i] === ')') depth -= 1
      if (depth === 0 && i < expr.length - 1) {
        wrapped = false
        break
      }
    }
    if (wrapped) return evaluateCondition(expr.slice(1, -1), ctx)
  }

  const orParts = splitTopLevel(expr, 'or')
  if (orParts) return orParts.some((p) => evaluateCondition(p, ctx))

  const andParts = splitTopLevel(expr, 'and')
  if (andParts) return andParts.every((p) => evaluateCondition(p, ctx))

  return evalAtomic(expr, ctx)
}

/** Build condition context from project settings. */
export function settingsConditionContext(settings: {
  entry_type?: string
  enable_delivery?: boolean
  creation_preferences?: {
    enable_delivery?: boolean
    deliverables?: string[]
    [key: string]: unknown
  }
  deliverables?: string[]
  reference_dramas?: unknown
  [key: string]: unknown
}): ConditionContext {
  const enableDelivery =
    settings.enable_delivery ?? settings.creation_preferences?.enable_delivery ?? false
  const deliverables =
    settings.deliverables ?? settings.creation_preferences?.deliverables ?? []
  const referenceDramas = Array.isArray(settings.reference_dramas)
    ? settings.reference_dramas
    : []
  return {
    ...settings,
    entry_type: settings.entry_type,
    enable_delivery: enableDelivery,
    deliverables,
    reference_dramas: referenceDramas,
  }
}
