import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Eye, BookOpen, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import AiGenerateButton from '@/components/creation/AiGenerateButton'
import ToolsShell from '@/components/tools/ToolsShell'
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
    }).catch(() => {
      toast.error('加载计费配置失败')
    })
  }, [])

  return (
    <ToolsShell
        active="pullsheet"
        title="拉片分析"
        subtitle="对标参考作品拆解节奏、钩子与镜头语言，独立于剧本创作表单。"
      >
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-gray-200 bg-white border border-gray-200 p-6 space-y-6"
        >
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-900 mb-2">
              <BookOpen className="w-4 h-4 text-brand-600" />
              参考作品 <span className="text-red-400">*</span>
            </label>
            <textarea
              value={referenceWork}
              onChange={(e) => setReferenceWork(e.target.value.slice(0, 500))}
              placeholder="例：《回家的诱惑》— 家庭伦理、反转节奏、情绪钩子…"
              className="sf-control h-28 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">题材（可选）</label>
            <input
              value={theme}
              onChange={(e) => setTheme(e.target.value.slice(0, 50))}
              placeholder="例：甜宠虐恋"
              className="sf-control"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">你的创意方向（可选）</label>
            <textarea
              value={coreIdea}
              onChange={(e) => setCoreIdea(e.target.value.slice(0, 300))}
              placeholder="简要描述你想对标学习的叙事方向…"
              className="sf-control h-24 resize-none"
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
            <div className="rounded-xl border border-gray-200 bg-white border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-brand-600 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                分析结果
              </h3>
              <pre className="whitespace-pre-wrap text-sm text-gray-600 leading-relaxed font-sans">{analysis}</pre>
            </div>
          )}
        </motion.div>
      </ToolsShell>
  )
}
