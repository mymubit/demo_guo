import { useState, useRef, useMemo, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDramaProject,
  getEpisodeList,
  getEpisodeContent,
  getEpisodeQualityList,
  getQualityRadar,
  applyEpisodeSuggestions,
} from '../../services/drama';
import { Button, Badge, Card } from '../../components/ui';
import { ArrowLeft, Loader2, Copy, AlertTriangle, Check, X, CheckCircle2 } from 'lucide-react';

const GRADE_CONFIG = {
  S: { tone: 'accent', label: 'S · 商业精品' },
  A: { tone: 'success', label: 'A · 质量优良' },
  B: { tone: 'brand', label: 'B · 达到基准' },
  C: { tone: 'warning', label: 'C · 需要优化' },
  D: { tone: 'danger', label: 'D · 不达标' },
};

const SEVERITY_CONFIG = {
  error:   { tone: 'danger',  icon: '✕', label: '必须修复', bgClass: 'bg-danger-50', borderClass: 'border-danger-200' },
  warning: { tone: 'warning', icon: '⚠', label: '建议优化', bgClass: 'bg-warning-50', borderClass: 'border-warning-200' },
  info:    { tone: 'info',    icon: '💡', label: '参考建议', bgClass: 'bg-info-50', borderClass: 'border-info-200' },
};

const DIM_META = {
  format:      { name: '格式规范',   abbr: '格式', color: 'var(--brand-600)', subItems: ['场景头格式','台词格式','△标记','字数达标','台词占比','场景数量'] },
  narrative:   { name: '叙事效率',   abbr: '叙事', color: 'var(--brand-700)', subItems: ['推进型节拍占比','无废戏','节奏紧凑','进入-升级-退出'] },
  conflict:    { name: '冲突处理',   abbr: '冲突', color: 'var(--accent-600)', subItems: ['核心冲突贯穿','持续升级','反转自然','解决有力'] },
  character:   { name: '角色一致性', abbr: '角色', color: 'var(--accent-700)', subItems: ['对白辨识度','行为符合人设','知识边界','Ghost/Lie/Flaw'] },
  emotion:     { name: '情感深度',   abbr: '情感', color: 'var(--success-600)', subItems: ['情感弧线完整','每集3-5次情绪','复杂情绪','切换自然'] },
  logic:       { name: '逻辑一致性', abbr: '逻辑', color: 'var(--warning-600)', subItems: ['与前集一致','与大纲一致','记忆检查点匹配','无逻辑断裂'] },
  satisfaction:{ name: '爽点密度',   abbr: '爽感', color: 'var(--info-600)', subItems: ['每集2-3个爽点','打脸','揭穿','逆袭','宣爱','类型多样'] },
  hooks:       { name: '钩子强度',   abbr: '钩子', color: 'var(--success-700)', subItems: ['开头10秒抓力','集末cliffhanger','付费墙前钩子极强'] },
  paywall:     { name: '付费点优化', abbr: '付费', color: 'var(--danger-600)', subItems: ['付费墙在最大张力处','付费后立即兑现','S级付费设计'] },
  genre_fit:   { name: '赛道匹配度', abbr: '赛道', color: 'var(--accent-500)', subItems: ['符合赛道套路','受众预期匹配','平台特性适配'] },
};

const DIM_KEYS = ['format','narrative','conflict','character','emotion','logic','satisfaction','hooks','paywall','genre_fit'];

