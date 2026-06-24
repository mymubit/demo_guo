import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { getModelConfig, updateModelConfig, getTokenStats } from '../../../services/drama';
import { Button, Card } from '../../../components/ui';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';

const DEPT_COLORS = {
  strategy: { badge: 'bg-blue-100 text-blue-700', border: 'border-blue-100' },
  worldbuilding: { badge: 'bg-green-100 text-green-700', border: 'border-green-100' },
  plot_engine: { badge: 'bg-purple-100 text-purple-700', border: 'border-purple-100' },
  writing: { badge: 'bg-yellow-100 text-yellow-700', border: 'border-yellow-100' },
  review: { badge: 'bg-orange-100 text-orange-700', border: 'border-orange-100' },
  polish: { badge: 'bg-pink-100 text-pink-700', border: 'border-pink-100' },
  production: { badge: 'bg-indigo-100 text-indigo-700', border: 'border-indigo-100' },
  ops: { badge: 'bg-red-100 text-red-700', border: 'border-red-100' },
};

const DEPT_NAMES = {
  strategy: '战略选题部',
  worldbuilding: '世界构建部',
  plot_engine: '剧情引擎部',
  writing: '创作执行部',
  review: '评审质控部',
  polish: '修改润色部',
  production: '制作宣发部',
  ops: '合规总编室',
};

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      <p className="text-slate-500 text-sm">加载中...</p>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="w-14 h-14 rounded-full bg-red-50 flex items-center justify-center">
        <AlertCircle className="w-7 h-7 text-red-500" />
      </div>
      <div className="text-center">
        <p className="text-slate-800 font-medium">加载失败</p>
        <p className="text-slate-500 text-sm mt-1">{message || '请检查网络后重试'}</p>
      </div>
      <Button variant="outline" size="sm" onClick={onRetry} className="gap-2">
        <RefreshCw className="w-4 h-4" />
        重新加载
      </Button>
    </div>
  );
}

