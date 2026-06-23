/** C 端「我的作品」状态展示 — Drama 阶段对齐 */

export const DRAMA_STAGE_LABELS = {
  strategy: '战略选题',
  worldbuilding: '世界构建',
  plot_design: '剧情设计',
  writing: '剧本创作',
  review: '评审质控',
  polish: '修改润色',
  production: '制作宣发',
  compliance: '合规审查',
  delivered: '已交付',
  ready: '可交付',
}

/** 将 API status 规范为卡片用 key */
export function normalizeWorkStatus(raw, work = {}) {
  const progress = Number(work.progress_percent) || 0
  if (raw === 'running') return 'generating'
  if (raw === 'awaiting') return 'awaiting'
  if (raw === 'failed') return 'failed'
  if (raw === 'completed') return 'completed'
  if (raw === 'pending') {
    if (progress > 0 || work.has_scripts) {
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
  } else if (key === 'generating') {
    const stage = work.current_stage || work.drama?.current_stage
    const stageLabel = stage ? DRAMA_STAGE_LABELS[stage] : ''
    if (stageLabel) hint = stageLabel
  } else if (key === 'draft') {
    hint = '点击进入 Drama 工作台开始创作'
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