export default function ScriptsPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [tab, setTab] = useState(searchParams.get('tab') || 'scripts');
  const [selectedEpisode, setSelectedEpisode] = useState(null);
  const reportRef = useRef(null);

  const { data: projectRes } = useQuery({
    queryKey: ['drama-project', projectId],
    queryFn: () => getDramaProject(projectId),
  });
  const project = projectRes?.data || projectRes;

  const { data: episodesRes } = useQuery({
    queryKey: ['drama-episodes', projectId],
    queryFn: () => getEpisodeList(projectId),
  });
  const episodes = episodesRes?.data?.episodes || [];
  const completedCount = episodesRes?.data?.completed_episodes || 0;

  const { data: qualityListRes } = useQuery({
    queryKey: ['drama-episode-quality-list', projectId],
    queryFn: () => getEpisodeQualityList(projectId),
  });
  const qualityList = qualityListRes?.data?.episodes || [];

  const { data: radarRes } = useQuery({
    queryKey: ['drama-quality-radar', projectId, selectedEpisode],
    queryFn: () => getQualityRadar(projectId, selectedEpisode),
    enabled: tab === 'quality',
  });
  const radar = radarRes?.data;

  const { data: episodeContentRes } = useQuery({
    queryKey: ['drama-episode-content', projectId, selectedEpisode],
    queryFn: () => getEpisodeContent(projectId, selectedEpisode),
    enabled: !!selectedEpisode && tab === 'scripts',
  });
  const episodeContent = episodeContentRes?.data;

  const applyMut = useMutation({
    mutationFn: ({ episodeNumber, suggestions, agentId }) =>
      applyEpisodeSuggestions(projectId, episodeNumber, suggestions, agentId),
    onSuccess: () => {
      queryClient.invalidateQueries(['drama-episode-content', projectId, selectedEpisode]);
    },
  });

  if (!project) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
    </div>
  );

  const totalScore = radar?.overall_score || 0;
  const grade = radar?.grade || '—';
  const gradeCfg = GRADE_CONFIG[grade] || GRADE_CONFIG.D;

  return (
    <div className="min-h-screen bg-slate-25">
      <div className="bg-white border-b border-slate-200 px-6 py-3 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(`/drama/workspace/${projectId}`)}
              className="text-slate-400 hover:text-slate-700 transition-colors p-1 -ml-1"
              aria-label="返回工作台"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className="font-bold text-slate-900">《{project.title}》</h1>
              <p className="text-xs text-slate-400">{project.episode_count}集 · {completedCount}集已生成</p>
            </div>
          </div>
          <div className="flex gap-2">
            {['scripts','quality'].map((t) => (
              <Button
                key={t}
                variant={tab === t ? 'brand' : 'secondary'}
                onClick={() => setTab(t)}
              >
                {t === 'scripts' ? '📖 剧本内容' : '📊 质量报告'}
              </Button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-5 flex gap-5">
        <div className="w-44 flex-shrink-0">
          <Card padding="none" className="overflow-hidden sticky top-16">
            <div className="px-3 py-2 bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-600">
              分集（{completedCount}/{project.episode_count}）
            </div>
            <div className="max-h-[calc(100vh-120px)] overflow-y-auto">
              {completedCount === 0 && (
                <div className="p-4 text-xs text-slate-400 text-center">暂无已生成的集数</div>
              )}
              {Array.from({ length: Math.max(completedCount, qualityList.length) }, (_, i) => {
                const ep = i + 1;
                const q = qualityList.find((q) => q.episode_number === ep);
                const g = q?.grade;
                const gCfg = g ? GRADE_CONFIG[g] : null;
                return (
                  <button
                    key={ep}
                    onClick={() => setSelectedEpisode(ep)}
                    className={`w-full px-3 py-2.5 text-left flex items-center justify-between hover:bg-slate-50 transition-colors text-sm ${
                      selectedEpisode === ep ? 'bg-brand-50 border-l-2 border-brand-500' : 'border-l-2 border-transparent'
                    }`}
                  >
                    <span className="text-slate-700 font-medium">第{ep}集</span>
                    {g ? (
                      <Badge tone={gCfg?.tone || 'default'} size="sm">{g}</Badge>
                    ) : ep <= completedCount ? (
                      <span className="text-slate-300 text-xs">—</span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </Card>
        </div>

        <div className="flex-1 min-w-0">
          {tab === 'scripts' ? (
            <ScriptView
              episode={selectedEpisode}
              content={episodeContent}
              applyMut={applyMut}
              qualityList={qualityList}
            />
          ) : (
            <QualityReport
              radar={radar}
              episode={selectedEpisode}
              qualityList={qualityList}
              totalEpisodes={project.episode_count}
              projectTitle={project.title}
              reportRef={reportRef}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function ScriptView({ episode, content, applyMut, qualityList }) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [copied, setCopied] = useState(false);
  const quality = qualityList.find((q) => q.episode_number === episode);
  const gradeCfg = quality?.grade ? GRADE_CONFIG[quality.grade] : null;

  const handleCopy = async () => {
    if (!content?.content) return;
    try {
      await navigator.clipboard.writeText(content.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('复制失败:', err);
    }
  };

  if (!episode) return (
    <Card padding="xl" className="text-center">
      <div className="text-4xl mb-3">📖</div>
      <p className="text-slate-400">从左侧选择集数查看剧本内容</p>
    </Card>
  );

  return (
    <div className="space-y-4">
      <Card padding="lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900 text-lg">第{episode}集</h3>
            <div className="flex gap-3 mt-1.5 text-xs text-slate-500">
              {content?.word_count && <span>📝 {content.word_count}字</span>}
              {content?.version && <span>版本 v{content.version}</span>}
              {quality?.overall_score && (
                <span className={`font-semibold ${gradeCfg ? '' : ''}`}>
                  <Badge tone={gradeCfg?.tone || 'default'} size="sm">
                    质量 {quality.overall_score}分 ({quality.grade})
                  </Badge>
                </span>
              )}
            </div>
            {content?.diff_summary && (
              <p className="text-xs text-brand-600 mt-1.5 font-medium">最近修改：{content.diff_summary}</p>
            )}
          </div>
          <div className="flex gap-2">
            {quality?.issue_count > 0 && (
              <Button
                variant="warning"
                onClick={() => setShowSuggestions(!showSuggestions)}
                iconLeft={<AlertTriangle className="w-4 h-4" />}
              >
                {quality.error_count}个问题需修复
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={handleCopy}
              iconLeft={copied ? <Check className="w-4 h-4 text-success-600" /> : <Copy className="w-4 h-4" />}
              disabled={!content?.content}
            >
              {copied ? '已复制' : '复制'}
            </Button>
          </div>
        </div>
      </Card>

      {showSuggestions && quality && (
        <SuggestionsPanel
          episode={episode}
          quality={quality}
          applyMut={applyMut}
          onClose={() => setShowSuggestions(false)}
        />
      )}

      <Card padding="xl">
        {content ? (
          <ScriptRenderer content={content.content} />
        ) : (
          <div className="text-center py-10 text-slate-400">
            <Loader2 className="w-6 h-6 text-brand-400 animate-spin mx-auto mb-3" />
            加载中...
          </div>
        )}
      </Card>
    </div>
  );
}

function ScriptRenderer({ content }) {
  if (!content) return <div className="text-sm text-slate-400 text-center py-8">暂无内容</div>;
  const text = typeof content === 'string' ? content
    : content.script || content.text || JSON.stringify(content, null, 2);
  return (
    <div className="font-mono text-sm leading-7 space-y-0.5">
      {text.split('\n').map((line, i) => {
        if (/^\d+-\d+\s+[日夜晨昏]\s+[内外]/.test(line))
          return <div key={i} className="text-brand-700 font-bold mt-5 mb-1 tracking-wide">{line}</div>;
        if (/^[^\n]+（[^）]+）：/.test(line)) {
          const colonIdx = line.indexOf('）：');
          const actor = line.slice(0, colonIdx + 2);
          const speech = line.slice(colonIdx + 2);
          return (
            <div key={i} className="mb-0.5">
              <span className="text-accent-700 font-medium">{actor}</span>
              <span className="text-slate-800">{speech}</span>
            </div>
          );
        }
        if (line.startsWith('△'))
          return <div key={i} className="text-slate-400 italic text-xs pl-6 mb-0.5">{line}</div>;
        if (/^人物：/.test(line))
          return <div key={i} className="text-success-700 text-xs mb-0.5">{line}</div>;
        if (!line.trim()) return <div key={i} className="h-2" />;
        return <div key={i} className="text-slate-700 mb-0.5">{line}</div>;
      })}
    </div>
  );
}

function SuggestionsPanel({ episode, quality, applyMut, onClose }) {
  const [selected, setSelected] = useState([]);

  const realIssues = useMemo(() => {
    const allIssues = quality?.all_issues || [];
    const topSuggestions = quality?.top_suggestions || [];
    if (allIssues.length > 0) return allIssues;
    if (topSuggestions.length > 0) {
      return topSuggestions.map((s, idx) => ({
        id: `ts-${idx}`,
        severity: s.severity || 'warning',
        dimension: s.dimension || '综合建议',
        desc: s.desc || s.suggestion || '',
        suggestion: s.suggestion || '',
      }));
    }
    return [];
  }, [quality]);

  const toggleAll = () => setSelected(selected.length === realIssues.length ? [] : realIssues.map(i => i.id));

  useEffect(() => {
    setSelected([]);
  }, [episode]);

  if (realIssues.length === 0) {
    return (
      <Card padding="lg" className="border-success-200 bg-success-50/30">
        <div className="flex items-center gap-2 text-success-700">
          <CheckCircle2 className="w-5 h-5" />
          <span className="font-medium">本集无待修复问题，质量达标</span>
        </div>
      </Card>
    );
  }

  return (
    <Card padding="none" className="border-warning-300 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-warning-50 border-b border-warning-200">
        <h4 className="text-sm font-semibold text-warning-800">
          第{episode}集 — 修改建议（{realIssues.length}条）
        </h4>
        <div className="flex gap-3 items-center">
          <button
            onClick={toggleAll}
            className="text-xs text-warning-700 hover:underline font-medium"
          >
            {selected.length === realIssues.length ? '取消全选' : '全选'}
          </button>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
            aria-label="关闭"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="divide-y divide-slate-100">
        {realIssues.map((issue) => {
          const sevKey = issue.severity || 'warning';
          const cfg = SEVERITY_CONFIG[sevKey] || SEVERITY_CONFIG.warning;
          const isSelected = selected.includes(issue.id);
          return (
            <label
              key={issue.id}
              className={`flex gap-3 p-4 cursor-pointer hover:bg-slate-50 transition-colors ${
                isSelected ? 'bg-brand-50/50' : ''
              }`}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() =>
                  setSelected(isSelected ? selected.filter(id => id !== issue.id) : [...selected, issue.id])
                }
                className="mt-0.5 accent-brand-600 w-4 h-4"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <Badge tone={cfg.tone} size="sm">
                    {cfg.icon} {cfg.label}
                  </Badge>
                  <span className="text-xs text-slate-400">{issue.dimension}</span>
                </div>
                <p className="text-sm text-slate-800">{issue.desc}</p>
                {issue.suggestion && (
                  <p className="text-xs text-slate-500 mt-0.5">→ {issue.suggestion}</p>
                )}
              </div>
            </label>
          );
        })}
      </div>
      <div className="px-4 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-3">
        <p className="text-xs text-slate-400">应用后生成新版本（原版本保留），需配置 LLM 才能自动修改</p>
        <Button
          variant="brand"
          disabled={selected.length === 0 || applyMut.isPending}
          isLoading={applyMut.isPending}
          onClick={() => applyMut.mutate({
            episodeNumber: episode,
            suggestions: realIssues.filter(i => selected.includes(i.id)),
            agentId: 'drama.polish-master',
          })}
        >
          应用已选（{selected.length}条）
        </Button>
      </div>
    </Card>
  );
}

function QualityReport({ radar, episode, qualityList, totalEpisodes, projectTitle, reportRef }) {
  const [expandedDim, setExpandedDim] = useState(null);
  const [reportSection, setReportSection] = useState('overview');

  const scores = {};
  if (radar?.dimensions) {
    radar.dimensions.forEach(d => { scores[d.key] = d.score; });
  }
  const overall = radar?.overall_score || 0;
  const grade = radar?.grade || 'D';
  const gradeCfg = GRADE_CONFIG[grade] || GRADE_CONFIG.D;

  if (!radar && qualityList.length === 0) return (
    <Card padding="xl" className="text-center">
      <div className="text-4xl mb-3">📊</div>
      <p className="text-base font-medium text-slate-600 mb-2">暂无质量评估数据</p>
      <p className="text-sm text-slate-500">请先执行「质量报告官」角色，生成详细评估报告</p>
    </Card>
  );

  return (
    <div ref={reportRef} className="space-y-4">
      <Card padding="none" className="overflow-hidden">
        <div className="flex border-b border-slate-100">
          {[['overview','📊 综合概览'],['detail','🔍 维度详情'],['summary','📝 汇总报告']].map(([k,l]) => (
            <button
              key={k}
              onClick={() => setReportSection(k)}
              className={`flex-1 py-3 text-sm font-medium transition-all ${
                reportSection === k
                  ? 'bg-brand-50 text-brand-700 border-b-2 border-brand-600'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              {l}
            </button>
          ))}
        </div>

        {reportSection === 'overview' && (
          <div className="p-5">
            <div className="flex items-start justify-between mb-5">
              <div>
                <div className="text-xs text-slate-400 mb-1">剧本质量评估报告</div>
                <h2 className="text-xl font-bold text-slate-900">
                  《{projectTitle}》{episode ? `第${episode}集` : '整剧综合'}
                </h2>
                {radar?.grade_desc && <p className="text-sm text-slate-500 mt-1">{radar.grade_desc}</p>}
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-400 mb-1">综合评估得分</div>
                <div className="text-5xl font-black text-brand-700">{overall || '—'}</div>
                <div className="mt-2">
                  <Badge tone={gradeCfg.tone} size="md">
                    评价等级：{gradeCfg.label}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-5">
              <div className="flex items-center justify-center">
                <RadarChart scores={scores} />
              </div>

              <div className="grid grid-cols-2 gap-2">
                {DIM_KEYS.map((key) => {
                  const meta = DIM_META[key];
                  const score = scores[key] || 0;
                  const dim = radar?.dimensions?.find(d => d.key === key);
                  const issueCount = dim?.issues?.length || 0;
                  return (
                    <button
                      key={key}
                      onClick={() => { setExpandedDim(expandedDim === key ? null : key); setReportSection('detail'); }}
                      className="p-3 rounded-xl border border-slate-200 text-left hover:border-brand-300 hover:shadow-sm transition-all group bg-white"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-semibold text-slate-600">{meta.name}</span>
                        <span className="text-lg font-black text-brand-700">{score || '—'}</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all bg-brand-500"
                          style={{ width: `${score}%` }}
                        />
                      </div>
                      {issueCount > 0 && (
                        <p className="text-xs text-warning-600 mt-1 font-medium">
                          {dim?.issue_count?.error > 0 ? `✕${dim.issue_count.error} ` : ''}
                          {dim?.issue_count?.warning > 0 ? `⚠${dim.issue_count.warning}` : ''}
                        </p>
                      )}
                      <p className="text-xs text-brand-500 opacity-0 group-hover:opacity-100 mt-1 font-medium transition-opacity">
                        点击查看详情 →
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>

            {qualityList.length > 1 && (
              <div className="mt-5 pt-4 border-t border-slate-100">
                <h3 className="text-sm font-semibold text-slate-700 mb-3">作者设计情绪强度（全剧情绪曲线）</h3>
                <EmotionCurve qualityList={qualityList} />
              </div>
            )}

            {(radar?.error_count || 0) > 0 && (
              <div className="mt-4 p-4 bg-danger-50 rounded-xl border border-danger-200">
                <h4 className="text-xs font-semibold text-danger-700 mb-2 flex items-center gap-1.5">
                  <X className="w-3.5 h-3.5" />
                  必须修复（{radar.error_count}项）
                </h4>
                <div className="space-y-1.5">
                  {(radar.all_issues || []).filter(i => i.severity === 'error').slice(0, 5).map((issue, idx) => (
                    <div key={idx} className="text-xs text-danger-700">
                      <span className="font-semibold">[{issue.dimension}] </span>{issue.desc}
                      <span className="text-slate-400 ml-1">→ {issue.suggestion}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {reportSection === 'detail' && (
          <div className="p-5 space-y-3">
            <div className="flex gap-2 flex-wrap mb-4">
              {DIM_KEYS.map(key => {
                const meta = DIM_META[key];
                const score = scores[key] || 0;
                return (
                  <button
                    key={key}
                    onClick={() => setExpandedDim(expandedDim === key ? null : key)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                      expandedDim === key
                        ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                        : 'bg-white border-slate-200 text-slate-600 hover:border-brand-300 hover:text-brand-700'
                    }`}
                  >
                    {meta.abbr} {score || '—'}
                  </button>
                );
              })}
            </div>

            {DIM_KEYS.map(key => {
              const meta = DIM_META[key];
              const score = scores[key] || 0;
              const dim = radar?.dimensions?.find(d => d.key === key);
              const isExpanded = expandedDim === key || expandedDim === null;
              if (!isExpanded) return null;

              return (
                <div key={key} className="rounded-xl border border-slate-200 overflow-hidden bg-white">
                  <div
                    className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-slate-50 transition-colors"
                    style={{ borderLeft: '4px solid var(--brand-600)' }}
                    onClick={() => setExpandedDim(expandedDim === key ? null : key)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-slate-800">{meta.name}</span>
                      <span className="text-xs text-slate-400">{dim?.desc || meta.subItems.join(' / ')}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-24 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-brand-500"
                          style={{ width: `${score}%` }}
                        />
                      </div>
                      <span className="text-xl font-black w-10 text-right text-brand-700">{score || '—'}</span>
                    </div>
                  </div>

                  {expandedDim === key && (
                    <div className="px-4 pb-4 pt-2 border-t border-slate-100">
                      {dim?.issues?.length > 0 ? (
                        <div className="mb-3">
                          <div className="text-xs text-slate-500 mb-2">评估要点：{meta.subItems.join(' / ')}</div>
                        </div>
                      ) : score > 0 ? (
                        <div className="mb-3 p-2.5 bg-success-50 rounded-lg text-success-700 text-sm flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>本维度各项评估要点均达标</span>
                        </div>
                      ) : (
                        <div className="mb-3 p-2.5 bg-slate-50 rounded-lg text-slate-500 text-sm">
                          本维度尚未进行细粒度评估
                        </div>
                      )}

                      {dim?.summary && (
                        <p className="text-sm text-slate-700 mb-3 p-2.5 bg-slate-50 rounded-lg">{dim.summary}</p>
                      )}

                      {dim?.issues?.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">本维度问题</h5>
                          {dim.issues.map((issue, idx) => {
                            const sevKey = issue.severity || 'warning';
                            const cfg = SEVERITY_CONFIG[sevKey] || SEVERITY_CONFIG.warning;
                            return (
                              <div key={idx} className={`p-3 rounded-lg border text-sm ${cfg.bgClass} ${cfg.borderClass}`}>
                                <div className="flex items-center gap-1.5 mb-1">
                                  <Badge tone={cfg.tone} size="sm">{cfg.icon} {cfg.label}</Badge>
                                </div>
                                <p className="font-medium text-slate-800">{issue.desc}</p>
                                <p className="text-xs text-slate-500 mt-1">修复建议：{issue.suggestion}</p>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {(!dim?.issues?.length && score > 0) && (
                        <div className="text-sm text-success-700 bg-success-50 p-2.5 rounded-lg border border-success-200 flex items-center gap-1.5">
                          <Check className="w-4 h-4" />
                          此维度表现良好，无明显问题
                        </div>
                      )}
                      {score === 0 && (
                        <div className="text-sm text-slate-400 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                          ⏳ 尚未进行质量评估，请先执行「质量报告官」角色
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {reportSection === 'summary' && (
          <SummaryReport
            radar={radar}
            qualityList={qualityList}
            projectTitle={projectTitle}
            scores={scores}
            overall={overall}
            grade={grade}
          />
        )}
      </Card>

      {qualityList.length > 0 && (
        <Card padding="lg">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">
            分集质量概况（{qualityList.length}集已评估 / 共{totalEpisodes}集）
          </h3>
          <div className="grid grid-cols-6 gap-1.5 sm:grid-cols-8 lg:grid-cols-10">
            {Array.from({ length: totalEpisodes }, (_, i) => {
              const ep = i + 1;
              const q = qualityList.find(q => q.episode_number === ep);
              const g = q?.grade;
              const gCfg = g ? GRADE_CONFIG[g] : null;
              return (
                <div
                  key={ep}
                  className={`p-1.5 rounded text-center border text-xs ${
                    gCfg ? `bg-${gCfg.tone}-50 border-${gCfg.tone}-200 text-${gCfg.tone}-700` : 'border-slate-100 bg-slate-50 text-slate-300'
                  }`}
                >
                  <div className="text-slate-500 text-[10px] font-medium">E{ep}</div>
                  <div className="font-bold">{q?.overall_score || '—'}</div>
                  {g && <div className="text-[10px] font-semibold">{g}</div>}
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}

function RadarChart({ scores }) {
  const keys = DIM_KEYS;
  const count = keys.length;
  const cx = 120, cy = 120, r = 90;
  const levels = [20, 40, 60, 80, 100];

  const toXY = (idx, val) => {
    const angle = (Math.PI * 2 * idx) / count - Math.PI / 2;
    const dist = (val / 100) * r;
    return { x: cx + Math.cos(angle) * dist, y: cy + Math.sin(angle) * dist };
  };

  const radarPoints = keys.map((k, i) => toXY(i, scores[k] || 0));
  const radarPath = radarPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';

  return (
    <svg viewBox="0 0 240 240" className="w-full max-w-[220px]">
      {levels.map((lvl) => {
        const pts = keys.map((_, i) => { const p = toXY(i, lvl); return `${p.x},${p.y}`; }).join(' ');
        return <polygon key={lvl} points={pts} fill="none" stroke="#e2e8f0" strokeWidth="0.8" />;
      })}
      {keys.map((_, i) => {
        const outer = toXY(i, 100);
        return <line key={i} x1={cx} y1={cy} x2={outer.x} y2={outer.y} stroke="#e2e8f0" strokeWidth="0.8" />;
      })}
      <path d={radarPath} fill="rgb(59 130 246 / 0.2)" stroke="rgb(59 130 246)" strokeWidth="1.5" />
      {radarPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3" fill="rgb(59 130 246)" />
      ))}
      {keys.map((k, i) => {
        const label = toXY(i, 118);
        const meta = DIM_META[k];
        const score = scores[k] || 0;
        return (
          <text
            key={k}
            x={label.x}
            y={label.y}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="9"
            fill={score > 0 ? 'rgb(51 65 85)' : '#94a3b8'}
            fontWeight="600"
          >
            {meta.abbr}{score > 0 ? ` ${score}` : ''}
          </text>
        );
      })}
    </svg>
  );
}

function EmotionCurve({ qualityList }) {
  if (!qualityList.length) return null;

  const sorted = [...qualityList].sort((a, b) => a.episode_number - b.episode_number);
  const maxEp = sorted[sorted.length - 1]?.episode_number || 1;
  const W = 600, H = 100, PAD = 30;
  const plotW = W - PAD * 2, plotH = H - PAD * 2;

  const emotionValues = sorted.map(q => {
    const score = q.scores?.emotion || 0;
    if (!score) return null;
    return { ep: q.episode_number, val: ((score - 50) / 10).toFixed(1) };
  }).filter(Boolean);

  if (emotionValues.length < 2) return (
    <div className="text-xs text-slate-400 text-center py-4">需要更多集数的评估数据才能显示情绪曲线</div>
  );

  const toX = (ep) => PAD + ((ep - 1) / (maxEp - 1)) * plotW;
  const toY = (val) => PAD + plotH - ((parseFloat(val) + 5) / 10) * plotH;

  const linePath = emotionValues.map((v, i) => `${i === 0 ? 'M' : 'L'} ${toX(v.ep)} ${toY(v.val)}`).join(' ');
  const areaPath = `${linePath} L ${toX(emotionValues[emotionValues.length-1].ep)} ${toY(0)} L ${toX(1)} ${toY(0)} Z`;

  return (
    <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto">
      <div className="text-xs text-slate-400 mb-2">+为正向情绪，-为负向情绪 · 1:温和 2:中等 3:强烈 4:极度 5:极端</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full min-w-[400px]" style={{ height: '120px' }}>
        <line x1={PAD} y1={toY(0)} x2={W-PAD} y2={toY(0)} stroke="#374151" strokeDasharray="3,3" strokeWidth="1" />
        {[-4,-2,0,2,4].map(v => (
          <text
            key={v}
            x={PAD-4}
            y={toY(v)}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize="8"
            fill="#6b7280"
          >
            {v > 0 ? `+${v}` : v}
          </text>
        ))}
        {emotionValues.filter((_, i) => i % Math.max(1, Math.floor(emotionValues.length/10)) === 0).map(v => (
          <text
            key={v.ep}
            x={toX(v.ep)}
            y={H-10}
            textAnchor="middle"
            fontSize="8"
            fill="#6b7280"
          >
            {v.ep}
          </text>
        ))}
        <path d={areaPath} fill="rgb(99 102 241 / 0.1)" />
        <path d={linePath} fill="none" stroke="rgb(129 140 248)" strokeWidth="1.5" />
        {emotionValues.map(v => (
          <circle key={v.ep} cx={toX(v.ep)} cy={toY(v.val)} r="2.5" fill="rgb(99 102 241)" />
        ))}
      </svg>
    </div>
  );
}

function SummaryReport({ radar, qualityList, projectTitle, scores, overall, grade }) {
  const gradeLabel = grade === 'S' ? '商业精品' : grade === 'A' ? '质量优良' : grade === 'B' ? 'B级合格品' : grade === 'C' ? '需大幅优化' : '不达标';
  const weakEps = qualityList.filter(q => (q.overall_score || 0) < 75);
  const passEps = qualityList.filter(q => (q.overall_score || 0) >= 75);

  const dimScores = DIM_KEYS.map(k => ({ key: k, name: DIM_META[k].name, score: scores[k] || 0 }))
    .filter(d => d.score > 0)
    .sort((a, b) => b.score - a.score);
  const topDims = dimScores.slice(0, 3);
  const weakDims = [...dimScores].sort((a, b) => a.score - b.score).slice(0, 3);
  const errors = (radar?.all_issues || []).filter(i => i.severity === 'error');
  const warnings = (radar?.all_issues || []).filter(i => i.severity === 'warning');

  return (
    <div className="p-5 space-y-5 text-sm">
      <div>
        <h3 className="text-base font-bold text-slate-900 border-b border-slate-200 pb-2 mb-3">— 汇总报告</h3>

        <section className="mb-4">
          <h4 className="font-semibold text-slate-800 mb-2">核心诊断</h4>
          <div className="mb-2">
            <span className="font-bold text-slate-700">开篇定性</span>
            <p className="text-slate-600 mt-1">
              {projectTitle && `《${projectTitle}》`}综合评分{overall}分，等级{grade}（{gradeLabel}）。
              {topDims.length > 0 && `${topDims.map(d=>d.name).join('、')}（${topDims.map(d=>d.score).join('/')}分）表现较强，`}
              {weakDims.length > 0 && `${weakDims.map(d=>d.name).join('、')}（${weakDims.map(d=>d.score).join('/')}分）需要重点提升。`}
              {weakEps.length > 0 && `共${weakEps.length}集质量低于75分，需优先处理。`}
            </p>
          </div>
        </section>

        <section className="mb-4">
          <h4 className="font-semibold text-slate-800 mb-2">关键数据支撑</h4>
          <div className="grid grid-cols-2 gap-3">
            {dimScores.map(d => {
              const scoreColor = d.score >= 80
                ? 'text-success-700'
                : d.score >= 70
                ? 'text-brand-700'
                : d.score >= 60
                ? 'text-warning-700'
                : 'text-danger-700';
              return (
                <div key={d.key} className="flex items-center justify-between bg-slate-50 px-3 py-2 rounded-lg">
                  <span className="text-slate-600">{d.name}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-brand-500"
                        style={{ width: `${d.score}%` }}
                      />
                    </div>
                    <span className={`font-bold text-sm ${scoreColor}`}>{d.score}/10</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {(errors.length > 0 || warnings.length > 0) && (
          <section className="mb-4">
            <h4 className="font-semibold text-slate-800 mb-2">风险与缺陷分析</h4>
            {errors.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-semibold text-danger-600 mb-1.5 flex items-center gap-1.5">
                  <X className="w-3.5 h-3.5" />
                  致命缺陷（内容层面）
                </p>
                {errors.map((e, idx) => (
                  <div key={idx} className="text-slate-700 mb-1.5">
                    <span className="font-medium text-danger-600">[{e.dimension}] </span>{e.desc}
                    <p className="text-slate-500 text-xs mt-0.5 pl-4">→ {e.suggestion}</p>
                  </div>
                ))}
              </div>
            )}
            {warnings.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-warning-600 mb-1.5 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  优化建议（审美层面）
                </p>
                {warnings.slice(0, 4).map((w, idx) => (
                  <div key={idx} className="text-slate-600 mb-1 text-xs">
                    <span className="font-medium">[{w.dimension}] </span>{w.desc}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        <section className="mb-4">
          <h4 className="font-semibold text-slate-800 mb-2">资产估计</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-success-50 rounded-lg p-3 border border-success-200">
              <p className="text-xs font-semibold text-success-700 mb-1.5 flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5" />
                可取之处
              </p>
              {topDims.slice(0,2).map(d => (
                <p key={d.key} className="text-xs text-slate-700 mb-0.5">✓ {d.name}（{d.score}分）表现突出</p>
              ))}
              {passEps.length > 0 && (
                <p className="text-xs text-slate-700">✓ {passEps.length}集已达质量标准</p>
              )}
            </div>
            <div className="bg-danger-50 rounded-lg p-3 border border-danger-200">
              <p className="text-xs font-semibold text-danger-700 mb-1.5 flex items-center gap-1.5">
                <X className="w-3.5 h-3.5" />
                资产的局限性
              </p>
              {weakDims.slice(0,2).map(d => (
                <p key={d.key} className="text-xs text-slate-700 mb-0.5">⚠ {d.name}（{d.score}分）存在明显短板</p>
              ))}
              {weakEps.length > 0 && (
                <p className="text-xs text-slate-700">
                  ⚠ 第{weakEps.map(e=>e.episode_number).join('、')}集低于75分
                </p>
              )}
            </div>
          </div>
        </section>

        <section>
          <h4 className="font-semibold text-slate-800 mb-2">最终裁决与修改路径</h4>
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
            <p className="font-bold text-slate-800 mb-2">
              项目评级【{grade}级 — {overall >= 80 ? '可投入优化' : overall >= 60 ? '需系统性修改' : '建议重构核心'}】
            </p>
            <p className="text-slate-600 text-xs mb-3">
              {overall >= 80
                ? '当前版本具备基础商业价值，针对核心短板进行手术式修改后可交付。'
                : overall >= 60
                ? '剧本存在可修复问题，建议按优先级逐步改进，先解决必修项再优化推荐项。'
                : '剧本质量有明显不足，建议重新执行关键角色（情节架构师/人设设计师），以更好的输入质量重新生成。'}
            </p>
            <div className="space-y-1">
              {[...errors, ...warnings].slice(0,5).map((issue, idx) => (
                <div key={idx} className="text-xs text-slate-600">
                  <span className="font-semibold text-slate-700">{idx+1}. [{issue.dimension}] </span>
                  {issue.suggestion}
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
