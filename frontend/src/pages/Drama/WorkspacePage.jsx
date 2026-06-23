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
  1: { label: '核心必需', badge: '必须', color: 'bg-blue-100 text-blue-700', dot: 'bg-blue-500', priority: '必执行', desc: '8个快速通道角色，所有项目都要执行' },
  2: { label: '增强复合', badge: '增强', color: 'bg-purple-100 text-purple-700', dot: 'bg-purple-500', priority: '按需执行', desc: '4个复合角色，每个整合多项专业能力' },
  3: { label: '专项', badge: '专项', color: 'bg-gray-100 text-gray-500', dot: 'bg-gray-300', priority: '特需', desc: '已整合进复合角色，后台自动调用' },
};

const PLATFORM_LABELS = {
  douyin: '抖音',
  kuaishou: '快手',
  weixin: '微信小程序',
  all: '通用',
};

function sortByWorkspaceOrder(roles) {
  return [...roles].sort(
    (a, b) => (a.workspace_order ?? 999) - (b.workspace_order ?? 999),
  );
}

function formatPlatform(platform) {
  return PLATFORM_LABELS[platform] || platform || '';
}

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
  const [execFeedback, setExecFeedback] = useState(null);

  const { data: projectRes } = useQuery({
    queryKey: ['drama-project', projectId],
    queryFn: () => getDramaProject(projectId),
    enabled: Boolean(projectId && projectId !== 'undefined'),
  });
  const project = projectRes?.data ?? projectRes;

  const { data: progressRes } = useQuery({
    queryKey: ['drama-progress', projectId],
    queryFn: () => getProjectProgress(projectId),
    enabled: Boolean(projectId && projectId !== 'undefined'),
    refetchInterval: (query) => {
      const roles = query.state.data?.roles || [];
      return roles.some((r) => r.execution?.status === 'running') ? 2000 : 5000;
    },
  });
  const progress = progressRes?.data ?? progressRes;

  const { data: rolesRes } = useQuery({
    queryKey: ['drama-roles'],
    queryFn: getDramaRoles,
    staleTime: 60 * 1000,
    refetchOnMount: 'always',
  });
  const departments = rolesRes?.departments || rolesRes?.data?.departments || [];

  // 分集进度
  const { data: episodesRes } = useQuery({
    queryKey: ['drama-episodes', projectId],
    queryFn: () => getEpisodeList(projectId),
    enabled: Boolean(projectId && projectId !== 'undefined'),
  });
  const episodeProgress = progress?.episode_progress;
  const completedEpisodes = episodesRes?.data?.completed_episodes || episodeProgress?.completed || 0;

  const runMut = useMutation({
    mutationFn: ({ projId, roleId, options = {} }) => runRole(projId, roleId, options),
    onSuccess: (res) => {
      queryClient.invalidateQueries(['drama-progress', projectId]);
      queryClient.invalidateQueries(['drama-episodes', projectId]);
      queryClient.invalidateQueries(['drama-project', projectId]);
      const payload = res?.data ?? res;
      const roleName = payload?.role_name || '角色';
      const scope = payload?.scope || '已提交执行';
      const tip = payload?.is_new === false ? '（已有进行中的任务）' : '';
      toast.success(`${roleName}：${scope}${tip}`);
      setExecFeedback(`✅ ${roleName} — ${scope}${tip}`);
      setTimeout(() => setExecFeedback(null), 5000);
    },
    onError: (err) => {
      const message = err?.message || '未知错误';
      toast.error(`执行失败：${message}`);
      setExecFeedback(`❌ 执行失败：${message}`);
      setTimeout(() => setExecFeedback(null), 6000);
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

  // 按 tier 分组并排序
  const rolesByTier = { 1: [], 2: [], 3: [] };
  sortByWorkspaceOrder(allRoles).forEach((r) => {
    const tier = r.tier || (r.is_fast_track ? 1 : 2);
    (rolesByTier[tier] || rolesByTier[2]).push(r);
  });

  const handleRunRole = (roleId, options = {}) => {
    runMut.mutate({ projId: projectId, roleId, options });
    setSelectedRole(roleId);
  };

  if (!projectId || projectId === 'undefined') {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-gray-500">
        <p>无效的项目地址，请从创作中心重新进入。</p>
        <button
          type="button"
          onClick={() => navigate('/drama')}
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          返回创作中心
        </button>
      </div>
    );
  }

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
            <span>{project.episode_count}集</span>
            <span>·</span>
            <span className={project.track_mode === 'fast' ? 'text-indigo-600' : 'text-purple-600'}>
              {project.track_mode === 'fast' ? '⚡快速通道' : '🎬专家通道'}
            </span>
            {progress?.drama_stage_display && (
              <>
                <span>·</span>
                <span className="text-gray-600">{progress.drama_stage_display}</span>
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
          {project.episode_count > 0 && (
            <div>
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>集数完成</span>
                <span>{completedEpisodes}/{project.episode_count}集</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full">
                <div
                  className="h-full bg-purple-400 rounded-full transition-all"
                  style={{ width: `${(completedEpisodes / project.episode_count) * 100}%` }}
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
      <main className="flex-1 overflow-y-auto p-6">
        {/* 执行反馈 Toast */}
        {execFeedback && (
          <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all ${
            execFeedback.startsWith('✅') ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
          }`}>
            {execFeedback}
          </div>
        )}
        {selectedRole ? (
          <RoleDetailPanel
            roleId={selectedRole}
            allRoles={allRoles}
            roleProgress={roleStatusMap[selectedRole]}
            onRun={handleRunRole}
            runLoading={runMut.isPending && runMut.variables?.roleId === selectedRole}
            completedSet={completedSet}
            project={project}
            lastExecResult={runMut.data?.data ?? runMut.data}
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
  const tier = role.tier || (role.is_fast_track ? 1 : 2);
  const tierCfg = TIER_CONFIG[tier] || TIER_CONFIG[2];

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
          {role.is_composite && <span className="text-xs text-purple-400">◈</span>}
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
  const totalEp = project?.episode_count || 0;
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
            {project?.target_platform ? ` · ${formatPlatform(project.target_platform)}` : ''}
            {progress?.drama_stage_display ? ` · ${progress.drama_stage_display}` : ''}
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
            <Step n={4} title="应用修改建议" desc="审稿官与精修大师的建议可一键应用到原始剧本" />
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
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">创作流程（重构后）</h3>
        <div className="space-y-2">
          <Step n={1} title="执行8个核心角色（⚡蓝色）" desc="按顺序：立项→世界观→人设→大纲→剧本→审稿→质量→合规。这8个角色已深度整合山音方法论。" />
          <Step n={2} title="分批生成剧本（每批5集）" desc="剧本执笔师严格执行：首集900-1100字，其余700-900字，台词≥35%，场景≤3个。" />
          <Step n={3} title="按需选择复合角色（◈紫色）" desc="4个复合角色各自整合了5-6项专业能力：市场分析师/叙事工程师/精修大师/制作发行师。" />
          <Step n={4} title="查看质量报告并应用修改" desc="质量报告包含：雷达图+情绪曲线+8维扣分详情+汇总报告。建议可一键应用。" />
        </div>

        <div className="mt-4 p-3 bg-blue-50 rounded-lg text-xs text-blue-700 border border-blue-100">
          <strong>角色架构说明：</strong>12 个可见角色 = 8 核心 + 4 复合增强。
          左侧「增强复合」分组中可找到市场分析师、叙事工程师、精修大师、制作发行师。
        </div>
      </div>

      {recommendRoles.length > 0 && (
        <div className="bg-white rounded-xl border border-purple-100 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-gray-900">增强复合角色（按需执行）</h3>
            <span className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded-full">◈ 4 个</span>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {recommendRoles.map((role) => (
              <button
                key={role.agent_id}
                type="button"
                onClick={() => onSelectRole(role.agent_id)}
                className="text-left p-4 rounded-xl border border-purple-100 hover:border-purple-300 hover:bg-purple-50/50 transition-colors"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-purple-500 text-sm">◈</span>
                  <span className="font-medium text-gray-900">{role.name_zh}</span>
                </div>
                <p className="text-xs text-gray-500 line-clamp-2">{role.description}</p>
              </button>
            ))}
          </div>
        </div>
      )}
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
  lastExecResult,
}) {
  const role = allRoles.find((r) => r.agent_id === roleId);
  const [episodeRange, setEpisodeRange] = useState('1-5');

  if (!role) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        未找到角色数据，请刷新页面后重试。
      </div>
    );
  }

  const isCompleted = completedSet.has(roleId);
  const tier = role.tier || (role.is_fast_track ? 1 : 2);
  const tierCfg = TIER_CONFIG[tier] || TIER_CONFIG[2];
  const execution = roleProgress?.execution;
  const execStatus = runLoading
    ? 'running'
    : (execution?.status ?? (isCompleted ? 'success' : 'pending'));
  const isRunning = execStatus === 'running';
  const outputViews = execution?.output_views ?? {};
  const outputKeys = Object.keys(outputViews).filter(Boolean);

  const RANGE_ROLES = [
    'drama.script-writer',
    'drama.polish-master',
    'drama.narrative-engineer',
    'drama.production-pack',
  ];
  const COUNT_ROLES = ['drama.plot-architect'];
  const isBatchRole =
    (RANGE_ROLES.includes(roleId) || COUNT_ROLES.includes(roleId))
    && (project?.episode_count || 0) > 1;
  const isCountMode = COUNT_ROLES.includes(roleId);

  const handleExecute = () => {
    onRun(roleId, {
      episode_range: isBatchRole && !isCountMode ? episodeRange : undefined,
      episode_count: isCountMode ? project.episode_count : undefined,
    });
  };

  return (
    <div className="w-full flex flex-col gap-4 min-h-[calc(100vh-4rem)]">
      <div className="rounded-2xl border border-gray-200/80 bg-white shadow-sm overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-slate-50/80 to-white">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h2 className="text-lg font-bold text-gray-900">{role.name_zh}</h2>
              <span className={`text-xs px-2 py-0.5 rounded-full ${tierCfg.color}`}>{tierCfg.label}</span>
              {role.is_fast_track && (
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">⚡ 快速通道</span>
              )}
              {role.is_composite && (
                <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">◈ 复合增强</span>
              )}
              {isCompleted && (
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">✅ 已完成</span>
              )}
            </div>
            <p className="text-sm text-gray-500">{role.description}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleExecute}
              disabled={runLoading}
              className="px-5 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
            >
              {runLoading ? (
                <>
                  <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  执行中...
                </>
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

        <div className="px-5 py-4 space-y-4">
          {isBatchRole && (
            <div className="p-3 bg-purple-50 rounded-lg border border-purple-100">
              {isCountMode ? (
                <>
                  <p className="text-xs font-medium text-purple-700 mb-2">
                    📋 大纲生成配置（将生成全部 {project.episode_count} 集分集大纲）
                  </p>
                  <p className="text-xs text-purple-500">
                    分集大纲一次性生成所有集，建议先生成大纲再按需分批写剧本。
                  </p>
                </>
              ) : (
                <>
                  <p className="text-xs font-medium text-purple-700 mb-2">
                    📌 分集生成配置（共 {project.episode_count} 集，建议每批 5 集）
                  </p>
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-600">生成集数范围</label>
                      <input
                        type="text"
                        value={episodeRange}
                        onChange={(e) => setEpisodeRange(e.target.value)}
                        placeholder="如：1-5"
                        className="border border-gray-200 rounded px-2 py-1 text-sm w-24 focus:ring-1 focus:ring-purple-400"
                      />
                    </div>
                    <div className="flex max-h-24 gap-1.5 overflow-y-auto flex-wrap">
                      {Array.from({ length: Math.ceil(project.episode_count / 5) }, (_, i) => {
                        const start = i * 5 + 1;
                        const end = Math.min((i + 1) * 5, project.episode_count);
                        const range = `${start}-${end}`;
                        return (
                          <button
                            key={range}
                            type="button"
                            onClick={() => setEpisodeRange(range)}
                            className={`shrink-0 text-xs px-2 py-1 rounded border transition-colors ${
                              episodeRange === range
                                ? 'bg-purple-600 text-white border-purple-600'
                                : 'bg-white text-gray-600 border-gray-200 hover:border-purple-400'
                            }`}
                          >
                            {range} 集
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {lastExecResult?.scope && (
            <div className="p-3 bg-green-50 rounded-lg border border-green-100 text-xs text-green-700">
              ✅ 上次执行：{lastExecResult.scope}
              {lastExecResult.execution_id ? ` · ID: ${lastExecResult.execution_id.slice(0, 8)}` : ''}
            </div>
          )}

          <div className="flex flex-col md:flex-row gap-3">
            <div className="flex-1 rounded-xl bg-gray-50/80 border border-gray-100 px-3 py-3">
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

            <div className="flex-1 rounded-xl bg-gray-50/80 border border-gray-100 px-3 py-3">
              <h4 className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-2">输出产物</h4>
              <div className="flex flex-wrap gap-1.5">
                {(role.output_contract?.artifacts || []).map((a) => (
                  <span key={a} className="text-xs px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-md border border-emerald-100">{a}</span>
                ))}
              </div>
            </div>
          </div>

          {role.is_composite && (
            <div className="p-3 bg-purple-50 rounded-lg border border-purple-100 text-xs text-purple-700">
              <div className="font-semibold mb-1">◈ 复合增强角色</div>
              <p>整合多项专业能力，建议在 8 个核心角色完成后按需执行。</p>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 flex-1">
        <h3 className="text-sm font-medium text-gray-700 mb-3">执行输出</h3>
        {isRunning && (
          <div className="text-center py-8 text-blue-500 text-sm animate-pulse">
            正在生成，请稍候…
          </div>
        )}
        {!isRunning && execStatus === 'failed' && (
          <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3">
            ❌ 执行失败：{execution?.error_message || '未知错误'}
          </div>
        )}
        {!isRunning && execStatus === 'success' && outputKeys.length > 0 && (
          <DramaPresentation views={outputViews} rawArtifacts={execution?.output_artifacts || {}} />
        )}
        {!isRunning && execStatus === 'success' && outputKeys.length === 0 && (
          <div className="text-sm text-gray-600 bg-green-50 rounded-lg p-3">
            ✅ 执行已完成。
            {lastExecResult?.scope ? ` 范围：${lastExecResult.scope}` : ''}
          </div>
        )}
        {!isRunning && execStatus === 'pending' && (
          <div className="text-center py-8 text-gray-400 text-sm">
            点击「执行此角色」开始生成内容
          </div>
        )}
      </div>
    </div>
  );
}