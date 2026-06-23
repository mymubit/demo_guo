import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDramaProject,
  getDramaRoles,
  getProjectProgress,
  runRole,
  getEpisodeList,
} from '../../services/drama';

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
  const [execFeedback, setExecFeedback] = useState(null);

  const { data: projectRes } = useQuery({
    queryKey: ['drama-project', projectId],
    queryFn: () => getDramaProject(projectId),
  });
  const project = projectRes?.data || projectRes;

  const { data: progressRes } = useQuery({
    queryKey: ['drama-progress', projectId],
    queryFn: () => getProjectProgress(projectId),
    refetchInterval: 5000,
  });
  const progress = progressRes?.data;

  const { data: rolesRes } = useQuery({
    queryKey: ['drama-roles'],
    queryFn: getDramaRoles,
    staleTime: 5 * 60 * 1000,
  });
  const departments = rolesRes?.data?.departments || [];

  // 分集进度
  const { data: episodesRes } = useQuery({
    queryKey: ['drama-episodes', projectId],
    queryFn: () => getEpisodeList(projectId),
  });
  const episodeProgress = progress?.episode_progress;
  const completedEpisodes = episodesRes?.data?.completed_episodes || episodeProgress?.completed || 0;

  const runMut = useMutation({
    mutationFn: ({ projId, roleId, options = {} }) => runRole(projId, roleId, options),
    onSuccess: (res) => {
      queryClient.invalidateQueries(['drama-progress', projectId]);
      queryClient.invalidateQueries(['drama-episodes', projectId]);
      // 显示执行反馈
      if (res?.data?.scope) {
        setExecFeedback(`✅ ${res.data.role_name} — ${res.data.scope}`);
        setTimeout(() => setExecFeedback(null), 4000);
      }
    },
    onError: (err) => {
      setExecFeedback(`❌ 执行失败：${err?.message || '未知错误'}`);
      setTimeout(() => setExecFeedback(null), 5000);
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

  const handleRunRole = (roleId, options = {}) => {
    runMut.mutate({ projId: projectId, roleId, options });
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
            projectId={projectId}
            roleId={selectedRole}
            allRoles={allRoles}
            onRun={handleRunRole}
            runLoading={runMut.isPending && runMut.variables?.roleId === selectedRole}
            completedSet={completedSet}
            project={project}
            lastExecResult={runMut.data?.data}
          />
        ) : (
          <WelcomePanel project={project} progress={progress} episodeProgress={episodeProgress} completedEpisodes={completedEpisodes} />
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
  const execStatus = execution?.status || (isCompleted ? 'success' : 'pending');
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
function WelcomePanel({ project, progress, episodeProgress, completedEpisodes }) {
  const completionRate = progress?.completion_rate || 0;
  const totalEp = project?.total_episodes || 0;

  return (
    <div className="max-w-2xl">
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-4">
        <h2 className="text-xl font-bold text-gray-900 mb-1">{project?.title}</h2>
        <p className="text-sm text-gray-500 mb-4">
          {totalEp}集 · {project?.track_mode === 'fast' ? '快速通道' : '专家通道'} · {project?.target_platform}
        </p>

        <div className="grid grid-cols-3 gap-4 mb-5">
          <StatCard label="角色完成度" value={`${completionRate}%`} color="indigo" />
          <StatCard label="已生成集数" value={`${completedEpisodes}/${totalEp}`} color="purple" />
          <StatCard label="质量等级" value={project?.quality_scores?.grade || '—'} color="green" />
        </div>

        {/* 100集提示 */}
        {totalEp >= 50 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-700">
            <strong>📌 大体量剧本建议：</strong>此项目共{totalEp}集，建议采用
            <strong>分批生成策略</strong>（每批5-10集）：
            ①大纲先行（1次生成）→ ②分批执行剧本执笔师 → ③每批完成后立即质检 → ④低于75分自动重写
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">如何开始</h3>
        <div className="space-y-2">
          <Step n={1} title="从左侧选择「核心必需」层的角色" desc="8个蓝色角色是所有项目必须执行的，按顺序执行效果最佳" />
          <Step n={2} title="执行角色生成内容" desc="点击角色，查看输入依赖和输出说明，确认依赖已满足后点击执行" />
          <Step n={3} title="分批生成剧本（推荐5集/批）" desc="剧本执笔师支持指定集数范围，建议每批5集，完成后立即质检" />
          <Step n={4} title="应用修改建议" desc="审稿官和对白专家的建议可直接一键应用到原始剧本，生成新版本" />
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  const colors = {
    indigo: 'bg-indigo-50 text-indigo-700',
    purple: 'bg-purple-50 text-purple-700',
    green: 'bg-green-50 text-green-700',
  };
  return (
    <div className={`rounded-lg p-3 ${colors[color]}`}>
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs opacity-70 mt-0.5">{label}</div>
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
function RoleDetailPanel({ projectId, roleId, allRoles, onRun, runLoading, completedSet, project, lastExecResult }) {
  const role = allRoles.find((r) => r.agent_id === roleId);
  const [episodeRange, setEpisodeRange] = useState('1-5');

  if (!role) return null;

  const isCompleted = completedSet.has(roleId);
  const tier = role.tier || (role.is_fast_track ? 1 : 3);
  const tierCfg = TIER_CONFIG[tier];

  // 需要指定集数范围的角色
  const RANGE_ROLES = ['drama.script-writer', 'drama.dialogue-expert', 'drama.hook-designer',
                       'drama.storyboard-director', 'drama.pacing-optimizer'];
  // 需要指定总集数的角色（生成全剧大纲）
  const COUNT_ROLES = ['drama.plot-architect'];
  const isBatchRole = (RANGE_ROLES.includes(roleId) || COUNT_ROLES.includes(roleId)) && (project?.total_episodes || 0) > 1;
  const isCountMode = COUNT_ROLES.includes(roleId); // 大纲类：用集数而非范围

  return (
    <div className="max-w-3xl">
      {/* 角色信息卡 */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-4">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h2 className="text-xl font-bold text-gray-900">{role.name_zh}</h2>
              <span className={`text-xs px-2 py-0.5 rounded-full ${tierCfg.color}`}>
                {tierCfg.label}
              </span>
              {role.is_fast_track && (
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">⚡ 快速通道</span>
              )}
              {isCompleted && (
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">✅ 已完成</span>
              )}
            </div>
            <p className="text-sm text-gray-600">{role.description}</p>
          </div>
        </div>

        {/* 执行配置（分集范围支持） */}
        {isBatchRole && (
          <div className="mb-4 p-3 bg-purple-50 rounded-lg border border-purple-100">
            {isCountMode ? (
              <>
                <p className="text-xs font-medium text-purple-700 mb-2">
                  📋 大纲生成配置（将生成全部{project.total_episodes}集分集大纲）
                </p>
                <p className="text-xs text-purple-500">
                  ⚠️ 分集大纲一次性生成所有集，建议先生成再按需分批写剧本。
                </p>
              </>
            ) : (
              <>
                <p className="text-xs font-medium text-purple-700 mb-2">
                  📌 分集生成配置（共{project.total_episodes}集，建议每批5集以控制质量）
                </p>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-gray-600">生成集数范围</label>
                    <input
                      type="text"
                      value={episodeRange}
                      onChange={(e) => setEpisodeRange(e.target.value)}
                      placeholder="如：1-5 或 6-10"
                      className="border border-gray-200 rounded px-2 py-1 text-sm w-24 focus:ring-1 focus:ring-purple-400"
                    />
                  </div>
                  <div className="flex gap-1.5 flex-wrap">
                    {Array.from({ length: Math.ceil(project.total_episodes / 5) }, (_, i) => {
                      const start = i * 5 + 1;
                      const end = Math.min((i + 1) * 5, project.total_episodes);
                      const range = `${start}-${end}`;
                      return (
                        <button
                          key={range}
                          onClick={() => setEpisodeRange(range)}
                          className={`text-xs px-2 py-1 rounded border transition-colors ${
                            episodeRange === range
                              ? 'bg-purple-600 text-white border-purple-600'
                              : 'bg-white text-gray-600 border-gray-200 hover:border-purple-400'
                          }`}
                        >
                          {range}集
                        </button>
                      );
                    }).slice(0, 8)}
                  </div>
                </div>
                <p className="text-xs text-purple-500 mt-2">
                  当前选择：第{episodeRange}集（{(() => {
                    const [s, e] = episodeRange.split('-').map(Number);
                    return isNaN(s) || isNaN(e) ? '？' : e - s + 1;
                  })()}集）· 预估 Token：~{(() => {
                    const [s, e] = episodeRange.split('-').map(Number);
                    const count = isNaN(s) || isNaN(e) ? 5 : e - s + 1;
                    return `${(count * 12000 / 1000).toFixed(0)}K`;
                  })()}
                </p>
              </>
            )}
          </div>
        )}

        {/* 上次执行结果 */}
        {lastExecResult && lastExecResult.scope && (
          <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-100 text-xs text-green-700">
            ✅ 上次执行：{lastExecResult.scope} · 执行ID: {lastExecResult.execution_id?.slice(0,8)}
          </div>
        )}

        {/* 输入/输出契约 */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-gray-500 mb-2">输入依赖</h4>
            {role.input_contract?.required_artifacts?.length > 0 && (
              <div className="mb-2">
                <span className="text-xs text-red-500 font-medium">必需：</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {role.input_contract.required_artifacts.map((a) => (
                    <span key={a} className="text-xs px-1.5 py-0.5 bg-red-50 text-red-600 rounded border border-red-100">{a}</span>
                  ))}
                </div>
              </div>
            )}
            {role.input_contract?.optional_artifacts?.length > 0 && (
              <div>
                <span className="text-xs text-gray-400">可选：</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {role.input_contract.optional_artifacts.map((a) => (
                    <span key={a} className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">{a}</span>
                  ))}
                </div>
              </div>
            )}
            {!role.input_contract?.required_artifacts?.length && !role.input_contract?.optional_artifacts?.length && (
              <span className="text-xs text-gray-400">无依赖，可直接执行</span>
            )}
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-gray-500 mb-2">输出产物</h4>
            <div className="flex flex-wrap gap-1">
              {role.output_contract?.artifacts?.map((a) => (
                <span key={a} className="text-xs px-1.5 py-0.5 bg-green-50 text-green-700 rounded border border-green-100">{a}</span>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">
              当前模型：{role.current_model || '跟随全局'}
            </p>
          </div>
        </div>

        {/* 执行按钮区 */}
        <div className="flex gap-3 pt-3 border-t border-gray-100">
          <button
            onClick={() => onRun(roleId, {
              episode_range: isBatchRole && !isCountMode ? episodeRange : undefined,
              episode_count: isCountMode ? project.total_episodes : undefined,
            })}
            disabled={runLoading}
            className="flex-1 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {runLoading ? (
              <><span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />执行中...</>
            ) : (
              `🚀 ${isCompleted ? '重新执行' : '执行此角色'}`
            )}
          </button>
          <a
            href="/admin/drama-models"
            className="px-4 py-2.5 border border-gray-200 text-gray-600 text-sm rounded-lg hover:bg-gray-50 flex items-center gap-1"
          >
            ⚙️ 配置模型
          </a>
        </div>

        {/* 专项层角色提示 */}
        {tier === 3 && (
          <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-500">
            💡 此角色属于「专项增强」层，在完成核心必需角色后按需使用，可显著提升特定方面的质量。
          </div>
        )}
      </div>

      {/* 输出区（占位，实际输出需SSE流式填充） */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">执行输出</h3>
        {isCompleted ? (
          <div className="text-sm text-gray-600 bg-green-50 rounded-lg p-3">
            ✅ 此角色已完成执行。
            <span className="text-indigo-600 cursor-pointer ml-1 hover:underline" onClick={() => {}}>
              查看最新产物 →
            </span>
          </div>
        ) : (
          <div className="text-center py-8 text-sm text-gray-400">
            点击「执行此角色」后，输出内容将在此实时流式显示
          </div>
        )}
      </div>
    </div>
  );
}
