import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Eye, BookOpen, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import AiGenerateButton from '@/components/creation/AiGenerateButton'
import { billing } from '@/services/api'

export default function PullSheetAnalyze() {
  const [referenceWork, setReferenceWork] = useState('')
  const [coreIdea, setCoreIdea] = useState('')
  const [theme, setTheme] = useState('')
  const [analysis, setAnalysis] = useState('')
  const [currencyName, setCurrencyName] = useState('创作币')
  const [actionCost, setActionCost] = useState(50)

  useEffect(() => {
    billing.catalog().then((data) => {
      setCurrencyName(data?.currency_name || '创作币')
      const row = (data?.field_actions || []).find((a) => a.action_key === 'ai.generate.pull_sheet')
      if (row?.coin_cost != null) setActionCost(row.coin_cost)
    }).catch(() => {})
  }, [])

  return (
    <div className="relative min-h-screen py-12">
      <div className="particles-bg" />
      <div className="max-w-3xl mx-auto px-6 relative z-10">
        <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-4 badge">
            <Eye className="w-4 h-4" />
            <span>会员工具</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-3">拉片分析</h1>
          <p className="text-navy-300 max-w-xl mx-auto leading-relaxed">
            对标参考作品拆解节奏、钩子与镜头语言，独立于剧本创作表单。与「参考作品」字段填写的用途不同。
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-2xl p-6 space-y-6"
        >
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-white mb-2">
              <BookOpen className="w-4 h-4 text-gold-400" />
              参考作品 <span className="text-red-400">*</span>
            </label>
            <textarea
              value={referenceWork}
              onChange={(e) => setReferenceWork(e.target.value.slice(0, 500))}
              placeholder="例：《回家的诱惑》— 家庭伦理、反转节奏、情绪钩子…"
              className="w-full h-28 p-4 rounded-xl bg-navy-900/50 border border-navy-600/30 text-white placeholder-navy-500 focus:border-gold-400/40 outline-none resize-none text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">题材（可选）</label>
            <input
              value={theme}
              onChange={(e) => setTheme(e.target.value.slice(0, 50))}
              placeholder="例：甜宠虐恋"
              className="w-full px-4 py-3 rounded-xl bg-navy-900/50 border border-navy-600/30 text-white placeholder-navy-500 focus:border-gold-400/40 outline-none text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">你的创意方向（可选）</label>
            <textarea
              value={coreIdea}
              onChange={(e) => setCoreIdea(e.target.value.slice(0, 300))}
              placeholder="简要描述你想对标学习的叙事方向…"
              className="w-full h-24 p-4 rounded-xl bg-navy-900/50 border border-navy-600/30 text-white placeholder-navy-500 focus:border-gold-400/40 outline-none resize-none text-sm"
            />
          </div>

          <div className="flex justify-center pt-2">
            <AiGenerateButton
              actionKey="ai.generate.pull_sheet"
              coinCost={actionCost}
              currencyName={currencyName}
              label="开始拉片分析"
              context={() => ({
                theme: theme || '都市情感',
                core_idea: coreIdea,
                reference_work: referenceWork,
                references: referenceWork,
              })}
              disabled={!referenceWork.trim()}
              onGenerated={(text) => {
                setAnalysis(text)
                toast.success('拉片分析已生成')
              }}
              className="px-8 py-3 rounded-xl"
            />
          </div>

          {analysis && (
            <div className="rounded-xl bg-navy-900/60 border border-navy-700/40 p-5">
              <h3 className="text-sm font-semibold text-gold-400 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                分析结果
              </h3>
              <pre className="whitespace-pre-wrap text-sm text-navy-200 leading-relaxed font-sans">{analysis}</pre>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
