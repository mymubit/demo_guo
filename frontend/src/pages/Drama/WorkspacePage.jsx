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
import { creation } from '../../services/creation';
import DramaPresentation from '../../components/drama/presentation/DramaPresentation';
import PlotArchitectOutput from '../../components/drama/PlotArchitectOutput';
import {
  BATCH_RANGE_ROLES,
  BATCH_ROLE_PROGRESS,
  getBatchProgressForRole,
  resolveDefaultEpisodeRange,
  resolveExecuteButtonLabel,
  resolveRoleCompletedBadge,
  resolveRunKindFromParams,
  STRUCTURE_BATCH_ROLES,
  shouldShowStructureButton,
} from '../../utils/dramaBatchRoleUi';
import { Button, Badge, Card } from '../../components/ui';
import {
  ArrowLeft, Zap, Settings, Play, Loader2, ChevronLeft, ChevronRight,
  BookOpen, BarChart3, PanelLeftClose, PanelLeftOpen, Layers,
} from 'lucide-react';

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

const WORKFLOW_STAGES = [
  { code: 'strategy', name: '战略选题', dept: 'strategy', roles: ['drama.topic-planner', 'drama.market-analyst'] },
  { code: 'worldbuilding', name: '世界构建', dept: 'worldbuilding', roles: ['drama.world-architect', 'drama.character-designer'] },
  { code: 'plot_design', name: '剧情引擎', dept: 'plot_engine', roles: ['drama.plot-architect', 'drama.narrative-engineer'] },
  { code: 'writing', name: '剧本创作', dept: 'writing', roles: ['drama.script-writer'] },
  { code: 'review', name: '评审质控', dept: 'review', roles: ['drama.script-reviewer', 'drama.quality-reporter'] },
  { code: 'polish', name: '修改润色', dept: 'polish', roles: ['drama.polish-master'], expertOnly: true },
  { code: 'compliance', name: '合规审查', dept: 'ops', roles: ['drama.compliance-guard'] },
  { code: 'production', name: '制作宣发', dept: 'production', roles: ['drama.production-pack'], expertOnly: true },
];

