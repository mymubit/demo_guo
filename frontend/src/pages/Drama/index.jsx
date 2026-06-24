import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { createDramaProject } from '../../services/drama';
import { works as worksApi } from '../../services/api';
import { normalizeWorkItem } from '../../services/adapters/businessAdapters';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, Badge, Card, EmptyState, Modal } from '../../components/ui';
import { Plus, Sparkles, Film, Zap, Palette, Loader2 } from 'lucide-react';

const GENRE_MATRIX = {
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

const INNOVATIVE_COMBOS = [
  { label: '古装×职场权谋', code: 'ancient-workplace', dims: { emotion:'ambition', identity:'hidden', conflict:'workplace', world:'ancient' }, heat: '新兴热点' },
  { label: '甜宠×悬疑反转', code: 'sweet-mystery',     dims: { emotion:'suspense', identity:'hidden', conflict:'secret', world:'modern' }, heat: '破圈潜力' },
  { label: '普通女性×隐藏大佬', code: 'hidden-boss',   dims: { emotion:'love', identity:'hidden', conflict:'romance', world:'modern' }, heat: '高爆款率' },
  { label: '重生复仇×家族内斗', code: 'reborn-revenge', dims: { emotion:'revenge', identity:'reborn', conflict:'family', world:'modern' }, heat: '经典爆款' },
  { label: '职场逆袭×情感治愈', code: 'career-healing',dims: { emotion:'healing', identity:'ordinary', conflict:'workplace', world:'modern' }, heat: '长尾用户' },
];

const GENRE_DIM_ORDER = ['emotion', 'identity', 'conflict', 'world'];
const THEME_MAX_LENGTH = 64;

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

export default function DramaIndex() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [genreMode, setGenreMode] = useState('matrix');
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

  const { data: projectsRes, isLoading: projectsLoading, isError: projectsError } = useQuery({
    queryKey: ['drama-projects', 'works-unified'],
    queryFn: async () => {
      const result = await worksApi.list(1, 'all', 100, { scope: 'drama', ordering: 'newest' });
      return (result.items || []).map(normalizeWorkItem).map(mapWorkToWorkspace).filter(Boolean);
    },
    onError: (err) => {
      toast.error(`加载项目列表失败：${err?.message || '请刷新重试'}`);
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
    <div className="min-h-full bg-navy-950">
      <div className="bg-navy-900/80 backdrop-blur-xl border-b border-white/10 px-6 py-5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">短剧创作工作室</h1>
            <p className="text-sm text-slate-400 mt-1">12个专业角色 · 双轨创作模式 · AI驱动</p>
          </div>
          <Button
            variant="gold"
            iconLeft={<Plus className="w-4 h-4" />}
            onClick={() => setShowNew(true)}
          >
            新建剧本项目
          </Button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <Card variant="glass" padding="lg" className="border-gold-500/20 bg-gradient-to-br from-gold-500/10 to-navy-900/50">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-gold-500/20 flex items-center justify-center">
                <Zap className="w-5 h-5 text-gold-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">快速通道</h3>
                <Badge tone="gold" size="sm">8核心角色</Badge>
              </div>
            </div>
            <p className="text-sm text-slate-400">适合：初次创作、快速验证、10集以内</p>
            <p className="text-xs text-slate-500 mt-1">立项→世界构建→人设→大纲→剧本→审稿→评分→合规</p>
          </Card>

          <Card variant="glass" padding="lg" className="border-slate-500/20 bg-gradient-to-br from-slate-800/30 to-navy-900/50">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center">
                <Film className="w-5 h-5 text-slate-300" />
              </div>
              <div>
                <h3 className="font-semibold text-white">专家通道</h3>
                <Badge tone="default" size="sm">12角色</Badge>
              </div>
            </div>
            <p className="text-sm text-slate-400">适合：商业精品、30集+长剧、精细化创作</p>
            <p className="text-xs text-slate-500 mt-1">8个职能部门全流程，每个环节都有专业角色</p>
          </Card>
        </div>

        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">我的项目</h2>
            {projects.length > 0 && (
              <span className="text-xs text-slate-500">共 {projects.length} 个项目</span>
            )}
          </div>

          {projects.length === 0 ? (
            <EmptyState
              type="empty-create"
              title="还没有剧本项目"
              description="点击「新建剧本项目」开始你的短剧创作之旅"
              icon={<Palette className="w-12 h-12 text-gold-400" />}
              action={
                <Button variant="gold" onClick={() => setShowNew(true)}>
                  新建剧本项目
                </Button>
              }
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((p) => (
                <ProjectCard
                  key={p.id}
                  project={p}
                  onClick={() => navigate(`/drama/workspace/${p.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <Modal
        open={showNew}
        onClose={() => setShowNew(false)}
        title="新建剧本项目"
        size="2xl"
      >
        <form onSubmit={handleCreate} className="space-y-5 pt-2">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              剧名 <span className="text-red-400">*</span>
            </label>
            <input
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="暂定剧名，可后续修改"
              className="sf-control px-3 py-2.5"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-300">题材定位</label>
              <div className="flex gap-1 bg-white/5 p-0.5 rounded-lg">
                {[['matrix','矩阵选择'],['preset','快速预设'],['free','自由输入']].map(([m,l]) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setGenreMode(m)}
                    className={`px-2.5 py-1 text-xs rounded-md transition-all ${
                      genreMode === m
                        ? 'bg-gold-500/20 text-gold-300 font-medium shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>

            {genreMode === 'matrix' && (
              <div className="space-y-3">
                <div className="bg-gold-500/10 rounded-xl p-4 border border-gold-500/20">
                  <p className="text-xs font-semibold text-gold-400 mb-2.5 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    创新组合推荐（对立面法）
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {INNOVATIVE_COMBOS.map(combo => (
                      <button
                        key={combo.code}
                        type="button"
                        onClick={() => applyCombo(combo)}
                        className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                          computedTheme === combo.code
                            ? 'bg-gold-500 text-navy-950 border-gold-500 shadow-sm'
                            : 'bg-white/5 text-slate-300 border-white/10 hover:border-gold-500/30 hover:text-gold-300'
                        }`}
                      >
                        {combo.heat} · {combo.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(GENRE_MATRIX).map(([axis, config]) => (
                    <div key={axis}>
                      <div className="text-xs font-semibold text-slate-400 mb-1.5">
                        {config.label}
                        <span className="text-slate-500 font-normal ml-1">· {config.hint}</span>
                      </div>
                      <div className="space-y-1">
                        {config.options.map(opt => (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() => selectDim(axis, opt.value)}
                            className={`w-full text-left px-2.5 py-2 rounded-lg text-xs border transition-all ${
                              dimSelections[axis] === opt.value
                                ? 'bg-gold-500 text-navy-950 border-gold-500 font-medium'
                                : 'bg-white/5 text-slate-300 border-white/10 hover:border-gold-500/30 hover:text-gold-300'
                            }`}
                          >
                            <span className="font-medium">{opt.label}</span>
                            <span className={`ml-1 ${dimSelections[axis] === opt.value ? 'text-navy-900/70' : 'text-slate-500'}`}>
                              — {opt.desc}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-white/5 rounded-lg px-3 py-2.5 text-xs text-slate-400 border border-white/10">
                  当前组合：
                  <span className="font-medium text-gold-400 ml-1">
                    {Object.entries(dimSelections).filter(([,v])=>v).map(([axis,val]) => {
                      const opt = GENRE_MATRIX[axis]?.options.find(o => o.value === val);
                      return opt?.label;
                    }).filter(Boolean).join(' × ') || '请从上方选择维度…'}
                  </span>
                </div>
              </div>
            )}

            {genreMode === 'preset' && (
              <div className="grid grid-cols-2 gap-2">
                {INNOVATIVE_COMBOS.map(combo => (
                  <button
                    key={combo.code}
                    type="button"
                    onClick={() => { applyCombo(combo); setForm(f=>({...f,theme:combo.code})); }}
                    className={`p-3 rounded-xl border text-left text-sm transition-all ${
                      form.theme===combo.code
                        ? 'bg-gold-500/15 border-gold-500/30 ring-1 ring-gold-500/30'
                        : 'border-white/10 bg-white/5 hover:border-gold-500/20 hover:bg-gold-500/5'
                    }`}
                  >
                    <div className="font-medium text-slate-200">{combo.label}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{combo.heat}</div>
                  </button>
                ))}
              </div>
            )}

            {genreMode === 'free' && (
              <div>
                <input
                  value={form.theme}
                  onChange={(e) => setForm({...form, theme: e.target.value})}
                  placeholder="自定义题材标签，如：都市×悬疑×女主觉醒"
                  className="sf-control px-3 py-2.5 w-full"
                />
                <p className="text-xs text-slate-500 mt-1.5">自由描述你的题材方向，选题策划官会依据此输入生成更精准的立项建议</p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">总集数</label>
              <input
                type="number"
                min={5}
                max={200}
                value={form.episode_count}
                onChange={(e) => setForm({ ...form, episode_count: +e.target.value })}
                className="sf-control px-3 py-2.5 w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">目标平台</label>
              <select
                value={form.target_platform}
                onChange={(e) => setForm({ ...form, target_platform: e.target.value })}
                className="sf-control px-3 py-2.5 w-full appearance-none"
              >
                {PLATFORM_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">创作模式</label>
              <select
                value={form.track_mode}
                onChange={(e) => setForm({ ...form, track_mode: e.target.value })}
                className="sf-control px-3 py-2.5 w-full appearance-none"
              >
                <option value="fast">⚡ 快速（8核心角色）</option>
                <option value="expert">🎬 专家（12角色）</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              一句话核心创意
              <span className="text-slate-500 font-normal ml-1">（可选，越具体创作质量越高）</span>
            </label>
            <textarea
              value={form.core_idea}
              onChange={(e) => setForm({ ...form, core_idea: e.target.value })}
              placeholder="例：被家人抛弃的天才医生，携带前世记忆重生，在宫廷权谋中用现代医术完成复仇"
              rows={2}
              className="sf-control px-3 py-2.5 w-full resize-none"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="secondary"
              className="flex-1"
              onClick={() => setShowNew(false)}
            >
              取消
            </Button>
            <Button
              type="submit"
              variant="gold"
              className="flex-1"
              isLoading={createMut.isPending}
              iconLeft={<Sparkles className="w-4 h-4" />}
            >
              {createMut.isPending ? '创建中...' : '开始创作'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function ProjectCard({ project, onClick }) {
  const completionRate = Math.min(100, Number(project.completion_rate) || 0);

  return (
    <Card
      interactive
      variant="glass"
      padding="lg"
      onClick={onClick}
      className="cursor-pointer hover:border-gold-500/30"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-white line-clamp-1">{project.title}</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {project.episode_count}集 · {project.target_platform === 'douyin' ? '抖音' : project.target_platform}
          </p>
        </div>
        {project.quality_scores?.grade && project.quality_scores?.overall && (
          <Badge tone="gold" size="sm" className="flex-shrink-0">
            {project.quality_scores.grade}级 {project.quality_scores.overall}分
          </Badge>
        )}
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
          <span>完成度</span>
          <span className="font-medium text-slate-300">{completionRate}%</span>
        </div>
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-gold-400 to-gold-500 rounded-full transition-all shadow-gold/30"
            style={{ width: `${completionRate}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <Badge tone={project.track_mode === 'fast' ? 'gold' : 'default'} size="sm">
          {project.track_mode === 'fast' ? '⚡ 快速通道' : '🎬 专家通道'}
        </Badge>
        <Badge
          tone={
            project.delivery_status === 'delivered'
              ? 'success'
              : project.delivery_status === 'ready'
              ? 'warning'
              : 'default'
          }
          size="sm"
        >
          {project.delivery_status === 'delivered' ? '已交付'
           : project.delivery_status === 'ready' ? '待交付'
           : '创作中'}
        </Badge>
      </div>
    </Card>
  );
}
