import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { createDramaProject } from '../../services/drama';
import { works as worksApi } from '../../services/api';
import { normalizeWorkItem } from '../../services/adapters/businessAdapters';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// ─── 多维度题材矩阵（破除固定选项限制，支持创新组合）────────────────────────
// 设计理念：参考《Save the Cat》剧情类型×情感轴×冲突类型三维矩阵
// 行业实践：爆款往往来自两个维度的"意外组合"（如：古装×职场、悬疑×甜宠）

const GENRE_MATRIX = {
  // 情感轴（核心驱动力）
  emotion: {
    label: '情感轴',
    hint: '驱动观众追剧的核心情绪',
    options: [
      { value: 'revenge',     label: '复仇爽感',   desc: '主角逆境反击，爽感高密度' },
      { value: 'love',        label: '爱情甜虐',   desc: '甜蜜与虐心交替，情绪拉扯' },
      { value: 'healing',     label: '治愈共鸣',   desc: '情感认同，慢热积累' },
      { value: 'suspense',    label: '悬疑烧脑',   desc: '信息差维持，反转成瘾' },
      { value: 'ambition',    label: '野心逐权',   desc: '权力博弈，人性复杂' },
    ],
  },
  // 身份轴（主角设定）
  identity: {
    label: '身份轴',
    hint: '主角的社会角色与身份冲突',
    options: [
      { value: 'ceo',         label: '豪门精英',   desc: '高权势，资源博弈' },
      { value: 'ordinary',    label: '普通女性',   desc: '真实代入感，草根逆袭' },
      { value: 'hidden',      label: '隐藏大佬',   desc: '错认身份，反差冲击' },
      { value: 'reborn',      label: '重生觉醒',   desc: '前世记忆，改写命运' },
      { value: 'transmigrate',label: '跨世界者',   desc: '穿越/降临，文化碰撞' },
    ],
  },
  // 冲突类型（核心矛盾）
  conflict: {
    label: '冲突轴',
    hint: '推动剧情前进的核心矛盾',
    options: [
      { value: 'family',      label: '家族内斗',   desc: '血缘关系中的权力与背叛' },
      { value: 'workplace',   label: '职场博弈',   desc: '利益链条，规则与阴谋' },
      { value: 'romance',     label: '情感纠葛',   desc: '三角关系，追逐与逃离' },
      { value: 'secret',      label: '身份秘密',   desc: '信息不对等，揭穿的时刻' },
      { value: 'survival',    label: '生存竞争',   desc: '资源稀缺，淘汰机制' },
    ],
  },
  // 世界观（时空背景）
  world: {
    label: '世界观',
    hint: '故事发生的时空与规则',
    options: [
      { value: 'modern',      label: '当代都市',   desc: '现实感强，快节奏' },
      { value: 'ancient',     label: '古代宫廷',   desc: '权谋服饰，历史质感' },
      { value: 'fantasy',     label: '架空仙侠',   desc: '规则自定义，想象空间大' },
      { value: 'near-future', label: '近未来',     desc: '科技+情感，新奇设定' },
      { value: 'overseas',    label: '海外异地',   desc: '文化差异，异域背景' },
    ],
  },
};

// 预设创新组合（对立面法：跨维度"意外配对"）
const INNOVATIVE_COMBOS = [
  { label: '古装×职场权谋', code: 'ancient-workplace', dims: { emotion:'ambition', identity:'hidden', conflict:'workplace', world:'ancient' }, heat: '🔥 新兴热点' },
  { label: '甜宠×悬疑反转', code: 'sweet-mystery',     dims: { emotion:'suspense', identity:'hidden', conflict:'secret', world:'modern' }, heat: '✨ 破圈潜力' },
  { label: '普通女性×隐藏大佬', code: 'hidden-boss',   dims: { emotion:'love', identity:'hidden', conflict:'romance', world:'modern' }, heat: '💡 高爆款率' },
  { label: '重生复仇×家族内斗', code: 'reborn-revenge', dims: { emotion:'revenge', identity:'reborn', conflict:'family', world:'modern' }, heat: '🔝 经典爆款' },
  { label: '职场逆袭×情感治愈', code: 'career-healing',dims: { emotion:'healing', identity:'ordinary', conflict:'workplace', world:'modern' }, heat: '🌟 长尾用户' },
];

const GENRE_DIM_ORDER = ['emotion', 'identity', 'conflict', 'world'];
const THEME_MAX_LENGTH = 64;

// 根据维度选择生成 theme 代码（固定轴顺序，避免 Object.values 顺序不稳定）
function themeCodeFromDims(dims) {
  return GENRE_DIM_ORDER.map((axis) => dims[axis]).filter(Boolean).join('-');
}

const PLATFORM_OPTIONS = [
  { value: 'douyin', label: '抖音' },
  { value: 'kuaishou', label: '快手' },
  { value: 'weixin', label: '微信小程序' },
  { value: 'all', label: '通用' },
];

