/**
 * Home.jsx — 设计稿首页
 *
 * 基于 docs/DESIGN_PROTOTYPE.html 的 Hero 段实现：
 *   1. 全屏电影感 Hero（真实剧照 + 倾斜海报）
 *   2. 7 节点主链叙事
 *   3. 用户评价 + 数据条
 *
 * 对应后端领域：portal/auth · portal/creation · membership/plans
 */
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Sparkles, ChevronRight, Star, Quote } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const HERO_BG =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20wide%20shot%20of%20a%20film%20director%20sitting%20in%20a%20dark%20luxurious%20editing%20room%20with%20glowing%20scripts%20and%20amber%20spotlights%2C%20anamorphic%20lens%2C%20deep%20navy%20and%20gold%20tones%2C%20moody%20atmosphere%2C%20photorealistic%2C%208k&image_size=landscape_16_9'

const POSTER_BG =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20poster%20of%20a%20chinese%20short%20drama%20script%20manuscript%20on%20a%20dark%20mahogany%20desk%2C%20golden%20spotlight%2C%20shallow%20depth%20of%20field%2C%20film%20noir%20mood%2C%20gold%20and%20navy%20color%20grade%2C%20photorealistic%2C%208k&image_size=portrait_4_3'

// 7 节点主链 —— 对应后端 creation/engine/node[1-7]
const PIPELINE = [
  { step: 1, name: '信息收集', time: '30s', state: 'done' },
  { step: 2, name: '结构规划', time: '60s', state: 'done' },
  { step: 3, name: '人设开发', time: '60s', state: 'done' },
  { step: 4, name: '大纲撰写', time: '120s', state: 'active' },
  { step: 5, name: '剧本创作', time: '3-5m', state: 'idle' },
  { step: 6, name: '质量审查', time: '60s', state: 'idle' },
  { step: 7, name: '输出交付', time: '30s', state: 'idle' },
]

const TESTIMONIAL = {
  quote: '过去我们开发一部 80 集短剧需要 2–3 周。现在只需输入一句话，团队拿到的是结构、人设、节奏、镜头建议一条龙。',
  author: '陈导',
  role: '短剧制作公司',
}

const STATS = [
  { num: '50,000+', lbl: '创作者' },
  { num: '200万+', lbl: '生成集数' },
  { num: '98.6%', lbl: '满意度' },
]

