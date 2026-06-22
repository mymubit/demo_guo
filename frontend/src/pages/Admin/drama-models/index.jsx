import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getModelConfig, updateModelConfig, getTokenStats } from '../../../services/drama';

const DEPT_COLORS = {
  strategy: 'bg-blue-50 text-blue-700',
  worldbuilding: 'bg-green-50 text-green-700',
  plot_engine: 'bg-purple-50 text-purple-700',
  writing: 'bg-yellow-50 text-yellow-700',
  review: 'bg-orange-50 text-orange-700',
  polish: 'bg-pink-50 text-pink-700',
  production: 'bg-indigo-50 text-indigo-700',
  ops: 'bg-red-50 text-red-700',
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

/** 模型配置管理面板 */
export default function DramaModelsAdmin() {
  const queryClient = useQueryClient();
  const [editingRole, setEditingRole] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [activeTab, setActiveTab] = useState('models');

  const { data: configRes } = useQuery({
    queryKey: ['drama-model-config'],
    queryFn: getModelConfig,
  });
  const configs = configRes?.data?.data?.configs || [];
  const providers = configRes?.data?.data?.available_providers || [];

  const { data: statsRes } = useQuery({
    queryKey: ['drama-token-stats'],
    queryFn: () => getTokenStats(30),
  });
  const stats = statsRes?.data?.data;

  const updateMut = useMutation({
    mutationFn: updateModelConfig,
    onSuccess: () => {
      queryClient.invalidateQueries(['drama-model-config']);
      setEditingRole(null);
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

  const handleSave = () => {
    updateMut.mutate({
      ...editForm,
      provider_id: editForm.provider_id ? +editForm.provider_id : null,
    });
  };

  // 按部门分组
  const grouped = {};
  configs.forEach((c) => {
    const dept = c.agent_id.replace('drama.', '').split('-')[0];
    // 简单通过agent_id前缀猜测部门
    let deptKey = 'strategy';
    if (c.display_name?.includes('世界') || c.display_name?.includes('人设') || c.display_name?.includes('梦境')) deptKey = 'worldbuilding';
    else if (c.display_name?.includes('情节') || c.display_name?.includes('钩子') || c.display_name?.includes('冲突') || c.display_name?.includes('反转') || c.display_name?.includes('节奏') || c.display_name?.includes('心理') || c.display_name?.includes('情绪架构')) deptKey = 'plot_engine';
    else if (c.display_name?.includes('剧本执笔') || c.display_name?.includes('对白') || c.display_name?.includes('场景') || c.display_name?.includes('IP改编')) deptKey = 'writing';
    else if (c.display_name?.includes('审稿') || c.display_name?.includes('读者') || c.display_name?.includes('情绪审') || c.display_name?.includes('质量报告')) deptKey = 'review';
    else if (c.display_name?.includes('修稿') || c.display_name?.includes('节奏优化') || c.display_name?.includes('格式') || c.display_name?.includes('字数') || c.display_name?.includes('风格')) deptKey = 'polish';
    else if (c.display_name?.includes('视觉') || c.display_name?.includes('分镜') || c.display_name?.includes('后期') || c.display_name?.includes('营销')) deptKey = 'production';
    else if (c.display_name?.includes('合规') || c.display_name?.includes('交付') || c.display_name?.includes('进化')) deptKey = 'ops';

    if (!grouped[deptKey]) grouped[deptKey] = [];
    grouped[deptKey].push(c);
  });

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">模型配置中心</h1>
            <p className="text-sm text-gray-500 mt-0.5">为36个角色分配最合适的LLM模型</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('models')}
              className={`px-4 py-2 text-sm rounded-lg ${activeTab === 'models' ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-gray-700'}`}
            >
              模型配置
            </button>
            <button
              onClick={() => setActiveTab('stats')}
              className={`px-4 py-2 text-sm rounded-lg ${activeTab === 'stats' ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-200 text-gray-700'}`}
            >
              Token统计
            </button>
          </div>
        </div>

        {activeTab === 'models' ? (
          <div className="space-y-4">
            {Object.entries(grouped).map(([deptKey, deptConfigs]) => (
              <div key={deptKey} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className={`px-5 py-3 flex items-center gap-2 border-b border-gray-100`}>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${DEPT_COLORS[deptKey] || 'bg-gray-100 text-gray-600'}`}>
                    {DEPT_NAMES[deptKey] || deptKey}
                  </span>
                  <span className="text-xs text-gray-400">{deptConfigs.length}个角色</span>
                </div>
                <table className="w-full">
                  <tbody>
                    {deptConfigs.map((config) => (
                      <tr key={config.agent_id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                        <td className="px-5 py-3 w-48">
                          <div className="text-sm font-medium text-gray-900">{config.display_name?.split(' (')[0]}</div>
                          <div className="text-xs text-gray-400">{config.agent_id}</div>
                        </td>
                        <td className="px-4 py-3">
                          {editingRole === config.agent_id ? (
                            <div className="flex items-center gap-2">
                              <select
                                value={editForm.provider_id}
                                onChange={(e) => setEditForm({ ...editForm, provider_id: e.target.value })}
                                className="border border-gray-200 rounded px-2 py-1 text-xs"
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
                                className="border border-gray-200 rounded px-2 py-1 text-xs w-40"
                              />
                            </div>
                          ) : (
                            <span className="text-sm text-gray-600">{config.provider_name || '全局默认'}</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {editingRole === config.agent_id ? (
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                min={0}
                                max={2}
                                step={0.1}
                                value={editForm.temperature}
                                onChange={(e) => setEditForm({ ...editForm, temperature: +e.target.value })}
                                className="border border-gray-200 rounded px-2 py-1 text-xs w-16"
                              />
                              <span className="text-xs text-gray-400">温度</span>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-400">T={config.temperature}</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {editingRole === config.agent_id ? (
                            <div className="flex justify-end gap-2">
                              <button
                                onClick={() => setEditingRole(null)}
                                className="text-xs px-3 py-1 border border-gray-200 rounded text-gray-600"
                              >
                                取消
                              </button>
                              <button
                                onClick={handleSave}
                                disabled={updateMut.isPending}
                                className="text-xs px-3 py-1 bg-indigo-600 text-white rounded disabled:opacity-50"
                              >
                                {updateMut.isPending ? '保存中...' : '保存'}
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleEdit(config)}
                              className="text-xs px-3 py-1 border border-gray-200 rounded text-gray-600 hover:bg-gray-50"
                            >
                              修改
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        ) : (
          <TokenStatsPanel stats={stats} />
        )}
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
      {/* 总计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: '总Token消耗', value: (stats.totals?.total_tokens || 0).toLocaleString(), icon: '🔤' },
          { label: '总调用次数', value: (stats.totals?.total_calls || 0).toLocaleString(), icon: '📞' },
          { label: '总费用', value: `¥${stats.totals?.total_cost_yuan || 0}`, icon: '💰' },
          { label: '统计周期', value: `${stats.period_days}天`, icon: '📅' },
        ].map(({ label, value, icon }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl mb-1">{icon}</div>
            <div className="text-xl font-bold text-gray-900">{value}</div>
            <div className="text-xs text-gray-500">{label}</div>
          </div>
        ))}
      </div>

      {/* 按角色统计 */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-5 py-3 border-b border-gray-100">
          <h3 className="text-sm font-medium text-gray-700">各角色Token消耗（Top 20）</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="text-xs text-gray-400 bg-gray-50">
              <th className="px-5 py-2 text-left">角色</th>
              <th className="px-4 py-2 text-right">调用次数</th>
              <th className="px-4 py-2 text-right">总Token</th>
              <th className="px-4 py-2 text-right">均Token</th>
              <th className="px-4 py-2 text-right">费用（元）</th>
            </tr>
          </thead>
          <tbody>
            {(stats.by_role || []).map((r) => (
              <tr key={r.agent_id} className="border-b border-gray-50 hover:bg-gray-50">
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
      </div>
    </div>
  );
}
