/** 角色 agent_id → 中文名（与 drama-skills/registry.yaml 对齐；API role_label 优先）。 */
export const ROLE_LABEL_ZH: Record<string, string> = {
  'drama.topic-director': '选题定调官',
  'drama.story-bible': '剧本蓝图官',
  'drama.episode-designer': '分集设计官',
  'drama.script-writer': '剧本正文官',
  'drama.script-scorer': '剧本评分官',
  'drama.compliance-guard': '合规审查官',
  'drama.revision-master': '剧本修复官',
  'drama.delivery-tool': '宣发交付工具',
  'admin.connectivity-test': '连通测试',
}

export const ROLE_FILTER_OPTIONS: Array<{ value: string; label: string }> = [
  ...Object.entries(ROLE_LABEL_ZH).map(([value, label]) => ({ value, label })),
]

export function formatRoleLabel(
  role: string | null | undefined,
  roleLabel?: string | null,
): string {
  if (roleLabel?.trim()) return roleLabel.trim()
  if (!role) return '—'
  return ROLE_LABEL_ZH[role] || role.replace(/^drama\./, '').replace(/^admin\./, '')
}
