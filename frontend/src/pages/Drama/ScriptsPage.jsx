import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  getDramaProject,
  getQualityRadar,
  validateWordCount,
} from '../../services/drama';

/**
 * 8维评分雷达图（纯CSS实现，不依赖图表库）
 */
function RadarChart({ data }) {
  if (!data || data.length === 0) return null;

  const size = 200;
  const center = size / 2;
  const radius = 80;
  const angleStep = (2 * Math.PI) / data.length;

  const getPoint = (index, value, maxValue = 100) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = (value / maxValue) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  const getLabelPoint = (index) => {
    const angle = index * angleStep - Math.PI / 2;
    const r = radius + 20;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  // 背景同心多边形
  const bgLevels = [20, 40, 60, 80, 100];
  const bgPolygons = bgLevels.map((level) =>
    data.map((_, i) => {
      const pt = getPoint(i, level);
      return `${pt.x},${pt.y}`;
    }).join(' ')
  );

  // 数据多边形
  const dataPolygon = data.map((d, i) => {
    const pt = getPoint(i, d.score);
    return `${pt.x},${pt.y}`;
  }).join(' ');

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="overflow-visible">
        {/* 背景网格 */}
        {bgPolygons.map((pts, i) => (
          <polygon
            key={i}
            points={pts}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="0.5"
          />
        ))}

        {/* 轴线 */}
        {data.map((_, i) => {
          const outer = getPoint(i, 100);
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={outer.x}
              y2={outer.y}
              stroke="#e5e7eb"
              strokeWidth="0.5"
            />
          );
        })}

        {/* 数据多边形 */}
        <polygon
          points={dataPolygon}
          fill="rgba(99, 102, 241, 0.2)"
          stroke="#6366f1"
          strokeWidth="2"
        />

        {/* 数据点 */}
        {data.map((d, i) => {
          const pt = getPoint(i, d.score);
          return (
            <circle
              key={i}
              cx={pt.x}
              cy={pt.y}
              r="3"
              fill="#6366f1"
            />
          );
        })}

        {/* 标签 */}
        {data.map((d, i) => {
          const labelPt = getLabelPoint(i);
          return (
            <text
              key={i}
              x={labelPt.x}
              y={labelPt.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="9"
              fill="#6b7280"
            >
              {d.dimension}
            </text>
          );
        })}
      </svg>

      {/* 图例 */}
      <div className="grid grid-cols-4 gap-2 mt-4 w-full text-xs">
        {data.map((d) => (
          <div key={d.key} className="flex flex-col items-center">
            <span className="font-semibold text-gray-700">{d.score || '--'}</span>
            <span className="text-gray-400">{d.dimension}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** 单集字数状态标签 */
function WordCountBadge({ stats }) {
  if (!stats) return null;
  const { word_count, overall } = stats;
  const isOk = overall === '通过';
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${
      isOk ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
    }`}>
      {word_count?.total}字 {isOk ? '✅' : '❌'}
    </span>
  );
}

/** 剧本展示页 */
export default function ScriptsPage() {
  const { projectId } = useParams();
  const [selectedEp, setSelectedEp] = useState(1);
  const [wordValidation, setWordValidation] = useState({});

  const { data: projectRes } = useQuery({
    queryKey: ['drama-project', projectId],
    queryFn: () => getDramaProject(projectId),
  });
  const project = projectRes?.data?.data || projectRes?.data;

  const { data: radarRes } = useQuery({
    queryKey: ['drama-radar', projectId],
    queryFn: () => getQualityRadar(projectId),
  });
  const radarData = radarRes?.data?.data;

  if (!project) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  const wordStats = project.word_count_stats || {};
  const totalEpisodes = project.total_episodes || 30;

  const handleValidateWord = async (epNum, content) => {
    if (!content) return;
    try {
      const res = await validateWordCount(content, epNum);
      setWordValidation((prev) => ({ ...prev, [epNum]: res?.data?.data }));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部 */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <h1 className="text-lg font-bold text-gray-900">{project.title}</h1>
          <span className="text-sm text-gray-400">{totalEpisodes}集</span>

          {radarData && (
            <div className="ml-auto flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                radarData.grade === 'S' ? 'bg-yellow-100 text-yellow-700'
                : radarData.grade === 'A' ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-600'
              }`}>
                {radarData.grade}级 · {radarData.overall_score}分
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 flex gap-6">
        {/* 左侧：集数列表 + 字数统计 */}
        <aside className="w-64 shrink-0">
          {/* 字数统计概览 */}
          {Object.keys(wordStats).length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">字数统计</h3>
              <div className="space-y-1.5">
                {(() => {
                  const stats = Object.values(wordStats);
                  const totals = stats.map((s) => s.total || 0);
                  const avg = totals.length
                    ? Math.round(totals.reduce((a, b) => a + b, 0) / totals.length)
                    : 0;
                  const passCount = stats.filter((s) => s.pass).length;
                  return (
                    <>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">平均字数</span>
                        <span className="font-medium text-gray-700">{avg}字</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">达标集数</span>
                        <span className="font-medium text-green-600">
                          {passCount}/{stats.length}
                        </span>
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>
          )}

          {/* 集数列表 */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h3 className="text-sm font-medium text-gray-700">剧集列表</h3>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {Array.from({ length: totalEpisodes }, (_, i) => i + 1).map((ep) => {
                const epStats = wordStats[ep] || wordValidation[ep];
                const isSelected = selectedEp === ep;
                return (
                  <button
                    key={ep}
                    onClick={() => setSelectedEp(ep)}
                    className={`w-full flex items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0 ${
                      isSelected ? 'bg-indigo-50' : ''
                    }`}
                  >
                    <span className={`font-medium ${isSelected ? 'text-indigo-700' : 'text-gray-700'}`}>
                      第{String(ep).padStart(2, '0')}集
                    </span>
                    {epStats ? (
                      <WordCountBadge stats={epStats} />
                    ) : (
                      <span className="text-xs text-gray-300">待生成</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </aside>

        {/* 主区域：剧本内容 + 评分 */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* 剧本内容 */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <h2 className="font-medium text-gray-900">第{selectedEp}集</h2>
              <div className="flex items-center gap-2">
                {wordStats[selectedEp] && (
                  <WordCountBadge stats={wordStats[selectedEp]} />
                )}
              </div>
            </div>

            <div className="p-5">
              {/* 剧本内容展示区（目前为占位符，实际会从artifacts读取） */}
              <div className="font-mono text-sm text-gray-700 whitespace-pre-wrap leading-relaxed min-h-64">
                {project?.episode_scripts?.[selectedEp] || (
                  <div className="text-center text-gray-400 py-16">
                    <div className="text-3xl mb-2">📝</div>
                    <p>第{selectedEp}集剧本尚未生成</p>
                    <p className="text-xs mt-1 text-gray-300">在工作台执行"剧本执笔师"角色后，内容将显示在这里</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 评分雷达图 */}
          <div className="space-y-4">
            {radarData ? (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-gray-700">质量评分</h3>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    radarData.grade === 'S' ? 'bg-yellow-100 text-yellow-700'
                    : radarData.grade === 'A' ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-600'
                  }`}>
                    {radarData.grade}级
                  </span>
                </div>
                <RadarChart data={radarData.radar} />
                <div className="mt-4 pt-4 border-t border-gray-100 text-center">
                  <span className="text-2xl font-bold text-gray-900">{radarData.overall_score}</span>
                  <span className="text-sm text-gray-400 ml-1">/ 100</span>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 p-5 text-center text-gray-400">
                <div className="text-3xl mb-2">📊</div>
                <p className="text-sm">评分雷达图</p>
                <p className="text-xs mt-1 text-gray-300">完成质量报告官后显示</p>
              </div>
            )}

            {/* 交付状态 */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">交付状态</h3>
              <div className="space-y-2">
                {[
                  { label: '剧本完整性', value: project.completed_roles?.includes('drama.script-writer') },
                  { label: '质量审稿通过', value: project.completed_roles?.includes('drama.quality-reporter') },
                  { label: '合规检测通过', value: project.completed_roles?.includes('drama.compliance-guard') },
                  { label: '字数达标', value: Object.values(wordStats).every((s) => s?.pass) },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">{label}</span>
                    <span className={value ? 'text-green-600' : 'text-gray-300'}>
                      {value ? '✅' : '○'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
