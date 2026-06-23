import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  getDramaProject,
  getDramaRoles,
  getProjectProgress,
  runRole,
  getEpisodeList,
} from '../../services/drama';
import DramaPresentation from '../../components/drama/presentation/DramaPresentation';

const DEPT_LABELS = {
  strategy: '战略选题部',
  worldbuilding: '世界构建部',
  plot_engine: '剧情引擎部',
  writing: '创作执行部',
  review: '评审质控部',
  polish: '修改润色部',
  production: '制作宣发部',
  ops: '合规总编室',
};

const TIER_CONFIG = {
  1: { label: '核心必需', badge: '必须', color: 'bg-blue-100 text-blue-700', dot: 'bg-blue-500', priority: '必执行' },
  2: { label: '优化推荐', badge: '推荐', color: 'bg-green-100 text-green-700', dot: 'bg-green-500', priority: '按需执行' },
  3: { label: '专项增强', badge: '可选', color: 'bg-gray-100 text-gray-600', dot: 'bg-gray-400', priority: '特需执行' },
};

const EXEC_STATUS = {
  success: { icon: '✅', label: '已完成', cls: 'text-green-600' },
  running: { icon: '⟳', label: '执行中', cls: 'text-blue-500 animate-pulse' },
  failed:  { icon: '❌', label: '失败',   cls: 'text-red-500' },
  pending: { icon: '○',  label: '待执行', cls: 'text-gray-400' },
};

