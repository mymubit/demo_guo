import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { BarChart3, Star, ArrowRight, FileText, Sparkles } from 'lucide-react'
import { works as worksApi, creation } from '@/services/api'
import ScoreReport from '@/components/creation/ScoreReport'
import ToolsShell from '@/components/tools/ToolsShell'

export default function ScriptEvaluate() {
  const navigate = useNavigate()
  const [works, setWorks] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState('')
  const [scoreReport, setScoreReport] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const data = await worksApi.list(1, 'completed')
        const items = data.items.filter((w) => w.score != null)
        if (!cancelled) {
          setWorks(items)
          if (items[0]?.project_id) setSelectedId(items[0].project_id)
        }
      } catch {
        if (!cancelled) setWorks([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!selectedId) {
      setScoreReport(null)
      return
    }
    let cancelled = false
    ;(async () => {
      setReportLoading(true)
      try {
        const [detail, progress] = await Promise.all([
          worksApi.detail(selectedId).catch(() => null),
          creation.progress(selectedId).catch(() => null),
        ])
        const report =
          detail?.fusion_snapshot?.scoreReport ||
          progress?.score_summary ||
          (detail?.overall_score != null
            ? {
                overallScore: detail.overall_score,
                grade: detail.grade,
                dimensions: [],
              }
            : null)
        if (!cancelled) setScoreReport(report || null)
      } catch {
        if (!cancelled) setScoreReport(null)
      } finally {
        if (!cancelled) setReportLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [selectedId])

  const selectedWork = works.find((w) => w.project_id === selectedId)

  return (
    <ToolsShell
        active="evaluate"
        title="剧本评估"
        subtitle="8 维质量评分与放行线判定，与创作流水线分离。创作完成后在此查看报告。"
      >
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-white/5 bg-slate-900/60 p-6 mb-6"
        >
          <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
            <Star className="w-5 h-5 text-gold-400" />
            选择已完成的剧本
          </h2>
          <p className="text-sm text-navy-400 mb-4">仅展示已有评分的作品；新剧本请在「开始创作」完成后自动评分</p>

          {loading ? (
            <p className="text-sm text-navy-400">加载中…</p>
          ) : works.length === 0 ? (
            <div className="text-center py-10">
              <FileText className="w-12 h-12 text-navy-400 mx-auto mb-3" />
              <p className="text-navy-300 mb-4">暂无带评分的已完成作品</p>
              <button type="button" onClick={() => navigate('/creation')} className="btn-gold px-6 py-2.5 rounded-xl">
                去创作
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {works.map((w) => {
                const active = w.project_id === selectedId
                const score = w.score ?? w.overall_score
                return (
                  <button
                    key={w.project_id}
                    type="button"
                    onClick={() => setSelectedId(w.project_id)}
                    className={`w-full text-left px-4 py-3 rounded-xl border transition-all flex items-center justify-between gap-3 ${
                      active
                        ? 'border-gold-400/50 bg-gold-400/10 shadow-gold'
                        : 'border-white/10 bg-white/[0.02] hover:border-white/20'
                    }`}
                  >
                    <div>
                      <div className="font-medium text-white">{w.title || '未命名剧本'}</div>
                      <div className="text-xs text-navy-400 mt-0.5">{w.episode_count || '—'} 集</div>
                    </div>
                    <span className="text-gold-400 font-bold shrink-0">{score != null ? `${score} 分` : '—'}</span>
                  </button>
                )
              })}
            </div>
          )}
        </motion.div>

        {(selectedWork || scoreReport) && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl border border-white/5 bg-slate-900/60 p-6 mb-6"
          >
            <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
              <h2 className="text-lg font-bold text-white">8 维评分报告</h2>
              {selectedId && (
                <button
                  type="button"
                  onClick={() => navigate(`/works/${selectedId}`)}
                  className="inline-flex items-center gap-1 text-sm text-gold-400 hover:text-gold-300"
                >
                  查看完整作品
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
            {reportLoading ? (
              <p className="text-sm text-navy-400">加载报告…</p>
            ) : scoreReport ? (
              <ScoreReport report={scoreReport} />
            ) : (
              <p className="text-sm text-navy-400">该作品暂无详细评分数据，请稍后在作品详情查看。</p>
            )}
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-dashed border-white/10 p-6 text-center"
        >
          <Sparkles className="w-8 h-8 text-navy-400 mx-auto mb-2" />
          <p className="text-sm text-navy-400">
            上传外部剧本文本直接评估的能力即将开放；当前请通过「开始创作」生成剧本后在此查看评分。
          </p>
        </motion.div>
      </ToolsShell>
  )
}