/** 模型配置管理面板 */
export default function DramaModelsAdmin() {
  const queryClient = useQueryClient();
  const [editingRole, setEditingRole] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [activeTab, setActiveTab] = useState('models');

  const {
    data: configRes,
    isLoading: configLoading,
    isError: configError,
    refetch: refetchConfig,
    error: configErrorObj,
  } = useQuery({
    queryKey: ['drama-model-config'],
    queryFn: getModelConfig,
  });
  const configs = configRes?.data?.data?.configs || [];
  const providers = configRes?.data?.data?.available_providers || [];

  const {
    data: statsRes,
    isLoading: statsLoading,
    isError: statsError,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['drama-token-stats'],
    queryFn: () => getTokenStats(30),
    enabled: activeTab === 'stats',
  });
  const stats = statsRes?.data?.data;

  const updateMut = useMutation({
    mutationFn: updateModelConfig,
    onSuccess: () => {
      queryClient.invalidateQueries(['drama-model-config']);
      setEditingRole(null);
      toast.success('模型配置已更新');
    },
    onError: (err) => {
      toast.error('保存失败', {
        description: err?.message || '请稍后重试',
      });
    },
  });

  const handleEdit = (config) => {
    setEditingRole(config.agent_id);
    setEditForm({
      agent_id: config.agent_id,
      provider_id: config.provider_id || '',
      model_name: config.model_name || '',
      temperature: config.temperature || 0.7,
      max_completion_tokens: config.max_completion_tokens || 8000,
    });
  };

  const handleCancel = () => {
    setEditingRole(null);
    setEditForm({});
  };

  const handleSave = () => {
    updateMut.mutate({
      ...editForm,
      provider_id: editForm.provider_id ? +editForm.provider_id : null,
    });
  };

  // 按部门分组
  const grouped = {};
  configs.forEach((c) => {
    let deptKey = 'strategy';
    const name = c.display_name || '';
    if (name.includes('世界') || name.includes('人设') || name.includes('梦境')) deptKey = 'worldbuilding';
    else if (name.includes('情节') || name.includes('钩子') || name.includes('冲突') || name.includes('反转') || name.includes('节奏') || name.includes('心理') || name.includes('情绪架构')) deptKey = 'plot_engine';
    else if (name.includes('剧本执笔') || name.includes('对白') || name.includes('场景') || name.includes('IP改编')) deptKey = 'writing';
    else if (name.includes('审稿') || name.includes('读者') || name.includes('情绪审') || name.includes('质量报告')) deptKey = 'review';
    else if (name.includes('修稿') || name.includes('节奏优化') || name.includes('格式') || name.includes('字数') || name.includes('风格')) deptKey = 'polish';
    else if (name.includes('视觉') || name.includes('分镜') || name.includes('后期') || name.includes('营销')) deptKey = 'production';
    else if (name.includes('合规') || name.includes('交付') || name.includes('进化')) deptKey = 'ops';

    if (!grouped[deptKey]) grouped[deptKey] = [];
    grouped[deptKey].push(c);
  });

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">模型配置中心</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">为12个角色分配最合适的LLM模型</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('models')}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                activeTab === 'models' ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
            >
              模型配置
            </button>
            <button
              onClick={() => setActiveTab('stats')}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                activeTab === 'stats' ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Token统计
            </button>
          </div>
        </div>

        {activeTab === 'models' ? (
          configLoading ? (
            <LoadingState />
          ) : configError ? (
            <ErrorState message={configErrorObj?.message} onRetry={refetchConfig} />
          ) : (
            <div className="space-y-4">
              {Object.entries(grouped).map(([deptKey, deptConfigs]) => {
                const deptStyle = DEPT_COLORS[deptKey] || DEPT_COLORS.strategy;
                return (
                  <Card key={deptKey} className={`overflow-hidden ${deptStyle.border}`} padding="none">
                    <div className={`px-5 py-3 flex items-center gap-2 border-b border-gray-100 bg-gray-50`}>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${deptStyle.badge}`}>
                        {DEPT_NAMES[deptKey] || deptKey}
                      </span>
                      <span className="text-xs text-gray-400">{deptConfigs.length}个角色</span>
                    </div>
                    <table className="w-full">
                      <tbody>
                        {deptConfigs.map((config) => (
                          <tr key={config.agent_id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
                            <td className="px-5 py-3 w-56">
                              <div className="text-sm font-medium text-gray-900">{config.display_name?.split(' (')[0]}</div>
                              <div className="text-xs text-gray-400">{config.agent_id}</div>
                            </td>
                            <td className="px-4 py-3">
                              {editingRole === config.agent_id ? (
                                <div className="flex items-center gap-2 flex-wrap">
                                  <select
                                    value={editForm.provider_id}
                                    onChange={(e) => setEditForm({ ...editForm, provider_id: e.target.value })}
                                    className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                                  >
                                    <option value="">-- 使用全局配置 --</option>
                                    {providers.map((p) => (
                                      <option key={p.id} value={p.id}>{p.name}</option>
                                    ))}
                                  </select>
                                  <input
                                    value={editForm.model_name}
                                    onChange={(e) => setEditForm({ ...editForm, model_name: e.target.value })}
                                    placeholder="模型名称（如 gpt-4o）"
                                    className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm w-44 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                                  />
                                </div>
                              ) : (
                                <span className="text-sm text-gray-600">{config.provider_name || '全局默认'}</span>
                              )}
                            </td>
                            <td className="px-4 py-3 w-40">
                              {editingRole === config.agent_id ? (
                                <div className="flex items-center gap-2">
                                  <input
                                    type="number"
                                    min={0}
                                    max={2}
                                    step={0.1}
                                    value={editForm.temperature}
                                    onChange={(e) => setEditForm({ ...editForm, temperature: +e.target.value })}
                                    className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm w-20 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                                  />
                                  <span className="text-xs text-gray-400">温度</span>
                                </div>
                              ) : (
                                <span className="text-xs text-gray-400">T={config.temperature}</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right w-32">
                              {editingRole === config.agent_id ? (
                                <div className="flex justify-end gap-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleCancel}
                                    disabled={updateMut.isPending}
                                  >
                                    取消
                                  </Button>
                                  <Button
                                    variant="brand"
                                    size="sm"
                                    onClick={handleSave}
                                    disabled={updateMut.isPending}
                                    className="gap-1.5"
                                  >
                                    {updateMut.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                                    {updateMut.isPending ? '保存中...' : '保存'}
                                  </Button>
                                </div>
                              ) : (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleEdit(config)}
                                >
                                  修改
                                </Button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Card>
                );
              })}
            </div>
          )
        ) : activeTab === 'stats' ? (
          statsLoading ? (
            <LoadingState />
          ) : statsError ? (
            <ErrorState onRetry={refetchStats} />
          ) : (
            <TokenStatsPanel stats={stats} />
          )
        ) : null}
      </div>
    </div>
  );
}

function TokenStatsPanel({ stats }) {
  if (!stats) {
    return (
      <div className="text-center py-16 text-gray-400">
        <div className="text-3xl mb-2">📊</div>
        <p>暂无统计数据</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: '总Token消耗', value: (stats.totals?.total_tokens || 0).toLocaleString(), icon: '🔤' },
          { label: '总调用次数', value: (stats.totals?.total_calls || 0).toLocaleString(), icon: '📞' },
          { label: '总费用', value: `¥${stats.totals?.total_cost_yuan || 0}`, icon: '💰' },
          { label: '统计周期', value: `${stats.period_days}天`, icon: '📅' },
        ].map(({ label, value, icon }) => (
          <Card key={label} padding="lg" className="text-center">
            <div className="text-2xl mb-1">{icon}</div>
            <div className="text-xl font-bold text-gray-900">{value}</div>
            <div className="text-xs text-gray-500">{label}</div>
          </Card>
        ))}
      </div>

      <Card padding="none" className="overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
          <h3 className="text-sm font-medium text-gray-700">各角色Token消耗（Top 20）</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="text-xs text-gray-400 bg-gray-50/50">
              <th className="px-5 py-2 text-left font-medium">角色</th>
              <th className="px-4 py-2 text-right font-medium">调用次数</th>
              <th className="px-4 py-2 text-right font-medium">总Token</th>
              <th className="px-4 py-2 text-right font-medium">均Token</th>
              <th className="px-4 py-2 text-right font-medium">费用（元）</th>
            </tr>
          </thead>
          <tbody>
            {(stats.by_role || []).map((r) => (
              <tr key={r.agent_id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="px-5 py-2.5 text-sm text-gray-700">{r.agent_name_zh || r.agent_id}</td>
                <td className="px-4 py-2.5 text-sm text-right text-gray-600">{r.total_calls}</td>
                <td className="px-4 py-2.5 text-sm text-right text-gray-600">{(r.total_tokens || 0).toLocaleString()}</td>
                <td className="px-4 py-2.5 text-sm text-right text-gray-600">{Math.round(r.avg_tokens || 0).toLocaleString()}</td>
                <td className="px-4 py-2.5 text-sm text-right text-gray-600">¥{((r.total_cost_cents || 0) / 100).toFixed(2)}</td>
              </tr>
            ))}
            {(stats.by_role || []).length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-sm text-gray-400">暂无数据</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
