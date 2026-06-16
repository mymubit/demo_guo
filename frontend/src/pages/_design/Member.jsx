/**
 * Member.jsx — 设计稿会员中心
 *
 * 3 档定价：体验版 / 专业版（推荐）/ 旗舰版
 * 对应后端：membership/models.py (MembershipPlan)
 */
import { motion } from 'framer-motion'
import { Check, Sparkles } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const PLANS = [
  {
    key: 'free',
    badge: { tone: 'gold', text: '体验版' },
    name: 'Free',
    desc: '首次体验主链全流程',
    price: { num: '¥0', unit: '/ 永久' },
    features: ['1 次创作（最多 20 集大纲）', '3 种题材模板', '不支持下载 / 分享'],
    cta: { variant: 'secondary', text: '立即体验' },
  },
  {
    key: 'pro',
    featured: true,
    badge: { tone: 'gold', text: '推荐 · 专业版' },
    name: 'Pro',
    desc: '独立编剧 / 小团队首选',
    price: { num: '¥299', unit: '/ 月' },
    features: [
      '月 30 次创作 · 单次最多 120 集',
      '8 题材模板 · 4 输出格式',
      '质量审查 + 数字水印 + 分享链接',
    ],
    cta: { variant: 'gold', text: '立即购买' },
  },
  {
    key: 'enterprise',
    badge: { tone: 'info', text: '企业 · 旗舰版' },
    name: 'Enterprise',
    desc: 'MCN / 制作公司',
    price: { num: '¥2,880', unit: '/ 月' },
    features: ['无限创作 · 优先队列', '团队协作 + 私有模板 + 独立部署', 'API 接入 + 专属客服'],
    cta: { variant: 'primary', text: '联系商务' },
  },
]

export default function Member() {
  return (
    <motion.div {...pageEnter} className="mx-auto max-w-7xl px-6 py-16 md:py-24">
      <header className="mx-auto mb-12 max-w-2xl text-center">
        <span className="text-xs uppercase tracking-[0.18em] text-gold-400 before:mr-2 before:inline-block before:h-px before:w-6 before:align-middle before:bg-gold-400">
          会员中心
        </span>
        <h1 className="mt-3 text-3xl font-bold leading-tight tracking-tight md:text-4xl">
          选择适合你团队的版本
        </h1>
        <p className="mt-2 text-navy-200">
          体验版 / 专业版 / 旗舰版 — 与后端 <code className="rounded bg-white/5 px-1.5 py-0.5 text-xs">MembershipPlan</code> 同源。
        </p>
      </header>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
        {PLANS.map((p) => (
          <article
            key={p.key}
            className={cn(
              'flex flex-col rounded-3xl border border-white/5 bg-gradient-to-br from-navy-900/65 to-navy-950/65 p-8 transition-shadow',
              p.featured && 'border-gold-400/50 shadow-gold -translate-y-1.5',
            )}
          >
            <Badge tone={p.badge.tone} size="md" className="self-start">
              {p.badge.text}
            </Badge>
            <h3 className="mt-3.5 mb-1 text-2xl font-bold text-white">{p.name}</h3>
            <div className="text-[13px] text-navy-300">{p.desc}</div>

            <div className="mt-5.5 mb-1.5 flex items-baseline gap-1.5">
              <span className="text-[44px] font-bold leading-none text-white">{p.price.num}</span>
              <span className="text-navy-300">{p.price.unit}</span>
            </div>

            <ul className="mb-6 mt-4.5 flex list-none flex-col gap-2.5 p-0">
              {p.features.map((f) => (
                <li key={f} className="flex gap-2.5 text-sm text-navy-100 before:text-gold-400 before:content-['✓']">
                  {f}
                </li>
              ))}
            </ul>

            <div className="mt-auto">
              <Button variant={p.cta.variant} size="lg" className="w-full justify-center">
                {p.cta.text}
              </Button>
            </div>
          </article>
        ))}
      </div>
    </motion.div>
  )
}
