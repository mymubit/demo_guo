import { useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  getDramaProject,
  getEpisodeContent,
  getEpisodeList,
  getQualityRadar,
  applyEpisodeSuggestions,
} from '../../services/drama';
import { Button, Badge, Card, Tabs } from '../../components/ui';
import {
  ArrowLeft, Loader2, BookOpen, BarChart3, ChevronLeft, ChevronRight,
  List, Download, FileText, CheckCircle2,
} from 'lucide-react';
import { toast } from 'sonner';
import { useMutation, useQueryClient } from '@tanstack/react-query';

function formatPlatform(platform) {
  const map = { douyin: '抖音', kuaishou: '快手', weixin: '微信小程序', all: '通用' };
  return map[platform] || platform || '';
}

export default function ScriptsPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'script');
  const [episode, setEpisode] = useState(1);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { data: projectRes, isLoading: projectLoading } = useQuery({
    queryKey: ['drama-project', projectId],
    queryFn: () => getDramaProject(projectId),
    enabled: Boolean(projectId && projectId !== 'undefined'),
    onError: (err) => toast.error(`加载项目失败：${err?.message || '请刷新'}`),
  });
  const project = projectRes?.data ?? projectRes;

  const { data: episodesRes, isLoading: epsLoading } = useQuery({
    queryKey: ['drama-episodes', projectId],
    queryFn: () => getEpisodeList(projectId),
    enabled: Boolean(projectId && projectId !== 'undefined'),
    onError: (err) => toast.error(`加载集数列表失败：${err?.message || '将重试'}`),
  });
  const completedEpisodes = episodesRes?.data?.completed_episodes || 0;
  const episodeStatuses = episodesRes?.data?.episodes || Array.from({ length: completedEpisodes }, (_, i) => ({ number: i + 1, status: 'done' }));
  const maxEpisode = Math.max(1, completedEpisodes || project?.episode_count || 1);

  const { data: scriptRes, isLoading: scriptLoading } = useQuery({
    queryKey: ['drama-script-ep', projectId, episode],
    queryFn: () => getEpisodeContent(projectId, episode),
    enabled: Boolean(projectId && projectId !== 'undefined') && episode > 0 && episode <= maxEpisode,
    onError: (err) => {
      const msg = err?.message || '';
      if (!msg.includes('404') && !msg.includes('尚未') && !msg.includes('not found')) {
        toast.error(`加载剧本失败：${msg || '请刷新'}`);
      }
    },
    retry: false,
  });
  const scriptData = scriptRes?.data ?? scriptRes;

  const { data: qualityRes, isLoading: qualityLoading } = useQuery({
    queryKey: ['drama-quality', projectId, episode],
    queryFn: () => getQualityRadar(projectId, episode),
    enabled: Boolean(projectId && projectId !== 'undefined') && activeTab === 'quality',
    onError: (err) => {
      const msg = err?.message || '';
      if (!msg.includes('404') && !msg.includes('尚未')) {
        toast.error(`加载质量报告失败：${msg || ''}`);
      }
    },
    retry: false,
  });
  const quality = qualityRes?.data ?? qualityRes;

  const applyRevM = useMutation({
    mutationFn: (suggestionId) => applyEpisodeSuggestions(projectId, episode, [suggestionId]),
    onSuccess: (res) => {
      const data = res?.data ?? res;
      toast.success(data?.message || '修改已应用');
      queryClient.invalidateQueries(['drama-script-ep', projectId, episode]);
      queryClient.invalidateQueries(['drama-episodes', projectId]);
    },
    onError: (err) => toast.error(`应用失败：${err?.message || ''}`),
  });

  const tabs = [
    { id: 'script', label: '剧本', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'quality', label: '质量评分', icon: <BarChart3 className="w-4 h-4" /> },
  ];

  const changeEpisode = (ep) => {
    if (ep >= 1 && ep <= maxEpisode) {
      setEpisode(ep);
      setSidebarOpen(false);
    }
  };

  const goPrev = () => changeEpisode(episode - 1);
  const goNext = () => changeEpisode(episode + 1);

  if (!projectId || projectId === 'undefined') {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-slate-400">
        <p>无效的项目地址。</p>
        <Button variant="brand" onClick={() => navigate('/drama')}>返回创作中心</Button>
      </div>
    );
  }

  if (projectLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <Loader2 className="w-6 h-6 text-gold-500 animate-spin" />
        <p className="text-slate-400 text-sm">加载剧本中...</p>
      </div>
    );
  }

  const hasContent = scriptData?.content || scriptData?.script_html || scriptData?.html_content;

  return (
    <div className="min-h-screen bg-navy-950 flex flex-col">
      <header className="sticky top-0 z-30 bg-navy-950/80 backdrop-blur-xl border-b border-white/10 shadow-lg shadow-black/10 flex-shrink-0">
        <div className="px-4 py-3 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => navigate(`/drama/workspace/${projectId}`)}
              className="p-2 rounded-lg text-slate-400 hover:bg-white/5 hover:text-slate-200 transition-colors"
              aria-label="返回工作台"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={`p-2 rounded-lg transition-colors lg:hidden ${
                sidebarOpen ? 'bg-gold-500/20 text-gold-400' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
              }`}
              aria-label="分集列表"
            >
              <List className="w-5 h-5" />
            </button>
            <div className="min-w-0 hidden sm:block">
              <h1 className="text-lg font-bold text-white truncate">{project?.title}</h1>
              <p className="text-xs text-slate-500">
                {project?.episode_count} 集 · {formatPlatform(project?.target_platform)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center bg-white/5 rounded-xl border border-white/10 p-1">
              <button
                onClick={goPrev}
                disabled={episode <= 1}
                className="p-1.5 rounded-lg hover:bg-white/5 disabled:opacity-30 text-slate-400 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <select
                value={episode}
                onChange={(e) => changeEpisode(Number(e.target.value))}
                className="bg-transparent text-sm text-slate-200 font-medium px-2 focus:outline-none cursor-pointer"
              >
                {Array.from({ length: maxEpisode }, (_, i) => (
                  <option key={i+1} value={i+1} className="bg-navy-900 text-slate-200">第 {i+1} 集</option>
                ))}
              </select>
              <button
                onClick={goNext}
                disabled={episode >= maxEpisode}
                className="p-1.5 rounded-lg hover:bg-white/5 disabled:opacity-30 text-slate-400 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <Button
              variant="secondary"
              size="sm"
              iconLeft={<Download className="w-4 h-4" />}
              onClick={() => toast.info('导出功能开发中')}
            >
              导出
            </Button>
          </div>
        </div>

        <div className="px-4 pb-0">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={(id) => { setActiveTab(id); setSearchParams({ tab: id }); }} />
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside
          className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-20 w-64 bg-navy-900/95 backdrop-blur-xl border-r border-white/10 flex flex-col transition-transform lg:transition-none flex-shrink-0 mt-14 lg:mt-0`}
        >
          <div className="p-4 border-b border-white/5">
            <h3 className="text-sm font-semibold text-slate-200">分集列表</h3>
            <p className="text-xs text-slate-500 mt-1">已生成 {completedEpisodes}/{maxEpisode} 集</p>
          </div>
          <div className="flex-1 overflow-y-auto py-2 scrollbar-thin">
            {Array.from({ length: maxEpisode }, (_, i) => {
              const ep = i + 1;
              const isDone = ep <= completedEpisodes;
              const isActive = ep === episode;
              return (
                <button
                  key={ep}
                  onClick={() => changeEpisode(ep)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                    isActive
                      ? 'bg-gold-500/10 border-r-2 border-gold-500 text-gold-300'
                      : isDone
                        ? 'text-slate-300 hover:bg-white/5'
                        : 'text-slate-500 opacity-60'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  ) : (
                    <FileText className="w-4 h-4 flex-shrink-0" />
                  )}
                  <span className="text-sm font-medium">第 {ep} 集</span>
                </button>
              );
            })}
          </div>
        </aside>

        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-10 lg:hidden mt-14"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-4 sm:px-8 py-6 pb-24">
            {activeTab === 'script' && (
              <ScriptContent
                loading={scriptLoading}
                data={scriptData}
                episode={episode}
                hasContent={hasContent}
                projectId={projectId}
                onNavigate={navigate}
                maxEpisode={maxEpisode}
                onPrev={goPrev}
                onNext={goNext}
              />
            )}
            {activeTab === 'quality' && (
              <QualityContent loading={qualityLoading} quality={quality} episode={episode} />
            )}
          </div>
        </main>
      </div>

      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-20 bg-navy-900/95 backdrop-blur-xl border-t border-white/10 px-4 py-3 flex items-center justify-between">
        <Button
          variant="secondary"
          size="sm"
          disabled={episode <= 1}
          onClick={goPrev}
          iconLeft={<ChevronLeft className="w-4 h-4" />}
        >
          上一集
        </Button>
        <span className="text-sm text-slate-400">第 {episode}/{maxEpisode} 集</span>
        <Button
          variant="gold"
          size="sm"
          disabled={episode >= maxEpisode}
          onClick={goNext}
        >
          下一集
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}

function ScriptContent({ loading, data, episode, hasContent, projectId, onNavigate, maxEpisode, onPrev, onNext }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 className="w-6 h-6 text-gold-500 animate-spin" />
        <p className="text-slate-400 text-sm">加载第 {episode} 集剧本...</p>
      </div>
    );
  }

  if (!hasContent) {
    return (
      <Card variant="default" padding="xl" className="max-w-md mx-auto mt-20 text-center border-white/10 bg-white/[0.04]">
        <div className="text-5xl mb-4">📝</div>
        <h3 className="text-lg font-semibold text-slate-100 mb-2">第 {episode} 集剧本尚未生成</h3>
        <p className="text-slate-400 text-sm mb-6">
          请先前往工作台执行剧本执笔师角色来生成剧本内容
        </p>
        <Button variant="brand" onClick={() => onNavigate(`/drama/workspace/${projectId}`)}>
          前往工作台
        </Button>
      </Card>
    );
  }

  const contentHtml = data?.script_html || data?.html_content;
  const contentText = data?.content || data?.text || '';

  return (
    <article className="prose prose-invert max-w-none">
      <Card padding="xl" className="border-white/10 bg-white/[0.03] backdrop-blur-sm">
        <header className="mb-8 pb-6 border-b border-white/5 text-center">
          <p className="text-xs text-gold-400 font-medium tracking-wider uppercase mb-3">第 {episode} 集</p>
          <h2 className="text-2xl sm:text-3xl font-serif font-bold text-white mb-3">
            {data?.title || `第 ${episode} 集`}
          </h2>
          {data?.summary && (
            <p className="text-slate-400 text-sm leading-relaxed max-w-xl mx-auto">{data.summary}</p>
          )}
        </header>

        {contentHtml ? (
          <div
            className="sf-script-content text-slate-200 leading-[1.85] text-[15px]"
            dangerouslySetInnerHTML={{ __html: contentHtml }}
          />
        ) : (
          <pre className="whitespace-pre-wrap font-sans text-sm text-slate-200 leading-relaxed font-[inherit]">
            {contentText}
          </pre>
        )}
      </Card>

      <div className="hidden lg:flex items-center justify-between mt-8 pt-6 border-t border-white/5">
        <Button
          variant="secondary"
          onClick={onPrev}
          disabled={episode <= 1}
          iconLeft={<ChevronLeft className="w-4 h-4" />}
        >
          上一集
        </Button>
        <span className="text-sm text-slate-500">第 {episode} / {maxEpisode} 集</span>
        <Button
          variant="gold"
          onClick={onNext}
          disabled={episode >= maxEpisode}
        >
          下一集
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>
    </article>
  );
}

function QualityContent({ loading, quality, episode }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 className="w-6 h-6 text-gold-500 animate-spin" />
        <p className="text-slate-400 text-sm">加载质量报告...</p>
      </div>
    );
  }

  if (!quality || !quality.scores) {
    return (
      <Card variant="default" padding="xl" className="max-w-md mx-auto mt-20 text-center border-white/10 bg-white/[0.04]">
        <div className="text-5xl mb-4">📊</div>
        <h3 className="text-lg font-semibold text-slate-100 mb-2">第 {episode} 集尚未质检</h3>
        <p className="text-slate-400 text-sm">请先执行质量分析师角色</p>
      </Card>
    );
  }

  const scores = quality.scores || {};
  const scoreKeys = Object.keys(scores);
  const totalScore = scoreKeys.length > 0
    ? Math.round(scoreKeys.reduce((sum, k) => sum + (typeof scores[k] === 'number' ? scores[k] : 0), 0) / scoreKeys.length)
    : 0;
  const grade = totalScore >= 90 ? 'S' : totalScore >= 80 ? 'A' : totalScore >= 70 ? 'B' : totalScore >= 60 ? 'C' : 'D';

  const gradeColor = {
    S: 'text-emerald-400',
    A: 'text-gold-400',
    B: 'text-cyan-400',
    C: 'text-orange-400',
    D: 'text-red-400',
  }[grade] || 'text-slate-300';

  return (
    <div className="space-y-6">
      <Card padding="xl" className="border-gold-500/20 bg-gradient-to-br from-gold-600/10 to-navy-900/60 backdrop-blur-sm text-center">
        <p className="text-sm text-gold-300/80 mb-2">第 {episode} 集 · 综合质量评分</p>
        <div className={`text-7xl font-bold ${gradeColor} mb-2 font-serif`}>{totalScore}</div>
        <Badge tone={totalScore >= 80 ? 'success' : totalScore >= 70 ? 'brand' : 'danger'} size="lg">{grade} 级</Badge>
      </Card>

      {scoreKeys.length > 0 && (
        <Card padding="lg" className="border-white/10 bg-white/[0.04]">
          <h3 className="text-base font-semibold text-slate-100 mb-4">维度评分</h3>
          <div className="space-y-3">
            {scoreKeys.map((key) => {
              const pct = typeof scores[key] === 'number' ? scores[key] : 0;
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300">{key}</span>
                    <span className="text-slate-100 font-medium">{pct}</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        pct >= 80 ? 'bg-emerald-500' : pct >= 70 ? 'bg-gold-500' : 'bg-orange-500'
                      }`}
                      style={{ width: `${Math.min(100, pct)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {quality.summary && (
        <Card padding="lg" className="border-white/10 bg-white/[0.04]">
          <h3 className="text-base font-semibold text-slate-100 mb-3">质检总结</h3>
          <p className="text-sm text-slate-400 leading-relaxed">{quality.summary}</p>
        </Card>
      )}

      {quality.suggestions && quality.suggestions.length > 0 && (
        <Card padding="lg" className="border-white/10 bg-white/[0.04]">
          <h3 className="text-base font-semibold text-slate-100 mb-4">修改建议</h3>
          <div className="space-y-3">
            {quality.suggestions.map((sugg, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20">
                <p className="text-sm text-amber-300 mb-2">{sugg.text || sugg}</p>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => applyRevM.mutate(sugg.id || idx)}
                  isLoading={applyRevM.isPending && applyRevM.variables === (sugg.id || idx)}
                >
                  应用此建议
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
