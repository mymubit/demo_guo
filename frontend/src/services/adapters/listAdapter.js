import { DEFAULT_PAGE, DEFAULT_PAGE_SIZE } from '../constants/businessEnums'

export function normalizePagination(raw, fallback = {}) {
  const source = raw && typeof raw === 'object' ? raw : {}
  return {
    total: Number(source.total ?? fallback.total ?? 0),
    page: Number(source.page ?? fallback.page ?? DEFAULT_PAGE),
    page_size: Number(source.page_size ?? fallback.page_size ?? DEFAULT_PAGE_SIZE),
    total_pages: Number(source.total_pages ?? fallback.total_pages ?? 1),
  }
}

/**
 * 从统一列表响应中提取数组（{ data: [] } 或 { items: [] }）。
 */
export function extractListItems(result) {
  if (Array.isArray(result)) {
    return result
  }
  if (!result || typeof result !== 'object') {
    return []
  }
  if (Array.isArray(result.data)) {
    return result.data
  }
  if (Array.isArray(result.items)) {
    return result.items
  }
  return []
}

export function normalizeListResult(result, itemMapper = (item) => item) {
  const source = result && typeof result === 'object' && !Array.isArray(result) ? result : {}
  const items = extractListItems(result)
  return {
    items: items.map(itemMapper).filter(Boolean),
    pagination: normalizePagination(source.pagination),
    facets: source.facets,
    meta: source.meta,
    summary: source.summary,
    total: source.total,
  }
}

export function normalizeArrayResult(result, itemMapper = (item) => item) {
  const items = extractListItems(result)
  return items.map(itemMapper).filter(Boolean)
}

/** http 层已解包为裸数组，或 { data/items: array } 信封 */
export function coerceUnwrappedArray(result, itemMapper = (item) => item) {
  return normalizeArrayResult(result, itemMapper)
}
