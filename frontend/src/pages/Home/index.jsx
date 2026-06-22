import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Sparkles,
  Zap,
  Shield,
  Palette,
  ChevronRight,
  Star,
  Users,
  FileText,
  Eye,
  Quote,
} from 'lucide-react'

import { THEME_META_LIST } from '@/constants/themeMeta'
import ThemeBadge from '@/components/ui/ThemeBadge'
import { Badge, Button } from '@/components/ui'
import { SectionEyebrow, PageContainer } from '@/components/shared/ConsumerSection'
import { useConfig } from '@/services/api'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { renderLucideIcon } from '@/utils/renderLucideIcon'

const HERO_BG =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20wide%20shot%20of%20a%20film%20director%20sitting%20in%20a%20dark%20luxurious%20editing%20room%20with%20glowing%20scripts%20and%20amber%20spotlights%2C%20anamorphic%20lens%2C%20deep%20navy%20and%20gold%20tones%2C%20moody%20atmosphere%2C%20photorealistic%2C%208k&image_size=landscape_16_9'

const POSTER_BG =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20poster%20of%20a%20chinese%20short%20drama%20script%20manuscript%20on%20a%20dark%20mahogany%20desk%2C%20golden%20spotlight%2C%20shallow%20depth%20of%20field%2C%20film%20noir%20mood%2C%20gold%20and%20navy%20color%20grade%2C%20photorealistic%2C%208k&image_size=portrait_4_3'

// 用户评价
const TESTIMONIALS = [
  {
    name: '陈**',
    role: '短剧制作公司 / 导演',
    avatar: '陈',
    content: '过去我们团队开发一部短剧剧本需要2-3周，现在只需要输入创意，几个小时就能拿到完整的80集剧本，效率提升了10倍以上！而且质量非常专业，人物设定和结构都很扎实。',
    rating: 5,
  },
  {
    name: '林**',
    role: '独立编剧',
    avatar: '林',
    content: '作为独立创作者，最困难的就是创意到大纲的转化。ScriptForge帮我解决了这个痛点，它的Drama Skills 36角色体系非常科学，从创意收集到剧本导出一气呵成。',
    rating: 5,
  },
  {
    name: '王**',
    role: '影视学院 / 导师',
    avatar: '王',
    content: '我用这个平台给学生做剧本教学演示，学生们反馈非常好。它不仅是一个工具，更像一位专业的剧本导师，能够引导学生建立结构化思维。',
    rating: 5,
  },
  {
    name: '张**',
    role: '短视频创作者',
    avatar: '张',
    content: '作为非专业背景的创作者，我一直担心剧本不够专业。用了ScriptForge后，我的作品质量肉眼可见地提升，最近一部剧已经被平台签约了！',
    rating: 5,
  },
]

// 数据展示（后端 home.hero_stats 为空时回退本地默认）
const DEFAULT_HERO_STATS = [
  { value: '50,000+', label: '创作者使用' },
  { value: '200万+', label: '剧本集数生成' },
  { value: '98.6%', label: '用户满意度' },
  { value: '8大', label: '热门题材覆盖' },
]

function normalizeHeroStats(raw, fallback) {
  if (!Array.isArray(raw) || raw.length === 0) return fallback
  const items = raw
    .map((item) => ({
      value: String(item?.value ?? '').trim(),
      label: String(item?.label ?? '').trim(),
    }))
    .filter((item) => item.value && item.label)
  return items.length > 0 ? items : fallback
}

// 功能卡片
const FEATURES = [
  {
    icon: Sparkles,
    title: '智能创作',
    description: '基于先进AI模型，将一句话创意自动扩展为80集完整剧本，包含人物设定、分集大纲、场景对话',
    color: '#667eea',
  },
  {
    icon: Palette,
    title: '多题材模板',
    description: '家庭复仇、豪门霸总、甜宠虐恋、穿越重生等8大热门题材，每种题材都有专业优化的结构模板',
    color: '#f6ad55',
  },
  {
    icon: FileText,
    title: '格式标准',
    description: '支持4种行业标准剧本格式，从精简版到分镜版，满足不同制作团队需求，可直接用于拍摄',
    color: '#68d391',
  },
  {
    icon: Shield,
    title: '质量审查',
    description: '四维评分系统，从格式、节奏、内容、制作可行性进行自动化评估，帮你快速定位问题并改进',
    color: '#fc8181',
  },
  {
    icon: Zap,
    title: '极速生成',
    description: '异步任务队列 + 智能调度，完整剧本生成仅需数分钟，行业标准速度10倍提升',
    color: '#fbd38d',
  },
  {
    icon: Eye,
    title: '作品管理',
    description: '作品自动云端保存，随时查看编辑，支持分享链接和多格式导出，团队协作功能完善',
    color: '#9f7aea',
  },
]

