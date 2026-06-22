import { useState } from 'react';
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

const GRADE_CONFIG = {
  S: { label: 'S级 · 商业精品', color: 'text-yellow-700 bg-yellow-50 border-yellow-200' },
  A: { label: 'A级 · 质量优良', color: 'text-green-700 bg-green-50 border-green-200' },
  B: { label: 'B级 · 达到基准', color: 'text-blue-700 bg-blue-50 border-blue-200' },
  C: { label: 'C级 · 需要优化', color: 'text-orange-700 bg-orange-50 border-orange-200' },
  D: { label: 'D级 · 不达标',   color: 'text-red-700 bg-red-50 border-red-200' },
};

const SEVERITY_CONFIG = {
  error:   { icon: '❌', label: '必须修复', color: 'text-red-700 bg-red-50 border-red-200' },
  warning: { icon: '⚠️', label: '建议优化', color: 'text-amber-700 bg-amber-50 border-amber-200' },
  info:    { icon: 'ℹ️', label: '参考建议', color: 'text-blue-700 bg-blue-50 border-blue-200' },
};

/** 剧本查看器 + 质量报告 */
export default function ScriptsPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const initialTab = searchParams.get('tab') || 'scripts';
  const [tab, setTab] = useState(initialTab);
  const [selectedEpisode, setSelectedEpisode] = useState(null);

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

  // 当前集详情
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

  if (!project) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" /></div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate(`/drama/workspace/${projectId}`)} className="text-gray-400 hover:text-gray-700 text-lg">←</button>
            <div>
              <h1 className="font-bold text-gray-900">{project.title}</h1>
              <p className="text-xs text-gray-500">
                {project.total_episodes}集 · {completedCount}集已生成 · {project.track_mode === 'fast' ? '快速通道' : '专家通道'}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setTab('scripts')}
              className={`px-4 py-1.5 text-sm rounded-lg ${tab === 'scripts' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              📖 剧本内容
            </button>
            <button
              onClick={() => setTab('quality')}
              className={`px-4 py-1.5 text-sm rounded-lg ${tab === 'quality' ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              📊 质量报告
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 flex gap-6">
        {/* 左侧：分集列表 */}
        <div className="w-48 flex-shrink-0">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden sticky top-6">
            <div className="px-3 py-2 bg-gray-50 border-b border-gray-100 text-xs font-medium text-gray-600">
              分集列表（{completedCount}/{project.total_episodes}集）
            </div>
            <div className="max-h-[calc(100vh-160px)] overflow-y-auto">
              {completedCount === 0 ? (
                <div className="p-3 text-xs text-gray-400 text-center">暂无已生成的集数</div>
              ) : (
                Array.from({ length: completedCount }, (_, i) => i + 1).map((ep) => {
                  const quality = qualityList.find((q) => q.episode_number === ep);
                  const grade = quality?.grade || '—';
                  const gradeColor = grade === 'S' ? 'text-yellow-600' : grade === 'A' ? 'text-green-600' : grade === 'B' ? 'text-blue-600' : grade === 'C' ? 'text-orange-500' : grade === 'D' ? 'text-red-500' : 'text-gray-400';

                  return (
                    <button
                      key={ep}
                      onClick={() => setSelectedEpisode(ep)}
                      className={`w-full px-3 py-2 text-left flex items-center justify-between hover:bg-gray-50 ${selectedEpisode === ep ? 'bg-indigo-50 border-l-2 border-indigo-500' : ''}`}
                    >
                      <span className="text-sm text-gray-700">第{ep}集</span>
                      <span className={`text-xs font-medium ${gradeColor}`}>{grade}</span>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* 右侧：内容区 */}
        <div className="flex-1 min-w-0">
          {tab === 'scripts' ? (
            <ScriptView
              episode={selectedEpisode}
              content={episodeContent}
              applyMut={applyMut}
              qualityList={qualityList}
            />
          ) : (
            <QualityView
              radar={radar}
              episode={selectedEpisode}
              qualityList={qualityList}
              totalEpisodes={project.total_episodes}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// ─── 剧本内容视图 ─────────────────────────────────────────────────────────────
function ScriptView({ episode, content, applyMut, qualityList }) {
  const [showSuggestions, setShowSuggestions] = useState(false);

  if (!episode) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
        <div className="text-3xl mb-3">📖</div>
        <p>从左侧选择一集查看内容</p>
      </div>
    );
  }

  if (!content) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
        <div className="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-3" />
        <p>加载中...</p>
      </div>
    );
  }

  const quality = qualityList.find((q) => q.episode_number === episode);
  const issues = quality?.issue_count > 0;

  return (
    <div className="space-y-4">
      {/* 集信息栏 */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">第{episode}集</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            v{content.version || 1} · {content.word_count || 0}字
            {content.quality_score ? ` · 质量${content.quality_score}分` : ''}
          </p>
          {content.diff_summary && (
            <p className="text-xs text-indigo-600 mt-0.5">最近修改：{content.diff_summary}</p>
          )}
        </div>
        <div className="flex gap-2">
          {issues && (
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="px-3 py-1.5 text-sm bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200"
            >
              ⚠️ 查看修改建议（{quality.error_count}个问题）
            </button>
          )}
          <button className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
            📋 复制
          </button>
        </div>
      </div>

      {/* 修改建议面板 */}
      {showSuggestions && quality && (
        <SuggestionsPanel
          episodeNumber={episode}
          quality={quality}
          applyMut={applyMut}
          onClose={() => setShowSuggestions(false)}
        />
      )}

      {/* 剧本内容 */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <ScriptContentRenderer content={content.content} />
      </div>
    </div>
  );
}

// ─── 修改建议面板（diff视图 + 一键应用） ─────────────────────────────────────
function SuggestionsPanel({ episodeNumber, quality, applyMut, onClose }) {
  const [selectedSuggestions, setSelectedSuggestions] = useState([]);

  // 从质量评估中提取issues（这里简化展示，实际应从质量API获取详情）
  const sampleIssues = [
    { id: 's1', severity: 'error', dimension: '格式规范', desc: '本集有2处台词使用引号格式', suggestion: '将"台词"改为：角色（情绪）：台词内容', auto_applicable: false },
    { id: 's2', severity: 'warning', dimension: '对白质量', desc: '检测到可能的AI腔台词', suggestion: '将"因此他不得不承认"改为口语化表达', auto_applicable: false },
  ];

  const toggleSelection = (id) => {
    setSelectedSuggestions((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleApply = () => {
    const selected = sampleIssues.filter((i) => selectedSuggestions.includes(i.id));
    applyMut.mutate({
      episodeNumber,
      suggestions: selected,
      agentId: 'drama.script-editor',
    });
  };

  return (
    <div className="bg-white rounded-xl border border-amber-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-800">第{episodeNumber}集修改建议</h4>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg">×</button>
      </div>

      <div className="space-y-2 mb-4">
        {sampleIssues.map((issue) => {
          const cfg = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.info;
          const isSelected = selectedSuggestions.includes(issue.id);
          return (
            <div
              key={issue.id}
              onClick={() => toggleSelection(issue.id)}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${cfg.color} ${isSelected ? 'ring-2 ring-indigo-400' : ''}`}
            >
              <div className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={isSelected}
                  readOnly
                  className="mt-0.5"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-1 mb-0.5">
                    <span className="text-xs font-medium">{cfg.icon} {cfg.label}</span>
                    <span className="text-xs opacity-70">· {issue.dimension}</span>
                  </div>
                  <p className="text-xs">{issue.desc}</p>
                  <p className="text-xs mt-1 font-medium">建议：{issue.suggestion}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleApply}
          disabled={selectedSuggestions.length === 0 || applyMut.isPending}
          className="flex-1 py-2 bg-indigo-600 text-white text-sm rounded-lg disabled:opacity-50 hover:bg-indigo-700"
        >
          {applyMut.isPending ? '应用中...' : `应用选中建议（${selectedSuggestions.length}条）`}
        </button>
        <button
          onClick={() => setSelectedSuggestions(sampleIssues.map((i) => i.id))}
          className="px-3 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
        >
          全选
        </button>
      </div>

      <p className="text-xs text-gray-400 mt-2">
        ⚠️ 建议应用后将生成新版本（v{(quality?.version || 1) + 1}），原版本保留可随时回滚。
        需配置 LLM 才能自动修改，当前保存建议记录供人工参考。
      </p>
    </div>
  );
}

// ─── 剧本内容渲染 ─────────────────────────────────────────────────────────────
function ScriptContentRenderer({ content }) {
  if (!content) return <div className="text-sm text-gray-400 text-center py-8">暂无内容</div>;

  const text = typeof content === 'string' ? content
    : content.script || content.text || content.content
    || JSON.stringify(content, null, 2);

  // 简单的剧本格式化渲染
  const lines = text.split('\n');
  return (
    <div className="font-mono text-sm leading-relaxed">
      {lines.map((line, i) => {
        // 场景头（1-1 日 外 地点）
        if (/^\d+-\d+\s+[日夜晨昏]\s+[内外]/.test(line)) {
          return <div key={i} className="text-indigo-700 font-semibold mt-4 mb-1">{line}</div>;
        }
        // 台词（角色（情绪）：台词）
        if (/^[^\n]+（[^）]+）：/.test(line)) {
          const [actor, ...rest] = line.split('：');
          return (
            <div key={i} className="mb-1">
              <span className="text-purple-700 font-medium">{actor}：</span>
              <span className="text-gray-800">{rest.join('：')}</span>
            </div>
          );
        }
        // 动作行（△开头）
        if (line.startsWith('△')) {
          return <div key={i} className="text-gray-500 italic text-xs mb-1 ml-4">{line}</div>;
        }
        // 人物提示行
        if (/^人物：/.test(line)) {
          return <div key={i} className="text-green-700 text-xs mb-1">{line}</div>;
        }
        // 空行
        if (!line.trim()) return <div key={i} className="h-2" />;
        // 普通内容
        return <div key={i} className="text-gray-700 mb-0.5">{line}</div>;
      })}
    </div>
  );
}

// ─── 质量报告视图 ─────────────────────────────────────────────────────────────
function QualityView({ radar, episode, qualityList, totalEpisodes }) {
  const [showEpisodeDetail, setShowEpisodeDetail] = useState(null);

  return (
    <div className="space-y-4">
      {/* 整体评分 */}
      {radar && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="font-semibold text-gray-900">
                {episode ? `第${episode}集质量评估` : '全剧质量概况'}
              </h3>
              {radar.grade_desc && (
                <p className="text-sm text-gray-500 mt-0.5">{radar.grade_desc}</p>
              )}
            </div>
            <div className={`text-2xl font-bold px-4 py-2 rounded-lg border ${GRADE_CONFIG[radar.grade]?.color || 'text-gray-600'}`}>
              {radar.overall_score}分 {radar.grade}
            </div>
          </div>

          {/* 8维度评分（带扣分说明） */}
          <div className="space-y-2">
            {(radar.dimensions || []).map((dim) => (
              <DimensionBar key={dim.key} dim={dim} />
            ))}
          </div>

          {/* 必修项 */}
          {radar.error_count > 0 && (
            <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-100">
              <h4 className="text-xs font-semibold text-red-700 mb-2">❌ 必须修复（{radar.error_count}项）</h4>
              {(radar.all_issues || []).filter((i) => i.severity === 'error').map((issue, idx) => (
                <div key={idx} className="text-xs text-red-600 mb-1">
                  <span className="font-medium">{issue.dimension}：</span>{issue.desc}
                  <span className="text-gray-500 ml-1">→ {issue.suggestion}</span>
                </div>
              ))}
            </div>
          )}

          {/* 优化建议 */}
          {radar.top_suggestions?.length > 0 && (
            <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
              <h4 className="text-xs font-semibold text-amber-700 mb-2">💡 重点优化建议</h4>
              {radar.top_suggestions.map((sg, idx) => (
                <div key={idx} className="text-xs text-amber-700 mb-1">
                  {idx + 1}. <span className="font-medium">{sg.dimension}：</span>{sg.suggestion}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 分集质量概况 */}
      {qualityList.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">
            分集质量详情（已评估{qualityList.length}/{totalEpisodes}集）
          </h3>
          <div className="grid grid-cols-5 gap-2">
            {qualityList.map((eq) => {
              const cfg = GRADE_CONFIG[eq.grade] || {};
              return (
                <button
                  key={eq.episode_number}
                  onClick={() => setShowEpisodeDetail(showEpisodeDetail === eq.episode_number ? null : eq.episode_number)}
                  className={`p-2 rounded-lg border text-center hover:shadow-sm transition-all ${cfg.color || 'bg-gray-50 border-gray-200'}`}
                >
                  <div className="text-xs text-gray-500">第{eq.episode_number}集</div>
                  <div className="text-sm font-bold">{eq.overall_score}</div>
                  <div className="text-xs">{eq.grade}</div>
                  {eq.error_count > 0 && (
                    <div className="text-xs text-red-500 mt-0.5">!{eq.error_count}个错误</div>
                  )}
                </button>
              );
            })}
          </div>

          {/* 集详情展开 */}
          {showEpisodeDetail && (() => {
            const eq = qualityList.find((q) => q.episode_number === showEpisodeDetail);
            if (!eq) return null;
            return (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-medium text-gray-700 mb-2">第{showEpisodeDetail}集详情</h4>
                <p className="text-sm text-gray-600">{eq.summary || '暂无评估意见'}</p>
                {eq.issue_count > 0 && (
                  <p className="text-xs text-amber-600 mt-1">共{eq.issue_count}个问题，其中{eq.error_count}个需立即修复</p>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {/* 全剧系列质量 */}
      {radar?.series_summary && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">全剧综合评估</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-700">{radar.series_summary.series_overall_score || '—'}</div>
              <div className="text-xs text-gray-500">全剧综合分</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-700">{radar.series_summary.series_grade || '—'}</div>
              <div className="text-xs text-gray-500">综合等级</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-700">{radar.series_summary.weak_count || 0}</div>
              <div className="text-xs text-gray-500">低分集（&lt;75分）</div>
            </div>
          </div>

          {radar.series_summary.weak_episodes?.length > 0 && (
            <div className="mt-3 p-2 bg-amber-50 rounded text-xs text-amber-700">
              低分集需重点关注：第
              {radar.series_summary.weak_episodes.map((e) => e.episode).join('、')}
              集（质量低于75分），建议优先执行修稿师角色。
            </div>
          )}
        </div>
      )}

      {!radar && (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
          <div className="text-3xl mb-3">📊</div>
          <p>执行「质量报告官」角色后，此处将显示详细的评分报告</p>
          <p className="text-xs mt-2">支持整剧整体评估和分集单集评估</p>
        </div>
      )}
    </div>
  );
}

// ─── 维度进度条 ────────────────────────────────────────────────────────────────
function DimensionBar({ dim }) {
  const [expanded, setExpanded] = useState(false);
  const score = dim.score || 0;
  const barColor = score >= 85 ? 'bg-green-500' : score >= 75 ? 'bg-blue-500' : score >= 60 ? 'bg-amber-500' : 'bg-red-500';
  const hasIssues = dim.issues?.length > 0;

  return (
    <div>
      <div
        className={`flex items-center gap-3 cursor-pointer ${hasIssues ? 'hover:bg-gray-50 rounded p-1 -m-1' : ''}`}
        onClick={() => hasIssues && setExpanded(!expanded)}
      >
        <span className="text-xs text-gray-600 w-16 flex-shrink-0">{dim.name}</span>
        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${score}%` }} />
        </div>
        <span className="text-xs font-medium text-gray-700 w-8 text-right">{score}</span>
        {hasIssues && (
          <span className="text-xs text-amber-500 w-16 text-right">
            {dim.issue_count?.error > 0 ? `❌${dim.issue_count.error}` : ''}
            {dim.issue_count?.warning > 0 ? ` ⚠️${dim.issue_count.warning}` : ''}
            {expanded ? ' ▾' : ' ▸'}
          </span>
        )}
      </div>

      {expanded && dim.issues?.length > 0 && (
        <div className="mt-1 ml-20 space-y-1">
          {dim.issues.map((issue, idx) => {
            const cfg = SEVERITY_CONFIG[issue.severity] || SEVERITY_CONFIG.info;
            return (
              <div key={idx} className={`text-xs p-2 rounded border ${cfg.color}`}>
                <span className="font-medium">{cfg.icon} {issue.desc}</span>
                <br />
                <span className="opacity-80">→ {issue.suggestion}</span>
              </div>
            );
          })}
        </div>
      )}

      {!hasIssues && score === 0 && (
        <div className="text-xs text-gray-400 ml-20 mt-0.5">尚未评分</div>
      )}
    </div>
  );
}
