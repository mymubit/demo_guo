/** C 端「我的作品」状态展示 — 与后台 Project.status 对齐 */

export const FUSION_STATUS_LABELS = {
  draft: '立项中',
  planning: '策划中',
  writing: '撰写中',
  reviewing: '质检中',
  scoring: '评分中',
  ready: '可发布',
  blocked: '需修改',
}

/** 将 API status 规范为卡片用 key */
export function normalizeWorkStatus(raw, work = {}) {
  const progress = Number(work.progress_percent) || 0
  if (raw === 'running') return 'generating'
  if (raw === 'awaiting') return 'awaiting'
  if (raw === 'failed') return 'failed'
  if (raw === 'completed') return 'completed'
  if (raw === 'pending') {
    if (work.pipeline_mode === 'workspace' && (progress > 0 || work.has_scripts)) {
      return 'generating'
    }
    return 'draft'
  }
  return raw || 'draft'
}

const STATUS_META = {
  completed: {
    label: '已完成',
    color: '#68d391',
    bg: 'rgba(104, 211, 145, 0.15)',
    hint: '',
    cta: '查看详情',
  },
  generating: {
    label: '创作中',
    color: '#f6ad55',
    bg: 'rgba(246, 173, 85, 0.15)',
    hint: '',
    cta: '继续创作',
    spin: true,
  },
  awaiting: {
    label: '待确认',
    color: '#63b3ed',
    bg: 'rgba(99, 179, 237, 0.15)',
    hint: '某一步已完成，等你确认后继续',
    cta: '去确认',
  },
  draft: {
    label: '草稿',
    color: '#a0aec0',
    bg: 'rgba(160, 174, 192, 0.15)',
    hint: '已保存项目，尚未开始 AI 生成',
    cta: '继续填写',
  },
  failed: {
    label: '创作失败',
    color: '#fc8181',
    bg: 'rgba(252, 129, 129, 0.15)',
    hint: '生成中断，可进入工作台重试',
    cta: '查看原因',
  },
}

export function getWorkStatusMeta(statusKey, work = {}) {
  const key = normalizeWorkStatus(statusKey, work)
  const base = STATUS_META[key] || STATUS_META.draft
  const progress = Number(work.progress_percent) || 0
  let hint = base.hint

  if (key === 'generating' && progress > 0 && progress < 100) {
    hint = `已完成约 ${progress}%`
  } else if (key === 'generating' && work.fusion_status) {
    const fusionLabel = FUSION_STATUS_LABELS[work.fusion_status]
    if (fusionLabel) hint = fusionLabel
  } else if (key === 'draft' && work.pipeline_mode === 'workspace') {
    hint = '点击进入工作台，从步骤 1 开始创作'
  }

  return { ...base, key, progress, hint }
}

export const WORK_FILTER_OPTIONS = [
  { key: 'all', name: '全部作品', color: '#f6d365' },
  { key: 'completed', name: '已完成', color: '#68d391' },
  { key: 'generating', name: '创作中', color: '#f6ad55' },
  { key: 'awaiting', name: '待确认', color: '#63b3ed' },
  { key: 'draft', name: '草稿', color: '#a0aec0' },
  { key: 'failed', name: '失败', color: '#fc8181' },
]
