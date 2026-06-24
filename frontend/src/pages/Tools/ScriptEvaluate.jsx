import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Loader2, BarChart3, Star, ArrowRight, FileText, Sparkles, Plus } from 'lucide-react'
import { works as worksApi, creation } from '@/services/api'
import ScoreReport from '@/components/creation/ScoreReport'
import ToolsShell from '@/components/tools/ToolsShell'
import { Button } from '@/components/ui'
import EmptyState from '@/components/ui/EmptyState'

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
        const items = data.items
        if (!cancelled) {
          setWorks(items)
          if (items[0]?.project_id) setSelectedId(items[0].project_id)
        }
      } catch (err) {
        if (!cancelled) {
          setWorks([])
          toast.error(err?.message || '加载作品列表失败')
        }
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
          detail?.scoreReport ||
          detail?.fusionSnapshot?.scoreReport ||
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
      subtitle="8 维质量评分与放行线判定，创作完成后在此查看专业评估报告"
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-6 mb-6"
      >
        <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
          <Star className="w-5 h-5 text-gold-400" />
          选择已完成的剧本
        </h2>
        <p className="text-sm text-slate-400 mb-4">展示已完成作品，选中后自动加载评分报告</p>

        {loading ? (
          <div className="flex items-center justify-center py-10 gap-2 text-slate-400">
            <Loader2 className="w-5 h-5 animate-spin text-gold-400" />
            加载中…
          </div>
        ) : works.length === 0 ? (
          <EmptyState
            icon={<FileText className="w-12 h-12 text-gold-400" />}
            title="暂无已完成作品"
            description="完成剧本创作后，即可在此查看专业评分报告"
            actionLabel="去创作"
            onAction={() => navigate('/drama')}
            compact
          />
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
                      ? 'border-gold-500/30 bg-gold-500/10'
                      : 'border-white/5 bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.05]'
                  }`}
                >
                  <div>
                    <div className="font-medium text-white">{w.title || '未命名剧本'}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{w.episode_count || w.episodes || '—'} 集</div>
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
          className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-6 mb-6"
        >
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-gold-400" />
              8 维评分报告
            </h2>
            {selectedId && (
              <button
                type="button"
                onClick={() => navigate(`/works/${selectedId}`)}
                className="inline-flex items-center gap-1 text-sm text-gold-400 hover:text-gold-300 transition-colors"
              >
                查看完整作品
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
          {reportLoading ? (
            <div className="flex items-center justify-center py-10 gap-2 text-slate-400">
              <Loader2 className="w-5 h-5 animate-spin text-gold-400" />
              加载报告…
            </div>
          ) : scoreReport ? (
            <ScoreReport report={scoreReport} />
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">该作品暂无详细评分数据</p>
          )}
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-6 text-center"
      >
        <Sparkles className="w-8 h-8 text-slate-500 mx-auto mb-2" />
        <p className="text-sm text-slate-400 mb-4">
          上传外部剧本文本直接评估的能力即将开放
        </p>
        <Button
          variant="gold"
          size="sm"
          iconLeft={<Plus className="w-4 h-4" />}
          onClick={() => navigate('/drama')}
        >
          开始新创作
        </Button>
      </motion.div>
    </ToolsShell>
  )
}
