import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { createDramaProject, getThemeMatrix } from '../../services/drama';
import { works as worksApi } from '../../services/api';
import { normalizeWorkItem } from '../../services/adapters/businessAdapters';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, Badge, Card, Modal } from '../../components/ui';
import PageShell from '../../components/layout/PageShell';
import EmptyState from '../../components/ui/EmptyState';
import { Plus, Sparkles, Film, Zap, Palette, Loader2, Clock, CheckCircle2 } from 'lucide-react';
import ThemeMatrixPicker from './ThemeMatrixPicker';

const GENRE_DIM_ORDER_FALLBACK = ['emotion', 'identity', 'conflict', 'world'];
const THEME_MAX_LENGTH = 128;

function themeCodeFromDims(dims, dimOrder = GENRE_DIM_ORDER_FALLBACK) {
  return dimOrder.map((axis) => dims[axis]).filter(Boolean).join('-');
}

function buildMatrixThemeCode(dimSelections, flavorTags = [], dimOrder = GENRE_DIM_ORDER_FALLBACK) {
  const axisCode = themeCodeFromDims(dimSelections, dimOrder);
  if (!axisCode) return '';
  const tags = [...new Set(flavorTags.filter(Boolean))].sort();
  if (!tags.length) return axisCode;
  return `${axisCode}|${tags.join('+')}`;
}

function axisDimsFromSelection(dims = {}) {
  const { flavor_tags: _flavorTags, ...axisDims } = dims;
  return axisDims;
}

const PLATFORM_OPTIONS = [
  { value: 'douyin', label: '抖音' },
  { value: 'kuaishou', label: '快手' },
  { value: 'weixin', label: '微信小程序' },
  { value: 'all', label: '通用' },
];

const GENRE_COLORS = {
  revenge: { bg: 'from-red-500/20 to-orange-500/10', accent: 'text-red-400', border: 'border-red-500/20' },
  love: { bg: 'from-pink-500/20 to-rose-500/10', accent: 'text-pink-400', border: 'border-pink-500/20' },
  healing: { bg: 'from-emerald-500/20 to-teal-500/10', accent: 'text-emerald-400', border: 'border-emerald-500/20' },
  suspense: { bg: 'from-indigo-500/20 to-violet-500/10', accent: 'text-indigo-400', border: 'border-indigo-500/20' },
  ambition: { bg: 'from-amber-500/20 to-yellow-500/10', accent: 'text-amber-400', border: 'border-amber-500/20' },
};

function getGenreTheme(theme) {
  const themeStr = String(theme || '');
  if (themeStr.includes('revenge')) return GENRE_COLORS.revenge;
  if (themeStr.includes('love') || themeStr.includes('romance')) return GENRE_COLORS.love;
  if (themeStr.includes('healing')) return GENRE_COLORS.healing;
  if (themeStr.includes('suspense') || themeStr.includes('mystery')) return GENRE_COLORS.suspense;
  if (themeStr.includes('ambition') || themeStr.includes('workplace')) return GENRE_COLORS.ambition;
  return { bg: 'from-gold-500/15 to-navy-800/40', accent: 'text-gold-400', border: 'border-gold-500/20' };
}

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
    updated_at: work.updated_at || work.created_at,
  };
}

