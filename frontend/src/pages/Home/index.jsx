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
} from 'lucide-react'

import { THEME_META_LIST } from '@/constants/themeMeta'
import ThemeBadge from '@/components/ui/ThemeBadge'
import { useConfig } from '@/services/api'

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
    content: '作为独立创作者，最困难的就是创意到大纲的转化。ScriptForge帮我解决了这个痛点，它的7节点流水线非常科学，从创意收集到剧本导出一气呵成。',
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

// 5 节点创作主链
const PIPELINE = [
  { step: 1, name: '立项整理' },
  { step: 2, name: '结构规划' },
  { step: 3, name: '人设开发' },
  { step: 4, name: '大纲撰写' },
  { step: 5, name: '剧本创作' },
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
    <div className="relative">
      {/* ========= Hero 区 ========= */}
      <section className="relative overflow-hidden pt-20 pb-32">
        <div className="particles-bg" />

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center max-w-4xl mx-auto"
          >
            <h1 className="text-5xl md:text-7xl font-bold mb-16 leading-tight">
              从一句话创意
              <br />
              到 <span className="gradient-text">80集专业剧本</span>
            </h1>

            {/* 数据展示 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8 max-w-3xl mx-auto">
              {stats.map((stat, idx) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + idx * 0.1 }}
                  className="p-4 rounded-2xl glass-card"
                >
                  <div className="text-2xl md:text-3xl font-bold gradient-text mb-1">{stat.value}</div>
                  <div className="text-sm text-navy-300">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* 装饰图形 */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-navy-950 to-transparent pointer-events-none" />
      </section>

      {/* ========= 功能展示 ========= */}
      <section id="features" className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
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
                whileHover={{ y: -5 }}
                className="p-8 rounded-3xl glass-card hover:shadow-card-hover transition-all group"
              >
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform"
                  style={{
                    background: `${feature.color}20`,
                    boxShadow: `0 8px 24px -8px ${feature.color}60`,
                  }}
                >
                  <feature.icon className="w-7 h-7" style={{ color: feature.color }} />
                </div>
                <h3 className="text-xl font-bold mb-3 text-white">{feature.title}</h3>
                <p className="text-navy-200 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ========= 题材选择 ========= */}
      <section className="py-24 relative">
        <div className="absolute inset-0 opacity-30 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-purple-600 blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-gold-500 blur-3xl" />
        </div>

        <div className="max-w-7xl mx-auto px-6 relative z-10">
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
                whileHover={{ y: -3, scale: 1.02 }}
                className="p-6 rounded-2xl glass-card cursor-pointer text-center group"
              >
                <ThemeBadge theme={theme} size="xl" />
                <div className="text-xs text-navy-300 mt-2">专业优化模板</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ========= 5 节点流水线 ========= */}
      <section className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="section-title">
              <span className="gradient-text">5 节点</span> 专业创作流水线
            </h2>
            <p className="section-subtitle">
              从创意收集到剧本交付，每一步都经过专业设计和质量把控
            </p>
          </motion.div>

          <div className="relative">
            {/* 连接线 */}
            <div className="hidden lg:block absolute top-[3.25rem] left-10 right-10 h-px bg-navy-600/40" />

            <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-7 gap-4">
              {PIPELINE.map((node, idx) => (
                <motion.div
                  key={node.step}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.08 }}
                  className="relative"
                >
                  <div className="glass-card rounded-2xl p-6 text-center h-full">
                    <div className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center text-xl font-bold text-gold-400 bg-navy-800/60 border border-gold-400/20">
                      {node.step}
                    </div>
                    <div className="font-bold text-white">{node.name}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ========= 用户评价 ========= */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute top-1/2 left-0 w-[600px] h-[600px] rounded-full bg-navy-700/30 blur-3xl -translate-y-1/2 -translate-x-1/2" />

        <div className="max-w-7xl mx-auto px-6 relative z-10">
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
                className="p-8 rounded-3xl glass-card"
              >
                <div className="flex items-center gap-1 mb-4">
                  {Array.from({ length: t.rating }).map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-gold-400 fill-gold-400" />
                  ))}
                </div>
                <p className="text-navy-100 leading-relaxed mb-6 text-lg">{t.content}</p>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-950 font-bold">
                    {t.avatar}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{t.name}</div>
                    <div className="text-sm text-navy-300">{t.role}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ========= FAQ ========= */}
      <section className="py-24 relative">
        <div className="max-w-4xl mx-auto px-6">
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
        </div>
      </section>

      {/* ========= CTA ========= */}
      <section className="py-24 relative">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center p-12 md:p-16 rounded-[40px] glass-card-gold relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-64 h-64 rounded-full bg-gold-500/20 blur-3xl" />
            <div className="absolute bottom-0 right-0 w-64 h-64 rounded-full bg-purple-500/20 blur-3xl" />

            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                准备好让你的创意 <span className="gradient-text">腾飞</span> 了吗？
              </h2>
              <p className="text-xl text-navy-200 mb-10 max-w-2xl mx-auto">
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
        </div>
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
      className="rounded-2xl glass-card overflow-hidden"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-6 flex items-center justify-between text-left"
      >
        <span className="font-semibold text-white pr-4">{q}</span>
        <motion.div
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.3 }}
          className="w-8 h-8 rounded-full bg-gold-400/20 flex items-center justify-center flex-shrink-0"
        >
          <ChevronRight className="w-4 h-4 text-gold-400" />
        </motion.div>
      </button>
      <motion.div
        initial={{ height: 0 }}
        animate={{ height: open ? 'auto' : 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      >
        <div className="px-6 pb-6 text-navy-200 leading-relaxed">{a}</div>
      </motion.div>
    </motion.div>
  )
}

import { useState as useStateOpen } from 'react'
