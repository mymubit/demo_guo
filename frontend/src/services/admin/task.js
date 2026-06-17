/**
 * admin/task.js — 创作任务管理中心 API
 *
 * 接口前缀：/api/admin/creation/tasks/
 * 覆盖：任务列表、详情、人工重试、人工取消
 */
import { adminRequest } from './http'

const BASE = '/api/admin/creation/tasks/'

/**
 * 获取任务列表
 * @param {object} params - { project_id, state, trigger_mode, page }
 */
export async function listCreationTasks(params = {}) {
  const res = await adminRequest('GET', BASE, { params })
  return res.data?.data || { items: [], total: 0, page: 1, page_size: 20 }
}

/**
 * 获取任务详情
 * @param {string} taskId
 */
export async function getCreationTask(taskId) {
  const res = await adminRequest('GET', `${BASE}${taskId}/`)
  return res.data?.data || null
}

/**
 * 人工重试失败任务
 * @param {string} taskId
 */
export async function retryCreationTask(taskId) {
  const res = await adminRequest('POST', `${BASE}${taskId}/retry/`)
  return res.data?.data || null
}

/**
 * 人工取消任务
 * @param {string} taskId
 */
export async function cancelCreationTask(taskId) {
  const res = await adminRequest('POST', `${BASE}${taskId}/cancel/`)
  return res.data?.data || null
}

export const adminTask = {
  listCreationTasks,
  getCreationTask,
  retryCreationTask,
  cancelCreationTask,
}
