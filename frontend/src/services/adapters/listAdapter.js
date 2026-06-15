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

export function normalizeListResult(result, itemMapper = (item) => item) {
  const items = Array.isArray(result?.data) ? result.data : []
  return {
    items: items.map(itemMapper).filter(Boolean),
    pagination: normalizePagination(result?.pagination),
    facets: result?.facets,
    meta: result?.meta,
  }
}

export function normalizeArrayResult(result, itemMapper = (item) => item) {
  const items = Array.isArray(result?.data) ? result.data : []
  return items.map(itemMapper).filter(Boolean)
}
