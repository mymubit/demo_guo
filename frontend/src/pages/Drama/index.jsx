import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createDramaProject, getDramaProjects } from '../../services/drama';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const GENRE_OPTIONS = [
  { value: 'family-revenge', label: '家庭伦理复仇' },
  { value: 'domineering-ceo', label: '豪门霸总' },
  { value: 'sweet-pet', label: '甜宠虐恋' },
  { value: 'time-travel', label: '穿越重生' },
  { value: 'urban-counterattack', label: '都市逆袭' },
  { value: 'ancient-power', label: '古装权谋' },
  { value: 'mystery-reversal', label: '悬疑反转' },
  { value: 'healing', label: '情感疗愈' },
];

const PLATFORM_OPTIONS = [
  { value: 'douyin', label: '抖音' },
  { value: 'kuaishou', label: '快手' },
  { value: 'weixin', label: '微信小程序' },
  { value: 'all', label: '通用' },
];

/** 创作中心首页 */
export default function DramaIndex() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState({
    title: '',
    genre_code: 'family-revenge',
    total_episodes: 30,
    target_platform: 'douyin',
    track_mode: 'fast',
    core_idea: '',
  });

  const { data: projectsRes } = useQuery({
    queryKey: ['drama-projects'],
    queryFn: getDramaProjects,
  });
  const projects = projectsRes?.data?.results || projectsRes?.data || [];

  const createMut = useMutation({
    mutationFn: createDramaProject,
    onSuccess: (res) => {
      queryClient.invalidateQueries(['drama-projects']);
      const id = res?.data?.data?.id;
      if (id) navigate(`/drama/workspace/${id}`);
      setShowNew(false);
    },
  });

  const handleCreate = (e) => {
    e.preventDefault();
    createMut.mutate(form);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部标题栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">短剧创作工作室</h1>
            <p className="text-sm text-gray-500 mt-0.5">36个专业角色 · 双轨创作模式 · AI驱动</p>
          </div>
          <button
            onClick={() => setShowNew(true)}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
          >
            + 新建剧本项目
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 双轨模式说明 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div className="bg-white rounded-xl border border-indigo-100 p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">⚡</span>
              <h3 className="font-semibold text-gray-900">快速通道</h3>
              <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded-full">8角色</span>
            </div>
            <p className="text-sm text-gray-500">适合：初次创作、快速验证、10集以内</p>
            <p className="text-sm text-gray-400 mt-1">立项→世界构建→人设→大纲→剧本→审稿→评分→合规</p>
          </div>
          <div className="bg-white rounded-xl border border-purple-100 p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">🎬</span>
              <h3 className="font-semibold text-gray-900">专家通道</h3>
              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">36角色</span>
            </div>
            <p className="text-sm text-gray-500">适合：商业精品、30集+长剧、精细化创作</p>
            <p className="text-sm text-gray-400 mt-1">8个职能部门全流程，每个环节都有专业角色</p>
          </div>
        </div>

        {/* 项目列表 */}
        <div>
          <h2 className="text-base font-semibold text-gray-800 mb-4">我的项目</h2>
          {projects.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <div className="text-4xl mb-3">🎭</div>
              <p>还没有剧本项目，点击"新建剧本项目"开始创作</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((p) => (
                <ProjectCard key={p.id} project={p} onClick={() => navigate(`/drama/workspace/${p.id}`)} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 新建项目对话框 */}
      {showNew && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-5">新建剧本项目</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">剧名</label>
                <input
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="暂定剧名，可后续修改"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">题材</label>
                  <select
                    value={form.genre_code}
                    onChange={(e) => setForm({ ...form, genre_code: e.target.value })}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  >
                    {GENRE_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">总集数</label>
                  <input
                    type="number"
                    min={5}
                    max={200}
                    value={form.total_episodes}
                    onChange={(e) => setForm({ ...form, total_episodes: +e.target.value })}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">目标平台</label>
                  <select
                    value={form.target_platform}
                    onChange={(e) => setForm({ ...form, target_platform: e.target.value })}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  >
                    {PLATFORM_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">创作模式</label>
                  <select
                    value={form.track_mode}
                    onChange={(e) => setForm({ ...form, track_mode: e.target.value })}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="fast">快速通道（8角色）</option>
                    <option value="expert">专家通道（36角色）</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">一句话核心创意（可选）</label>
                <textarea
                  value={form.core_idea}
                  onChange={(e) => setForm({ ...form, core_idea: e.target.value })}
                  placeholder="例：全职太太隐忍三年，发现丈夫秘密后觉醒反击"
                  rows={2}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNew(false)}
                  className="flex-1 py-2 border border-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={createMut.isPending}
                  className="flex-1 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {createMut.isPending ? '创建中...' : '开始创作'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function ProjectCard({ project, onClick }) {
  const completionRate = project.completion_rate || 0;
  const gradeColor = {
    S: 'text-yellow-600 bg-yellow-50',
    A: 'text-green-600 bg-green-50',
    B: 'text-blue-600 bg-blue-50',
    C: 'text-orange-600 bg-orange-50',
    D: 'text-red-600 bg-red-50',
  };
  const grade = project.quality_scores?.grade;
  const overallScore = project.quality_scores?.overall;

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl border border-gray-200 p-5 cursor-pointer hover:shadow-md hover:border-indigo-200 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900 line-clamp-1">{project.title}</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {project.total_episodes}集 · {project.target_platform === 'douyin' ? '抖音' : project.target_platform}
          </p>
        </div>
        {grade && overallScore && (
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${gradeColor[grade] || 'text-gray-600 bg-gray-50'}`}>
            {grade}级 {overallScore}分
          </span>
        )}
      </div>

      {/* 进度条 */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>完成度</span>
          <span>{completionRate}%</span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-500 rounded-full transition-all"
            style={{ width: `${completionRate}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className={`text-xs px-2 py-0.5 rounded-full ${
          project.track_mode === 'fast'
            ? 'bg-indigo-50 text-indigo-600'
            : 'bg-purple-50 text-purple-600'
        }`}>
          {project.track_mode === 'fast' ? '⚡ 快速通道' : '🎬 专家通道'}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded-full ${
          project.delivery_status === 'delivered'
            ? 'bg-green-50 text-green-600'
            : project.delivery_status === 'ready'
            ? 'bg-yellow-50 text-yellow-600'
            : 'bg-gray-50 text-gray-500'
        }`}>
          {project.delivery_status === 'delivered' ? '✅ 已交付'
           : project.delivery_status === 'ready' ? '📦 待交付'
           : '🔨 创作中'}
        </span>
      </div>
    </div>
  );
}
