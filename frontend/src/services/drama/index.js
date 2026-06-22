import http from '../http';

// 角色列表
export const getDramaRoles = () => http.get('/api/drama/roles/');

// 项目管理
export const createDramaProject = (data) => http.post('/api/drama/projects/', data);
export const getDramaProjects = () => http.get('/api/drama/projects/');
export const getDramaProject = (id) => http.get(`/api/drama/projects/${id}/`);
export const getProjectProgress = (id) => http.get(`/api/drama/projects/${id}/progress/`);
export const runRole = (projectId, roleId) =>
  http.post(`/api/drama/projects/${projectId}/run/${roleId}/`);

// 质量评分雷达
export const getQualityRadar = (projectId) =>
  http.get(`/api/drama/projects/${projectId}/quality-radar/`);

// 字数验证
export const validateWordCount = (content, episodeNumber) =>
  http.post('/api/drama/validate/word-count/', {
    content,
    episode_number: episodeNumber,
  });

// Token统计
export const getTokenStats = (days = 30) =>
  http.get('/api/drama/stats/token/', { params: { days } });

// 模型配置
export const getModelConfig = () => http.get('/api/drama/models/config/');
export const updateModelConfig = (data) => http.put('/api/drama/models/config/', data);