export default function DramaIndex() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [matrixPickerSession, setMatrixPickerSession] = useState(0);
  const [genreMode, setGenreMode] = useState('preset');
  const [dimSelections, setDimSelections] = useState({});
  const [flavorTagSelections, setFlavorTagSelections] = useState([]);
  const [form, setForm] = useState({
    title: '',
    theme: '',
    episode_count: 30,
    target_platform: 'douyin',
    track_mode: 'fast',
    core_idea: '',
  });

  const { data: themeMatrixRes, isLoading: themeMatrixLoading, isError: themeMatrixError } = useQuery({
    queryKey: ['drama-theme-matrix'],
    queryFn: () => getThemeMatrix(),
    enabled: showNew,
    staleTime: 5 * 60 * 1000,
    onError: (err) => {
      toast.error(`题材矩阵加载失败：${err?.message || '请刷新重试'}`);
    },
  });

  const themeMatrix = themeMatrixRes || null;
  const dimOrder = themeMatrix?.dim_order || GENRE_DIM_ORDER_FALLBACK;
  const axes = themeMatrix?.axes || {};
  const presetTemplates = themeMatrix?.preset_templates || [];
  const featuredCombos = themeMatrix?.featured_combos || [];
  const flavorConfig = themeMatrix?.flavor_tags || {};
  const flavorGroups = flavorConfig.groups || [];
  const flavorMaxSelect = flavorConfig.max_select || 5;

  const computedTheme = useMemo(() => {
    if (genreMode === 'free') return form.theme;
    if (genreMode === 'preset') return form.theme;
    if (form.theme) return form.theme;
    return buildMatrixThemeCode(dimSelections, flavorTagSelections, dimOrder);
  }, [genreMode, dimSelections, flavorTagSelections, form.theme, dimOrder]);

  const selectDim = (axis, value) => {
    setDimSelections(prev => ({ ...prev, [axis]: prev[axis] === value ? undefined : value }));
    setForm(f => ({ ...f, theme: '' }));
  };

  const toggleFlavorTag = (value) => {
    setFlavorTagSelections((prev) => {
      if (prev.includes(value)) return prev.filter(v => v !== value);
      if (prev.length >= flavorMaxSelect) {
        toast.error(`风味标签最多选 ${flavorMaxSelect} 个`);
        return prev;
      }
      return [...prev, value];
    });
    setForm(f => ({ ...f, theme: '' }));
  };

  const clearCustomSelection = () => {
    setDimSelections({});
    setFlavorTagSelections([]);
    setForm(f => ({ ...f, theme: '' }));
  };

  const clearFlavorTags = () => {
    setFlavorTagSelections([]);
    setForm(f => ({ ...f, theme: '' }));
  };

  const applySelection = (item) => {
    setDimSelections(axisDimsFromSelection(item.dims));
    setFlavorTagSelections(Array.isArray(item.dims?.flavor_tags) ? item.dims.flavor_tags : []);
    setForm(f => ({ ...f, theme: item.code }));
  };

  const { data: projectsRes, isLoading: projectsLoading } = useQuery({
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

  const stats = useMemo(() => {
    const total = projects.length;
    const inProgress = projects.filter(p => p.delivery_status === 'pending' || p.delivery_status === 'creating').length;
    const completed = projects.filter(p => p.delivery_status === 'delivered' || p.completion_rate >= 100).length;
    return { total, inProgress, completed };
  }, [projects]);

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
    const themeCode = (computedTheme || '').trim();
    if (genreMode !== 'free' && !themeCode) {
      toast.error('请先选择题材组合');
      return;
    }
    const finalTheme = themeCode || 'custom';
    if (finalTheme.length > THEME_MAX_LENGTH) {
      toast.error(`题材代码过长（${themeCode.length}/${THEME_MAX_LENGTH}），请减少维度选择或使用预设组合`);
      return;
    }
    createMut.mutate({
      title: form.title,
      theme: finalTheme,
      episode_count: form.episode_count,
      target_platform: form.target_platform,
      track_mode: form.track_mode,
      core_idea: form.core_idea,
    });
  };

  const openNewProject = (trackMode = 'fast') => {
    setDimSelections({});
    setFlavorTagSelections([]);
    setGenreMode('preset');
    setForm({
      title: '',
      theme: '',
      episode_count: 30,
      target_platform: 'douyin',
      track_mode: trackMode,
      core_idea: '',
    });
    setMatrixPickerSession(s => s + 1);
    setShowNew(true);
  };

  return (
    <PageShell
      title="短剧创作工作室"
      description="12个专业角色协作 · 双轨创作模式 · AI驱动全流程"
      maxWidth="xl"
      actions={
        <Button
          variant="gold"
          iconLeft={<Plus className="w-4 h-4" />}
          onClick={() => openNewProject('fast')}
        >
          新建剧本项目
        </Button>
      }
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-8">
        <Card variant="glass" padding="md" className="bg-gradient-to-br from-gold-500/10 to-transparent border-gold-500/20">
          <div className="text-2xl sm:text-3xl font-bold text-white">{stats.total}</div>
          <div className="text-xs sm:text-sm text-slate-400 mt-1">全部项目</div>
        </Card>
        <Card variant="glass" padding="md">
          <div className="text-2xl sm:text-3xl font-bold text-gold-400">{stats.inProgress}</div>
          <div className="text-xs sm:text-sm text-slate-400 mt-1">创作中</div>
        </Card>
        <Card variant="glass" padding="md">
          <div className="text-2xl sm:text-3xl font-bold text-emerald-400">{stats.completed}</div>
          <div className="text-xs sm:text-sm text-slate-400 mt-1">已完成</div>
        </Card>
        <Card variant="glass" padding="md" className="bg-gradient-to-br from-cyan-500/10 to-transparent border-cyan-500/20">
          <div className="text-2xl sm:text-3xl font-bold text-cyan-400">12</div>
          <div className="text-xs sm:text-sm text-slate-400 mt-1">专业角色</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <Card
          variant="glass"
          padding="lg"
          className="border-gold-500/30 bg-gradient-to-br from-gold-500/10 via-gold-500/5 to-navy-900/40 cursor-pointer hover:border-gold-500/50 transition-all group"
          onClick={() => openNewProject('fast')}
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gold-500/20 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
              <Zap className="w-6 h-6 text-gold-400" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1.5">
                <h3 className="font-semibold text-white text-lg">快速通道</h3>
                <Badge tone="gold" size="sm">推荐</Badge>
              </div>
              <p className="text-sm text-slate-400 mb-2">适合：初次创作、快速验证创意、30集以内短剧</p>
              <p className="text-xs text-slate-500">立项 → 世界构建 → 人设 → 大纲 → 剧本 → 审稿 → 交付</p>
            </div>
          </div>
        </Card>

        <Card
          variant="glass"
          padding="lg"
          className="border-slate-500/20 bg-gradient-to-br from-slate-700/20 to-navy-900/40 cursor-pointer hover:border-slate-500/40 transition-all group"
          onClick={() => openNewProject('expert')}
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-slate-700/50 flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform">
              <Film className="w-6 h-6 text-slate-300" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1.5">
                <h3 className="font-semibold text-white text-lg">专家通道</h3>
                <Badge tone="default" size="sm">全流程</Badge>
              </div>
              <p className="text-sm text-slate-400 mb-2">适合：商业精品、80集+长剧、精细化打磨</p>
              <p className="text-xs text-slate-500">8个职能部门 · 12个专业角色 · 多轮评审优化</p>
            </div>
          </div>
        </Card>
      </div>

      <div>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-white">我的剧本项目</h2>
          {projects.length > 0 && (
            <span className="text-sm text-slate-500">共 {projects.length} 个项目</span>
          )}
        </div>

        {projectsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1,2,3,4,5,6].map(i => (
              <Card key={i} variant="glass" padding="none" className="overflow-hidden">
                <div className="aspect-video bg-white/5 animate-pulse" />
                <div className="p-5 space-y-3">
                  <div className="h-5 bg-white/10 rounded w-3/4 animate-pulse" />
                  <div className="h-3 bg-white/5 rounded w-1/2 animate-pulse" />
                  <div className="h-2 bg-white/5 rounded-full animate-pulse" />
                  <div className="flex justify-between pt-2">
                    <div className="h-6 bg-white/5 rounded w-20 animate-pulse" />
                    <div className="h-6 bg-white/5 rounded w-16 animate-pulse" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <EmptyState
            type="empty-create"
            title="还没有剧本项目"
            description="选择创作模式，开始你的第一部短剧创作"
            icon={<Palette className="w-12 h-12 text-gold-400" />}
            actionLabel="新建剧本项目"
            onAction={() => openNewProject('fast')}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
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

      <Modal
        open={showNew}
        onClose={() => setShowNew(false)}
        title="新建剧本项目"
        size="full"
      >
        <form onSubmit={handleCreate} className="space-y-6 pt-1">
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
            <div className="xl:col-span-5">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                剧名 <span className="text-red-400">*</span>
              </label>
              <input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="暂定剧名，可后续修改"
                className="sf-control px-4 py-3 w-full text-base"
              />
            </div>
            <div className="xl:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">总集数</label>
                <input
                  type="number"
                  min={5}
                  max={200}
                  value={form.episode_count}
                  onChange={(e) => setForm({ ...form, episode_count: +e.target.value })}
                  className="sf-control px-4 py-3 w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">目标平台</label>
                <select
                  value={form.target_platform}
                  onChange={(e) => setForm({ ...form, target_platform: e.target.value })}
                  className="sf-control px-4 py-3 w-full appearance-none"
                >
                  {PLATFORM_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">创作模式</label>
                <select
                  value={form.track_mode}
                  onChange={(e) => setForm({ ...form, track_mode: e.target.value })}
                  className="sf-control px-4 py-3 w-full appearance-none"
                >
                  <option value="fast">⚡ 快速（8核心角色）</option>
                  <option value="expert">🎬 专家（12角色）</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-slate-300">题材定位</label>
              <div className="flex gap-1 bg-slate-800/80 p-0.5 rounded-lg border border-white/10">
                {[['preset','快速预设'],['matrix','组合搭配'],['free','自由输入']].map(([m,l]) => (
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

            {themeMatrixLoading ? (
              <div className="rounded-xl border border-white/10 bg-slate-900/60 p-6 flex items-center justify-center gap-2 text-sm text-slate-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                加载题材矩阵…
              </div>
            ) : themeMatrixError || !themeMatrix ? (
              <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-300">
                题材矩阵加载失败，请关闭弹窗后重试，或切换到「自由输入」。
              </div>
            ) : null}

            {!themeMatrixLoading && themeMatrix && genreMode === 'matrix' && (
              <ThemeMatrixPicker
                key={`matrix-${matrixPickerSession}`}
                dimOrder={dimOrder}
                axes={axes}
                featuredCombos={featuredCombos}
                flavorConfig={flavorConfig}
                flavorGroups={flavorGroups}
                flavorMaxSelect={flavorMaxSelect}
                dimSelections={dimSelections}
                flavorTagSelections={flavorTagSelections}
                activeThemeCode={form.theme || computedTheme}
                onSelectDim={selectDim}
                onToggleFlavorTag={toggleFlavorTag}
                onApplyCombo={applySelection}
                onClearCustom={clearCustomSelection}
                onClearFlavorTags={clearFlavorTags}
              />
            )}

            {!themeMatrixLoading && themeMatrix && genreMode === 'preset' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 rounded-xl border border-white/10 bg-slate-900/60 p-4">
                {presetTemplates.map(preset => (
                  <button
                    key={preset.code}
                    type="button"
                    onClick={() => applySelection(preset)}
                    className={`p-4 rounded-xl border text-left transition-all min-h-[80px] w-full ${
                      form.theme === preset.code
                        ? 'bg-gold-500/20 border-gold-500/40 ring-1 ring-gold-500/30'
                        : 'border-white/12 bg-slate-950/60 hover:border-gold-500/30 hover:bg-gold-500/10'
                    }`}
                  >
                    <div className="font-medium text-base text-slate-100">{preset.label}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{preset.code}</div>
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

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              一句话核心创意
              <span className="text-slate-500 font-normal ml-1">（可选，越具体创作质量越高）</span>
            </label>
            <textarea
              value={form.core_idea}
              onChange={(e) => setForm({ ...form, core_idea: e.target.value })}
              placeholder="例：被家人抛弃的天才医生，携带前世记忆重生，在宫廷权谋中用现代医术完成复仇"
              rows={3}
              className="sf-control px-4 py-3 w-full resize-none text-base"
            />
          </div>

          <div className="flex gap-4 pt-1">
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
    </PageShell>
  );
}

function ProjectCard({ project, onClick }) {
  const completionRate = Math.min(100, Number(project.completion_rate) || 0);
  const genreTheme = getGenreTheme(project.theme);
  const platformLabel = project.target_platform === 'douyin' ? '抖音'
    : project.target_platform === 'kuaishou' ? '快手'
    : project.target_platform === 'weixin' ? '微信'
    : '通用';

  const isCompleted = project.delivery_status === 'delivered' || completionRate >= 100;
  const isCreating = !isCompleted && completionRate > 0;

  return (
    <Card
      interactive
      variant="glass"
      padding="none"
      onClick={onClick}
      className="cursor-pointer hover:border-white/20 transition-all overflow-hidden group"
    >
      <div className={`aspect-video bg-gradient-to-br ${genreTheme.bg} relative overflow-hidden border-b border-white/5`}>
        <div className="absolute inset-0 flex items-center justify-center">
          <Film className={`w-12 h-12 ${genreTheme.accent} opacity-40 group-hover:opacity-60 transition-opacity`} />
        </div>
        <div className="absolute top-3 right-3">
          {isCompleted ? (
            <Badge tone="success" size="sm" className="shadow-lg">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              已完成
            </Badge>
          ) : isCreating ? (
            <Badge tone="gold" size="sm" className="shadow-lg">
              <Clock className="w-3 h-3 mr-1 animate-pulse" />
              创作中
            </Badge>
          ) : (
            <Badge tone="default" size="sm" className="shadow-lg">
              草稿
            </Badge>
          )}
        </div>
        {project.quality_scores?.grade && project.quality_scores?.overall && (
          <div className="absolute bottom-3 left-3">
            <Badge tone="gold" size="sm" className="shadow-lg">
              {project.quality_scores.grade}级 · {project.quality_scores.overall}分
            </Badge>
          </div>
        )}
      </div>

      <div className="p-5">
        <h3 className="font-semibold text-white text-base line-clamp-1 group-hover:text-gold-300 transition-colors">
          {project.title}
        </h3>
        <p className="text-xs text-slate-500 mt-1.5 flex items-center gap-2">
          <span>{project.episode_count}集</span>
          <span className="w-1 h-1 rounded-full bg-slate-600" />
          <span>{platformLabel}</span>
          <span className="w-1 h-1 rounded-full bg-slate-600" />
          <span>{project.track_mode === 'fast' ? '快速模式' : '专家模式'}</span>
        </p>

        <div className="mt-4">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-slate-500">完成进度</span>
            <span className="font-medium text-slate-300">{completionRate}%</span>
          </div>
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all shadow-gold/30 ${
                isCompleted
                  ? 'bg-gradient-to-r from-emerald-400 to-emerald-500'
                  : 'bg-gradient-to-r from-gold-400 to-gold-500'
              }`}
              style={{ width: `${completionRate}%` }}
            />
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <Badge tone={project.track_mode === 'fast' ? 'gold' : 'default'} size="sm">
            {project.track_mode === 'fast' ? '⚡ 快速通道' : '🎬 专家通道'}
          </Badge>
          <span className="text-xs text-slate-500 group-hover:text-gold-400 transition-colors flex items-center gap-1">
            进入工作台
            <span className="group-hover:translate-x-0.5 transition-transform">→</span>
          </span>
        </div>
      </div>
    </Card>
  );
}