/** 项目工作台 — 三层角色执行面板 */
export default function WorkspacePage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedRole, setSelectedRole] = useState(null);
  // 视图模式：tier（分层）| dept（分部门）| fast（只看核心）
  const [viewMode, setViewMode] = useState('tier');

  const { data: projectRes } = useQuery({
    queryKey: ['drama-project', projectId],
    queryFn: () => getDramaProject(projectId),
  });
  const project = projectRes?.id ? projectRes : projectRes?.data;

  const { data: progressRes } = useQuery({
    queryKey: ['drama-progress', projectId],
    queryFn: () => getProjectProgress(projectId),
    refetchInterval: (query) => {
      const roles = query.state.data?.roles || query.state.data?.data?.roles || [];
      const hasRunning = roles.some(
        (r) => r.execution?.status === 'running' || r.execution?.status === 'pending',
      );
      return hasRunning ? 2000 : 5000;
    },
  });
  const progress = progressRes?.roles ? progressRes : progressRes?.data;

  const { data: rolesRes } = useQuery({
    queryKey: ['drama-roles'],
    queryFn: getDramaRoles,
    staleTime: 5 * 60 * 1000,
  });
  const departments = rolesRes?.departments || rolesRes?.data?.departments || [];

  // 分集进度
  const { data: episodesRes } = useQuery({
    queryKey: ['drama-episodes', projectId],
    queryFn: () => getEpisodeList(projectId),
  });
  const episodeProgress = progress?.episode_progress;
  const completedEpisodes = episodesRes?.data?.completed_episodes || episodeProgress?.completed || 0;

  const runMut = useMutation({
    mutationFn: ({ projId, roleId }) => runRole(projId, roleId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['drama-progress', projectId] });
      const status = data?.status || data?.data?.status;
      if (status === 'running' || status === 'pending') {
        toast.success('已加入执行队列，正在生成…');
      } else if (data?.created_new_run === false) {
        toast.info('该角色正在执行中');
      }
    },
    onError: (err) => {
      toast.error(err?.message || '执行失败，请稍后重试');
    },
  });

  const completedSet = new Set(project?.completed_roles || []);

  // 角色执行状态映射
  const roleStatusMap = {};
  if (progress?.roles) {
    progress.roles.forEach((r) => { roleStatusMap[r.agent_id] = r; });
  }

  // 扁平化所有角色
  const allRoles = departments.flatMap((d) =>
    d.roles.map((r) => ({ ...r, dept_name: DEPT_LABELS[d.dept_code] || d.dept_name }))
  );

  // 按tier分组
  const rolesByTier = { 1: [], 2: [], 3: [] };
  allRoles.forEach((r) => {
    const tier = r.tier || (r.is_fast_track ? 1 : 3);
    (rolesByTier[tier] || rolesByTier[3]).push(r);
  });

  const handleRunRole = (roleId) => {
    runMut.mutate({ projId: projectId, roleId });
    setSelectedRole(roleId);
  };

  if (!project) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 左侧导航面板 */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
        {/* 项目信息 */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-2 mb-2">
            <button onClick={() => navigate('/drama')} className="text-gray-400 hover:text-gray-600 text-lg">←</button>
            <h2 className="font-semibold text-gray-900 text-sm truncate flex-1">{project.title}</h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
            <span>{project.total_episodes}集</span>
            <span>·</span>
            <span className={project.track_mode === 'fast' ? 'text-indigo-600' : 'text-purple-600'}>
              {project.track_mode === 'fast' ? '⚡快速通道' : '🎬专家通道'}
            </span>
            {progress?.current_stage_display && (
              <>
                <span>·</span>
                <span className="text-gray-600">{progress.current_stage_display}</span>
              </>
            )}
          </div>
          {/* 角色进度 */}
          <div className="mb-2">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>角色完成度</span>
              <span>{progress?.completion_rate || 0}%</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full">
              <div className="h-full bg-indigo-500 rounded-full transition-all" style={{ width: `${progress?.completion_rate || 0}%` }} />
            </div>
          </div>
          {/* 分集进度 */}
          {project.total_episodes > 0 && (
            <div>
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>集数完成</span>
                <span>{completedEpisodes}/{project.total_episodes}集</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full">
                <div
                  className="h-full bg-purple-400 rounded-full transition-all"
                  style={{ width: `${(completedEpisodes / project.total_episodes) * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* 视图切换 */}
        <div className="px-3 py-2 border-b border-gray-100 flex gap-1">
          {[
            { id: 'tier', label: '分层视图' },
            { id: 'dept', label: '部门视图' },
            { id: 'fast', label: '快速通道' },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setViewMode(m.id)}
              className={`flex-1 text-xs py-1.5 rounded-lg transition-colors ${
                viewMode === m.id
                  ? 'bg-indigo-100 text-indigo-700 font-medium'
                  : 'text-gray-500 hover:bg-gray-50'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* 角色列表 */}
        <div className="flex-1 overflow-y-auto">
          {viewMode === 'tier' && (
            <TierView roles={rolesByTier} completedSet={completedSet} roleStatusMap={roleStatusMap} selectedRole={selectedRole} onSelect={setSelectedRole} />
          )}
          {viewMode === 'dept' && (
            <DeptView departments={departments} completedSet={completedSet} roleStatusMap={roleStatusMap} selectedRole={selectedRole} onSelect={setSelectedRole} />
          )}
          {viewMode === 'fast' && (
            <FastTrackView roles={rolesByTier[1]} completedSet={completedSet} roleStatusMap={roleStatusMap} selectedRole={selectedRole} onSelect={setSelectedRole} />
          )}
        </div>

        {/* 底部操作 */}
        <div className="p-3 border-t border-gray-100 space-y-2">
          <button
            onClick={() => navigate(`/drama/scripts/${projectId}`)}
            className="w-full py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
          >
            📖 查看剧本（{completedEpisodes}集）
          </button>
          <button
            onClick={() => navigate(`/drama/scripts/${projectId}?tab=quality`)}
            className="w-full py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            📊 质量评分报告
          </button>
        </div>
      </aside>

      {/* 右侧详情区 */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="w-full min-h-full p-6 lg:p-8">
        {selectedRole ? (
          <RoleDetailPanel
            roleId={selectedRole}
            allRoles={allRoles}
            roleProgress={roleStatusMap[selectedRole]}
            onRun={handleRunRole}
            runLoading={runMut.isPending && runMut.variables?.roleId === selectedRole}
            completedSet={completedSet}
            project={project}
          />
        ) : (
          <WelcomePanel
            project={project}
            progress={progress}
            episodeProgress={episodeProgress}
            completedEpisodes={completedEpisodes}
            rolesByTier={rolesByTier}
            completedSet={completedSet}
            roleStatusMap={roleStatusMap}
            onSelectRole={setSelectedRole}
          />
        )}
        </div>
      </main>
    </div>
  );
}

// ─── 分层视图 ────────────────────────────────────────────────────────────────
function TierView({ roles, completedSet, roleStatusMap, selectedRole, onSelect }) {
  const [collapsed, setCollapsed] = useState({ 3: true });  // 专项层默认折叠

  return (
    <>
      {[1, 2, 3].map((tier) => {
        const tierRoles = roles[tier] || [];
        if (tierRoles.length === 0) return null;
        const cfg = TIER_CONFIG[tier];
        const completedCount = tierRoles.filter((r) => completedSet.has(r.agent_id)).length;
        const isCollapsed = collapsed[tier];

        return (
          <div key={tier} className="border-b border-gray-100 last:border-0">
            <button
              onClick={() => setCollapsed((c) => ({ ...c, [tier]: !c[tier] }))}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50"
            >
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                <span className="text-xs font-semibold text-gray-700">{cfg.label}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${cfg.color}`}>{cfg.priority}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <span>{completedCount}/{tierRoles.length}</span>
                <span>{isCollapsed ? '▸' : '▾'}</span>
              </div>
            </button>

            {!isCollapsed && tierRoles.map((role) => (
              <RoleItem
                key={role.agent_id}
                role={role}
                isCompleted={completedSet.has(role.agent_id)}
                execution={roleStatusMap[role.agent_id]?.execution}
                isSelected={selectedRole === role.agent_id}
                onSelect={onSelect}
                showDeptTag
              />
            ))}
          </div>
        );
      })}
    </>
  );
}

// ─── 部门视图 ────────────────────────────────────────────────────────────────
function DeptView({ departments, completedSet, roleStatusMap, selectedRole, onSelect }) {
  return (
    <>
      {departments.map((dept) => (
        <div key={dept.dept_code} className="py-1">
          <div className="px-4 py-1.5 text-xs font-medium text-gray-400 uppercase tracking-wide">
            {dept.dept_name}
          </div>
          {dept.roles.map((role) => (
            <RoleItem
              key={role.agent_id}
              role={role}
              isCompleted={completedSet.has(role.agent_id)}
              execution={roleStatusMap[role.agent_id]?.execution}
              isSelected={selectedRole === role.agent_id}
              onSelect={onSelect}
            />
          ))}
        </div>
      ))}
    </>
  );
}

// ─── 快速通道视图 ─────────────────────────────────────────────────────────────
function FastTrackView({ roles, completedSet, roleStatusMap, selectedRole, onSelect }) {
  return (
    <div className="py-2">
      <div className="px-4 py-1.5 text-xs font-medium text-blue-500 uppercase tracking-wide">
        ⚡ 快速通道 · 8个核心角色
      </div>
      {(roles || []).map((role) => (
        <RoleItem
          key={role.agent_id}
          role={role}
          isCompleted={completedSet.has(role.agent_id)}
          execution={roleStatusMap[role.agent_id]?.execution}
          isSelected={selectedRole === role.agent_id}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

// ─── 单个角色条目 ─────────────────────────────────────────────────────────────
function RoleItem({ role, isCompleted, execution, isSelected, onSelect, showDeptTag }) {
  const execStatus = execution?.status ?? 'pending';
  const statusCfg = EXEC_STATUS[execStatus] || EXEC_STATUS.pending;
  const tier = role.tier || (role.is_fast_track ? 1 : 3);
  const tierCfg = TIER_CONFIG[tier];

  return (
    <button
      onClick={() => onSelect(role.agent_id)}
      className={`w-full flex items-center gap-2 px-4 py-2 text-left hover:bg-gray-50 transition-colors ${
        isSelected ? 'bg-indigo-50 border-r-2 border-indigo-500' : ''
      }`}
    >
      <span className={`text-xs w-4 text-center ${statusCfg.cls}`}>{statusCfg.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1">
          <span className="text-sm text-gray-800 truncate">{role.name_zh}</span>
          {tier === 1 && <span className="text-xs text-blue-400">⚡</span>}
        </div>
        {showDeptTag && role.dept_name && (
          <span className="text-xs text-gray-400">{role.dept_name}</span>
        )}
      </div>
      <span className={`text-xs px-1.5 py-0.5 rounded hidden group-hover:block ${tierCfg.color}`}>
        {tierCfg.badge}
      </span>
    </button>
  );
}

// ─── 欢迎面板 ────────────────────────────────────────────────────────────────
function WelcomePanel({
  project,
  progress,
  completedEpisodes,
  rolesByTier,
  completedSet,
  roleStatusMap,
  onSelectRole,
}) {
  const completionRate = progress?.completion_rate || 0;
  const totalEp = project?.total_episodes || 0;
  const coreRoles = rolesByTier[1] || [];
  const recommendRoles = rolesByTier[2] || [];
  const coreDone = coreRoles.filter((r) => completedSet.has(r.agent_id)).length;

  return (
    <div className="w-full space-y-6">
      {/* 顶部概览 */}
      <div className="relative overflow-hidden rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 p-6 lg:p-8 text-white shadow-sm">
        <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute -bottom-20 right-1/3 h-40 w-40 rounded-full bg-purple-400/20 blur-3xl" />
        <div className="relative">
          <p className="text-indigo-200 text-sm mb-1">短剧创作工作台</p>
          <h2 className="text-2xl lg:text-3xl font-bold mb-2">{project?.title}</h2>
          <p className="text-indigo-100 text-sm mb-6">
            {totalEp} 集 · {project?.track_mode === 'fast' ? '⚡ 快速通道' : '🎬 专家通道'}
            {project?.target_platform ? ` · ${project.target_platform}` : ''}
            {progress?.current_stage_display ? ` · ${progress.current_stage_display}` : ''}
          </p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
            <HeroStat label="角色完成度" value={`${completionRate}%`} sub={`${coreDone}/${coreRoles.length} 核心角色`} />
            <HeroStat label="已生成集数" value={`${completedEpisodes}/${totalEp}`} sub="剧本进度" />
            <HeroStat label="质量等级" value={project?.quality_scores?.grade || '—'} sub="综合评分" />
            <HeroStat
              label="当前通道"
              value={project?.track_mode === 'fast' ? '快速' : '专家'}
              sub={`${(rolesByTier[1]?.length || 0) + (rolesByTier[2]?.length || 0) + (rolesByTier[3]?.length || 0)} 个可用角色`}
            />
          </div>
        </div>
      </div>

      {totalEp >= 50 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          <strong>📌 大体量剧本建议：</strong>此项目共 {totalEp} 集，建议采用
          <strong> 分批生成策略</strong>（每批 5–10 集）：大纲先行 → 分批执行剧本执笔师 → 每批完成后质检 → 低于 75 分自动重写。
        </div>
      )}

      <div className="grid lg:grid-cols-5 gap-6">
        {/* 如何开始 */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4">如何开始</h3>
          <div className="space-y-4">
            <Step n={1} title="从左侧选择「核心必需」层的角色" desc="蓝色角色是所有项目必须执行的，按顺序执行效果最佳" />
            <Step n={2} title="执行角色生成内容" desc="查看输入依赖与输出说明，确认依赖满足后点击执行" />
            <Step n={3} title="分批生成剧本（推荐 5 集/批）" desc="剧本执笔师支持指定集数范围，完成后立即质检" />
            <Step n={4} title="应用修改建议" desc="审稿官与对白专家的建议可一键应用到原始剧本" />
          </div>
        </div>

        {/* 核心角色进度 */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-gray-900">核心执行路径</h3>
            <span className="text-xs text-gray-500">{coreDone}/{coreRoles.length} 已完成</span>
          </div>
          <div className="space-y-2">
            {coreRoles.map((role, idx) => {
              const exec = roleStatusMap[role.agent_id]?.execution;
              const execStatus = exec?.status ?? 'pending';
              const statusCfg = EXEC_STATUS[execStatus] || EXEC_STATUS.pending;
              return (
                <button
                  key={role.agent_id}
                  type="button"
                  onClick={() => onSelectRole(role.agent_id)}
                  className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:border-indigo-200 hover:bg-indigo-50/50 transition-colors text-left group"
                >
                  <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 text-xs font-medium flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <span className={`flex-shrink-0 text-sm ${statusCfg.cls}`}>{statusCfg.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-800 truncate">{role.name_zh}</div>
                    {role.dept_name && (
                      <div className="text-xs text-gray-400 truncate">{role.dept_name}</div>
                    )}
                  </div>
                  <span className="text-xs text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                    进入 →
                  </span>
                </button>
              );
            })}
          </div>

          {recommendRoles.length > 0 && (
            <>
              <h4 className="text-sm font-medium text-gray-500 mt-6 mb-3">优化推荐（按需执行）</h4>
              <div className="grid sm:grid-cols-2 gap-2">
                {recommendRoles.slice(0, 6).map((role) => {
                  const isDone = completedSet.has(role.agent_id);
                  return (
                    <button
                      key={role.agent_id}
                      type="button"
                      onClick={() => onSelectRole(role.agent_id)}
                      className="flex items-center gap-2 p-2.5 rounded-lg border border-gray-100 hover:border-green-200 hover:bg-green-50/50 transition-colors text-left text-sm"
                    >
                      <span className={isDone ? 'text-green-600' : 'text-gray-300'}>{isDone ? '✅' : '○'}</span>
                      <span className="truncate text-gray-700">{role.name_zh}</span>
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function HeroStat({ label, value, sub }) {
  return (
    <div className="rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 px-4 py-3">
      <div className="text-xl lg:text-2xl font-bold">{value}</div>
      <div className="text-xs text-indigo-100 mt-0.5">{label}</div>
      {sub && <div className="text-[10px] text-indigo-200/80 mt-1">{sub}</div>}
    </div>
  );
}

function Step({ n, title, desc }) {
  return (
    <div className="flex gap-3">
      <div className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
        {n}
      </div>
      <div>
        <div className="text-sm font-medium text-gray-800">{title}</div>
        <div className="text-xs text-gray-500 mt-0.5">{desc}</div>
      </div>
    </div>
  );
}

// ─── 角色详情面板 ─────────────────────────────────────────────────────────────
function RoleDetailPanel({
  roleId,
  allRoles,
  roleProgress,
  onRun,
  runLoading,
  completedSet,
  project,
}) {
  const role = allRoles.find((r) => r.agent_id === roleId);
  const [episodeRange, setEpisodeRange] = useState('1-5');

  if (!role) return null;

  const isCompleted = completedSet.has(roleId);
  const tier = role.tier || (role.is_fast_track ? 1 : 3);
  const tierCfg = TIER_CONFIG[tier];
  const isScriptWriter = roleId === 'drama.script-writer' || roleId === 'drama.dialogue-expert';
  const isBatchRole = isScriptWriter && (project?.total_episodes || 0) > 1;

  const execution = roleProgress?.execution;
  const execStatus = execution?.status;
  const statusCfg = execStatus ? EXEC_STATUS[execStatus] : null;
  const isRunning = execStatus === 'running' || execStatus === 'pending' || runLoading;
  const outputArtifacts = execution?.output_artifacts || {};
  const outputViews = execution?.output_views || {};
  const outputKeys = Object.keys(outputViews).length
    ? Object.keys(outputViews)
    : Object.keys(outputArtifacts);

  const canShowOutput = !isRunning && execStatus === 'success' && outputKeys.length > 0;
  const showEmptyDone = !isRunning && execStatus === 'success' && outputKeys.length === 0;
  const showIdle = !isRunning && !execStatus;

  return (
    <div className="w-full flex flex-col min-h-[calc(100vh-4rem)]">
      {/* 顶部：角色信息与操作 */}
      <div className="rounded-2xl border border-gray-200/80 bg-white shadow-sm mb-4 overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-slate-50/80 to-white">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h2 className="text-lg font-bold text-gray-900">{role.name_zh}</h2>
              <span className={`text-xs px-2 py-0.5 rounded-full ${tierCfg.color}`}>{tierCfg.label}</span>
              {role.is_fast_track && (
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">⚡ 快速通道</span>
              )}
              {isCompleted && (
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">✅ 已完成</span>
              )}
            </div>
            <p className="text-sm text-gray-500 line-clamp-2">{role.description}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => onRun(roleId)}
              disabled={runLoading}
              className="px-5 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
            >
              {runLoading ? (
                <><span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />执行中...</>
              ) : (
                `🚀 ${isCompleted ? '重新执行' : '执行此角色'}`
              )}
            </button>
            <a
              href="/admin/drama-models"
              className="px-3 py-2.5 border border-gray-200 text-gray-600 text-sm rounded-xl hover:bg-gray-50"
              title="配置模型"
            >
              ⚙️
            </a>
          </div>
        </div>

        <div className="px-5 py-4 flex flex-wrap gap-3">
          {isBatchRole && (
            <div className="w-full p-3 bg-purple-50 rounded-xl border border-purple-100">
              <p className="text-xs font-medium text-purple-700 mb-2">
                📌 分集生成（共 {project.total_episodes} 集，建议每批 5 集）
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <input
                  type="text"
                  value={episodeRange}
                  onChange={(e) => setEpisodeRange(e.target.value)}
                  placeholder="例：1-5"
                  className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm w-28 bg-white"
                />
                <div className="flex flex-wrap gap-1.5">
                  {['1-5', '6-10', '11-15', '16-20'].filter((r) => {
                    const end = parseInt(r.split('-')[1], 10)
                    return end <= (project.total_episodes || 0)
                  }).map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setEpisodeRange(r)}
                      className={`text-xs px-2.5 py-1 rounded-lg transition-colors ${
                        episodeRange === r
                          ? 'bg-purple-600 text-white'
                          : 'bg-white border border-gray-200 text-gray-600 hover:border-purple-300'
                      }`}
                    >
                      {r} 集
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="flex-1 min-w-[220px] rounded-xl bg-gray-50/80 border border-gray-100 px-3 py-3">
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-2">输入依赖</h4>
            {role.input_contract?.required_artifacts?.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {role.input_contract.required_artifacts.map((a) => (
                  <span key={a} className="text-xs px-2 py-0.5 bg-red-50 text-red-700 rounded-md border border-red-100">{a}</span>
                ))}
              </div>
            ) : role.input_contract?.optional_artifacts?.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {role.input_contract.optional_artifacts.map((a) => (
                  <span key={a} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-md">{a}</span>
                ))}
              </div>
            ) : (
              <span className="text-xs text-gray-400">无依赖，可直接执行</span>
            )}
          </div>

          <div className="flex-1 min-w-[220px] rounded-xl bg-gray-50/80 border border-gray-100 px-3 py-3">
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-2">输出产物</h4>
            <div className="flex flex-wrap gap-1.5">
              {role.output_contract?.artifacts?.map((a) => (
                <span key={a} className="text-xs px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-md border border-emerald-100">{a}</span>
              ))}
            </div>
          </div>

          <div className="flex-1 min-w-[220px] rounded-xl bg-gray-50/80 border border-gray-100 px-3 py-3">
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-2">当前模型</h4>
            <p className="text-sm text-gray-700 truncate">{role.current_model || '跟随全局配置'}</p>
          </div>
        </div>

        {tier === 3 && (
          <div className="px-5 pb-4">
            <p className="text-xs text-gray-500 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
              💡 专项增强角色：完成核心步骤后按需使用，可显著提升特定方面质量。
            </p>
          </div>
        )}
      </div>

      {/* 执行输出 — 全宽占满剩余高度 */}
      <div className="flex-1 flex flex-col rounded-2xl border border-gray-200/80 bg-white shadow-sm min-h-[480px]">
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-gray-100 bg-gray-50/50 shrink-0">
          <h3 className="text-sm font-semibold text-gray-800">执行输出</h3>
          <div className="flex items-center gap-3">
            {!isRunning && execution?.elapsed_seconds != null && (
              <span className="text-xs text-gray-400 tabular-nums">
                耗时 {execution.elapsed_seconds.toFixed(1)}s
                {execution.total_tokens ? ` · ${execution.total_tokens} tokens` : ''}
              </span>
            )}
            {statusCfg && (
              <span className={`text-xs px-2.5 py-1 rounded-lg font-medium ${
                execStatus === 'success' ? 'bg-green-100 text-green-700'
                : execStatus === 'failed' ? 'bg-red-100 text-red-700'
                : execStatus === 'running' ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600'
              }`}>
                {statusCfg.icon} {statusCfg.label}
              </span>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-5 w-full">
          {isRunning && (
            <div className="flex flex-col items-center justify-center py-20 text-blue-600">
              <span className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mb-4" />
              <p className="text-sm font-medium">AI 正在生成内容，请稍候…</p>
            </div>
          )}

          {!isRunning && execStatus === 'failed' && (
            <div className="rounded-xl bg-red-50 border border-red-100 p-5 text-sm text-red-700 max-w-2xl">
              <p className="font-semibold mb-2">执行失败</p>
              <p className="text-red-600 whitespace-pre-wrap leading-relaxed">{execution?.error_message || '未知错误'}</p>
            </div>
          )}

          {canShowOutput && (
            <DramaPresentation views={outputViews} rawArtifacts={outputArtifacts} />
          )}

          {showIdle && (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <p className="text-4xl mb-3 opacity-30">📝</p>
              <p className="text-sm">点击上方「执行此角色」开始生成内容</p>
            </div>
          )}

          {showEmptyDone && (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <p className="text-sm">执行已完成，暂无输出产物</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
