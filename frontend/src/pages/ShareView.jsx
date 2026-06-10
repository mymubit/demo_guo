import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Film,
  User,
  Calendar,
  Star,
  FileText,
  Sparkles,
  Lock,
  ArrowRight,
  Users,
  Eye,
  Heart,
} from 'lucide-react'

export default function ShareView() {
  const { token } = useParams()
  const [loading, setLoading] = useState(true)
  const [work, setWork] = useState(null)

  useEffect(() => {
    const timer = setTimeout(() => {
      setWork({
        title: '豪门总裁的逆袭归来',
        author: '剧本创作达人',
        authorAvatar: 'S',
        createdAt: '2026-06-08',
        views: 1284,
        likes: 237,
        rating: 4.8,
        genre: '豪门霸总',
        episodeCount: 80,
        description:
          '三年前，他被诬陷逐出家族，流落街头。三年后，他带着千亿资产和滔天权势强势归来。那些曾经背叛他的人，都将付出沉重的代价。而她，在他最落魄时不离不弃，终将成为他此生唯一的挚爱。',
        characters: [
          { name: '顾霆深', role: '男主', desc: '30岁，顾氏集团继承人，三年前被陷害流放，如今强势回归。外表冷酷，内心深情。' },
          { name: '苏慕雪', role: '女主', desc: '26岁，苏家千金，善良坚韧。三年前不顾家族反对帮助顾霆深，两人感情深厚。' },
          { name: '顾天明', role: '反派', desc: '顾霆深的堂兄，野心家。当年策划阴谋陷害顾霆深，企图霸占顾氏集团。' },
          { name: '林婉儿', role: '女配角', desc: '苏慕雪的闺蜜，聪明机敏。在关键时刻多次帮助男女主角化解危机。' },
        ],
        episodes: [
          { title: '第01集 强势归来', content: '国际机场，私人飞机缓缓降落。顾霆深走出机舱，深邃的眼眸中闪过一丝寒光。三年了，他终于回来了。\n\n"顾总，一切都安排妥当了。"助理恭敬地递上一份文件。\n\n顾霆深接过文件，目光落在"顾氏集团"四个字上，嘴角勾起一抹冷笑。\n\n"顾天明，你欠我的，我会一点一点，连本带利地讨回来。"' },
          { title: '第02集 初次相遇', content: '高端酒店宴会厅，一场商业聚会正在举行。苏慕雪端着香槟，优雅地穿梭在人群中。\n\n忽然，她的目光被门口一道挺拔的身影吸引。那个男人……好像在哪里见过。\n\n顾霆深也注意到了她，四目相对的瞬间，两人都愣住了。\n\n"是你？"苏慕雪的声音微微颤抖。\n\n顾霆深缓步走来，低沉的声音在她耳边响起："慕雪，好久不见。"' },
          { title: '第03集 暗流涌动', content: '顾氏集团总部，董事会议室内气氛紧张。顾天明高坐在主位上，一副志得意满的样子。\n\n"各位董事，下季度的战略规划已经拟定完毕，大家过目一下。"顾天明得意地分发文件。\n\n就在这时，会议室的大门被推开。顾霆深身着剪裁合体的黑色西装，缓缓走入。\n\n"不好意思，我回来晚了。不过从今天起，顾氏集团，我说了算。"' },
          { title: '第04集 旧情复燃', content: '深夜，城市最高楼的天台。顾霆深独自站在栏杆边，望着脚下璀璨的城市灯火。\n\n"在想什么？"苏慕雪的声音从身后传来。\n\n顾霆深转身，眼中是她从未见过的温柔："在想，如果三年前我没有离开，我们现在会是什么样子。"\n\n苏慕雪走到他身边，轻声说："现在也不晚。"\n\n顾霆深紧紧握住她的手，"是啊，不晚。这一次，我不会再放开你。"' },
          { title: '第05集 阴谋初现', content: '阴暗的地下停车场，两拨人正在秘密交易。\n\n"顾总那边最近动作很大，我们该怎么办？"手下低声问。\n\n顾天明阴冷地笑了笑："慌什么？他以为自己赢定了？游戏才刚刚开始。"\n\n他从口袋里掏出一枚U盘："这里面的东西，足够让他身败名裂。苏慕雪那个女人，也是时候发挥作用了。"' },
        ],
      })
      setLoading(false)
    }, 800)

    return () => clearTimeout(timer)
  }, [token])

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-950 flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 border-4 border-gold-400/30 border-t-gold-400 rounded-full mx-auto mb-4"
          />
          <div className="text-navy-300">加载中...</div>
        </div>
      </div>
    )
  }

  if (!work) {
    return (
      <div className="min-h-screen bg-navy-950 flex items-center justify-center">
        <div className="text-center">
          <Lock className="w-16 h-16 text-navy-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">链接已失效</h2>
          <p className="text-navy-300 mb-6">该分享链接不存在或已过期</p>
          <Link to="/" className="btn-gold inline-flex items-center gap-2">
            返回首页
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-navy-950 via-navy-900 to-navy-950 relative">
      {/* 水印背景 */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-10">
        <div className="absolute -rotate-30 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/[0.03] text-6xl font-bold whitespace-nowrap select-none">
          仅供预览 · 版权归属原创作者 · ScriptForge
        </div>
        <div className="absolute rotate-12 top-1/4 left-1/4 text-white/[0.02] text-4xl font-bold whitespace-nowrap select-none">
          © 原创作品 · 请勿转载
        </div>
        <div className="absolute -rotate-12 bottom-1/4 right-1/4 text-white/[0.02] text-4xl font-bold whitespace-nowrap select-none">
          ScriptForge AI 创作
        </div>
      </div>

      {/* 顶部导航 */}
      <header className="relative z-20 border-b border-navy-700/40 bg-navy-950/90 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <motion.div
              whileHover={{ rotate: 10, scale: 1.1 }}
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              }}
            >
              <Film className="w-5 h-5 text-white" />
            </motion.div>
            <span className="text-xl font-bold gradient-text">ScriptForge</span>
          </Link>

          <div className="flex items-center gap-3 text-sm text-navy-300">
            <Eye className="w-4 h-4" />
            <span>{work.views.toLocaleString()} 次预览</span>
          </div>
        </div>
      </header>

      {/* 水印提示条 */}
      <div className="relative z-20 bg-gold-500/10 border-b border-gold-500/20 text-center py-2">
        <span className="text-sm text-gold-400">
          🔒 本作品仅供预览，版权归属原创作者，未经许可不得转载或商用
        </span>
      </div>

      {/* 主要内容 */}
      <main className="relative z-20 max-w-4xl mx-auto px-6 py-12">
        {/* 作品头部 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gold-500/20 border border-gold-500/30 text-gold-400 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            {work.genre} · {work.episodeCount}集
          </div>

          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6 leading-tight">
            {work.title}
          </h1>

          {/* 作者信息 */}
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-950 font-bold">
              {work.authorAvatar}
            </div>
            <div className="text-left">
              <div className="text-white font-medium">{work.author}</div>
              <div className="text-xs text-navy-400 flex items-center gap-2">
                <Calendar className="w-3 h-3" />
                {work.createdAt}
              </div>
            </div>
          </div>

          {/* 评分和统计 */}
          <div className="flex items-center justify-center gap-6 mt-6">
            <div className="flex items-center gap-2 text-gold-400">
              <Star className="w-5 h-5 fill-gold-400" />
              <span className="font-bold">{work.rating.toFixed(1)}</span>
              <span className="text-sm text-navy-400">评分</span>
            </div>
            <div className="w-px h-4 bg-navy-700" />
            <div className="flex items-center gap-2 text-navy-300">
              <Eye className="w-4 h-4" />
              <span>{work.views.toLocaleString()}</span>
            </div>
            <div className="w-px h-4 bg-navy-700" />
            <div className="flex items-center gap-2 text-navy-300">
              <Heart className="w-4 h-4" />
              <span>{work.likes.toLocaleString()}</span>
            </div>
          </div>
        </motion.div>

        {/* 内容卡片 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-3xl p-8 md:p-10 mb-8 relative"
        >
          {/* 重复水印 */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-3xl">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="absolute text-white/[0.02] text-sm font-bold whitespace-nowrap select-none"
                style={{
                  top: `${10 + i * 15}%`,
                  left: `${5 + (i % 3) * 30}%`,
                  transform: 'rotate(-20deg)',
                }}
              >
                ScriptForge 预览
              </div>
            ))}
          </div>

          {/* 简介 */}
          <div className="relative z-10 mb-10">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <FileText className="w-5 h-5 text-gold-400" />
              作品简介
            </h2>
            <p className="text-navy-200 leading-relaxed text-lg">{work.description}</p>
          </div>

          {/* 人物设定 */}
          <div className="relative z-10 mb-10">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
              <User className="w-5 h-5 text-gold-400" />
              主要人物
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {work.characters.map((char, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + idx * 0.05 }}
                  className="p-5 rounded-2xl bg-navy-800/40 border border-navy-700/30"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-bold text-white text-lg">{char.name}</h3>
                    <span className="px-2 py-0.5 text-xs rounded-full bg-gold-500/20 text-gold-400">
                      {char.role}
                    </span>
                  </div>
                  <p className="text-sm text-navy-300 leading-relaxed">{char.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* 剧本正文 */}
          <div className="relative z-10">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
              <Film className="w-5 h-5 text-gold-400" />
              剧本预览
            </h2>

            <div className="space-y-6">
              {work.episodes.map((ep, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + idx * 0.08 }}
                  className="p-6 rounded-2xl bg-navy-900/60 border border-navy-700/30"
                >
                  <h3 className="text-lg font-bold text-gold-400 mb-4 flex items-center gap-2">
                    <span className="w-8 h-8 rounded-lg bg-gold-500/20 flex items-center justify-center text-sm">
                      {String(idx + 1).padStart(2, '0')}
                    </span>
                    {ep.title}
                  </h3>
                  <div className="text-navy-200 leading-loose whitespace-pre-line text-[15px]">
                    {ep.content}
                  </div>
                  {idx >= 3 && (
                    <div className="mt-6 pt-6 border-t border-navy-700/30">
                      <div className="flex items-center justify-center gap-2 text-navy-400">
                        <Lock className="w-4 h-4" />
                        <span className="text-sm">更多精彩内容需要注册后查看完整剧本</span>
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* CTA 注册按钮区 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card-gold rounded-3xl p-10 text-center relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-gold-500/10 via-transparent to-purple-500/10" />
          <div className="relative z-10">
            <motion.div
              animate={{ rotate: [0, 10, -10, 10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
              className="w-16 h-16 rounded-2xl mx-auto mb-6 flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
                boxShadow: '0 10px 40px -10px rgba(244, 183, 25, 0.5)',
              }}
            >
              <Sparkles className="w-8 h-8 text-navy-950" />
            </motion.div>

            <h2 className="text-3xl font-bold text-white mb-4">
              也想创作属于你的<span className="gradient-text">爆款剧本</span>？
            </h2>
            <p className="text-navy-200 text-lg mb-8 max-w-xl mx-auto">
              ScriptForge AI 让你从零开始，一句话创意即可生成完整剧本。
              加入 50,000+ 创作者，体验 AI 赋能的专业剧本创作。
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/register"
                className="btn-gold text-lg inline-flex items-center justify-center gap-2 !py-4 !px-10"
              >
                <Users className="w-5 h-5" />
                免费注册使用
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/"
                className="btn-ghost text-lg inline-flex items-center justify-center gap-2 !py-4 !px-10"
              >
                了解更多
              </Link>
            </div>

            <div className="mt-8 flex items-center justify-center gap-8 text-sm text-navy-400">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                无需信用卡
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                3次免费创作
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-400" />
                即注册即用
              </div>
            </div>
          </div>
        </motion.div>

        {/* 底部声明 */}
        <div className="mt-12 text-center text-sm text-navy-500">
          <p className="mb-2">本作品由 ScriptForge AI 辅助创作，版权归原创作者所有</p>
          <p>© 2026 ScriptForge · 保留所有权利</p>
        </div>
      </main>
    </div>
  )
}

import { Check } from 'lucide-react'
