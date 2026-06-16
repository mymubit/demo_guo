import { motion } from 'framer-motion'
import { Check, FileText, Zap, Star, BookOpen, Clapperboard } from 'lucide-react'

const FORMAT_META = {
  A: { badge: '阅读友好', icon: BookOpen, accent: 'text-sky-300 bg-sky-500/15 border-sky-500/30' },
  B: { badge: '拍摄推荐', icon: Clapperboard, accent: 'text-gold-300 bg-gold-500/15 border-gold-500/30' },
  C: { badge: '极速试稿', icon: Zap, accent: 'text-green-300 bg-green-500/15 border-green-500/30' },
  D: { badge: '精品分镜', icon: Star, accent: 'text-purple-300 bg-purple-500/15 border-purple-500/30' },
}

function previewLine(label, value) {
  if (!value) return null
  const text = String(value).replace(/\*\*/g, '')
  return (
    <div className="flex gap-2 text-[11px] leading-relaxed">
      <span className="text-navy-400 shrink-0 w-8">{label}</span>
      <code className="text-navy-200 font-mono break-all">{text}</code>
    </div>
  )
}

export default function FormatVariantPicker({ variants = [], value, onChange }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      {variants.map((f) => {
        const active = value === f.key
        const meta = FORMAT_META[f.key] || FORMAT_META.B
        const Icon = meta.icon
        return (
          <motion.button
            key={f.key}
            type="button"
            whileHover={{ scale: 1.005 }}
            whileTap={{ scale: 0.995 }}
            onClick={() => onChange(f.key)}
            className={`p-5 rounded-2xl text-left transition-all border ${
              active
                ? 'border-gold-400/50 bg-gold-400/10 ring-1 ring-gold-400/40 shadow-gold'
                : 'border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]'
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-start gap-3 min-w-0">
                <div
                  className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
                    active ? 'bg-gold-400/20' : 'border border-white/10 bg-white/5'
                  }`}
                >
                  <Icon className={`w-5 h-5 ${active ? 'text-gold-400' : 'text-navy-300'}`} />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`font-semibold ${active ? 'text-white' : 'text-navy-100'}`}>
                      {f.name}
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${meta.accent}`}>
                      {meta.badge}
                    </span>
                  </div>
                  {(f.description || f.desc) && (
                    <p className="text-xs text-navy-400 mt-1 leading-relaxed">{f.description || f.desc}</p>
                  )}
                </div>
              </div>
              {active && (
                <div className="w-5 h-5 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center shrink-0">
                  <Check className="w-3 h-3 text-navy-950" />
                </div>
              )}
            </div>

            <div className="rounded-xl border border-white/5 bg-slate-900/40 p-3 space-y-1.5">
              <div className="text-[10px] text-navy-400 uppercase tracking-wider mb-1">格式样例</div>
              {previewLine('场景', f.sceneHeading)}
              {previewLine('台词', f.dialogueMarker)}
              {previewLine('动作', f.actionMarker)}
              {!f.sceneHeading && !f.dialogueMarker && !f.actionMarker && (
                <div className="flex items-center gap-2 text-[11px] text-navy-400">
                  <FileText className="w-3.5 h-3.5" />
                  变体 {f.key}
                </div>
              )}
            </div>
          </motion.button>
        )
      })}
    </div>
  )
}
