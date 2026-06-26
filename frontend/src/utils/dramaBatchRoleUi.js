/** 分批执行角色的 UI 配置与按钮文案（与情节架构师一致） */

import { countDisplayableOutlineStages } from '../utils/outlineStructure';

export const BATCH_RANGE_ROLES = [
  'drama.script-writer',
  'drama.polish-master',
  'drama.narrative-engineer',
  'drama.production-pack',
  'drama.plot-architect',
];

/** 支持「全剧结构 / 分集」分离的分批角色 */
export const STRUCTURE_BATCH_ROLES = {
  'drama.plot-architect': {
    progressKey: 'outline',
    structureButtonLabel: '生成全剧结构',
    blobMode: 'structure_only',
  },
  'drama.narrative-engineer': {
    progressKey: 'narrative',
    structureButtonLabel: '生成全剧叙事框架',
    blobMode: 'structure_only',
  },
};

/** roleId -> 进度对象 + 默认 batchSize */
export const BATCH_ROLE_PROGRESS = {
  'drama.plot-architect': { progressKey: 'outline', defaultBatchSize: 10 },
  'drama.script-writer': { progressKey: 'script', defaultBatchSize: 5 },
  'drama.polish-master': { progressKey: 'polish', defaultBatchSize: 5 },
  'drama.narrative-engineer': { progressKey: 'narrative', defaultBatchSize: 5 },
  'drama.production-pack': { progressKey: 'script', defaultBatchSize: 5 },
};

export function getBatchProgressForRole(roleId, batchProgress) {
  const cfg = BATCH_ROLE_PROGRESS[roleId];
  if (!cfg || !batchProgress) return null;
  return batchProgress[cfg.progressKey] || null;
}

export function resolveDefaultEpisodeRange(roleId, projectEpisodeCount, batchProgress) {
  const prog = getBatchProgressForRole(roleId, batchProgress);
  const cfg = BATCH_ROLE_PROGRESS[roleId];
  const batchSize = prog?.batch_size || cfg?.defaultBatchSize || 5;
  if (prog?.suggested_range) return prog.suggested_range;
  if (roleId === 'drama.plot-architect') return '1-10';
  const end = Math.min(batchSize, projectEpisodeCount || batchSize);
  return `1-${end}`;
}

/**
 * 执行按钮文案：首次 → 开始/执行范围；部分完成 → 继续生成；否则 → 重新执行
 */
export function resolveRunKindFromParams(params = {}) {
  if (params.outline_mode === 'structure_only' || params.blob_mode === 'structure_only') {
    return 'structure';
  }
  if (params.episode_range) return 'episodes';
  return 'full';
}

export function resolveExecuteButtonLabel({
  runLoading,
  isAgentRunning,
  runKind,
  hasExecutedBefore,
  isBatchRole,
  episodeRange,
  roleProgress,
}) {
  const batchBusy = (runLoading || isAgentRunning) && runKind === 'episodes';
  if (batchBusy) return '分集生成中…';
  if (runLoading && runKind === 'episodes') return '提交中…';
  if (!hasExecutedBefore) {
    if (isBatchRole && episodeRange) return `执行 ${episodeRange} 集`;
    return '开始执行';
  }
  const generated = roleProgress?.generated ?? 0;
  const isComplete = Boolean(roleProgress?.is_complete);
  if (isBatchRole && generated > 0 && !isComplete && episodeRange) {
    return `继续生成 ${episodeRange} 集`;
  }
  if (isBatchRole && episodeRange) return `重新执行 ${episodeRange} 集`;
  return '重新执行';
}

export function resolveRoleCompletedBadge(roleId, batchProgress, completedSet) {
  const prog = getBatchProgressForRole(roleId, batchProgress);
  if (prog) return Boolean(prog.is_complete);
  return completedSet?.has(roleId) ?? false;
}

export function shouldShowStructureButton(roleId, { batchProgress, rawArtifact, outputView } = {}) {
  const cfg = STRUCTURE_BATCH_ROLES[roleId];
  if (!cfg) return false;
  if (roleId === 'drama.plot-architect') {
    return countDisplayableOutlineStages(rawArtifact, outputView) === 0;
  }
  return !batchProgress?.[cfg.progressKey]?.has_structure;
}
