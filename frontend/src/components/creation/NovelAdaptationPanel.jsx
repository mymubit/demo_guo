import { useRef } from 'react'
import { motion } from 'framer-motion'
import { BookOpen, Upload, FileSearch } from 'lucide-react'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

/** 网文改编 — 独立首屏：上传/粘贴小说，而非与原创表单混在一起 */
export default function NovelAdaptationPanel({ novelText, onChange, onFileLoaded, minLength = 200 }) {
  const inputRef = useRef(null)
  const textLength = (novelText || '').trim().length
  const hasContent = textLength >= minLength

  function handleFile(file) {
    if (!file) return
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = String(e.target?.result || '')
      onChange(text.slice(0, 20000))
      onFileLoaded?.(file.name)
    }
    reader.readAsText(file, 'UTF-8')
  }

  if (!hasContent) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="rounded-3xl border border-dashed border-white/10 bg-white/[0.02] py-16 px-8 text-center"
      >
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-slate-800/60 flex items-center justify-center">
          <FileSearch className="w-10 h-10 text-navy-400" />
        </div>
        <h3 className="text-xl font-bold text-white mb-2">上传小说，开始改编</h3>
        <p className="text-sm text-navy-400 max-w-md mx-auto mb-8 leading-relaxed">
          支持 .txt / .md 文件，或直接粘贴章节正文，至少 {minLength} 字。导入后将由技能链拆解结构并生成分集剧本。
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.md,text/plain,text/markdown"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-white text-navy-950 font-semibold hover:bg-navy-100 transition-colors"
        >
          <Upload className="w-5 h-5" />
          上传文件
        </button>
        <p className="text-xs text-navy-400 mt-6">或在下方直接粘贴小说正文，当前 {textLength} / {minLength} 字</p>
        <textarea
          value={novelText}
          onChange={(e) => onChange(e.target.value.slice(0, 20000))}
          placeholder="粘贴小说章节或全文…"
          className="mt-4 w-full max-w-2xl mx-auto h-32 p-4 rounded-xl bg-slate-900/50 border border-white/10 text-white text-sm placeholder-navy-400 focus:border-gold-400/40 outline-none resize-none text-left"
        />
      </motion.div>
    )
  }

  return (
    <SectionShell icon={BookOpen} title="小说正文" subtitle="已导入内容，可继续编辑或重新上传">
      <div className="flex flex-wrap gap-2 mb-3">
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.md,text/plain,text/markdown"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-navy-200 border border-white/10 hover:border-gold-500/30"
        >
          <Upload className="w-4 h-4" />
          重新上传
        </button>
        <button
          type="button"
          onClick={() => onChange('')}
          className="px-3 py-1.5 rounded-lg text-sm text-red-300/80 hover:bg-red-500/10"
        >
          清空
        </button>
      </div>
      <textarea
        value={novelText}
        onChange={(e) => onChange(e.target.value.slice(0, 20000))}
        className="w-full h-64 p-5 rounded-2xl bg-slate-900/50 border border-white/10 text-white text-sm leading-relaxed focus:border-gold-400/50 outline-none resize-y"
      />
      <p className="text-xs text-navy-400 mt-2">{novelText.length} / 20000 字</p>
    </SectionShell>
  )
}

function SectionShell({ icon, title, subtitle, children }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-gold-400/10 flex items-center justify-center">
          {renderLucideIcon(icon, 'w-5 h-5 text-gold-400')}
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">{title}</h3>
          {subtitle && <p className="text-xs text-navy-400">{subtitle}</p>}
        </div>
      </div>
      {children}
    </div>
  )
}
