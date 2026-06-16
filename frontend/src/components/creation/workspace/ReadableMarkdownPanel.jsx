import { FileText } from 'lucide-react'

export default function ReadableMarkdownPanel({ markdown, title = '可读预览' }) {
  if (!markdown?.trim()) {
    return (
      <div className="py-12 text-center text-navy-400 text-sm">
        暂无可读预览，请先生成内容
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-white/5 bg-slate-900/40">
      <div className="flex items-center gap-2 border-b border-white/5 bg-slate-900/60 px-5 py-3">
        <FileText className="w-4 h-4 text-gold-400/80" />
        <span className="text-sm text-navy-200">{title}</span>
        <span className="text-[10px] text-navy-400 ml-auto">Markdown 原文</span>
      </div>
      <pre className="text-sm text-navy-100 whitespace-pre-wrap leading-relaxed font-sans px-5 py-4 max-h-[70vh] overflow-y-auto">
        {markdown}
      </pre>
    </div>
  )
}
