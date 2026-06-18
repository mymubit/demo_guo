import { adminRequest, unwrapAdminList, unwrapAdminListData } from './http'

export const adminSkill = {
  // 技能定义列表
  listDefinitions: (params = {}) =>
    adminRequest('GET', '/api/admin/skills/definitions/', { params }).then(unwrapAdminList),
  // 技能定义详情
  getDefinition: (pk) =>
    adminRequest('GET', `/api/admin/skills/definitions/${pk}/`),
  // 更新技能定义
  updateDefinition: (pk, data) =>
    adminRequest('PUT', `/api/admin/skills/definitions/${pk}/`, { data }),
  // 发布技能（灰度）
  publishDefinition: (pk, { gray_weight } = {}) =>
    adminRequest('POST', `/api/admin/skills/definitions/${pk}/publish/`, {
      data: { gray_weight },
    }),

  // 回滚技能
  rollbackDefinition: (pk) =>
    adminRequest('POST', `/api/admin/skills/definitions/${pk}/rollback/`),

  // 废弃技能
  deprecateDefinition: (pk) =>
    adminRequest('POST', `/api/admin/skills/definitions/${pk}/deprecate/`),

  // 技能统计（全局聚合，可按 skill_id 在前端筛选）
  getDefinitionStats: (params = {}) =>
    adminRequest('GET', '/api/admin/skills/definitions/stats/', { params }).then((res) => {
      const data = res?.data?.data ?? res?.data ?? res
      return data
    }),

  // 技能版本历史
  listDefinitionVersions: (pk) =>
    adminRequest('GET', `/api/admin/skills/definitions/${pk}/versions/`).then(unwrapAdminListData),

  // 创建技能定义
  createDefinition: (data) =>
    adminRequest('POST', '/api/admin/skills/definitions/', { data }),
  // 删除技能定义
  deleteDefinition: (pk) =>
    adminRequest('DELETE', `/api/admin/skills/definitions/${pk}/`),
}
