/** 子技能术语：API 响应以 skill_id / sub_skill_id 为准 */

/** 解析 Admin API 返回的废弃字段说明（请求体别名） */
export function readDeprecatedFields(payload) {
  return payload?.api_meta?.deprecated_fields || {}
}

export function resolveSkillId(row) {
  if (!row || typeof row !== 'object') return ''
  return String(row.skill_id || row.sub_skill_id || '').trim()
}

/** 规范化子技能 ID 字段（仅输出 skill_id） */
export function aliasSkillFields(row) {
  if (!row || typeof row !== 'object') return row
  const skill_id = resolveSkillId(row)
  if (!skill_id) return row
  return {
    ...row,
    skill_id,
  }
}