// Drama Skills 36角色创作体系
const PIPELINE = [
  { step: 1, name: '信息收集', time: '30s', state: 'done' },
  { step: 2, name: '结构规划', time: '60s', state: 'done' },
  { step: 3, name: '人设开发', time: '60s', state: 'done' },
  { step: 4, name: '大纲撰写', time: '120s', state: 'active' },
  { step: 5, name: '剧本创作', time: '3-5m', state: 'idle' },
  { step: 6, name: '质量审查', time: '60s', state: 'idle' },
  { step: 7, name: '输出交付', time: '30s', state: 'idle' },
]

// FAQ
const FAQS = [
  {
    q: '使用ScriptForge需要什么技术背景吗？',
    a: '完全不需要。任何有创作想法的人都可以使用，从一句话创意开始，平台会引导你完成整个创作流程。内置的模板和专业流程让你获得媲美专业编剧的成果。',
  },
  {
    q: '生成的剧本可以直接用于拍摄吗？',
    a: '可以。平台输出4种行业标准格式，其中行业通用版（Variant-B）是为制作团队优化的精简版，包含场景、动作、对话等核心要素，可以直接用于拍摄或进一步精修。',
  },
  {
    q: '剧本的版权归属如何？',
    a: '用户输入的创意和平台输出的剧本，版权归用户所有。我们保留对生成内容的案例展示权（可在后台关闭）。建议对重要项目添加版权登记。',
  },
  {
    q: '创作数据安全吗？会不会泄露创意？',
    a: '我们采用端到端加密架构，原始剧本数据在后端加密存储，前端仅渲染展示不返回数据结构。下载文件内置可追溯的数字水印。后台技能配置和模板隔离存储，仅管理员可访问。',
  },
  {
    q: '会员套餐有什么区别？',
    a: '采用创作币计费：注册赠送体验币，字段 AI 与主链节点分别扣费；开通会员赠送更多创作币，并解锁灵感策划、拉片等权益。余额不足可在「创作币」页充值。',
  },
  {
    q: '可以定制题材模板吗？',
    a: '旗舰版用户可以申请定制题材模板，我们的内容团队会根据你的需求进行优化。企业版客户还可以使用私有模板库。',
  },
]

