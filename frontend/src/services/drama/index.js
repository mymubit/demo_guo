import { request } from '../http';

// ─── 角色列表（含三层分级） ────────────────────────────────────────────────
export const getDramaRoles = () => request('GET', '/api/drama/roles/');

// ─── 项目管理 ──────────────────────────────────────────────────────────────
export const createDramaProject = (data) => request('POST', '/api/drama/projects/', { data });
export const getDramaProjects = () => request('GET', '/api/drama/projects/');
export const getDramaProject = (id) => request('GET', `/api/drama/projects/${id}/`);
export const getProjectProgress = (id) => request('GET', `/api/drama/projects/${id}/progress/`);

// ─── 角色执行（支持分集范围参数） ──────────────────────────────────────────
export const runRole = (projectId, roleId, options = {}) =>
  request('POST', `/api/drama/projects/${projectId}/run/${roleId}/`, { data: options });

// ─── 分集产物（剧本内容读写） ────────────────────────────────────────────────
/** 获取项目所有集的产物摘要列表 */
export const getEpisodeList = (projectId, artifactKey = 'episode_script') =>
  request('GET', `/api/drama/projects/${projectId}/episodes/`, {
    params: { key: artifactKey },
  });

/** 获取指定集的产物内容 */
export const getEpisodeContent = (projectId, episodeNumber, artifactKey = 'episode_script') =>
  request('GET', `/api/drama/projects/${projectId}/episodes/`, {
    params: { episode: episodeNumber, key: artifactKey },
  });

/** 应用修改建议到指定集（生成新版本） */
export const applyEpisodeSuggestions = (projectId, episodeNumber, suggestions, agentId) =>
  request('POST', `/api/drama/projects/${projectId}/episodes/`, {
    data: {
      episode_number: episodeNumber,
      artifact_key: 'episode_script',
      suggestions,
      agent_id: agentId,
    },
  });

// ─── 分集质量评估 ─────────────────────────────────────────────────────────────
/** 获取项目所有集的质量评估概况 */
export const getEpisodeQualityList = (projectId) =>
  request('GET', `/api/drama/projects/${projectId}/episode-quality/`);

/** 提交单集质量评估结果 */
export const submitEpisodeQuality = (projectId, data) =>
  request('POST', `/api/drama/projects/${projectId}/episode-quality/`, { data });

// ─── 质量雷达（支持分集查询） ────────────────────────────────────────────────
export const getQualityRadar = (projectId, episodeNumber) =>
  request('GET', `/api/drama/projects/${projectId}/quality-radar/`, {
    params: episodeNumber ? { episode: episodeNumber } : {},
  });

// ─── 字数验证 ────────────────────────────────────────────────────────────────
export const validateWordCount = (content, episodeNumber) =>
  request('POST', '/api/drama/validate/word-count/', {
    data: { content, episode_number: episodeNumber },
  });

/** 批量验证所有集的字数 */
export const validateAllWordCounts = (episodes) =>
  request('POST', '/api/drama/validate/word-count/batch/', {
    data: { episodes },
  });

// ─── Token统计 ────────────────────────────────────────────────────────────────
export const getTokenStats = (days = 30) =>
  request('GET', '/api/drama/stats/token/', { params: { days } });

// ─── 模型配置 ────────────────────────────────────────────────────────────────
export const getModelConfig = () => request('GET', '/api/drama/models/config/');
export const updateModelConfig = (data) => request('PUT', '/api/drama/models/config/', { data });

// ─── 分集生成计划（解决100集token爆炸问题） ────────────────────────────────────
/** 获取项目的分集生成计划和进度 */
export const getGenerationPlan = (projectId) =>
  request('GET', `/api/drama/projects/${projectId}/generation-plan/`);

/**
 * 创建或更新生成计划
 * @param {string} projectId
 * @param {{batchSize: number, qualityGateScore: number, autoProceed: boolean}} options
 */
export const createGenerationPlan = (projectId, options = {}) =>
  request('POST', `/api/drama/projects/${projectId}/generation-plan/`, {
    data: {
      batch_size: options.batchSize || 5,
      quality_gate_score: options.qualityGateScore || 75,
      auto_proceed: options.autoProceed || false,
    },
  });
