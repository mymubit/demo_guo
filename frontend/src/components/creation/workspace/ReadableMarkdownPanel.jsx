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
    <div className="rounded-2xl bg-navy-800/20 border border-navy-700/30 overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b border-navy-700/30 bg-navy-900/30">
        <FileText className="w-4 h-4 text-gold-400/80" />
        <span className="text-sm text-navy-200">{title}</span>
        <span className="text-[10px] text-navy-500 ml-auto">Markdown 原文</span>
      </div>
      <pre className="text-sm text-navy-100 whitespace-pre-wrap leading-relaxed font-sans px-5 py-4 max-h-[70vh] overflow-y-auto">
        {markdown}
      </pre>
    </div>
  )
}