export default function Home() {
  const configHeroStats = useConfig('home.hero_stats', DEFAULT_HERO_STATS)
  const stats = normalizeHeroStats(configHeroStats, DEFAULT_HERO_STATS)

  return (
    <div className="relative bg-gray-50">
      {/* ========= Hero ========= */}
      <section className="relative w-full overflow-hidden border-b border-gray-200 bg-gradient-to-br from-brand-50 via-white to-gray-50">
        <PageContainer width="7xl" className="relative z-10 py-16 md:py-24">
          <div className="grid w-full grid-cols-1 items-center gap-12 lg:grid-cols-[1.1fr_0.9fr]">
            <motion.div {...pageEnter} className="max-w-[620px]">
              <div className="mb-5 flex flex-wrap gap-2">
                <Badge tone="gold" size="md">Drama Skills</Badge>
                <Badge tone="info" size="md">4 题材格式 · 8 题材模板</Badge>
              </div>
              <h1 className="font-display text-4xl font-bold leading-[1.08] tracking-tight text-gray-900 md:text-5xl xl:text-6xl">
                一句话创意，
                <br />
                <span className="bg-gradient-to-r from-brand-600 to-brand-500 bg-clip-text text-transparent">
                  80 集可拍摄
                </span>
                的 A 级剧本。
              </h1>
              <p className="mt-5 max-w-[56ch] text-base text-gray-600 md:text-lg">
                ScriptForge 用 Drama Skills 工作室把创意拆成结构、人设、大纲、剧本、质量与交付。
                全流程 8–12 分钟，生成即带数字水印，剧作 / 团队 / 平台三方可溯源。
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link to="/creation">
                  <Button variant="brand" size="lg" iconRight={<ChevronRight className={ICON.md} />}>
                    立即开始创作
                  </Button>
                </Link>
                <Link to="/member">
                  <Button variant="ghost" size="lg">查看会员方案</Button>
                </Link>
              </div>
              <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {stats.map((stat) => (
                  <div key={stat.label} className="sf-surface-card p-3">
                    <div className="text-xl font-bold text-gray-900 md:text-2xl">{stat.value}</div>
                    <div className="mt-1 text-xs text-gray-500">{stat.label}</div>
                  </div>
                ))}
              </div>
            </motion.div>

            <div className="hidden lg:block">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.2 }}
                className="relative aspect-[4/5] overflow-hidden rounded-2xl border border-gray-200 shadow-lg"
              >
                <img src={POSTER_BG} alt="剧本海报示意" className="h-full w-full object-cover" />
                <span className="absolute right-4 top-4 rounded-full bg-gradient-to-r from-accent-300 to-accent-500 px-3 py-1 text-xs font-bold text-gray-900">
                  第 17 集 · 钩子
                </span>
                <div className="absolute bottom-4 left-4 rounded-xl border border-gray-200 bg-white/90 px-3 py-2 text-xs text-gray-700 backdrop-blur-md">
                  <b className="text-gray-900">《逆光》</b> · 都市逆袭 · 80 集
                </div>
              </motion.div>
            </div>
          </div>
        </PageContainer>
      </section>

      {/* ========= 功能展示 ========= */}
      <section id="features" className="py-24 relative">
        <PageContainer width="7xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="section-title">为什么选择 <span className="gradient-text">ScriptForge</span></h2>
            <p className="section-subtitle">
              专业级创作工具，让每一个创意都能释放最大潜力
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature, idx) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className="sf-feature-card group"
              >
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform"
                  style={{
                    background: `${feature.color}15`,
                    boxShadow: `0 4px 12px -4px ${feature.color}40`,
                  }}
                >
                  {renderLucideIcon(feature.icon, 'w-7 h-7', { style: { color: feature.color } })}
                </div>
                <h3 className="text-xl font-bold mb-3 text-gray-900">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </PageContainer>
      </section>

      {/* ========= 题材选择 ========= */}
      <section className="relative py-24">
        <PageContainer width="7xl" className="relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="section-title">8大热门题材，总有一款适合你</h2>
            <p className="section-subtitle">
              每种题材都经过专业优化的结构模板、反转密度和情绪曲线，从创意到剧本的转化率显著提升
            </p>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {THEME_META_LIST.map((theme, idx) => (
              <motion.div
                key={theme.key}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.05 }}
                className="sf-surface-card cursor-pointer p-6 text-center group hover:border-brand-200 hover:shadow-md transition-all"
              >
                <ThemeBadge theme={theme} size="xl" />
                <div className="text-xs text-gray-400 mt-2">专业优化模板</div>
              </motion.div>
            ))}
          </div>
        </PageContainer>
      </section>

      {/* ========= Drama Skills 工作室叙事 ========= */}
      <section className="py-24">
        <PageContainer width="7xl" className="grid grid-cols-1 items-center gap-16 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <SectionEyebrow>Drama Skills</SectionEyebrow>
            <h2 className="mt-3 text-3xl font-bold leading-tight tracking-tight text-gray-900 md:text-4xl">
              从一句话到可拍摄剧本，
              <br />
              每一步都可被复盘。
            </h2>
            <p className="mt-4 max-w-[56ch] text-gray-600">
              创作不是黑箱。每完成一个节点，都能回看输入、决策、产出与评分。
              想要推到哪一步，由你说了算。
            </p>
          </div>

          <div className="sf-surface-card p-7">
            <div className="relative grid grid-cols-7 gap-0">
              <span className="pointer-events-none absolute left-[6%] right-[6%] top-7 h-px bg-gradient-to-r from-transparent via-brand-300 to-transparent" />
              {PIPELINE.map((n) => (
                <div key={n.step} className="flex flex-col items-center gap-2">
                  <span
                    className={cn(
                      'grid h-14 w-14 place-items-center rounded-2xl border text-sm font-bold',
                      n.state === 'active' && 'border-transparent bg-brand-600 text-white shadow-md',
                      n.state === 'done' && 'border-brand-200 bg-brand-50 text-brand-700',
                      n.state === 'idle' && 'border-gray-200 bg-gray-50 text-gray-400',
                    )}
                  >
                    {n.step}
                  </span>
                  <span className={cn('text-xs', n.state === 'active' ? 'text-gray-900 font-medium' : 'text-gray-500')}>{n.name}</span>
                  <span className="text-[10px] text-gray-400">{n.time}</span>
                </div>
              ))}
            </div>
            <div className="mt-6 h-1.5 overflow-hidden rounded-full bg-gray-100">
              <span className="block h-full w-[42%] rounded-full bg-brand-600" />
            </div>
            <div className="mt-3.5 flex flex-wrap items-center justify-between gap-2 text-[13px] text-gray-500">
              <span>
                当前：<b className="text-gray-900">第 4 节点 · 大纲撰写</b>
              </span>
              <span>已耗时 03:12 · 预计剩余 04:48</span>
            </div>
          </div>
        </PageContainer>
      </section>

      {/* ========= 用户评价 ========= */}
      <section className="relative overflow-hidden py-24">
        <PageContainer width="7xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="section-title">
              来自 <span className="gradient-text">50,000+</span> 创作者的信赖
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-16">
            {TESTIMONIALS.map((t, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className="sf-surface-card p-8"
              >
                <div className="flex items-center gap-1 mb-4">
                  {Array.from({ length: t.rating }).map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-accent-500 fill-accent-500" />
                  ))}
                </div>
                <p className="text-gray-700 leading-relaxed mb-6 text-lg">{t.content}</p>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-accent-300 to-accent-500 flex items-center justify-center text-gray-900 font-bold">
                    {t.avatar}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">{t.name}</div>
                    <div className="text-sm text-gray-500">{t.role}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </PageContainer>
      </section>

      {/* ========= FAQ ========= */}
      <section className="py-24 relative">
        <PageContainer width="4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="section-title">常见问题</h2>
            <p className="section-subtitle">如果没有找到答案，欢迎联系我们的客服团队</p>
          </motion.div>

          <div className="space-y-4">
            {FAQS.map((faq, idx) => (
              <FAQItem key={idx} {...faq} />
            ))}
          </div>
        </PageContainer>
      </section>

      {/* ========= CTA ========= */}
      <section className="py-24 relative">
        <PageContainer width="4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="relative overflow-hidden rounded-3xl border border-brand-200 bg-brand-50 p-12 text-center md:p-16"
          >
            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold mb-6 text-gray-900">
                准备好让你的创意 <span className="text-brand-600">腾飞</span> 了吗？
              </h2>
              <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
                加入 50,000+ 创作者的行列，体验 AI 赋能的专业剧本创作
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/register" className="btn-gold text-lg inline-flex items-center justify-center gap-2">
                  <Users className="w-5 h-5" />
                  免费注册
                </Link>
                <Link to="/creation" className="btn-primary text-lg inline-flex items-center justify-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  开始创作
                </Link>
              </div>
            </div>
          </motion.div>
        </PageContainer>
      </section>
    </div>
  )
}

// FAQ 单项组件
function FAQItem({ q, a }) {
  const [open, setOpen] = useStateOpen(false)
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="overflow-hidden rounded-xl border border-gray-200 bg-white"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-6 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
      >
        <span className="font-semibold text-gray-900 pr-4">{q}</span>
        <motion.div
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.3 }}
          className="w-8 h-8 rounded-full bg-brand-50 flex items-center justify-center flex-shrink-0"
        >
          <ChevronRight className="w-4 h-4 text-brand-600" />
        </motion.div>
      </button>
      <motion.div
        initial={{ height: 0 }}
        animate={{ height: open ? 'auto' : 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      >
        <div className="px-6 pb-6 text-gray-600 leading-relaxed">{a}</div>
      </motion.div>
    </motion.div>
  )
}

import { useState as useStateOpen } from 'react'