export default function Home() {
  return (
    <motion.div {...pageEnter} className="relative">
      {/* ============ Hero — 全屏电影感 ============ */}
      <section className="relative h-[calc(100svh-3.25rem)] min-h-[640px] w-full overflow-hidden">
        {/* 背景实景照 */}
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${HERO_BG})`, filter: 'brightness(.55) saturate(1.05)' }}
          aria-hidden
        />
        {/* 双层渐变叠加 — 强化品牌色 */}
        <div
          className="absolute inset-0"
          style={{
            background:
              'radial-gradient(60% 50% at 70% 30%, rgba(253,160,133,.18), transparent 70%),' +
              'radial-gradient(40% 30% at 20% 80%, rgba(102,126,234,.12), transparent 70%),' +
              'linear-gradient(180deg, rgba(3,13,36,.3) 0%, rgba(3,13,36,.85) 75%, #030d24 100%)',
          }}
          aria-hidden
        />

        <div className="relative z-10 mx-auto flex h-full max-w-7xl items-center px-6">
          <div className="grid w-full grid-cols-1 items-center gap-12 lg:grid-cols-[1.1fr_0.9fr]">
            {/* 文案列 — 控制在 620px 内 */}
            <div className="max-w-[620px]">
              <div className="mb-5 flex flex-wrap gap-2">
                <Badge tone="gold" size="md">v1.6 · 主链 7 节点</Badge>
                <Badge tone="info" size="md">4 题材格式 · 8 题材模板</Badge>
              </div>
              <h1 className="font-display text-5xl font-bold leading-[1.05] tracking-tight md:text-6xl xl:text-7xl">
                一句话创意，
                <br />
                <span className="bg-gradient-to-r from-gold-400 to-gold-200 bg-clip-text text-transparent">
                  80 集可拍摄
                </span>
                的 A 级剧本。
              </h1>
              <p className="mt-5 max-w-[56ch] text-base text-navy-100 md:text-lg">
                ScriptForge 用 7 节点主链把创意拆成结构、人设、大纲、剧本、质量与交付。
                全流程 8–12 分钟，生成即带数字水印，剧作 / 团队 / 平台三方可溯源。
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Button variant="gold" size="lg" iconRight={<ChevronRight className={ICON.md} />}>
                  立即开始创作
                </Button>
                <Button variant="ghost" size="lg">观看 60 秒演示</Button>
              </div>
            </div>

            {/* 海报 — 1.5° 倾斜，唯一强视觉锚点 */}
            <div className="hidden lg:block">
              <motion.div
                initial={{ opacity: 0, y: 20, rotate: 1.5 }}
                animate={{ opacity: 1, y: 0, rotate: 1.5 }}
                transition={{ duration: 0.7, delay: 0.2 }}
                className="relative aspect-[4/5] overflow-hidden rounded-3xl border border-white/10 shadow-[0_30px_80px_-20px_rgba(0,0,0,.7)]"
              >
                <img src={POSTER_BG} alt="《逆光》海报" className="h-full w-full object-cover" />
                <span className="absolute right-4 top-4 rounded-full bg-gradient-to-r from-gold-300 to-gold-500 px-3 py-1 text-xs font-bold text-navy-950">
                  第 17 集 · 钩子
                </span>
                <div className="absolute bottom-4 left-4 rounded-xl border border-white/10 bg-navy-950/70 px-3 py-2 text-xs text-navy-100 backdrop-blur-md">
                  <b className="text-white">《逆光》</b> · 都市逆袭 · 80 集
                </div>
              </motion.div>
            </div>
          </div>
        </div>

        {/* 滚动提示 */}
        <div className="absolute bottom-7 left-1/2 z-10 -translate-x-1/2 flex flex-col items-center gap-1.5 text-[11px] tracking-[0.2em] text-navy-300">
          SCROLL
          <span className="block h-9 w-px bg-gradient-to-b from-navy-300 to-transparent" />
        </div>
      </section>

      {/* ============ 7 节点主链叙事 ============ */}
      <section className="py-24">
        <div className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-16 px-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <span className="text-xs uppercase tracking-[0.18em] text-gold-400 before:mr-2 before:inline-block before:h-px before:w-6 before:align-middle before:bg-gold-400">
              主链 7 节点
            </span>
            <h2 className="mt-3 text-3xl font-bold leading-tight tracking-tight md:text-4xl">
              从一句话到可拍摄剧本，
              <br />
              每一步都可被复盘。
            </h2>
            <p className="mt-4 max-w-[56ch] text-navy-200">
              创作不是黑箱。每完成一个节点，都能回看输入、决策、产出与评分。
              想要推到哪一步，由你说了算。
            </p>
          </div>

          <div className="rounded-2xl border border-white/5 bg-gradient-to-br from-navy-900/80 to-navy-950/80 p-7">
            <div className="relative grid grid-cols-7 gap-0">
              <span className="pointer-events-none absolute left-[6%] right-[6%] top-7 h-px bg-gradient-to-r from-transparent via-gold-400/40 to-transparent" />
              {PIPELINE.map((n) => (
                <div key={n.step} className="flex flex-col items-center gap-2">
                  <span
                    className={cn(
                      'grid h-14 w-14 place-items-center rounded-2xl border text-sm font-bold',
                      n.state === 'active' && 'border-transparent bg-gradient-to-r from-gold-300 to-gold-500 text-navy-950 shadow-gold',
                      n.state === 'done' && 'border-gold-400/40 bg-gold-400/15 text-gold-300',
                      n.state === 'idle' && 'border-white/10 bg-white/5 text-navy-200',
                    )}
                  >
                    {n.step}
                  </span>
                  <span className={cn('text-xs', n.state === 'active' ? 'text-white' : 'text-navy-200')}>{n.name}</span>
                  <span className="text-[10px] text-navy-400">{n.time}</span>
                </div>
              ))}
            </div>
            <div className="mt-6 h-1.5 overflow-hidden rounded-full bg-white/5">
              <span className="block h-full w-[42%] rounded-full bg-gradient-to-r from-gold-300 to-gold-500 shadow-gold" />
            </div>
            <div className="mt-3.5 flex items-center justify-between text-[13px] text-navy-200">
              <span>
                当前：<b className="text-white">第 4 节点 · 大纲撰写</b>
              </span>
              <span>已耗时 03:12 · 预计剩余 04:48</span>
            </div>
          </div>
        </div>
      </section>

      {/* ============ 评价 + 数据条 ============ */}
      <section className="py-16">
        <div className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-6 lg:grid-cols-[1.4fr_0.6fr]">
          <div>
            <span className="text-xs uppercase tracking-[0.18em] text-gold-400 before:mr-2 before:inline-block before:h-px before:w-6 before:align-middle before:bg-gold-400">
              来自团队的评价
            </span>
            <p className="mt-4 font-display text-2xl leading-snug text-white md:text-3xl">
              <Quote className="mb-2 inline h-6 w-6 text-gold-400" />
              {TESTIMONIAL.quote}
            </p>
            <div className="mt-5 flex items-center gap-3 text-sm text-navy-200">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-gold-300 to-gold-500 text-xs font-bold text-navy-950">
                {TESTIMONIAL.author[0]}
              </span>
              <b className="text-white">{TESTIMONIAL.author}</b> · {TESTIMONIAL.role}
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {STATS.map((s) => (
              <div key={s.lbl} className="rounded-2xl border border-white/5 bg-white/[0.03] p-4">
                <div className="text-2xl font-bold text-white">{s.num}</div>
                <div className="mt-1 text-xs text-navy-300">{s.lbl}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </motion.div>
  )
}
