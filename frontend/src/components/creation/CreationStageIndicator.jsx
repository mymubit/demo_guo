import { motion } from 'framer-motion'
import { Check } from 'lucide-react'
import { Card } from '@/components/ui'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'

export default function CreationStageIndicator({ stage }) {
  const stages = [
    { id: 1, label: '创意输入' },
    { id: 2, label: '项目确认' },
    { id: 3, label: 'Agent 工作台' },
  ]
  return (
    <Card className="mb-6" padding="md">
      <div className="flex items-center justify-between">
        {stages.map((s, idx) => {
          const active = stage === s.id
          const passed = stage > s.id
          return (
            <div key={s.id} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center">
                <motion.div
                  animate={{ scale: active ? 1.1 : 1 }}
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all',
                    passed && 'bg-gradient-to-br from-gold-400 to-gold-600 text-navy-950',
                    active && 'bg-gradient-to-br from-gold-400 to-gold-600 text-navy-950 node-active',
                    !active && !passed && 'bg-white/[0.05] text-navy-300 border border-white/10',
                  )}
                >
                  {passed ? <Check className={ICON.lg} /> : s.id}
                </motion.div>
                <div className={cn('text-xs mt-2', active ? 'text-gold-400 font-semibold' : passed ? 'text-white' : 'text-navy-400')}>
                  {s.label}
                </div>
              </div>
              {idx < stages.length - 1 && (
                <div className="flex-1 mx-2 h-0.5 relative overflow-hidden bg-white/10">
                  <motion.div
                    initial={{ width: '0%' }}
                    animate={{ width: passed ? '100%' : active ? '50%' : '0%' }}
                    transition={{ duration: 0.5 }}
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-gold-400 to-gold-600"
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
