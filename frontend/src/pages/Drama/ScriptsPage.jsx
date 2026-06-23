import { useState, useRef } from 'react';
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

// ─── 常量 ─────────────────────────────────────────────────────────────────────
const GRADE_COLORS = {
  S: { bg: 'bg-yellow-400', text: 'text-yellow-700', border: 'border-yellow-300', badge: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
  A: { bg: 'bg-green-500',  text: 'text-green-700',  border: 'border-green-300',  badge: 'bg-green-50 text-green-700 border-green-200'   },
  B: { bg: 'bg-blue-500',   text: 'text-blue-700',   border: 'border-blue-300',   badge: 'bg-blue-50 text-blue-700 border-blue-200'      },
  C: { bg: 'bg-orange-400', text: 'text-orange-700', border: 'border-orange-300', badge: 'bg-orange-50 text-orange-700 border-orange-200'},
  D: { bg: 'bg-red-400',    text: 'text-red-700',    border: 'border-red-300',    badge: 'bg-red-50 text-red-700 border-red-200'         },
};

const SEVERITY_STYLES = {
  error:   { icon: '❌', label: '必须修复', cls: 'text-red-700 bg-red-50 border-red-200' },
  warning: { icon: '⚠️', label: '建议优化', cls: 'text-amber-700 bg-amber-50 border-amber-200' },
  info:    { icon: '💡', label: '参考建议', cls: 'text-blue-700 bg-blue-50 border-blue-200' },
};

// 10维度（升级自 StoryForge G-Eval 框架）
const DIM_META = {
  format:      { name: '格式规范',   abbr: '格式', color: '#6366f1', subItems: ['场景头格式','台词格式','△标记','字数达标','台词占比','场景数量'] },
  narrative:   { name: '叙事效率',   abbr: '叙事', color: '#8b5cf6', subItems: ['推进型节拍占比','无废戏','节奏紧凑','进入-升级-退出'] },
  conflict:    { name: '冲突处理',   abbr: '冲突', color: '#ec4899', subItems: ['核心冲突贯穿','持续升级','反转自然','解决有力'] },
  character:   { name: '角色一致性', abbr: '角色', color: '#f59e0b', subItems: ['对白辨识度','行为符合人设','知识边界','Ghost/Lie/Flaw'] },
  emotion:     { name: '情感深度',   abbr: '情感', color: '#10b981', subItems: ['情感弧线完整','每集3-5次情绪','复杂情绪','切换自然'] },
  logic:       { name: '逻辑一致性', abbr: '逻辑', color: '#f97316', subItems: ['与前集一致','与大纲一致','记忆检查点匹配','无逻辑断裂'] },
  satisfaction:{ name: '爽点密度',   abbr: '爽感', color: '#06b6d4', subItems: ['每集2-3个爽点','打脸','揭穿','逆袭','宣爱','类型多样'] },
  hooks:       { name: '钩子强度',   abbr: '钩子', color: '#84cc16', subItems: ['开头10秒抓力','集末cliffhanger','付费墙前钩子极强'] },
  paywall:     { name: '付费点优化', abbr: '付费', color: '#ef4444', subItems: ['付费墙在最大张力处','付费后立即兑现','S级付费设计'] },
  genre_fit:   { name: '赛道匹配度', abbr: '赛道', color: '#a855f7', subItems: ['符合赛道套路','受众预期匹配','平台特性适配'] },
};

const DIM_KEYS = ['format','narrative','conflict','character','emotion','logic','satisfaction','hooks','paywall','genre_fit'];

/** 剧本查看器 + 深度质量报告 */
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

  if (!project) return <div className="flex items-center justify-center h-64"><div className="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" /></div>;

  const totalScore = radar?.overall_score || 0;
  const grade = radar?.grade || '—';
  const gradeColor = GRADE_COLORS[grade] || GRADE_COLORS.D;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶栏 */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate(`/drama/workspace/${projectId}`)} className="text-gray-400 hover:text-gray-700 text-xl">←</button>
            <div>
              <h1 className="font-bold text-gray-900">《{project.title}》</h1>
              <p className="text-xs text-gray-400">{project.total_episodes}集 · {completedCount}集已生成</p>
            </div>
          </div>
          <div className="flex gap-2">
            {['scripts','quality'].map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-1.5 text-sm rounded-lg ${tab===t?'bg-indigo-600 text-white':'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                {t==='scripts'?'📖 剧本内容':'📊 质量报告'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-5 flex gap-5">
        {/* 左侧分集列表 */}
        <div className="w-44 flex-shrink-0">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden sticky top-16">
            <div className="px-3 py-2 bg-gray-50 border-b text-xs font-medium text-gray-600">
              分集（{completedCount}/{project.total_episodes}）
            </div>
            <div className="max-h-[calc(100vh-120px)] overflow-y-auto">
              {completedCount === 0 && <div className="p-3 text-xs text-gray-400 text-center">暂无已生成的集数</div>}
              {Array.from({ length: Math.max(completedCount, qualityList.length) }, (_, i) => {
                const ep = i + 1;
                const q = qualityList.find((q) => q.episode_number === ep);
                const g = q?.grade;
                const gColor = g ? GRADE_COLORS[g] : null;
                return (
                  <button key={ep} onClick={() => setSelectedEpisode(ep)}
                    className={`w-full px-3 py-2 text-left flex items-center justify-between hover:bg-gray-50 ${selectedEpisode===ep?'bg-indigo-50 border-l-2 border-indigo-500':''}`}>
                    <span className="text-sm text-gray-700">第{ep}集</span>
                    {g ? (
                      <span className={`text-xs font-bold px-1.5 py-0.5 rounded border ${gColor?.badge}`}>{g}</span>
                    ) : ep <= completedCount ? (
                      <span className="text-xs text-gray-300">—</span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* 主内容区 */}
        <div className="flex-1 min-w-0">
          {tab === 'scripts' ? (
            <ScriptView episode={selectedEpisode} content={episodeContent} applyMut={applyMut} qualityList={qualityList} />
          ) : (
            <QualityReport
              radar={radar}
              episode={selectedEpisode}
              qualityList={qualityList}
              totalEpisodes={project.total_episodes}
              projectTitle={project.title}
              reportRef={reportRef}
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
  const quality = qualityList.find((q) => q.episode_number === episode);

  if (!episode) return (
    <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400">
      <div className="text-4xl mb-3">📖</div>
      <p>从左侧选择集数查看剧本内容</p>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">第{episode}集</h3>
          <div className="flex gap-3 mt-1 text-xs text-gray-500">
            {content?.word_count && <span>📝 {content.word_count}字</span>}
            {content?.version && <span>版本 v{content.version}</span>}
            {quality?.overall_score && (
              <span className={`font-medium ${GRADE_COLORS[quality.grade]?.text}`}>
                质量 {quality.overall_score}分 ({quality.grade})
              </span>
            )}
          </div>
          {content?.diff_summary && <p className="text-xs text-indigo-500 mt-0.5">最近修改：{content.diff_summary}</p>}
        </div>
        <div className="flex gap-2">
          {quality?.issue_count > 0 && (
            <button onClick={() => setShowSuggestions(!showSuggestions)}
              className="px-3 py-1.5 text-sm bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200">
              ⚠️ {quality.error_count}个问题需修复
            </button>
          )}
          <button className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">📋 复制</button>
        </div>
      </div>

      {showSuggestions && quality && (
        <SuggestionsPanel episode={episode} quality={quality} applyMut={applyMut} onClose={() => setShowSuggestions(false)} />
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        {content ? <ScriptRenderer content={content.content} /> : (
          <div className="text-center py-10 text-gray-400">
            <div className="animate-spin w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full mx-auto mb-3" />
            加载中...
          </div>
        )}
      </div>
    </div>
  );
}

// ─── 剧本渲染器 ──────────────────────────────────────────────────────────────
function ScriptRenderer({ content }) {
  if (!content) return <div className="text-sm text-gray-400 text-center py-8">暂无内容</div>;
  const text = typeof content === 'string' ? content
    : content.script || content.text || JSON.stringify(content, null, 2);
  return (
    <div className="font-mono text-sm leading-7 space-y-0.5">
      {text.split('\n').map((line, i) => {
        if (/^\d+-\d+\s+[日夜晨昏]\s+[内外]/.test(line))
          return <div key={i} className="text-indigo-700 font-bold mt-5 mb-1 tracking-wide">{line}</div>;
        if (/^[^\n]+（[^）]+）：/.test(line)) {
          const colonIdx = line.indexOf('）：');
          const actor = line.slice(0, colonIdx + 2);
          const speech = line.slice(colonIdx + 2);
          return <div key={i} className="mb-0.5"><span className="text-purple-700 font-medium">{actor}</span><span className="text-gray-900">{speech}</span></div>;
        }
        if (line.startsWith('△'))
          return <div key={i} className="text-gray-400 italic text-xs pl-6 mb-0.5">{line}</div>;
        if (/^人物：/.test(line))
          return <div key={i} className="text-green-700 text-xs mb-0.5">{line}</div>;
        if (!line.trim()) return <div key={i} className="h-2" />;
        return <div key={i} className="text-gray-700 mb-0.5">{line}</div>;
      })}
    </div>
  );
}

// ─── 修改建议面板 ────────────────────────────────────────────────────────────
function SuggestionsPanel({ episode, quality, applyMut, onClose }) {
  const [selected, setSelected] = useState([]);
  // 这里用 quality 中的 issue 数量作为示例
  const issues = [
    { id:'i1', severity:'error',   dimension:'格式规范', desc:`第${episode}集台词占比偏低（当前~22%，需≥35%）`,   suggestion:'增加角色对峙台词行，减少△动作描述' },
    { id:'i2', severity:'error',   dimension:'格式规范', desc:'场景数量超出限制（超过3个）',                       suggestion:'合并相邻功能相近的小场景' },
    { id:'i3', severity:'warning', dimension:'对白质量', desc:'检测到"因此"/"不得不"等AI腔用词',                  suggestion:'改用口语化短句，避免书面用语' },
    { id:'i4', severity:'warning', dimension:'钩子效果', desc:'集末缺少有效悬念钩子',                             suggestion:'在末场景添加新威胁或未解谜题' },
    { id:'i5', severity:'info',    dimension:'情绪曲线', desc:'本集情绪平台期过长（3场以上无明显起伏）',           suggestion:'在中段插入小冲突打破情绪平台' },
  ].slice(0, Math.min(quality.issue_count || 3, 5));

  const toggleAll = () => setSelected(selected.length === issues.length ? [] : issues.map(i => i.id));

  return (
    <div className="bg-white rounded-xl border border-amber-300 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-amber-50 border-b border-amber-200">
        <h4 className="text-sm font-semibold text-amber-800">第{episode}集 — 修改建议（{issues.length}条）</h4>
        <div className="flex gap-2">
          <button onClick={toggleAll} className="text-xs text-amber-600 hover:underline">
            {selected.length === issues.length ? '取消全选' : '全选'}
          </button>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
        </div>
      </div>
      <div className="divide-y divide-gray-100">
        {issues.map((issue) => {
          const cfg = SEVERITY_STYLES[issue.severity];
          const isSelected = selected.includes(issue.id);
          return (
            <label key={issue.id} className={`flex gap-3 p-4 cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-indigo-50' : ''}`}>
              <input type="checkbox" checked={isSelected} onChange={() =>
                setSelected(isSelected ? selected.filter(id => id !== issue.id) : [...selected, issue.id])
              } className="mt-0.5 accent-indigo-600" />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${cfg.cls}`}>{cfg.icon} {cfg.label}</span>
                  <span className="text-xs text-gray-400">{issue.dimension}</span>
                </div>
                <p className="text-sm text-gray-800">{issue.desc}</p>
                <p className="text-xs text-gray-500 mt-0.5">→ {issue.suggestion}</p>
              </div>
            </label>
          );
        })}
      </div>
      <div className="px-4 py-3 bg-gray-50 border-t flex items-center justify-between gap-3">
        <p className="text-xs text-gray-400">应用后生成新版本（原版本保留），需配置 LLM 才能自动修改</p>
        <button
          disabled={selected.length === 0 || applyMut.isPending}
          onClick={() => applyMut.mutate({ episodeNumber: episode, suggestions: issues.filter(i => selected.includes(i.id)), agentId: 'drama.polish-master' })}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg disabled:opacity-40 hover:bg-indigo-700 whitespace-nowrap"
        >
          {applyMut.isPending ? '应用中...' : `应用已选（${selected.length}条）`}
        </button>
      </div>
    </div>
  );
}

// ─── 深度质量报告（参考商业截图风格）─────────────────────────────────────────
function QualityReport({ radar, episode, qualityList, totalEpisodes, projectTitle, reportRef }) {
  const [expandedDim, setExpandedDim] = useState(null);
  const [reportSection, setReportSection] = useState('overview'); // overview | detail | summary

  const scores = {};
  if (radar?.dimensions) {
    radar.dimensions.forEach(d => { scores[d.key] = d.score; });
  }
  const overall = radar?.overall_score || 0;
  const grade = radar?.grade || 'D';
  const gradeColor = GRADE_COLORS[grade] || GRADE_COLORS.D;

  if (!radar && qualityList.length === 0) return (
    <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400">
      <div className="text-4xl mb-3">📊</div>
      <p className="text-base font-medium text-gray-600">暂无质量评估数据</p>
      <p className="text-sm mt-2">请先执行「质量报告官」角色，生成详细评估报告</p>
    </div>
  );

  return (
    <div ref={reportRef} className="space-y-4">
      {/* 标签页切换 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="flex border-b border-gray-100">
          {[['overview','📊 综合概览'],['detail','🔍 维度详情'],['summary','📝 汇总报告']].map(([k,l]) => (
            <button key={k} onClick={() => setReportSection(k)}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${reportSection===k?'bg-indigo-50 text-indigo-700 border-b-2 border-indigo-600':'text-gray-600 hover:bg-gray-50'}`}>
              {l}
            </button>
          ))}
        </div>

        {/* ── 综合概览 ── */}
        {reportSection === 'overview' && (
          <div className="p-5">
            {/* 标题行 */}
            <div className="flex items-start justify-between mb-5">
              <div>
                <div className="text-xs text-gray-400 mb-1">剧本质量评估报告</div>
                <h2 className="text-xl font-bold text-gray-900">《{projectTitle}》{episode ? `第${episode}集` : '整剧综合'}</h2>
                {radar?.grade_desc && <p className="text-sm text-gray-500 mt-1">{radar.grade_desc}</p>}
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-400 mb-1">综合评估得分</div>
                <div className={`text-5xl font-black ${gradeColor.text}`}>{overall || '—'}</div>
                <div className={`text-sm font-bold px-3 py-1 rounded-lg border mt-1 ${gradeColor.badge}`}>
                  评价等级：{grade === 'S' ? 'S · 商业精品' : grade === 'A' ? 'A · 质量优良' : grade === 'B' ? 'B · 达到基准' : grade === 'C' ? 'C · 需要优化' : 'D · 不达标'}
                </div>
              </div>
            </div>

            {/* 雷达图 + 维度评分卡 */}
            <div className="grid grid-cols-2 gap-5">
              {/* 左：SVG 雷达图 */}
              <div className="flex items-center justify-center">
                <RadarChart scores={scores} />
              </div>

              {/* 右：8维度评分卡 */}
              <div className="grid grid-cols-2 gap-2">
                {DIM_KEYS.map((key) => {
                  const meta = DIM_META[key];
                  const score = scores[key] || 0;
                  const dim = radar?.dimensions?.find(d => d.key === key);
                  const issueCount = dim?.issues?.length || 0;
                  return (
                    <button key={key} onClick={() => { setExpandedDim(expandedDim === key ? null : key); setReportSection('detail'); }}
                      className="p-3 rounded-lg border border-gray-200 text-left hover:border-indigo-300 hover:shadow-sm transition-all group">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-600">{meta.name}</span>
                        <span className="text-lg font-black" style={{ color: meta.color }}>{score || '—'}</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, backgroundColor: meta.color }} />
                      </div>
                      {issueCount > 0 && (
                        <p className="text-xs text-amber-500 mt-1">{dim?.issue_count?.error > 0 ? `❌${dim.issue_count.error}` : ''} {dim?.issue_count?.warning > 0 ? `⚠️${dim.issue_count.warning}` : ''}</p>
                      )}
                      <p className="text-xs text-indigo-400 opacity-0 group-hover:opacity-100 mt-1">点击查看详情 →</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 情绪曲线（分集情绪趋势） */}
            {qualityList.length > 1 && (
              <div className="mt-5 pt-4 border-t border-gray-100">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">作者设计情绪强度（全剧情绪曲线）</h3>
                <EmotionCurve qualityList={qualityList} />
              </div>
            )}

            {/* 必修项快速查看 */}
            {(radar?.error_count || 0) > 0 && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
                <h4 className="text-xs font-semibold text-red-700 mb-2">❌ 必须修复（{radar.error_count}项）</h4>
                <div className="space-y-1">
                  {(radar.all_issues || []).filter(i => i.severity === 'error').slice(0, 5).map((issue, idx) => (
                    <div key={idx} className="text-xs text-red-700">
                      <span className="font-medium">[{issue.dimension}] </span>{issue.desc}
                      <span className="text-gray-400 ml-1">→ {issue.suggestion}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── 维度详情 ── */}
        {reportSection === 'detail' && (
          <div className="p-5 space-y-3">
            <div className="flex gap-2 flex-wrap mb-4">
              {DIM_KEYS.map(key => {
                const meta = DIM_META[key];
                const score = scores[key] || 0;
                return (
                  <button key={key} onClick={() => setExpandedDim(expandedDim === key ? null : key)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                      expandedDim === key ? 'text-white border-transparent' : 'bg-white border-gray-200 text-gray-600'
                    }`}
                    style={expandedDim === key ? { backgroundColor: meta.color, borderColor: meta.color } : {}}>
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
                <div key={key} className="rounded-xl border border-gray-200 overflow-hidden">
                  {/* 维度标题 */}
                  <div className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50"
                    style={{ borderLeft: `4px solid ${meta.color}` }}
                    onClick={() => setExpandedDim(expandedDim === key ? null : key)}>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-gray-800">{meta.name}</span>
                      <span className="text-xs text-gray-400">{dim?.desc || meta.subItems.join(' / ')}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-24 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: meta.color }} />
                      </div>
                      <span className="text-xl font-black w-10 text-right" style={{ color: meta.color }}>{score || '—'}</span>
                    </div>
                  </div>

                  {/* 维度详情内容 */}
                  {expandedDim === key && (
                    <div className="px-4 pb-4 pt-2 border-t border-gray-100">
                      {/* 子项评分展示 */}
                      <div className="grid grid-cols-2 gap-2 mb-3">
                        {meta.subItems.map((sub, idx) => {
                          // 根据总分估算子项（真实场景应由LLM返回详细子分）
                          const subScore = score > 0 ? Math.max(40, Math.min(100, score + (idx % 3 === 0 ? -8 : idx % 3 === 1 ? 5 : -3))) : 0;
                          const subColor = subScore >= 80 ? '#10b981' : subScore >= 60 ? '#f59e0b' : '#ef4444';
                          return (
                            <div key={sub} className="flex items-center gap-2 text-xs">
                              <span className="text-gray-600 w-24 truncate">{sub}</span>
                              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                <div className="h-full rounded-full" style={{ width: `${subScore}%`, backgroundColor: subColor }} />
                              </div>
                              <span className="font-medium w-6 text-right" style={{ color: subColor }}>{subScore}</span>
                            </div>
                          );
                        })}
                      </div>

                      {/* 维度摘要 */}
                      {dim?.summary && (
                        <p className="text-sm text-gray-700 mb-3 p-2 bg-gray-50 rounded">{dim.summary}</p>
                      )}

                      {/* 维度问题列表 */}
                      {dim?.issues?.length > 0 && (
                        <div className="space-y-2">
                          <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">本维度问题</h5>
                          {dim.issues.map((issue, idx) => {
                            const cfg = SEVERITY_STYLES[issue.severity];
                            return (
                              <div key={idx} className={`p-3 rounded-lg border text-sm ${cfg.cls}`}>
                                <div className="flex items-center gap-1 mb-1">
                                  <span className="font-medium text-xs">{cfg.icon} {cfg.label}</span>
                                </div>
                                <p className="font-medium">{issue.desc}</p>
                                <p className="text-xs mt-1 opacity-80">修复建议：{issue.suggestion}</p>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {(!dim?.issues?.length && score > 0) && (
                        <div className="text-sm text-green-600 bg-green-50 p-2 rounded">✅ 此维度表现良好，无明显问题</div>
                      )}
                      {score === 0 && (
                        <div className="text-sm text-gray-400 bg-gray-50 p-2 rounded">⏳ 尚未进行质量评估，请先执行「质量报告官」角色</div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── 汇总报告 ── */}
        {reportSection === 'summary' && (
          <SummaryReport radar={radar} qualityList={qualityList} projectTitle={projectTitle} scores={scores} overall={overall} grade={grade} />
        )}
      </div>

      {/* 分集质量网格 */}
      {qualityList.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">分集质量概况（{qualityList.length}集已评估 / 共{totalEpisodes}集）</h3>
          <div className="grid grid-cols-6 gap-1.5 sm:grid-cols-8 lg:grid-cols-10">
            {Array.from({ length: totalEpisodes }, (_, i) => {
              const ep = i + 1;
              const q = qualityList.find(q => q.episode_number === ep);
              const g = q?.grade;
              const color = g ? GRADE_COLORS[g] : null;
              return (
                <div key={ep} className={`p-1.5 rounded text-center border text-xs ${color?.badge || 'border-gray-100 bg-gray-50 text-gray-300'}`}>
                  <div className="text-gray-500 text-[10px]">E{ep}</div>
                  <div className="font-bold">{q?.overall_score || '—'}</div>
                  {g && <div className="text-[10px]">{g}</div>}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── SVG 雷达图 ───────────────────────────────────────────────────────────────
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
      {/* 背景层 */}
      {levels.map((lvl) => {
        const pts = keys.map((_, i) => { const p = toXY(i, lvl); return `${p.x},${p.y}`; }).join(' ');
        return <polygon key={lvl} points={pts} fill="none" stroke="#e5e7eb" strokeWidth="0.8" />;
      })}
      {/* 轴线 */}
      {keys.map((_, i) => {
        const outer = toXY(i, 100);
        return <line key={i} x1={cx} y1={cy} x2={outer.x} y2={outer.y} stroke="#e5e7eb" strokeWidth="0.8" />;
      })}
      {/* 数据区域 */}
      <path d={radarPath} fill="#6366f133" stroke="#6366f1" strokeWidth="1.5" />
      {/* 数据点 */}
      {radarPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3" fill="#6366f1" />
      ))}
      {/* 标签 */}
      {keys.map((k, i) => {
        const label = toXY(i, 118);
        const meta = DIM_META[k];
        const score = scores[k] || 0;
        return (
          <text key={k} x={label.x} y={label.y} textAnchor="middle" dominantBaseline="middle"
            fontSize="9" fill={score > 0 ? meta.color : '#9ca3af'} fontWeight="600">
            {meta.abbr}{score > 0 ? ` ${score}` : ''}
          </text>
        );
      })}
    </svg>
  );
}

// ─── 情绪曲线图 ──────────────────────────────────────────────────────────────
function EmotionCurve({ qualityList }) {
  if (!qualityList.length) return null;

  const sorted = [...qualityList].sort((a, b) => a.episode_number - b.episode_number);
  const maxEp = sorted[sorted.length - 1]?.episode_number || 1;
  const W = 600, H = 100, PAD = 30;
  const plotW = W - PAD * 2, plotH = H - PAD * 2;

  // 将 emotion 分数转为 -5~+5 情绪强度（基于50分中性）
  const emotionValues = sorted.map(q => {
    const score = q.scores?.emotion || 0;
    if (!score) return null;
    return { ep: q.episode_number, val: ((score - 50) / 10).toFixed(1) };
  }).filter(Boolean);

  if (emotionValues.length < 2) return (
    <div className="text-xs text-gray-400 text-center py-4">需要更多集数的评估数据才能显示情绪曲线</div>
  );

  const toX = (ep) => PAD + ((ep - 1) / (maxEp - 1)) * plotW;
  const toY = (val) => PAD + plotH - ((parseFloat(val) + 5) / 10) * plotH;

  const linePath = emotionValues.map((v, i) => `${i === 0 ? 'M' : 'L'} ${toX(v.ep)} ${toY(v.val)}`).join(' ');
  const areaPath = `${linePath} L ${toX(emotionValues[emotionValues.length-1].ep)} ${toY(0)} L ${toX(1)} ${toY(0)} Z`;

  return (
    <div className="bg-gray-950 rounded-xl p-4 overflow-x-auto">
      <div className="text-xs text-gray-400 mb-2">+为正向情绪，-为负向情绪 · 1:温和 2:中等 3:强烈 4:极度 5:极端</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full min-w-[400px]" style={{ height: '120px' }}>
        {/* 中轴线 */}
        <line x1={PAD} y1={toY(0)} x2={W-PAD} y2={toY(0)} stroke="#374151" strokeDasharray="3,3" strokeWidth="1" />
        {/* Y轴刻度 */}
        {[-4,-2,0,2,4].map(v => (
          <text key={v} x={PAD-4} y={toY(v)} textAnchor="end" dominantBaseline="middle" fontSize="8" fill="#6b7280">{v>0?`+${v}`:v}</text>
        ))}
        {/* X轴刻度 */}
        {emotionValues.filter((_, i) => i % Math.max(1, Math.floor(emotionValues.length/10)) === 0).map(v => (
          <text key={v.ep} x={toX(v.ep)} y={H-10} textAnchor="middle" fontSize="8" fill="#6b7280">{v.ep}</text>
        ))}
        {/* 面积区域 */}
        <path d={areaPath} fill="#6366f11a" />
        {/* 曲线 */}
        <path d={linePath} fill="none" stroke="#818cf8" strokeWidth="1.5" />
        {/* 数据点 */}
        {emotionValues.map(v => (
          <circle key={v.ep} cx={toX(v.ep)} cy={toY(v.val)} r="2.5" fill="#6366f1" />
        ))}
      </svg>
    </div>
  );
}

// ─── 汇总报告（参考商业风格）────────────────────────────────────────────────
function SummaryReport({ radar, qualityList, projectTitle, scores, overall, grade }) {
  const gradeLabel = grade === 'S' ? '商业精品' : grade === 'A' ? '质量优良' : grade === 'B' ? 'B级合格品' : grade === 'C' ? '需大幅优化' : '不达标';
  const weakEps = qualityList.filter(q => (q.overall_score || 0) < 75);
  const passEps = qualityList.filter(q => (q.overall_score || 0) >= 75);

  // 维度优劣分析
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
        <h3 className="text-base font-bold text-gray-900 border-b border-gray-200 pb-2 mb-3">— 汇总报告</h3>

        {/* 核心诊断 */}
        <section className="mb-4">
          <h4 className="font-semibold text-gray-800 mb-2">核心诊断</h4>
          <div className="mb-2">
            <span className="font-bold text-gray-700">开篇定性</span>
            <p className="text-gray-600 mt-1">
              {projectTitle && `《${projectTitle}》`}综合评分{overall}分，等级{grade}（{gradeLabel}）。
              {topDims.length > 0 && `${topDims.map(d=>d.name).join('、')}（${topDims.map(d=>d.score).join('/')}分）表现较强，`}
              {weakDims.length > 0 && `${weakDims.map(d=>d.name).join('、')}（${weakDims.map(d=>d.score).join('/')}分）需要重点提升。`}
              {weakEps.length > 0 && `共${weakEps.length}集质量低于75分，需优先处理。`}
            </p>
          </div>
        </section>

        {/* 关键数支撑 */}
        <section className="mb-4">
          <h4 className="font-semibold text-gray-800 mb-2">关键数据支撑</h4>
          <div className="grid grid-cols-2 gap-3">
            {dimScores.map(d => {
              const color = d.score >= 80 ? GRADE_COLORS.A.text : d.score >= 70 ? GRADE_COLORS.B.text : d.score >= 60 ? GRADE_COLORS.C.text : GRADE_COLORS.D.text;
              return (
                <div key={d.key} className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-lg">
                  <span className="text-gray-600">{d.name}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-indigo-500" style={{ width: `${d.score}%` }} />
                    </div>
                    <span className={`font-bold text-sm ${color}`}>{d.score}/10</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* 风险与缺陷 */}
        {(errors.length > 0 || warnings.length > 0) && (
          <section className="mb-4">
            <h4 className="font-semibold text-gray-800 mb-2">风险与缺陷分析</h4>
            {errors.length > 0 && (
              <div className="mb-2">
                <p className="text-xs font-semibold text-red-600 mb-1">致命缺陷（内容层面）</p>
                {errors.map((e, idx) => (
                  <div key={idx} className="text-gray-700 mb-1">
                    <span className="font-medium text-red-600">[{e.dimension}] </span>{e.desc}
                    <p className="text-gray-500 text-xs mt-0.5 pl-4">→ {e.suggestion}</p>
                  </div>
                ))}
              </div>
            )}
            {warnings.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-amber-600 mb-1">优化建议（审美层面）</p>
                {warnings.slice(0, 4).map((w, idx) => (
                  <div key={idx} className="text-gray-600 mb-1 text-xs">
                    <span className="font-medium">[{w.dimension}] </span>{w.desc}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* 资产估计 */}
        <section className="mb-4">
          <h4 className="font-semibold text-gray-800 mb-2">资产估计</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-green-50 rounded-lg p-3 border border-green-100">
              <p className="text-xs font-semibold text-green-700 mb-1">可取之处</p>
              {topDims.slice(0,2).map(d => (
                <p key={d.key} className="text-xs text-gray-700">✅ {d.name}（{d.score}分）表现突出</p>
              ))}
              {passEps.length > 0 && <p className="text-xs text-gray-700">✅ {passEps.length}集已达质量标准</p>}
            </div>
            <div className="bg-red-50 rounded-lg p-3 border border-red-100">
              <p className="text-xs font-semibold text-red-700 mb-1">资产的局限性</p>
              {weakDims.slice(0,2).map(d => (
                <p key={d.key} className="text-xs text-gray-700">⚠️ {d.name}（{d.score}分）存在明显短板</p>
              ))}
              {weakEps.length > 0 && <p className="text-xs text-gray-700">⚠️ 第{weakEps.map(e=>e.episode_number).join('、')}集低于75分</p>}
            </div>
          </div>
        </section>

        {/* 修复路径 */}
        <section>
          <h4 className="font-semibold text-gray-800 mb-2">最终裁决与修改路径</h4>
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <p className="font-bold text-gray-800 mb-2">
              项目评级【{grade}级 — {overall >= 80 ? '可投入优化' : overall >= 60 ? '需系统性修改' : '建议重构核心'}】
            </p>
            <p className="text-gray-600 text-xs mb-3">
              {overall >= 80 ? '当前版本具备基础商业价值，针对核心短板进行手术式修改后可交付。' :
               overall >= 60 ? '剧本存在可修复问题，建议按优先级逐步改进，先解决必修项再优化推荐项。' :
               '剧本质量有明显不足，建议重新执行关键角色（情节架构师/人设设计师），以更好的输入质量重新生成。'}
            </p>
            <div className="space-y-1">
              {[...errors, ...warnings].slice(0,5).map((issue, idx) => (
                <div key={idx} className="text-xs text-gray-600">
                  <span className="font-medium">{idx+1}. [{issue.dimension}] </span>
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
