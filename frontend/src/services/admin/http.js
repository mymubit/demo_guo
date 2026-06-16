/**
 * admin/http.js —— 后台管理专用请求层 + 响应规范化工具
 */
import { getAxios } from '../http'
import { coerceUnwrappedArray, normalizeListResult } from '../adapters/listAdapter'

/** 后台请求：直接使用 axios（不走 fetch fallback，确保拦截器生效） */
export async function adminRequest(method, path, { params, data } = {}) {
  const axios = await getAxios()
  if (!axios) throw new Error('axios 不可用')
  return axios.request({ method, url: path, params, data })
}

/** 解包分页列表：{items, pagination} */
export function unwrapAdminList(result) {
  return normalizeListResult(result)
}

/** 解包数组列表（兼容 axios 已解包为裸数组的响应） */
export function unwrapAdminListData(result) {
  return coerceUnwrappedArray(result)
}

export function normalizeTier1Catalog(data) {
  const detail = data?.tier1_section_catalog_detail
  return detail.map((item) => ({
    key: item.key,
    label: item.label,
  }))
}

export function normalizeWorkflowSteps(data) {
  return {
    items: data.items,
    meta: data?.meta || {},
    tier1SectionCatalog: normalizeTier1Catalog(data),
  }
}

export function normalizeAgentRegistry(data) {
  return {
    ...data,
    tier1SectionCatalog: normalizeTier1Catalog(data),
    defaultTier1SectionsByAgent: data?.default_tier1_sections_by_agent || {},
  }
}

export function normalizeFusionPacks(data) {
  return {
    items: data.items,
    meta: data?.meta || {},
  }
}

export function normalizeAgentLlmRoutes(data) {
  return coerceUnwrappedArray(data)
}
