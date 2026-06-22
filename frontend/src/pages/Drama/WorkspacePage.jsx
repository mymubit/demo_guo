import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  getDramaProject,
  getDramaRoles,
  getProjectProgress,
  runRole,
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

const STATUS_CONFIG = {
  success: { icon: '✅', color: 'text-green-600 bg-green-50', label: '已完成' },
  running: { icon: '⟳', color: 'text-blue-600 bg-blue-50 animate-pulse', label: '执行中' },
  failed: { icon: '❌', color: 'text-red-600 bg-red-50', label: '失败' },
  pending: { icon: '○', color: 'text-gray-400 bg-gray-50', label: '待执行' },
  skipped: { icon: '⏭', color: 'text-yellow-600 bg-yellow-50', label: '已跳过' },
};

/** 项目工作台 — 36角色执行面板 */
export default function WorkspacePage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedRole, setSelectedRole] = useState(null);
  const [filterFastTrack, setFilterFastTrack] = useState(false);

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
  });
  const departments = rolesRes?.departments || rolesRes?.data?.departments || [];

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

  // 角色执行状态映射
  const roleStatusMap = {};
  if (progress?.roles) {
    progress.roles.forEach((r) => {
      roleStatusMap[r.agent_id] = r;
    });
  }

  const completedSet = new Set(project?.completed_roles || []);

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
      {/* 左侧：角色流程面板 */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
        {/* 项目信息 */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-2 mb-1">
            <button onClick={() => navigate('/drama')} className="text-gray-400 hover:text-gray-600">
              ←
            </button>
            <h2 className="font-semibold text-gray-900 text-sm truncate">{project.title}</h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
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
          {/* 整体进度条 */}
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>完成度</span>
              <span>{progress?.completion_rate || 0}%</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full">
              <div
                className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                style={{ width: `${progress?.completion_rate || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* 快速通道过滤器 */}
        <div className="px-4 py-2 border-b border-gray-100">
          <button
            onClick={() => setFilterFastTrack(!filterFastTrack)}
            className={`text-xs px-3 py-1 rounded-full transition-colors ${
              filterFastTrack
                ? 'bg-indigo-100 text-indigo-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {filterFastTrack ? '✓ 只看快速通道' : '⚡ 只看快速通道'}
          </button>
        </div>

        {/* 角色列表 */}
        <div className="flex-1 overflow-y-auto">
          {departments.map((dept) => {
            const deptRoles = filterFastTrack
              ? dept.roles.filter((r) => r.is_fast_track)
              : dept.roles;
            if (deptRoles.length === 0) return null;

            return (
              <div key={dept.dept_code} className="py-2">
                <div className="px-4 py-1 text-xs font-medium text-gray-400 uppercase tracking-wide">
                  {dept.dept_name}
                </div>
                {deptRoles.map((role) => {
                  const roleStatus = roleStatusMap[role.agent_id];
                  const isCompleted = completedSet.has(role.agent_id);
                  const execStatus = roleStatus?.execution?.status || (isCompleted ? 'success' : 'pending');
                  const statusCfg = STATUS_CONFIG[execStatus] || STATUS_CONFIG.pending;
                  const isSelected = selectedRole === role.agent_id;

                  return (
                    <button
                      key={role.agent_id}
                      onClick={() => setSelectedRole(role.agent_id)}
                      className={`w-full flex items-center gap-2 px-4 py-2 text-left hover:bg-gray-50 transition-colors ${
                        isSelected ? 'bg-indigo-50 border-r-2 border-indigo-500' : ''
                      }`}
                    >
                      <span className={`text-xs px-1.5 py-0.5 rounded ${statusCfg.color}`}>
                        {statusCfg.icon}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1">
                          <span className="text-sm text-gray-700 truncate">{role.name_zh}</span>
                          {role.is_fast_track && (
                            <span className="text-xs text-indigo-400">⚡</span>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* 底部操作 */}
        <div className="p-4 border-t border-gray-100 space-y-2">
          <button
            onClick={() => navigate(`/drama/scripts/${projectId}`)}
            className="w-full py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            📖 查看剧本
          </button>
        </div>
      </aside>

      {/* 右侧：当前角色详情 */}
      <main className="flex-1 overflow-y-auto p-6">
        {selectedRole ? (
          <RoleDetailPanel
            projectId={projectId}
            roleId={selectedRole}
            departments={departments}
            roleProgress={roleStatusMap[selectedRole]}
            onRun={handleRunRole}
            runLoading={runMut.isPending && runMut.variables?.roleId === selectedRole}
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <div className="text-4xl mb-3">🎭</div>
            <p>从左侧选择一个角色开始执行</p>
          </div>
        )}
      </main>
    </div>
  );
}

function RoleDetailPanel({ roleId, departments, roleProgress, onRun, runLoading }) {
  // 找到该角色的详情
  const role = departments
    .flatMap((d) => d.roles)
    .find((r) => r.agent_id === roleId);

  if (!role) return null;

  const execution = roleProgress?.execution;
  const execStatus = execution?.status;
  const statusCfg = execStatus ? STATUS_CONFIG[execStatus] : null;
  const isRunning = execStatus === 'running' || execStatus === 'pending' || runLoading;
  const outputArtifacts = execution?.output_artifacts || {};
  const outputViews = execution?.output_views || {};
  const outputKeys = Object.keys(outputViews).length
    ? Object.keys(outputViews)
    : Object.keys(outputArtifacts);

  return (
    <div className="max-w-3xl">
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-bold text-gray-900">{role.name_zh}</h2>
              <span className="text-sm text-gray-400">({role.name})</span>
              {role.is_fast_track && (
                <span className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full">⚡快速通道</span>
              )}
            </div>
            <p className="text-sm text-gray-500">{role.description}</p>
          </div>
          <button
            onClick={() => onRun(roleId)}
            disabled={runLoading}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
          >
            {runLoading ? (
              <>
                <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                执行中...
              </>
            ) : (
              '🚀 执行角色'
            )}
          </button>
        </div>

        {/* 输入/输出契约 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-gray-500 mb-2">输入依赖</h4>
            {role.input_contract?.required_artifacts?.length > 0 && (
              <div className="mb-1">
                <span className="text-xs text-gray-400">必需：</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {role.input_contract.required_artifacts.map((a) => (
                    <span key={a} className="text-xs px-2 py-0.5 bg-red-50 text-red-600 rounded">
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {role.input_contract?.optional_artifacts?.length > 0 && (
              <div>
                <span className="text-xs text-gray-400">可选：</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {role.input_contract.optional_artifacts.map((a) => (
                    <span key={a} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-gray-500 mb-2">输出产物</h4>
            <div className="flex flex-wrap gap-1">
              {role.output_contract?.artifacts?.map((a) => (
                <span key={a} className="text-xs px-2 py-0.5 bg-green-50 text-green-600 rounded">
                  {a}
                </span>
              ))}
            </div>
            {role.output_contract?.schema_version && (
              <p className="text-xs text-gray-400 mt-2">
                Schema: {role.output_contract.schema_version}
              </p>
            )}
          </div>
        </div>

        {/* 模型配置 */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2">
          <span className="text-xs text-gray-400">当前模型：</span>
          <span className="text-xs font-medium text-gray-700">{role.current_model}</span>
          <a
            href="/admin/drama-models"
            className="text-xs text-indigo-500 hover:text-indigo-700 ml-auto"
          >
            ⚙️ 配置模型
          </a>
        </div>
      </div>

      {/* 执行结果 */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-700">执行输出</h3>
          {statusCfg && (
            <span className={`text-xs px-2 py-0.5 rounded ${statusCfg.color}`}>
              {statusCfg.icon} {statusCfg.label}
            </span>
          )}
        </div>

        {isRunning && (
          <div className="flex items-center gap-3 py-6 text-blue-600 text-sm">
            <span className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full" />
            AI 正在生成内容，请稍候…
          </div>
        )}

        {!isRunning && execStatus === 'failed' && (
          <div className="rounded-lg bg-red-50 border border-red-100 p-4 text-sm text-red-700">
            <p className="font-medium mb-1">执行失败</p>
            <p className="text-red-600 whitespace-pre-wrap">{execution?.error_message || '未知错误'}</p>
          </div>
        )}

        {!isRunning && execStatus === 'success' && outputKeys.length > 0 && (
          <div className="space-y-4">
            {execution?.elapsed_seconds != null && (
              <p className="text-xs text-gray-400">
                耗时 {execution.elapsed_seconds.toFixed(1)}s
                {execution.total_tokens ? ` · ${execution.total_tokens} tokens` : ''}
              </p>
            )}
            <DramaPresentation
              views={outputViews}
              rawArtifacts={outputArtifacts}
            />
          </div>
        )}

        {!isRunning && !execStatus && (
          <div className="text-center py-8 text-gray-400 text-sm">
            点击「执行角色」开始生成内容
          </div>
        )}

        {!isRunning && execStatus === 'success' && outputKeys.length === 0 && (
          <div className="text-center py-8 text-gray-400 text-sm">
            执行已完成，暂无输出产物
          </div>
        )}
      </div>
    </div>
  );
}