function mapWorkToWorkspace(work) {
  if (!work) return null;
  return {
    id: work.project_id,
    project_id: work.project_id,
    title: work.title,
    theme: work.theme,
    episode_count: work.episode_count ?? work.episodes,
    target_platform: work.target_platform || 'douyin',
    track_mode: work.track_mode || 'fast',
    drama_stage: work.drama_stage || '',
    completion_rate: Math.min(100, Number(work.completion_rate ?? work.progress_percent) || 0),
    delivery_status: work.delivery_status || 'pending',
    quality_scores: work.quality_scores,
  };
}

/** 创作中心首页 */
export default function DramaIndex() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [genreMode, setGenreMode] = useState('matrix'); // 'matrix' | 'preset' | 'free'
  const [dimSelections, setDimSelections] = useState({});
  const [form, setForm] = useState({
    title: '',
    theme: '',
    episode_count: 30,
    target_platform: 'douyin',
    track_mode: 'fast',
    core_idea: '',
  });

  const computedTheme = useMemo(() => {
    if (genreMode === 'free') return form.theme;
    if (genreMode === 'preset') return form.theme;
    return themeCodeFromDims(dimSelections);
  }, [genreMode, dimSelections, form.theme]);

  const selectDim = (axis, value) => {
    setDimSelections(prev => ({ ...prev, [axis]: prev[axis] === value ? undefined : value }));
  };

  const applyCombo = (combo) => {
    setDimSelections(combo.dims);
    setForm(f => ({ ...f, theme: combo.code }));
  };

  const { data: projectsRes } = useQuery({
    queryKey: ['drama-projects', 'works-unified'],
    queryFn: async () => {
      const result = await worksApi.list(1, 'all', 100, { scope: 'drama', ordering: 'newest' });
      return (result.items || []).map(normalizeWorkItem).map(mapWorkToWorkspace).filter(Boolean);
    },
  });
  const projects = Array.isArray(projectsRes) ? projectsRes : [];

  const createMut = useMutation({
    mutationFn: createDramaProject,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['drama-projects'] });
      queryClient.invalidateQueries({ queryKey: ['works'] });
      const project = res?.data ?? res;
      const id = project?.id;
      setShowNew(false);
      if (!id) {
        toast.error('项目已创建，但未返回项目 ID，请从列表进入');
        return;
      }
      navigate(`/drama/workspace/${id}`);
    },
    onError: (err) => {
      toast.error(err?.message || '创建失败，请稍后重试');
    },
  });

  const handleCreate = (e) => {
    e.preventDefault();
    const themeCode = (computedTheme || 'custom').trim();
    if (themeCode.length > THEME_MAX_LENGTH) {
      toast.error(`题材代码过长（${themeCode.length}/${THEME_MAX_LENGTH}），请减少维度选择或使用预设组合`);
      return;
    }
    createMut.mutate({
      title: form.title,
      theme: themeCode,
      episode_count: form.episode_count,
      target_platform: form.target_platform,
      track_mode: form.track_mode,
      core_idea: form.core_idea,
    });
  };

  return (
    <div className="min-h-full">
      {/* 顶部标题栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">短剧创作工作室</h1>
            <p className="text-sm text-gray-500 mt-0.5">12个专业角色 · 双轨创作模式 · AI驱动</p>
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
              <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded-full">8核心角色</span>
            </div>
            <p className="text-sm text-gray-500">适合：初次创作、快速验证、10集以内</p>
            <p className="text-sm text-gray-400 mt-1">立项→世界构建→人设→大纲→剧本→审稿→评分→合规</p>
          </div>
          <div className="bg-white rounded-xl border border-purple-100 p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">🎬</span>
              <h3 className="font-semibold text-gray-900">专家通道</h3>
              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">12角色</span>
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

      {/* 新建项目弹窗 */}
      {showNew && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">新建剧本项目</h2>
              <button onClick={() => setShowNew(false)} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">×</button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-5">
              {/* 基础信息 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">剧名 <span className="text-red-400">*</span></label>
                <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="暂定剧名，可后续修改" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500" />
              </div>

              {/* 题材选择 — 多维度矩阵 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">题材定位</label>
                  <div className="flex gap-1">
                    {[['matrix','矩阵选择'],['preset','快速预设'],['free','自由输入']].map(([m,l]) => (
                      <button key={m} type="button" onClick={() => setGenreMode(m)}
                        className={`px-2 py-1 text-xs rounded ${genreMode===m?'bg-indigo-100 text-indigo-700 font-medium':'text-gray-500 hover:bg-gray-100'}`}>
                        {l}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 矩阵选择模式 */}
                {genreMode === 'matrix' && (
                  <div className="space-y-3">
                    {/* 创新组合推荐 */}
                    <div className="bg-indigo-50 rounded-xl p-3">
                      <p className="text-xs font-medium text-indigo-700 mb-2">💡 创新组合推荐（对立面法）</p>
                      <div className="flex flex-wrap gap-2">
                        {INNOVATIVE_COMBOS.map(combo => (
                          <button key={combo.code} type="button" onClick={() => applyCombo(combo)}
                            className={`text-xs px-2 py-1.5 rounded-lg border transition-all ${
                              computedTheme === combo.code
                                ? 'bg-indigo-600 text-white border-indigo-600'
                                : 'bg-white text-gray-700 border-gray-200 hover:border-indigo-400'
                            }`}>
                            {combo.heat} {combo.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    {/* 四维选择 */}
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(GENRE_MATRIX).map(([axis, config]) => (
                        <div key={axis}>
                          <div className="text-xs font-semibold text-gray-600 mb-1">
                            {config.label}
                            <span className="text-gray-400 font-normal ml-1">· {config.hint}</span>
                          </div>
                          <div className="space-y-1">
                            {config.options.map(opt => (
                              <button key={opt.value} type="button" onClick={() => selectDim(axis, opt.value)}
                                className={`w-full text-left px-2 py-1.5 rounded-lg text-xs border transition-all ${
                                  dimSelections[axis] === opt.value
                                    ? 'bg-indigo-600 text-white border-indigo-600'
                                    : 'bg-white text-gray-700 border-gray-100 hover:border-indigo-300'
                                }`}>
                                <span className="font-medium">{opt.label}</span>
                                <span className="opacity-70 ml-1">— {opt.desc}</span>
                              </button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                    {/* 当前组合 */}
                    <div className="bg-gray-50 rounded-lg px-3 py-2 text-xs text-gray-600">
                      当前组合：<span className="font-medium text-indigo-700">
                        {Object.entries(dimSelections).filter(([,v])=>v).map(([axis,val]) => {
                          const opt = GENRE_MATRIX[axis]?.options.find(o => o.value === val);
                          return opt?.label;
                        }).filter(Boolean).join(' × ') || '请从上方选择维度…'}
                      </span>
                    </div>
                  </div>
                )}

                {/* 快速预设模式 */}
                {genreMode === 'preset' && (
                  <div className="grid grid-cols-2 gap-2">
                    {INNOVATIVE_COMBOS.map(combo => (
                      <button key={combo.code} type="button" onClick={() => { applyCombo(combo); setForm(f=>({...f,theme:combo.code})); }}
                        className={`p-2 rounded-lg border text-left text-sm transition-all ${form.theme===combo.code?'bg-indigo-50 border-indigo-400':'border-gray-200 hover:border-indigo-300'}`}>
                        <div className="font-medium text-gray-800">{combo.label}</div>
                        <div className="text-xs text-gray-400 mt-0.5">{combo.heat}</div>
                      </button>
                    ))}
                  </div>
                )}

                {/* 自由输入模式 */}
                {genreMode === 'free' && (
                  <div>
                    <input value={form.theme} onChange={(e) => setForm({...form, theme: e.target.value})}
                      placeholder="自定义题材标签，如：都市×悬疑×女主觉醒"
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500" />
                    <p className="text-xs text-gray-400 mt-1">自由描述你的题材方向，选题策划官会依据此输入生成更精准的立项建议</p>
                  </div>
                )}
              </div>

              {/* 其他配置 */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">总集数</label>
                  <input type="number" min={5} max={200} value={form.episode_count}
                    onChange={(e) => setForm({ ...form, episode_count: +e.target.value })}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">目标平台</label>
                  <select value={form.target_platform} onChange={(e) => setForm({ ...form, target_platform: e.target.value })}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
                    {PLATFORM_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">创作模式</label>
                  <select value={form.track_mode} onChange={(e) => setForm({ ...form, track_mode: e.target.value })}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
                    <option value="fast">⚡ 快速（8核心角色）</option>
                    <option value="expert">🎬 专家（12角色）</option>
                  </select>
                </div>
              </div>

              {/* 核心创意 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  一句话核心创意 <span className="text-gray-400 font-normal">（可选，越具体创作质量越高）</span>
                </label>
                <textarea value={form.core_idea} onChange={(e) => setForm({ ...form, core_idea: e.target.value })}
                  placeholder="例：被家人抛弃的天才医生，携带前世记忆重生，在宫廷权谋中用现代医术完成复仇"
                  rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none" />
              </div>

              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setShowNew(false)}
                  className="flex-1 py-2.5 border border-gray-200 text-gray-700 text-sm rounded-xl hover:bg-gray-50">
                  取消
                </button>
                <button type="submit" disabled={createMut.isPending}
                  className="flex-1 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50">
                  {createMut.isPending ? '创建中...' : '🚀 开始创作'}
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
  const completionRate = Math.min(100, Number(project.completion_rate) || 0);
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
            {project.episode_count}集 · {project.target_platform === 'douyin' ? '抖音' : project.target_platform}
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
