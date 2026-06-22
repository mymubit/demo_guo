import { request } from '../http'

// 角色列表
export const getDramaRoles = () => request('GET', '/api/drama/roles/')

// 项目管理
export const createDramaProject = (data) =>
  request('POST', '/api/drama/projects/', { data })

export const getDramaProjects = () => request('GET', '/api/drama/projects/')

export const getDramaProject = (id) => request('GET', `/api/drama/projects/${id}/`)

export const getProjectProgress = (id) =>
  request('GET', `/api/drama/projects/${id}/progress/`)

export const runRole = (projectId, roleId) =>
  request('POST', `/api/drama/projects/${projectId}/run/${roleId}/`)

// 质量评分雷达
export const getQualityRadar = (projectId) =>
  request('GET', `/api/drama/projects/${projectId}/quality-radar/`)

// 字数验证
export const validateWordCount = (content, episodeNumber) =>
  request('POST', '/api/drama/validate/word-count/', {
    data: {
      content,
      episode_number: episodeNumber,
    },
  })

// Token 统计
export const getTokenStats = (days = 30) =>
  request('GET', '/api/drama/stats/token/', { params: { days } })

// 模型配置
export const getModelConfig = () => request('GET', '/api/drama/models/config/')

export const updateModelConfig = (data) =>
  request('PUT', '/api/drama/models/config/', { data })
