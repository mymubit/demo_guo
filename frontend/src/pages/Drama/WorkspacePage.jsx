import { useState, useRef, useEffect, useMemo } from 'react';
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
import { Button, Badge, Card } from '../../components/ui';
import { ArrowLeft, Zap, Settings, Play, Loader2 } from 'lucide-react';

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
  1: { label: '核心必需', badge: '必须', tone: 'brand', dot: 'bg-brand-500', priority: '必执行', desc: '8个快速通道角色，所有项目都要执行' },
  2: { label: '增强复合', badge: '增强', tone: 'accent', dot: 'bg-accent-500', priority: '按需执行', desc: '4个复合角色，每个整合多项专业能力' },
  3: { label: '专项', badge: '专项', tone: 'default', dot: 'bg-slate-300', priority: '特需', desc: '已整合进复合角色，后台自动调用' },
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
  success: { icon: '✓', label: '已完成', tone: 'success' },
  running: { icon: '⟳', label: '执行中', tone: 'brand' },
  failed:  { icon: '✕', label: '失败',   tone: 'danger' },
  pending: { icon: '○',  label: '待执行', tone: 'default' },
};

export default function WorkspacePage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedRole, setSelectedRole] = useState(null);
  const [viewMode, setViewMode] = useState('tier');
  const [execFeedback, setExecFeedback] = useState(null);
  const feedbackTimerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (feedbackTimerRef.current) {
        clearTimeout(feedbackTimerRef.current);
      }
    };
  }, []);

  const { data: projectRes, isLoading: projectLoading, isError: projectError } = useQuery({
    queryKey: ['drama-project', projectId],
    queryFn: () => getDramaProject(projectId),
    enabled: Boolean(projectId && projectId !== 'undefined'),
    onError: (err) => {
      toast.error(`加载项目失败：${err?.message || '请刷新重试'}`);
    },
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
    onError: (err) => {
      toast.error(`加载进度失败：${err?.message || '将自动重试'}`);
    },
  });
  const progress = progressRes?.data ?? progressRes;

  const { data: rolesRes } = useQuery({
    queryKey: ['drama-roles'],
    queryFn: getDramaRoles,
    staleTime: 60 * 1000,
    refetchOnMount: 'always',
    onError: (err) => {
      toast.error(`加载角色列表失败：${err?.message || '请刷新重试'}`);
    },
  });
  const departments = rolesRes?.departments || rolesRes?.data?.departments || [];

  const { data: episodesRes } = useQuery({
    queryKey: ['drama-episodes', projectId],
    queryFn: () => getEpisodeList(projectId),
    enabled: Boolean(projectId && projectId !== 'undefined'),
    onError: (err) => {
      toast.error(`加载剧集进度失败：${err?.message || '将自动重试'}`);
    },
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
      setExecFeedback(`✓ ${roleName} — ${scope}${tip}`);
      if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
      feedbackTimerRef.current = setTimeout(() => setExecFeedback(null), 5000);
    },
    onError: (err) => {
      const message = err?.message || '未知错误';
      toast.error(`执行失败：${message}`);
      setExecFeedback(`✕ 执行失败：${message}`);
      if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
      feedbackTimerRef.current = setTimeout(() => setExecFeedback(null), 6000);
    },
  });

  const completedSet = useMemo(() => new Set(project?.completed_roles || []), [project?.completed_roles]);

  const roleStatusMap = {};
  if (progress?.roles) {
    progress.roles.forEach((r) => { roleStatusMap[r.agent_id] = r; });
  }

  const allRoles = departments.flatMap((d) =>
    d.roles.map((r) => ({ ...r, dept_name: DEPT_LABELS[d.dept_code] || d.dept_name }))
  );

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
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-slate-500">
        <p>无效的项目地址，请从创作中心重新进入。</p>
        <Button variant="brand" onClick={() => navigate('/drama')}>
          返回创作中心
        </Button>
      </div>
    );
  }

  if (projectLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
        <p className="text-slate-500 text-sm">加载工作台中...</p>
      </div>
    );
  }

  if (projectError || !project) {
    return (
      <Card padding="xl" className="max-w-md mx-auto mt-20 text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <h3 className="font-semibold text-slate-900 mb-2">加载失败</h3>
        <p className="text-slate-500 text-sm mb-4">项目不存在或您无权访问</p>
        <Button variant="brand" onClick={() => navigate('/drama')}>返回创作中心</Button>
      </Card>
    );
  }

  return (
    <div className="flex h-screen bg-slate-25">
      <aside className="w-72 bg-white border-r border-slate-200 flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={() => navigate('/drama')}
              className="text-slate-400 hover:text-slate-600 transition-colors p-1 -ml-1"
              aria-label="返回"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h2 className="font-semibold text-slate-900 text-sm truncate flex-1">{project.title}</h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
            <span>{project.episode_count}集</span>
            <span>·</span>
            <span className={project.track_mode === 'fast' ? 'text-brand-600 font-medium' : 'text-accent-600 font-medium'}>
              {project.track_mode === 'fast' ? '⚡快速通道' : '🎬专家通道'}
            </span>
          </div>
          {progress?.drama_stage_display && (
            <div className="text-xs text-slate-500 mb-3">
              当前阶段：<span className="text-slate-700 font-medium">{progress.drama_stage_display}</span>
            </div>
          )}

          <div className="space-y-2.5">
            <div>
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>角色完成度</span>
                <span className="text-slate-600 font-medium">{progress?.completion_rate || 0}%</span>
              </div>
              <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-brand-500 rounded-full transition-all" style={{ width: `${progress?.completion_rate || 0}%` }} />
              </div>
            </div>

            {project.episode_count > 0 && (
              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>集数完成</span>
                  <span className="text-slate-600 font-medium">{completedEpisodes}/{project.episode_count}集</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent-500 rounded-full transition-all"
                    style={{ width: `${(completedEpisodes / project.episode_count) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="px-3 py-2 border-b border-slate-100 flex gap-1">
          {[
            { id: 'tier', label: '分层视图' },
            { id: 'dept', label: '部门视图' },
            { id: 'fast', label: '快速通道' },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setViewMode(m.id)}
              className={`flex-1 text-xs py-1.5 rounded-lg transition-all font-medium ${
                viewMode === m.id
                  ? 'bg-brand-100 text-brand-700'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto py-1">
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

        <div className="p-3 border-t border-slate-100 space-y-2">
          <Button
            variant="brand"
            className="w-full justify-center"
            onClick={() => navigate(`/drama/scripts/${projectId}`)}
          >
            📖 查看剧本（{completedEpisodes}集）
          </Button>
          <Button
            variant="secondary"
            className="w-full justify-center"
            onClick={() => navigate(`/drama/scripts/${projectId}?tab=quality`)}
          >
            📊 质量评分报告
          </Button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-6">
        {execFeedback && (
          <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium transition-all ${
            execFeedback.startsWith('✓') ? 'bg-success-600 text-white' : 'bg-danger-600 text-white'
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

function TierView({ roles, completedSet, roleStatusMap, selectedRole, onSelect }) {
  const [collapsed, setCollapsed] = useState({ 3: true });

  return (
    <>
      {[1, 2, 3].map((tier) => {
        const tierRoles = roles[tier] || [];
        if (tierRoles.length === 0) return null;
        const cfg = TIER_CONFIG[tier];
        const completedCount = tierRoles.filter((r) => completedSet.has(r.agent_id)).length;
        const isCollapsed = collapsed[tier];

        return (
          <div key={tier} className="border-b border-slate-100 last:border-0">
            <button
              onClick={() => setCollapsed((c) => ({ ...c, [tier]: !c[tier] }))}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                <span className="text-xs font-semibold text-slate-700">{cfg.label}</span>
                <Badge tone={cfg.tone} size="sm">{cfg.priority}</Badge>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="font-medium text-slate-600">{completedCount}/{tierRoles.length}</span>
                <span className="text-slate-400">{isCollapsed ? '▸' : '▾'}</span>
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

function DeptView({ departments, completedSet, roleStatusMap, selectedRole, onSelect }) {
  return (
    <>
      {departments.map((dept) => (
        <div key={dept.dept_code} className="py-1">
          <div className="px-4 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wide">
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

function FastTrackView({ roles, completedSet, roleStatusMap, selectedRole, onSelect }) {
  return (
    <div className="py-2">
      <div className="px-4 py-1.5 text-xs font-semibold text-brand-600 uppercase tracking-wide flex items-center gap-1.5">
        <Zap className="w-3 h-3" />
        快速通道 · 8个核心角色
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

function RoleItem({ role, isCompleted, execution, isSelected, onSelect, showDeptTag }) {
  const execStatus = execution?.status ?? 'pending';
  const statusCfg = EXEC_STATUS[execStatus] || EXEC_STATUS.pending;
  const tier = role.tier || (role.is_fast_track ? 1 : 2);
  const tierCfg = TIER_CONFIG[tier] || TIER_CONFIG[2];

  const iconColorClass = {
    success: 'text-success-600',
    running: 'text-brand-500 animate-pulse',
    failed: 'text-danger-500',
    pending: 'text-slate-400',
  }[statusCfg.tone];

  return (
    <button
      onClick={() => onSelect(role.agent_id)}
      className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-left hover:bg-slate-50 transition-colors ${
        isSelected ? 'bg-brand-50/70 border-r-2 border-brand-500' : ''
      }`}
    >
      <span className={`text-sm w-4 text-center flex-shrink-0 font-medium ${iconColorClass}`}>
        {statusCfg.icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-slate-800 truncate font-medium">{role.name_zh}</span>
          {tier === 1 && <Zap className="w-3 h-3 text-brand-400 flex-shrink-0" />}
          {role.is_composite && <span className="text-xs text-accent-500 flex-shrink-0">◈</span>}
        </div>
        {showDeptTag && role.dept_name && (
          <span className="text-xs text-slate-400">{role.dept_name}</span>
        )}
      </div>
      {isCompleted && (
        <Badge tone="success" size="sm" className="flex-shrink-0">
          ✓
        </Badge>
      )}
    </button>
  );
}

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
      <div className="relative overflow-hidden rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-600 via-brand-700 to-brand-900 p-6 lg:p-8 text-white shadow-sm">
        <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute -bottom-20 right-1/3 h-40 w-40 rounded-full bg-accent-400/20 blur-3xl" />
        <div className="relative">
          <p className="text-brand-200 text-sm mb-1">短剧创作工作台</p>
          <h2 className="text-2xl lg:text-3xl font-bold mb-2">{project?.title}</h2>
          <p className="text-brand-100 text-sm mb-6">
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
        <Card variant="default" padding="md" className="border-warning-200 bg-warning-50/50">
          <p className="text-sm text-warning-800">
            <strong className="font-semibold">📌 大体量剧本建议：</strong>此项目共 {totalEp} 集，建议采用
            <strong> 分批生成策略</strong>（每批 5–10 集）：大纲先行 → 分批执行剧本执笔师 → 每批完成后质检 → 低于 75 分自动重写。
          </p>
        </Card>
      )}

      <div className="grid lg:grid-cols-5 gap-6">
        <Card padding="lg" className="lg:col-span-2">
          <h3 className="text-base font-semibold text-slate-900 mb-4">如何开始</h3>
          <div className="space-y-4">
            <Step n={1} title="从左侧选择「核心必需」层的角色" desc="品牌色角色是所有项目必须执行的，按顺序执行效果最佳" />
            <Step n={2} title="执行角色生成内容" desc="查看输入依赖与输出说明，确认依赖满足后点击执行" />
            <Step n={3} title="分批生成剧本（推荐 5 集/批）" desc="剧本执笔师支持指定集数范围，完成后立即质检" />
            <Step n={4} title="应用修改建议" desc="审稿官与精修大师的建议可一键应用到原始剧本" />
          </div>
        </Card>

        <Card padding="lg" className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-slate-900">核心执行路径</h3>
            <span className="text-xs text-slate-500">{coreDone}/{coreRoles.length} 已完成</span>
          </div>
          <div className="space-y-2">
            {coreRoles.map((role, idx) => {
              const exec = roleStatusMap[role.agent_id]?.execution;
              const execStatus = exec?.status ?? 'pending';
              const statusCfg = EXEC_STATUS[execStatus] || EXEC_STATUS.pending;
              const iconColorClass = {
                success: 'text-success-600',
                running: 'text-brand-500 animate-pulse',
                failed: 'text-danger-500',
                pending: 'text-slate-400',
              }[statusCfg.tone];
              return (
                <button
                  key={role.agent_id}
                  type="button"
                  onClick={() => onSelectRole(role.agent_id)}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-100 hover:border-brand-200 hover:bg-brand-50/50 transition-all text-left group"
                >
                  <span className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-100 text-brand-700 text-xs font-semibold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <span className={`flex-shrink-0 text-base font-medium ${iconColorClass}`}>{statusCfg.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-800 truncate">{role.name_zh}</div>
                    {role.dept_name && (
                      <div className="text-xs text-slate-400 truncate">{role.dept_name}</div>
                    )}
                  </div>
                  <span className="text-xs text-brand-600 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 font-medium">
                    进入 →
                  </span>
                </button>
              );
            })}
          </div>
        </Card>
      </div>

      <Card padding="lg">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">创作流程</h3>
        <div className="space-y-2">
          <Step n={1} title="执行8个核心角色（⚡品牌色）" desc="按顺序：立项→世界观→人设→大纲→剧本→审稿→质量→合规。这8个角色已深度整合山音方法论。" />
          <Step n={2} title="分批生成剧本（每批5集）" desc="剧本执笔师严格执行：首集900-1100字，其余700-900字，台词≥35%，场景≤3个。" />
          <Step n={3} title="按需选择复合角色（◈强调色）" desc="4个复合角色各自整合了5-6项专业能力：市场分析师/叙事工程师/精修大师/制作发行师。" />
          <Step n={4} title="查看质量报告并应用修改" desc="质量报告包含：雷达图+情绪曲线+8维扣分详情+汇总报告。建议可一键应用。" />
        </div>

        <div className="mt-4 p-3 bg-brand-50 rounded-xl text-xs text-brand-700 border border-brand-100">
          <strong className="font-semibold">角色架构说明：</strong>12 个可见角色 = 8 核心 + 4 复合增强。
          左侧「增强复合」分组中可找到市场分析师、叙事工程师、精修大师、制作发行师。
        </div>
      </Card>

      {recommendRoles.length > 0 && (
        <Card padding="lg" className="border-accent-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-slate-900">增强复合角色（按需执行）</h3>
            <Badge tone="accent" size="sm">◈ {recommendRoles.length} 个</Badge>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {recommendRoles.map((role) => (
              <button
                key={role.agent_id}
                type="button"
                onClick={() => onSelectRole(role.agent_id)}
                className="text-left p-4 rounded-xl border border-accent-100 hover:border-accent-300 hover:bg-accent-50/50 transition-all"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-accent-500 text-sm">◈</span>
                  <span className="font-medium text-slate-900">{role.name_zh}</span>
                </div>
                <p className="text-xs text-slate-500 line-clamp-2">{role.description}</p>
              </button>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

function HeroStat({ label, value, sub }) {
  return (
    <div className="rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 px-4 py-3">
      <div className="text-xl lg:text-2xl font-bold">{value}</div>
      <div className="text-xs text-brand-100 mt-0.5">{label}</div>
      {sub && <div className="text-[10px] text-brand-200/80 mt-1">{sub}</div>}
    </div>
  );
}

function Step({ n, title, desc }) {
  return (
    <div className="flex gap-3">
      <div className="w-5 h-5 rounded-full bg-brand-100 text-brand-700 text-xs font-semibold flex items-center justify-center flex-shrink-0 mt-0.5">
        {n}
      </div>
      <div>
        <div className="text-sm font-medium text-slate-800">{title}</div>
        <div className="text-xs text-slate-500 mt-0.5">{desc}</div>
      </div>
    </div>
  );
}

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
      <Card variant="default" padding="md" className="border-warning-200 bg-warning-50">
        <p className="text-sm text-warning-800">未找到角色数据，请刷新页面后重试。</p>
      </Card>
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
      <Card padding="none" className="overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50/80 to-white">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <h2 className="text-lg font-bold text-slate-900">{role.name_zh}</h2>
              <Badge tone={tierCfg.tone} size="sm">{tierCfg.label}</Badge>
              {role.is_fast_track && (
                <Badge tone="brand" size="sm">⚡ 快速通道</Badge>
              )}
              {role.is_composite && (
                <Badge tone="accent" size="sm">◈ 复合增强</Badge>
              )}
              {isCompleted && (
                <Badge tone="success" size="sm">✓ 已完成</Badge>
              )}
            </div>
            <p className="text-sm text-slate-500">{role.description}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="brand"
              onClick={handleExecute}
              disabled={runLoading}
              iconLeft={runLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            >
              {runLoading ? '执行中...' : isCompleted ? '重新执行' : '执行此角色'}
            </Button>
            <a
              href="/admin/drama-models"
              className="p-2.5 border border-slate-200 text-slate-600 rounded-xl hover:bg-slate-50 transition-colors"
              title="配置模型"
            >
              <Settings className="w-4 h-4" />
            </a>
          </div>
        </div>

        <div className="px-5 py-4 space-y-4">
          {isBatchRole && (
            <Card padding="md" className="border-accent-100 bg-accent-50/50">
              {isCountMode ? (
                <>
                  <p className="text-xs font-semibold text-accent-700 mb-2">
                    📋 大纲生成配置（将生成全部 {project.episode_count} 集分集大纲）
                  </p>
                  <p className="text-xs text-accent-600">
                    分集大纲一次性生成所有集，建议先生成大纲再按需分批写剧本。
                  </p>
                </>
              ) : (
                <>
                  <p className="text-xs font-semibold text-accent-700 mb-2">
                    📌 分集生成配置（共 {project.episode_count} 集，建议每批 5 集）
                  </p>
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-slate-600">生成集数范围</label>
                      <input
                        type="text"
                        value={episodeRange}
                        onChange={(e) => setEpisodeRange(e.target.value)}
                        placeholder="如：1-5"
                        className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-sm w-24 focus:ring-2 focus:ring-accent-400 focus:border-accent-400 outline-none transition-all"
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
                            className={`shrink-0 text-xs px-2.5 py-1 rounded-lg border transition-all font-medium ${
                              episodeRange === range
                                ? 'bg-accent-600 text-white border-accent-600 shadow-sm'
                                : 'bg-white text-slate-600 border-slate-200 hover:border-accent-400 hover:text-accent-700'
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
            </Card>
          )}

          {lastExecResult?.scope && (
            <Card padding="md" className="border-success-200 bg-success-50">
              <p className="text-xs text-success-700 font-medium">
                ✓ 上次执行：{lastExecResult.scope}
                {lastExecResult.execution_id ? ` · ID: ${lastExecResult.execution_id.slice(0, 8)}` : ''}
              </p>
            </Card>
          )}

          <div className="flex flex-col md:flex-row gap-3">
            <div className="flex-1 rounded-xl bg-slate-50/80 border border-slate-100 px-4 py-3">
              <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-2">输入依赖</h4>
              {role.input_contract?.required_artifacts?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {role.input_contract.required_artifacts.map((a) => (
                    <Badge key={a} tone="danger" size="sm">{a}</Badge>
                  ))}
                </div>
              ) : role.input_contract?.optional_artifacts?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {role.input_contract.optional_artifacts.map((a) => (
                    <Badge key={a} tone="default" size="sm">{a}</Badge>
                  ))}
                </div>
              ) : (
                <span className="text-xs text-slate-400">无依赖，可直接执行</span>
              )}
            </div>

            <div className="flex-1 rounded-xl bg-slate-50/80 border border-slate-100 px-4 py-3">
              <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-2">输出产物</h4>
              <div className="flex flex-wrap gap-1.5">
                {(role.output_contract?.artifacts || []).map((a) => (
                  <Badge key={a} tone="success" size="sm">{a}</Badge>
                ))}
              </div>
            </div>
          </div>

          {role.is_composite && (
            <Card padding="md" className="border-accent-100 bg-accent-50/50">
              <p className="text-xs text-accent-700">
                <strong className="font-semibold">◈ 复合增强角色</strong><br />
                整合多项专业能力，建议在 8 个核心角色完成后按需执行。
              </p>
            </Card>
          )}
        </div>
      </Card>

      <Card padding="lg" className="flex-1">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">执行输出</h3>
        {isRunning && (
          <div className="text-center py-8 text-brand-500 text-sm flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            正在生成，请稍候…
          </div>
        )}
        {!isRunning && execStatus === 'failed' && (
          <div className="text-sm text-danger-600 bg-danger-50 rounded-xl p-3 border border-danger-100">
            ✕ 执行失败：{execution?.error_message || '未知错误'}
          </div>
        )}
        {!isRunning && execStatus === 'success' && outputKeys.length > 0 && (
          <DramaPresentation views={outputViews} rawArtifacts={execution?.output_artifacts || {}} />
        )}
        {!isRunning && execStatus === 'success' && outputKeys.length === 0 && (
          <div className="text-sm text-success-700 bg-success-50 rounded-xl p-3 border border-success-100">
            ✓ 执行已完成。
            {lastExecResult?.scope ? ` 范围：${lastExecResult.scope}` : ''}
          </div>
        )}
        {!isRunning && execStatus === 'pending' && (
          <div className="text-center py-8 text-slate-400 text-sm">
            点击「执行此角色」开始生成内容
          </div>
        )}
      </Card>
    </div>
  );
}
