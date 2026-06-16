/**
 * Works.jsx — 设计稿作品库
 *
 * 对应后端：creation/services/works.py
 * 视觉重点：图片化卡片网格（真实剧照），克制 chips 过滤
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Badge } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const FILTERS = ['全部', '已完成', '生成中', '已分享']

// 作品 — 与后端 ScriptWork 模型字段对齐
const WORKS = [
  {
    id: 'P-10248',
    title: '《逆光》',
    theme: '都市逆袭',
    episodes: 80,
    size: '4.6 MB',
    state: 'completed',
    score: 86,
    cover:
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20city%20rooftop%20at%20dusk%2C%20a%20woman%20in%20a%20red%20coat%20looking%20at%20the%20skyline%2C%20dark%20mood%2C%20anamorphic%2C%20photorealistic&image_size=landscape_16_9',
  },
  {
    id: 'P-10241',
    title: '《权倾长乐》',
    theme: '古装权谋',
    episodes: 60,
    size: '3.8 MB',
    state: 'running',
    progress: 64,
    cover:
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=ancient%20chinese%20imperial%20palace%20corridor%2C%20lanterns%2C%20silk%20robes%2C%20fog%2C%20golden%20cinematic%20light%2C%20photorealistic&image_size=landscape_16_9',
  },
  {
    id: 'P-10236',
    title: '《错位》',
    theme: '悬疑反转',
    episodes: 50,
    size: '3.1 MB',
    state: 'completed',
    score: 91,
    cover:
      'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=rainy%20night%20in%20shanghai%2C%20a%20man%20and%20woman%20standing%20under%20a%20neon%20sign%2C%20film%20noir%2C%20photorealistic%2C%20anamorphic&image_size=landscape_16_9',
  },
]

function StatusBadge({ work }) {
  if (work.state === 'completed') {
    return (
      <div className="mt-2.5 flex items-center gap-2">
        <Badge tone="success">已完成</Badge>
        <Badge tone="gold">评分 {work.score}</Badge>
      </div>
    )
  }
  return <Badge tone="info" className="mt-2.5">生成中 {work.progress}%</Badge>
}

export default function Works() {
  const [filter, setFilter] = useState('全部')

  return (
    <motion.div {...pageEnter} className="mx-auto max-w-7xl px-6 py-16 md:py-24">
      <header className="mb-7 flex flex-wrap items-end justify-between gap-6">
        <div>
          <span className="text-xs uppercase tracking-[0.18em] text-gold-400 before:mr-2 before:inline-block before:h-px before:w-6 before:align-middle before:bg-gold-400">
            我的作品
          </span>
          <h1 className="mt-3 text-3xl font-bold leading-tight tracking-tight md:text-4xl">
            12 部剧本 · 5 部正在生成
          </h1>
          <p className="mt-2 max-w-[56ch] text-navy-200">
            所有作品自动加密存档，可随时回看、对比、续写。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={cn(
                'rounded-full border px-3 py-1.5 text-xs transition-colors',
                filter === f
                  ? 'border-gold-400/40 bg-gold-400/10 text-white'
                  : 'border-white/10 bg-white/[0.03] text-navy-200 hover:border-white/20 hover:text-white',
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
        {WORKS.map((w) => (
          <motion.article
            key={w.id}
            whileHover={{ y: -2 }}
            transition={{ duration: 0.18 }}
            className="group overflow-hidden rounded-2xl border border-white/5 bg-gradient-to-br from-navy-900/65 to-navy-950/65 transition-all hover:border-gold-400/35 hover:shadow-gold"
          >
            <div
              className="aspect-video w-full bg-cover bg-center"
              style={{ backgroundImage: `url(${w.cover})` }}
              role="img"
              aria-label={w.title}
            />
            <div className="p-4.5 pb-5">
              <h3 className="m-0 mb-1 text-base font-semibold text-white">{w.title}</h3>
              <div className="text-xs text-navy-300">
                {w.theme} · {w.episodes} 集 · {w.size}
              </div>
              <StatusBadge work={w} />
            </div>
          </motion.article>
        ))}
      </div>
    </motion.div>
  )
}
