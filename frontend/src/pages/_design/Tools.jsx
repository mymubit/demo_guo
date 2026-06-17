/**
 * Tools.jsx — 工具合集（剧本评估 + 拉片分析）
 *
 * 对应后端：portal/creation/views.py (ScriptEvaluate / PullSheetAnalyze)
 * 视觉：左右分屏，左侧工具导航，右侧工作区
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, Eye, Upload, Sparkles, ChevronRight, FileText, Check, X } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const TOOLS = [
  { k: 'evaluate', n: '剧本评估', icon: BarChart3, desc: '上传剧本，AI 给出四维评分与改进建议' },
  { k: 'pullsheet', n: '拉片分析', icon: Eye, desc: '粘贴分镜或视频链接，AI 拆解镜头与节奏' },
]

const DIMENSIONS = [
  { k: '格式', v: 92 },
  { k: '节奏', v: 84 },
  { k: '内容', v: 86 },
  { k: '制作', v: 80 },
]

const SUGGESTIONS = [
  { tone: 'warning', text: '第 17 集后半段情绪曲线塌陷，建议补一场转折戏' },
  { tone: 'info', text: '第 22 集钩子力度不足，可在「会议室」场景末加 1 句独白' },
  { tone: 'success', text: '人物关系图谱清晰，主角弧线完整' },
  { tone: 'warning', text: '「李明远」前 3 集动机铺垫偏弱' },
]

export default function Tools() {
  const [tool, setTool] = useState('evaluate')

  return (
    <motion.div {...pageEnter} className="grid min-h-[calc(100svh-3.25rem)] grid-cols-1 lg:grid-cols-[280px_1fr]">
      {/* 左侧 — 工具导航 */}
      <aside className="border-r border-white/5 bg-navy-950/60 p-5">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">专业工具</div>
        <nav className="mt-3 space-y-1.5">
          {TOOLS.map((t) => (
            <button
              key={t.k}
              type="button"
              onClick={() => setTool(t.k)}
              className={cn(
                'flex w-full items-start gap-3 rounded-xl border p-3 text-left transition-colors',
                tool === t.k
                  ? 'border-gold-400/40 bg-gold-400/10 text-white'
                  : 'border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20',
              )}
            >
              {renderLucideIcon(t.icon, cn(ICON.md, 'mt-0.5 shrink-0', tool === t.k ? 'text-gold-400' : 'text-slate-400'))}
              <div>
                <div className="text-sm font-semibold">{t.n}</div>
                <div className="mt-0.5 text-[11px] text-slate-400">{t.desc}</div>
              </div>
            </button>
          ))}
        </nav>

        <div className="mt-5 rounded-xl border border-dashed border-indigo-500/40 bg-indigo-500/[0.08] p-3 text-[12px] text-slate-300">
          <b className="text-indigo-300">提示</b>
          <p className="mt-1 text-slate-400">评估结果会自动入库到「质量缺陷」，帮助主链团队迭代技能模板。</p>
        </div>
      </aside>

      {/* 右侧 — 工作区 */}
      <main className="p-7">
        {tool === 'evaluate' ? <EvaluateWork /> : <PullSheetWork />}
      </main>
    </motion.div>
  )
}

function EvaluateWork() {
  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <header>
        <div className="text-xs text-slate-500">Tools / <b className="text-white">剧本评估</b></div>
        <h1 className="mt-1 text-2xl font-bold">上传你的剧本，拿到专业级四维评分</h1>
      </header>

      {/* 上传区 */}
      <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-8 text-center">
        <Upload className="mx-auto h-10 w-10 text-slate-500" />
        <p className="mt-3 text-sm text-slate-300">
          拖入文件 · 或
          <Button variant="ghost" size="sm" className="ml-2">选择文件</Button>
        </p>
        <p className="mt-1 text-xs text-slate-500">支持 .txt / .md / .fountain / .fdx · 单文件 ≤ 10 MB</p>
      </div>

      {/* 评分结果 */}
      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="m-0 text-base font-semibold">《逆光》第 17 集 · 评估结果</h2>
            <div className="mt-1 text-xs text-slate-500">综合 86 / 100 · 用时 1.2s · doubao-pro-32k</div>
          </div>
          <Button variant="gold" size="md" iconRight={<ChevronRight className={ICON.md} />}>查看详细报告</Button>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {DIMENSIONS.map((d) => (
            <div key={d.k} className="rounded-xl border border-white/5 bg-white/[0.03] p-3">
              <div className="text-xs text-slate-400">{d.k}</div>
              <div className="mt-1 text-2xl font-bold text-white">{d.v}</div>
              <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-white/5">
                <span className="block h-full rounded-full bg-gradient-to-r from-gold-300 to-gold-500" style={{ width: `${d.v}%` }} />
              </div>
            </div>
          ))}
        </div>

        <h3 className="mt-5 mb-2 text-sm font-semibold text-white">改进建议</h3>
        <ul className="m-0 space-y-1.5 p-0">
          {SUGGESTIONS.map((s, i) => (
            <li key={i} className="flex items-start gap-2.5 rounded-lg border border-white/5 bg-white/[0.02] p-2.5 text-[13px] text-slate-200">
              <Badge tone={s.tone} className="mt-0.5 shrink-0">{s.tone === 'success' ? <Check className={ICON.xs} /> : s.tone === 'warning' ? '!' : 'i'}</Badge>
              {s.text}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function PullSheetWork() {
  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <header>
        <div className="text-xs text-slate-500">Tools / <b className="text-white">拉片分析</b></div>
        <h1 className="mt-1 text-2xl font-bold">把一段视频 / 分镜，拆成可学习的镜头表</h1>
      </header>

      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5">
        <div className="flex flex-wrap items-center gap-3">
          <input
            placeholder="粘贴分镜 / 视频链接（如 B 站 / 抖音）"
            className="h-10 min-w-0 flex-1 rounded-xl border border-white/10 bg-white/5 px-3 text-sm text-white placeholder:text-slate-500 focus:border-gold-400/60 focus:outline-none"
          />
          <Button variant="gold" size="md" iconLeft={<Sparkles className={ICON.md} />}>开始拆解</Button>
        </div>
      </div>

      {/* 镜头表 */}
      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5">
        <h3 className="m-0 mb-3 text-sm font-semibold text-white">镜头 1–12 / 共 86</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="overflow-hidden rounded-xl border border-white/5 bg-white/[0.02]">
              <div
                className="aspect-video bg-cover bg-center"
                style={{
                  backgroundImage: `url(https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20film%20still%20${i + 1}%2C%20anamorphic%2C%20dark%20mood%2C%20photorealistic&image_size=square)`,
                }}
              />
              <div className="p-2.5 text-[11px]">
                <div className="flex items-center justify-between text-slate-300">
                  <span>镜 {i + 1}</span>
                  <Badge tone="info">2.3s</Badge>
                </div>
                <div className="mt-1 text-slate-500 line-clamp-2">特写 · 中景 · 推镜 · 苏敏转头</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
