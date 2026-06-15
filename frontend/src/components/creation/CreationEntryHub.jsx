import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import { getEntryMeta } from '@/utils/creationEntryMeta'
import SkillPipelineShowcase from './SkillPipelineShowcase'

export default function CreationEntryHub({ catalog, pipelineNodes, currencyName, onSelectEntry }) {
  const entries = catalog.creationEntries || []

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="space-y-8"
    >
      <SkillPipelineShowcase
        nodes={pipelineNodes}
        currencyName={currencyName}
        showTotalCost
      />

      <div>
        <h2 className="text-xl font-bold text-white mb-1">选择创作方式</h2>
        <p className="text-sm text-navy-400 mb-4">不同方式对应不同表单，确认后走同一套技能流水线</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {entries.map((entry, idx) => {
            const meta = getEntryMeta(entry.key, entry, catalog)
            const Icon = meta.icon
            return (
              <motion.button
                key={entry.key}
                type="button"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => onSelectEntry(entry.key)}
                className="group text-left glass-card rounded-2xl p-6 border border-navy-700/40 hover:border-gold-500/40 hover:bg-navy-800/30 transition-all"
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gold-400/20 to-purple-500/20 flex items-center justify-center border border-gold-500/20">
                      <Icon className="w-6 h-6 text-gold-400" />
                    </div>
                    <div>
                      <span className="text-[10px] uppercase tracking-wider text-purple-300 font-semibold">
                        {meta.tag}
                      </span>
                      <h3 className="text-lg font-bold text-white group-hover:text-gold-300 transition-colors">
                        {meta.name}
                      </h3>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-navy-500 group-hover:text-gold-400 group-hover:translate-x-0.5 transition-all shrink-0 mt-2" />
                </div>
                <p className="text-sm text-navy-300 leading-relaxed">{meta.description}</p>
              </motion.button>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}