const TIER_CONFIG = {
  1: { label: '核心必需', badge: '必须', tone: 'brand', dot: 'bg-gold-500', priority: '必执行', desc: '8个快速通道角色，所有项目都要执行' },
  2: { label: '增强复合', badge: '增强', tone: 'accent', dot: 'bg-cyan-400', priority: '按需执行', desc: '4个复合角色，每个整合多项专业能力' },
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
  const [pendingRunKind, setPendingRunKind] = useState(null);
  const [viewMode, setViewMode] = useState('tier');
  const [execFeedback, setExecFeedback] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
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
  const batchProgress = useMemo(() => ({
    outline: progress?.outline_progress,
    script: progress?.script_progress,
    polish: progress?.polish_progress,
    narrative: progress?.narrative_progress,
  }), [progress]);

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
      queryClient.invalidateQueries(['drama-series-outline', projectId]);
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
      setPendingRunKind(null);
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
    d.roles
      .filter(r => !r.hidden && (r.tier === 1 || r.tier === 2 || r.fast_track))
      .map((r) => ({ ...r, dept_name: DEPT_LABELS[d.dept_code] || d.dept_name }))
  );

  const rolesByTier = { 1: [], 2: [] };
  sortByWorkspaceOrder(allRoles).forEach((r) => {
    const tier = r.tier || (r.is_fast_track ? 1 : 2);
    if (tier === 1 || tier === 2) {
      (rolesByTier[tier] || rolesByTier[2]).push(r);
    }
  });

  const workflowStages = useMemo(() => {
    const isExpert = project?.track_mode === 'expert';
    return WORKFLOW_STAGES.filter((stage) => !stage.expertOnly || isExpert);
  }, [project?.track_mode]);

  const currentStageIndex = useMemo(() => {
    const currentStage = progress?.drama_stage || project?.drama_stage;
    if (!currentStage) return 0;
    const idx = workflowStages.findIndex((s) => s.code === currentStage);
    return idx >= 0 ? idx : workflowStages.length - 1;
  }, [progress?.drama_stage, project?.drama_stage, workflowStages]);

  const handleRunRole = (roleId, options = {}) => {
    setPendingRunKind(resolveRunKindFromParams(options));
    runMut.mutate({ projId: projectId, roleId, options });
    setSelectedRole(roleId);
  };

  const isPlotArchitectSelected = selectedRole === 'drama.plot-architect';
  const plotArchitectRunning = Boolean(
    roleStatusMap['drama.plot-architect']?.execution?.status === 'running'
    || roleStatusMap['drama.plot-architect']?.execution?.status === 'pending',
  );

  const { data: liveOutlineRes } = useQuery({
    queryKey: ['drama-series-outline', projectId],
    queryFn: () => creation.artifact(projectId, 'series_outline'),
    enabled: Boolean(projectId && isPlotArchitectSelected),
    refetchInterval: plotArchitectRunning ? 3000 : false,
  });
  const liveSeriesOutline = liveOutlineRes?.data ?? liveOutlineRes ?? null;

  if (!projectId || projectId === 'undefined') {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-slate-400">
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
        <Loader2 className="w-6 h-6 text-gold-500 animate-spin" />
        <p className="text-slate-400 text-sm">加载工作台中...</p>
      </div>
    );
  }

  if (projectError || !project) {
    return (
      <Card padding="xl" className="max-w-md mx-auto mt-20 text-center border-white/10 bg-white/[0.04]">
        <div className="text-4xl mb-3">⚠️</div>
        <h3 className="font-semibold text-slate-100 mb-2">加载失败</h3>
        <p className="text-slate-400 text-sm mb-4">项目不存在或您无权访问</p>
        <Button variant="brand" onClick={() => navigate('/drama')}>返回创作中心</Button>
      </Card>
    );
  }

  return (
    <div className="flex h-screen bg-navy-950 overflow-hidden">
      <aside
        className={`${sidebarCollapsed ? 'w-0 opacity-0' : 'w-72 opacity-100'} transition-all duration-300 bg-navy-900/80 backdrop-blur-xl border-r border-white/10 flex flex-col overflow-hidden flex-shrink-0`}
      >
        <div className="p-4 border-b border-white/5">
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={() => navigate('/drama')}
              className="text-slate-500 hover:text-slate-300 transition-colors p-1 -ml-1"
              aria-label="返回"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h2 className="font-semibold text-slate-100 text-sm truncate flex-1">{project.title}</h2>
            <button
              onClick={() => setSidebarCollapsed(true)}
              className="text-slate-500 hover:text-slate-300 transition-colors p-1"
              aria-label="收起侧边栏"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
            <span>{project.episode_count}集</span>
            <span>·</span>
            <span className={project.track_mode === 'fast' ? 'text-gold-400 font-medium' : 'text-cyan-400 font-medium'}>
              {project.track_mode === 'fast' ? '⚡快速' : '🎬专家'}
            </span>
          </div>

          <div className="space-y-2.5">
            <div>
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>角色完成度</span>
                <span className="text-slate-300 font-medium">{progress?.completion_rate || 0}%</span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-gold-400 to-gold-600 rounded-full transition-all" style={{ width: `${progress?.completion_rate || 0}%` }} />
              </div>
            </div>

            {project.episode_count > 0 && (
              <div>
                <div className="flex justify-between text-xs text-slate-500 mb-1">
                  <span>集数完成</span>
                  <span className="text-slate-300 font-medium">{completedEpisodes}/{project.episode_count}集</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-400 to-cyan-600 rounded-full transition-all"
                    style={{ width: `${(completedEpisodes / project.episode_count) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="px-3 py-2 border-b border-white/5 flex gap-1">
          {[
            { id: 'tier', label: '分层' },
            { id: 'dept', label: '部门' },
            { id: 'fast', label: '快速' },
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setViewMode(m.id)}
              className={`flex-1 text-xs py-1.5 rounded-lg transition-all font-medium ${
                viewMode === m.id
                  ? 'bg-gold-500/15 text-gold-300'
                  : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto py-1 scrollbar-thin">
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

        <div className="p-3 border-t border-white/5 space-y-2">
          <Button
            variant="brand"
            className="w-full justify-center text-sm"
            onClick={() => navigate(`/drama/scripts/${projectId}`)}
            iconLeft={<BookOpen className="w-4 h-4" />}
          >
            查看剧本（{completedEpisodes}集）
          </Button>
          <Button
            variant="secondary"
            className="w-full justify-center text-sm"
            onClick={() => navigate(`/drama/scripts/${projectId}?tab=quality`)}
            iconLeft={<BarChart3 className="w-4 h-4" />}
          >
            质量评分报告
          </Button>
        </div>
      </aside>

      {sidebarCollapsed && (
        <button
          onClick={() => setSidebarCollapsed(false)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-30 bg-navy-800/90 backdrop-blur-sm border border-white/10 border-l-0 rounded-r-lg p-1.5 text-slate-400 hover:text-gold-300 hover:bg-navy-700/90 transition-all"
          aria-label="展开侧边栏"
        >
          <PanelLeftOpen className="w-4 h-4" />
        </button>
      )}

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-shrink-0 px-4 sm:px-6 py-3 border-b border-white/5 bg-navy-900/50 backdrop-blur-sm">
          <div className="flex items-center gap-1 overflow-x-auto scrollbar-thin pb-1">
            {workflowStages.map((stage, idx) => {
              const isDone = idx < currentStageIndex;
              const isCurrent = idx === currentStageIndex;
              const isFuture = idx > currentStageIndex;
              const stageRolesCompleted = stage.roles.every(rid => completedSet.has(rid));

              return (
                <div key={stage.code} className="flex items-center flex-shrink-0">
                  <button
                    onClick={() => {
                      const stageRoleId = stage.roles[0];
                      if (stageRoleId) setSelectedRole(stageRoleId);
                    }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                      isCurrent
                        ? 'bg-gold-500 text-navy-950 shadow-gold'
                        : isDone
                          ? stageRolesCompleted
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-gold-500/10 text-gold-400 border border-gold-500/20'
                          : 'bg-white/5 text-slate-500 border border-white/5 hover:bg-white/10'
                    }`}
                  >
                    <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      isCurrent
                        ? 'bg-navy-950 text-gold-400'
                        : isDone
                          ? 'bg-emerald-500 text-white'
                          : 'bg-white/10 text-slate-500'
                    }`}>
                      {isDone ? '✓' : idx + 1}
                    </span>
                    {stage.name}
                  </button>
                  {idx < workflowStages.length - 1 && (
                    <div className={`w-3 sm:w-6 h-px mx-0.5 ${
                      isDone ? 'bg-emerald-500/50' : 'bg-white/10'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 sm:p-6 scrollbar-thin">
          {execFeedback && (
            <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg text-sm font-medium transition-all backdrop-blur-xl ${
              execFeedback.startsWith('✓') ? 'bg-emerald-500/90 text-white' : 'bg-red-500/90 text-white'
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
              isSubmitting={runMut.isPending && runMut.variables?.roleId === selectedRole}
              pendingRunKind={pendingRunKind}
              onRunKindClear={() => setPendingRunKind(null)}
              completedSet={completedSet}
              project={project}
              batchProgress={batchProgress}
              outlineProgress={progress?.outline_progress}
              liveSeriesOutline={liveSeriesOutline}
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
              currentStageIndex={currentStageIndex}
              workflowStages={workflowStages}
            />
          )}
        </div>
      </main>
    </div>
  );
}

function TierView({ roles, completedSet, roleStatusMap, selectedRole, onSelect }) {
  const [collapsed, setCollapsed] = useState({});

  return (
    <>
      {[1, 2].map((tier) => {
        const tierRoles = roles[tier] || [];
        if (tierRoles.length === 0) return null;
        const cfg = TIER_CONFIG[tier];
        const completedCount = tierRoles.filter((r) => completedSet.has(r.agent_id)).length;
        const isCollapsed = collapsed[tier];

        return (
          <div key={tier} className="border-b border-white/5 last:border-0">
            <button
              onClick={() => setCollapsed((c) => ({ ...c, [tier]: !c[tier] }))}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-white/5 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                <span className="text-xs font-semibold text-slate-300">{cfg.label}</span>
                <Badge tone={cfg.tone} size="sm">{cfg.priority}</Badge>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="font-medium text-slate-300">{completedCount}/{tierRoles.length}</span>
                <span className="text-slate-500">{isCollapsed ? '▸' : '▾'}</span>
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
      {departments.map((dept) => {
        const deptRoles = dept.roles.filter(r => !r.hidden && (r.tier === 1 || r.tier === 2 || r.fast_track));
        if (deptRoles.length === 0) return null;
        return (
          <div key={dept.dept_code} className="py-1">
            <div className="px-4 py-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">
              {dept.dept_name}
            </div>
            {deptRoles.map((role) => (
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
      })}
    </>
  );
}

function FastTrackView({ roles, completedSet, roleStatusMap, selectedRole, onSelect }) {
  return (
    <div className="py-2">
      <div className="px-4 py-1.5 text-xs font-semibold text-gold-400 uppercase tracking-wide flex items-center gap-1.5">
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

  const iconColorClass = {
    success: 'text-emerald-400',
    running: 'text-gold-400 animate-pulse',
    failed: 'text-red-400',
    pending: 'text-slate-500',
  }[statusCfg.tone];

  return (
    <button
      onClick={() => onSelect(role.agent_id)}
      className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-left hover:bg-white/5 transition-colors ${
        isSelected ? 'bg-gold-500/10 border-r-2 border-gold-500' : ''
      }`}
    >
      <span className={`text-sm w-4 text-center flex-shrink-0 font-medium ${iconColorClass}`}>
        {statusCfg.icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-slate-200 truncate font-medium">{role.name_zh}</span>
          {tier === 1 && <Zap className="w-3 h-3 text-gold-400 flex-shrink-0" />}
          {role.is_composite && <span className="text-xs text-cyan-400 flex-shrink-0">◈</span>}
        </div>
        {showDeptTag && role.dept_name && (
          <span className="text-xs text-slate-500">{role.dept_name}</span>
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
  currentStageIndex,
  workflowStages,
}) {
  const completionRate = progress?.completion_rate || 0;
  const totalEp = project?.episode_count || 0;
  const coreRoles = rolesByTier[1] || [];
  const recommendRoles = rolesByTier[2] || [];
  const coreDone = coreRoles.filter((r) => completedSet.has(r.agent_id)).length;
  const stages = workflowStages?.length ? workflowStages : WORKFLOW_STAGES;
  const nextStage = stages[currentStageIndex] || stages[0];

  return (
    <div className="w-full space-y-6">
      <div className="relative overflow-hidden rounded-2xl border border-gold-500/20 bg-gradient-to-br from-gold-600/20 via-navy-900 to-navy-950 p-6 lg:p-8 shadow-gold/5">
        <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-gold-500/10 blur-3xl" />
        <div className="absolute -bottom-20 right-1/3 h-40 w-40 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="relative">
          <div className="flex items-center gap-2 mb-2">
            <p className="text-gold-300/80 text-sm">短剧创作工作台</p>
            {progress?.drama_stage_display && (
              <Badge tone="gold" size="sm" className="bg-gold-500/20 text-gold-300 border-gold-500/30">
                当前：{progress.drama_stage_display}
              </Badge>
            )}
          </div>
          <h2 className="text-2xl lg:text-3xl font-bold text-white mb-2">{project?.title}</h2>
          <p className="text-slate-400 text-sm mb-6">
            {totalEp} 集 · {project?.track_mode === 'fast' ? '⚡ 快速通道' : '🎬 专家通道'}
            {project?.target_platform ? ` · ${formatPlatform(project.target_platform)}` : ''}
          </p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-5">
            <HeroStat label="角色完成度" value={`${completionRate}%`} sub={`${coreDone}/${coreRoles.length} 核心角色`} />
            <HeroStat label="已生成集数" value={`${completedEpisodes}/${totalEp}`} sub="剧本进度" />
            <HeroStat label="质量等级" value={project?.quality_scores?.grade || '—'} sub="综合评分" />
            <HeroStat label="角色总数" value="12" sub="8核心 + 4增强" />
          </div>

          <Button
            variant="gold"
            size="lg"
            iconLeft={<Play className="w-4 h-4" />}
            onClick={() => {
              const nextRoleId = nextStage.roles?.[0];
              if (nextRoleId) onSelectRole(nextRoleId);
            }}
          >
            继续「{nextStage.name}」阶段
          </Button>
        </div>
      </div>

      {totalEp >= 50 && (
        <Card variant="default" padding="md" className="border-amber-500/20 bg-amber-500/5">
          <p className="text-sm text-amber-300">
            <strong className="font-semibold">📌 大体量剧本建议：</strong>此项目共 {totalEp} 集，建议采用
            <strong> 分批生成策略</strong>（每批 5–10 集）：大纲先行 → 分批执行剧本执笔师 → 每批完成后质检 → 低于 75 分自动重写。
          </p>
        </Card>
      )}

      <div className="grid lg:grid-cols-5 gap-6">
        <Card padding="lg" className="lg:col-span-2 border-white/10 bg-white/[0.04]">
          <h3 className="text-base font-semibold text-slate-100 mb-4">创作流程</h3>
          <div className="space-y-3">
            {stages.map((stage, idx) => {
              const isDone = idx < currentStageIndex;
              const isCurrent = idx === currentStageIndex;
              const isFuture = idx > currentStageIndex;
              const stageRoleId = stage.roles[0];
              return (
                <button
                  key={stage.code}
                  onClick={() => stageRoleId && onSelectRole(stageRoleId)}
                  className={`w-full flex items-center gap-3 p-2 rounded-lg text-left transition-all ${
                    isCurrent
                      ? 'bg-gold-500/10 border border-gold-500/20'
                      : isDone
                        ? 'hover:bg-white/5'
                        : 'opacity-60 hover:opacity-100 hover:bg-white/5'
                  }`}
                >
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                    isCurrent
                      ? 'bg-gold-500 text-navy-950'
                      : isDone
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-white/10 text-slate-500'
                  }`}>
                    {isDone ? '✓' : idx + 1}
                  </span>
                  <span className={`text-sm font-medium flex-1 ${
                    isCurrent ? 'text-gold-300' : isDone ? 'text-slate-300' : 'text-slate-500'
                  }`}>
                    {stage.name}
                  </span>
                  {isCurrent && <span className="text-xs text-gold-400 animate-pulse">进行中</span>}
                </button>
              );
            })}
          </div>
        </Card>

        <Card padding="lg" className="lg:col-span-3 border-white/10 bg-white/[0.04]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-slate-100">核心执行路径</h3>
            <span className="text-xs text-slate-400">{coreDone}/{coreRoles.length} 已完成</span>
          </div>
          <div className="space-y-2">
            {coreRoles.map((role, idx) => {
              const exec = roleStatusMap[role.agent_id]?.execution;
              const execStatus = exec?.status ?? 'pending';
              const statusCfg = EXEC_STATUS[execStatus] || EXEC_STATUS.pending;
              const iconColorClass = {
                success: 'text-emerald-400',
                running: 'text-gold-400 animate-pulse',
                failed: 'text-red-400',
                pending: 'text-slate-500',
              }[statusCfg.tone];
              return (
                <button
                  key={role.agent_id}
                  type="button"
                  onClick={() => onSelectRole(role.agent_id)}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-white/10 hover:border-gold-500/30 hover:bg-gold-500/5 transition-all text-left group"
                >
                  <span className="flex-shrink-0 w-7 h-7 rounded-full bg-gold-500/15 text-gold-300 text-xs font-semibold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <span className={`flex-shrink-0 text-base font-medium ${iconColorClass}`}>{statusCfg.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-200 truncate">{role.name_zh}</div>
                    {role.dept_name && (
                      <div className="text-xs text-slate-500 truncate">{role.dept_name}</div>
                    )}
                  </div>
                  <span className="text-xs text-gold-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 font-medium">
                    进入 →
                  </span>
                </button>
              );
            })}
          </div>
        </Card>
      </div>

      {recommendRoles.length > 0 && (
        <Card padding="lg" className="border-cyan-500/20 bg-white/[0.04]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-slate-100">增强复合角色（按需执行）</h3>
            <Badge tone="accent" size="sm">◈ {recommendRoles.length} 个</Badge>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {recommendRoles.map((role) => (
              <button
                key={role.agent_id}
                type="button"
                onClick={() => onSelectRole(role.agent_id)}
                className="text-left p-4 rounded-xl border border-white/10 hover:border-cyan-500/30 hover:bg-cyan-500/5 transition-all"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-cyan-400 text-sm">◈</span>
                  <span className="font-medium text-slate-100">{role.name_zh}</span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2">{role.description}</p>
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
    <div className="rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 px-4 py-3">
      <div className="text-xl lg:text-2xl font-bold text-white">{value}</div>
      <div className="text-xs text-slate-400 mt-0.5">{label}</div>
      {sub && <div className="text-[10px] text-slate-500 mt-1">{sub}</div>}
    </div>
  );
}

function RoleDetailPanel({
  roleId,
  allRoles,
  roleProgress,
  onRun,
  isSubmitting,
  pendingRunKind,
  onRunKindClear,
  completedSet,
  project,
  batchProgress,
  outlineProgress,
  liveSeriesOutline,
  lastExecResult,
}) {
  const role = allRoles.find((r) => r.agent_id === roleId);
  const roleBatchProgress = getBatchProgressForRole(roleId, batchProgress);
  const batchMeta = BATCH_ROLE_PROGRESS[roleId];
  const defaultBatchSize = roleBatchProgress?.batch_size || batchMeta?.defaultBatchSize || 5;
  const OUTLINE_BATCH_SIZE = outlineProgress?.batch_size || 10;
  const suggestedRange = resolveDefaultEpisodeRange(
    roleId,
    project?.episode_count || 0,
    batchProgress,
  );
  const [episodeRange, setEpisodeRange] = useState(suggestedRange);

  useEffect(() => {
    const next = resolveDefaultEpisodeRange(
      roleId,
      project?.episode_count || 0,
      batchProgress,
    );
    if (next) setEpisodeRange(next);
  }, [roleId, batchProgress, project?.episode_count, roleBatchProgress?.suggested_range, roleBatchProgress?.generated]);

  if (!role) {
    return (
      <Card variant="default" padding="md" className="border-amber-500/20 bg-amber-500/5">
        <p className="text-sm text-amber-300">未找到角色数据，请刷新页面后重试。</p>
      </Card>
    );
  }

  const isCompleted = completedSet.has(roleId);
  const tier = role.tier || (role.is_fast_track ? 1 : 2);
  const tierCfg = TIER_CONFIG[tier] || TIER_CONFIG[2];
  const execution = roleProgress?.execution;
  const agentStatus = execution?.status;
  const isAgentRunning = agentStatus === 'running' || agentStatus === 'pending';
  const serverRunKind = resolveRunKindFromParams(execution?.run_params || {});
  const activeRunKind = isAgentRunning || isSubmitting ? (pendingRunKind || serverRunKind) : null;
  const isStructureRunning = Boolean(activeRunKind === 'structure' && (isAgentRunning || isSubmitting));
  const isBatchRunning = Boolean(activeRunKind === 'episodes' && (isAgentRunning || isSubmitting));

  useEffect(() => {
    if (!isAgentRunning && !isSubmitting) {
      onRunKindClear?.();
    }
  }, [isAgentRunning, isSubmitting, onRunKindClear]);

  const execStatus = agentStatus ?? (completedSet.has(roleId) ? 'success' : 'pending');
  const isRunning = isAgentRunning;
  const isPlotArchitect = roleId === 'drama.plot-architect';
  const outputViews = execution?.output_views ?? {};
  const outputArtifacts = execution?.output_artifacts ?? {};
  const seriesOutlineArtifact = liveSeriesOutline || outputArtifacts?.series_outline;
  const structureRoleCfg = STRUCTURE_BATCH_ROLES[roleId];
  const showStructureButton = shouldShowStructureButton(roleId, {
    batchProgress,
    rawArtifact: seriesOutlineArtifact,
    outputView: outputViews?.series_outline,
  });
  const structureButtonLabel = structureRoleCfg?.structureButtonLabel || '生成全剧结构';
  const outputKeys = Object.keys(outputViews).filter(Boolean);
  const artifactKeys = Object.keys(outputArtifacts).filter(Boolean);
  const hasOutput = outputKeys.length > 0 || artifactKeys.length > 0;

  const isBatchRole =
    BATCH_RANGE_ROLES.includes(roleId) && (project?.episode_count || 0) > 1;

  const hasExecutedBefore = Boolean(
    hasOutput
    || execution?.status === 'success'
    || execution?.status === 'failed'
    || execution?.finished_at,
  );
  const showRoleCompletedBadge = resolveRoleCompletedBadge(roleId, batchProgress, completedSet);

  const executeButtonLabel = resolveExecuteButtonLabel({
    runLoading: isSubmitting,
    isAgentRunning: isBatchRunning,
    runKind: 'episodes',
    hasExecutedBefore,
    isBatchRole,
    episodeRange,
    roleProgress: roleBatchProgress,
  });

  const structureButtonBusy = isSubmitting && pendingRunKind === 'structure';
  const structureButtonRunning = isStructureRunning;
  const structureButtonText = structureButtonBusy || structureButtonRunning
    ? '结构生成中…'
    : (showStructureButton ? structureButtonLabel : '重新生成全剧结构');

  const SCRIPT_BATCH_SIZE = defaultBatchSize;

  const handleExecute = () => {
    onRun(roleId, {
      episode_range: isBatchRole ? episodeRange : undefined,
      episode_count: isPlotArchitect ? project.episode_count : undefined,
    });
  };

  const handleGenerateStructure = () => {
    if (!structureRoleCfg) return;
    const payload = {
      episode_count: project.episode_count,
    };
    if (roleId === 'drama.plot-architect') {
      payload.outline_mode = structureRoleCfg.blobMode;
    } else {
      payload.blob_mode = structureRoleCfg.blobMode;
    }
    onRun(roleId, payload);
  };

  const runningBannerText = isStructureRunning
    ? '正在生成全剧结构（六阶段、伏笔等），分集大纲不会改动，您仍可浏览下方集数地图。'
    : `正在生成第 ${episodeRange} 集大纲，完成后地图将自动更新…`;

  return (
    <div className="w-full flex flex-col gap-4 min-h-[calc(100vh-12rem)]">
      <Card padding="none" className="overflow-hidden border-white/10 bg-white/[0.04]">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 px-5 py-4 border-b border-white/5 bg-gradient-to-r from-navy-900/80 to-navy-950/60">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <h2 className="text-lg font-bold text-white">{role.name_zh}</h2>
              <Badge tone={tierCfg.tone} size="sm">{tierCfg.label}</Badge>
              {role.is_fast_track && (
                <Badge tone="brand" size="sm">⚡ 快速通道</Badge>
              )}
              {role.is_composite && (
                <Badge tone="accent" size="sm">◈ 复合增强</Badge>
              )}
              {showRoleCompletedBadge && (
                <Badge tone="success" size="sm">✓ 已完成</Badge>
              )}
            </div>
            <p className="text-sm text-slate-400">{role.description}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {isPlotArchitect ? (
              <Button
                variant="brand"
                onClick={handleGenerateStructure}
                disabled={structureButtonBusy || structureButtonRunning}
                iconLeft={(structureButtonBusy || structureButtonRunning) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
              >
                {structureButtonText}
              </Button>
            ) : showStructureButton ? (
              <Button
                variant="brand"
                onClick={handleGenerateStructure}
                disabled={structureButtonBusy || structureButtonRunning}
                iconLeft={(structureButtonBusy || structureButtonRunning) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
              >
                {structureButtonText}
              </Button>
            ) : null}
            <Button
              variant="brand"
              onClick={handleExecute}
              disabled={(isSubmitting && pendingRunKind === 'episodes') || isBatchRunning}
              iconLeft={(isSubmitting && pendingRunKind === 'episodes') || isBatchRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            >
              {executeButtonLabel}
            </Button>
            <a
              href="/admin/drama-models"
              className="p-2.5 border border-white/10 text-slate-400 rounded-xl hover:bg-white/5 transition-colors"
              title="配置模型"
            >
              <Settings className="w-4 h-4" />
            </a>
          </div>
        </div>

        <div className="px-5 py-4 space-y-4">
          {isBatchRole && (
            <Card padding="md" className="border-cyan-500/20 bg-cyan-500/5">
              {isPlotArchitect ? (
                <>
                  <p className="text-xs font-semibold text-cyan-300 mb-2">
                    📋 分集大纲分批生成（全剧共 {project.episode_count} 集，建议每批 {OUTLINE_BATCH_SIZE} 集）
                  </p>
                  <p className="text-xs text-cyan-400/80 mb-3">
                    已生成 {outlineProgress?.generated ?? 0} 集，新批次会合并进已有大纲，不会覆盖其他集数。
                  </p>
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-slate-400">生成集数范围</label>
                      <input
                        type="text"
                        value={episodeRange}
                        onChange={(e) => setEpisodeRange(e.target.value)}
                        placeholder="如：11-20"
                        className="border border-white/10 bg-white/5 rounded-lg px-2.5 py-1.5 text-sm text-slate-200 w-24 focus:ring-2 focus:ring-gold-500/30 focus:border-gold-500/50 outline-none transition-all"
                      />
                    </div>
                    <div className="flex max-h-24 gap-1.5 overflow-y-auto flex-wrap">
                      {Array.from({ length: Math.ceil(project.episode_count / OUTLINE_BATCH_SIZE) }, (_, i) => {
                        const start = i * OUTLINE_BATCH_SIZE + 1;
                        const end = Math.min((i + 1) * OUTLINE_BATCH_SIZE, project.episode_count);
                        const range = `${start}-${end}`;
                        return (
                          <button
                            key={range}
                            type="button"
                            onClick={() => setEpisodeRange(range)}
                            className={`shrink-0 text-xs px-2.5 py-1 rounded-lg border transition-all font-medium ${
                              episodeRange === range
                                ? 'bg-gold-500 text-navy-950 border-gold-500 shadow-gold'
                                : 'bg-white/5 text-slate-300 border-white/10 hover:border-gold-500/30 hover:text-gold-300'
                            }`}
                          >
                            {range} 集
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  {isPlotArchitect ? (
                    <div className="mt-4 pt-4 border-t border-amber-500/25 flex flex-col sm:flex-row sm:items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-amber-300">
                          六阶段叙事结构{showStructureButton ? ' · 未生成' : ''}
                        </p>
                        <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                          与上方分集批次独立；单独执行不会覆盖已有 {outlineProgress?.generated ?? 0} 集分集大纲。
                        </p>
                      </div>
                      <Button
                        variant="brand"
                        onClick={handleGenerateStructure}
                        disabled={structureButtonBusy || structureButtonRunning}
                        iconLeft={(structureButtonBusy || structureButtonRunning) ? <Loader2 className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
                        className="shrink-0"
                      >
                        {structureButtonText}
                      </Button>
                    </div>
                  ) : null}
                </>
              ) : (
                <>
                  <p className="text-xs font-semibold text-cyan-300 mb-2">
                    📌 分集生成配置（共 {project.episode_count} 集，建议每批 {SCRIPT_BATCH_SIZE} 集）
                  </p>
                  {roleBatchProgress?.generated > 0 ? (
                    <p className="text-xs text-cyan-400/80 mb-3">
                      已生成 {roleBatchProgress.generated} 集，新批次会合并进已有内容，不会覆盖其他集数。
                    </p>
                  ) : null}
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-slate-400">生成集数范围</label>
                      <input
                        type="text"
                        value={episodeRange}
                        onChange={(e) => setEpisodeRange(e.target.value)}
                        placeholder="如：1-5"
                        className="border border-white/10 bg-white/5 rounded-lg px-2.5 py-1.5 text-sm text-slate-200 w-24 focus:ring-2 focus:ring-gold-500/30 focus:border-gold-500/50 outline-none transition-all"
                      />
                    </div>
                    <div className="flex max-h-24 gap-1.5 overflow-y-auto flex-wrap">
                      {Array.from({ length: Math.ceil(project.episode_count / SCRIPT_BATCH_SIZE) }, (_, i) => {
                        const start = i * SCRIPT_BATCH_SIZE + 1;
                        const end = Math.min((i + 1) * SCRIPT_BATCH_SIZE, project.episode_count);
                        const range = `${start}-${end}`;
                        return (
                          <button
                            key={range}
                            type="button"
                            onClick={() => setEpisodeRange(range)}
                            className={`shrink-0 text-xs px-2.5 py-1 rounded-lg border transition-all font-medium ${
                              episodeRange === range
                                ? 'bg-gold-500 text-navy-950 border-gold-500 shadow-gold'
                                : 'bg-white/5 text-slate-300 border-white/10 hover:border-gold-500/30 hover:text-gold-300'
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
            <Card padding="md" className="border-emerald-500/20 bg-emerald-500/5">
              <p className="text-xs text-emerald-300 font-medium">
                ✓ 上次执行：{lastExecResult.scope}
                {lastExecResult.execution_id ? ` · ID: ${lastExecResult.execution_id.slice(0, 8)}` : ''}
              </p>
            </Card>
          )}

          <div className="flex flex-col md:flex-row gap-3">
            <div className="flex-1 rounded-xl bg-white/[0.03] border border-white/5 px-4 py-3">
              <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 mb-2">输入依赖</h4>
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
                <span className="text-xs text-slate-500">无依赖，可直接执行</span>
              )}
            </div>

            <div className="flex-1 rounded-xl bg-white/[0.03] border border-white/5 px-4 py-3">
              <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 mb-2">输出产物</h4>
              <div className="flex flex-wrap gap-1.5">
                {(role.output_contract?.artifacts || []).map((a) => (
                  <Badge key={a} tone="success" size="sm">{a}</Badge>
                ))}
              </div>
            </div>
          </div>

          {role.is_composite && (
            <Card padding="md" className="border-cyan-500/20 bg-cyan-500/5">
              <p className="text-xs text-cyan-300">
                <strong className="font-semibold">◈ 复合增强角色</strong><br />
                整合多项专业能力，建议在 8 个核心角色完成后按需执行。
              </p>
            </Card>
          )}
        </div>
      </Card>

      <Card padding="lg" className="flex-1 border-white/10 bg-white/[0.04]">
        {!isPlotArchitect ? (
          <h3 className="text-sm font-semibold text-slate-300 mb-3">执行输出</h3>
        ) : null}
        {isRunning && !isPlotArchitect ? (
          <div className="text-center py-8 text-gold-400 text-sm flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            正在生成，请稍候…
          </div>
        ) : null}
        {!isRunning && execStatus === 'failed' && (
          <div className="text-sm text-red-300 bg-red-500/10 rounded-xl p-3 border border-red-500/20 mb-4">
            ✕ 执行失败：{execution?.error_message || '未知错误'}
          </div>
        )}
        {isPlotArchitect && execStatus !== 'failed' && (
          <>
            {(isStructureRunning || isBatchRunning) ? (
              <div className={`mb-4 flex items-center gap-2 text-sm rounded-xl px-4 py-2.5 border ${
                isStructureRunning
                  ? 'text-amber-200 bg-amber-500/10 border-amber-500/25'
                  : 'text-gold-400 bg-gold-500/10 border-gold-500/20'
              }`}>
                <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                {runningBannerText}
              </div>
            ) : null}
            <PlotArchitectOutput
              rawArtifact={seriesOutlineArtifact}
              outputView={outputViews.series_outline}
              outlineProgress={outlineProgress}
              totalEpisodes={project?.episode_count || 60}
              batchSize={OUTLINE_BATCH_SIZE}
              onSelectRange={setEpisodeRange}
              onGenerateStructure={isPlotArchitect ? handleGenerateStructure : undefined}
              structureLoading={structureButtonBusy || structureButtonRunning}
            />
          </>
        )}
        {!isRunning && !isPlotArchitect && execStatus === 'success' && hasOutput && (
          <DramaPresentation
            views={outputViews}
            rawArtifacts={outputArtifacts}
            artifactKey={role.default_output_artifact_key || role.output_contract?.artifacts?.[0]}
          />
        )}
        {!isRunning && !isPlotArchitect && execStatus === 'success' && !hasOutput ? (
          <div className="text-sm text-emerald-300 bg-emerald-500/10 rounded-xl p-3 border border-emerald-500/20">
            ✓ 执行已完成。
            {lastExecResult?.scope ? ` 范围：${lastExecResult.scope}` : ''}
          </div>
        ) : null}
        {!isRunning && !isPlotArchitect && execStatus === 'pending' ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            点击「开始执行」生成内容
          </div>
        ) : null}
      </Card>
    </div>
  );
}
