import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FolderKanban,
  Search,
  Filter,
  ArrowLeft,
  Film,
  Clock,
  Calendar,
  Star,
  Sparkles,
  CheckCircle2,
  Loader2,
  FileText,
  ChevronDown,
  RefreshCw,
  ArrowRight,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { works } from '@/services/api'

const THEMES = [
  { key: 'family-revenge', name: '家庭伦理复仇', color: '#e53e3e', emoji: '⚔️' },
  { key: 'overbearing-ceo', name: '豪门霸总', color: '#d69e2e', emoji: '💎' },
  { key: 'sweet-pet', name: '甜宠虐恋', color: '#d53f8c', emoji: '💕' },
  { key: 'time-travel', name: '穿越重生', color: '#805ad5', emoji: '⏰' },
  { key: 'urban-rebirth', name: '都市逆袭', color: '#3182ce', emoji: '🏙️' },
  { key: 'ancient-costume', name: '古装权谋', color: '#2f855a', emoji: '⚜️' },
  { key: 'suspense-reversal', name: '悬疑反转', color: '#5a67d8', emoji: '🕵️' },
  { key: 'mixed-theme', name: '混合题材', color: '#dd6b20', emoji: '🎭' },
]

const STATUS_LIST = [
  { key: 'all', name: '全部作品', color: '#f6d365' },
  { key: 'completed', name: '已完成', color: '#68d391' },
  { key: 'generating', name: '创作中', color: '#f6ad55' },
  { key: 'draft', name: '草稿', color: '#a0aec0' },
]

// Mock 作品数据
const MOCK_WORKS = [
  {
    id: 'PRJ20260610',
    title: '豪门霸总的重生娇妻',
    theme: 'overbearing-ceo',
    episodes: 80,
    status: 'completed',
    score: 92.5,
    createdAt: '2026-06-10 14:32',
    idea: '一位惨遭背叛被害的豪门少奶奶重生回到悲剧发生前三年，决心改写命运并与真爱相遇。',
    format: '行业通用版',
  },
  {
    id: 'PRJ20260608',
    title: '都市逆袭之王牌归来',
    theme: 'urban-rebirth',
    episodes: 100,
    status: 'completed',
    score: 88.3,
    createdAt: '2026-06-08 09:15',
    idea: '曾经的王牌特工隐退都市，却意外卷入一场商业阴谋，被迫重出江湖守护家人。',
    format: '标准版',
  },
  {
    id: 'PRJ20260605',
    title: '古装权谋之凰权天下',
    theme: 'ancient-costume',
    episodes: 120,
    status: 'completed',
    score: 95.1,
    createdAt: '2026-06-05 20:48',
    idea: '亡国公主化名潜入敌朝，在权谋漩涡中步步为营，最终颠覆王朝复仇成功。',
    format: '行业通用版',
  },
  {
    id: 'PRJ20260602',
    title: '甜宠虐恋之总裁追妻',
    theme: 'sweet-pet',
    episodes: 60,
    status: 'completed',
    score: 85.7,
    createdAt: '2026-06-02 11:20',
    idea: '霸道总裁因误会伤害挚爱，五年后重逢展开猛烈追妻攻势，历经波折最终破镜重圆。',
    format: '精简版',
  },
  {
    id: 'PRJ20260530',
    title: '悬疑反转之夜半钟声',
    theme: 'suspense-reversal',
    episodes: 80,
    status: 'completed',
    score: 91.2,
    createdAt: '2026-05-30 16:05',
    idea: '一座古宅每到午夜便响起诡异钟声，女侦探调查发现隐藏二十年的家族秘密。',
    format: '标准版',
  },
  {
    id: 'PRJ20260528',
    title: '穿越重生之庶女翻身',
    theme: 'time-travel',
    episodes: 90,
    status: 'completed',
    score: 87.8,
    createdAt: '2026-05-28 22:30',
    idea: '现代女医生意外穿越成古代侯府庶女，凭借现代医术和智慧改变命运并收获爱情。',
    format: '分镜版',
  },
  {
    id: 'PRJ20260525',
    title: '家庭伦理复仇之觉醒',
    theme: 'family-revenge',
    episodes: 70,
    status: 'generating',
    score: null,
    createdAt: '2026-05-25 15:12',
    idea: '女儿发现父亲的意外死亡并非偶然，一步步揭开继母和舅舅的惊天阴谋。',
    format: '行业通用版',
  },
  {
    id: 'PRJ20260522',
    title: '混合题材之末日重生',
    theme: 'mixed-theme',
    episodes: 100,
    status: 'draft',
    score: null,
    createdAt: '2026-05-22 10:00',
    idea: '末日废土背景下的重生逆袭故事，融合科幻、权谋、感情多条线索。',
    format: '标准版',
  },
]

export default function Works() {
  const navigate = useNavigate()
  const [works, setWorks] = useState(MOCK_WORKS)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortBy, setSortBy] = useState('newest')
  const [showStatusMenu, setShowStatusMenu] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await works.list()
        if (data && Array.isArray(data) && data.length > 0) {
          setWorks(data)
        }
      } catch (e) {
        console.log('作品列表加载失败，使用 Mock 数据')
      } finally {
        setTimeout(() => setLoading(false), 500)
      }
    }
    load()
  }, [])

  const filtered = works
    .filter((w) => {
      if (statusFilter !== 'all' && w.status !== statusFilter) return false
      if (search && !w.title.includes(search) && !w.idea.includes(search)) return false
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'newest') return b.createdAt.localeCompare(a.createdAt)
      if (sortBy === 'score') return (b.score || 0) - (a.score || 0)
      if (sortBy === 'episodes') return b.episodes - a.episodes
      return 0
    })

  const getTheme = (key) => THEMES.find((t) => t.key === key) || THEMES[7]
  const getStatus = (key) => STATUS_LIST.find((s) => s.key === key) || STATUS_LIST[0]

  return (
    <div className="relative min-h-screen py-12">
      <div className="particles-bg" />
      <div className="max-w-7xl mx-auto px-6 relative z-10">
        {/* 顶部标题 */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => navigate('/')}
              className="w-10 h-10 rounded-xl flex items-center justify-center bg-navy-800/50 hover:bg-navy-700/50 text-navy-200 hover:text-white transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="inline-flex items-center gap-2 badge">
              <FolderKanban className="w-4 h-4" />
              <span>我的作品库</span>
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-3">
            我的<span className="gradient-text">作品</span>
          </h1>
          <p className="text-lg text-navy-300">
            共 <span className="text-gold-400 font-semibold">{works.length}</span> 个项目 · 已完成{' '}
            <span className="text-green-400 font-semibold">
              {works.filter((w) => w.status === 'completed').length}
            </span>{' '}
            个
          </p>
        </motion.div>

        {/* 搜索 + 筛选栏 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-2xl p-5 mb-8"
        >
          <div className="flex flex-col md:flex-row gap-3">
            {/* 搜索框 */}
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="搜索作品标题或创意描述..."
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-navy-800/50 border border-navy-600/30 text-white placeholder-navy-500 focus:border-gold-400/50 focus:ring-2 focus:ring-gold-400/20 outline-none transition-all"
              />
            </div>

            {/* 状态筛选 */}
            <div className="relative">
              <button
                onClick={() => setShowStatusMenu(!showStatusMenu)}
                className="w-full md:w-auto px-5 py-3 rounded-xl bg-navy-800/50 hover:bg-navy-700/50 border border-navy-600/30 text-white flex items-center gap-2 transition-all"
              >
                <Filter className="w-4 h-4 text-gold-400" />
                <span className="text-sm">{getStatus(statusFilter).name}</span>
                <ChevronDown className="w-4 h-4 text-navy-300" />
              </button>
              <AnimatePresence>
                {showStatusMenu && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 top-full mt-2 w-44 py-2 rounded-2xl glass-card shadow-xl z-20"
                  >
                    {STATUS_LIST.map((s) => (
                      <button
                        key={s.key}
                        onClick={() => {
                          setStatusFilter(s.key)
                          setShowStatusMenu(false)
                        }}
                        className={`w-full px-4 py-2.5 flex items-center gap-3 text-left transition-all ${
                          statusFilter === s.key
                            ? 'bg-gold-400/10 text-gold-400'
                            : 'text-navy-100 hover:bg-navy-700/30'
                        }`}
                      >
                        <span
                          className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{ background: s.color }}
                        />
                        <span className="text-sm">{s.name}</span>
                        <span className="ml-auto text-xs text-navy-400">
                          {s.key === 'all'
                            ? works.length
                            : works.filter((w) => w.status === s.key).length}
                        </span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* 排序 */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-5 py-3 rounded-xl bg-navy-800/50 hover:bg-navy-700/50 border border-navy-600/30 text-white outline-none transition-all cursor-pointer text-sm"
            >
              <option value="newest">最新创建</option>
              <option value="score">评分最高</option>
              <option value="episodes">集数最多</option>
            </select>

            {/* 新建按钮 */}
            <button
              onClick={() => navigate('/creation')}
              className="px-5 py-3 rounded-xl font-semibold flex items-center gap-2 btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
            >
              <Sparkles className="w-4 h-4" />
              新建创作
            </button>
          </div>
        </motion.div>

        {/* 作品列表 / 空状态 */}
        {loading ? (
          <LoadingSkeleton />
        ) : filtered.length === 0 ? (
          <EmptyState onNew={() => navigate('/creation')} hasFilter={!!search || statusFilter !== 'all'} />
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
          >
            {filtered.map((work, idx) => (
              <WorkCard key={work.id} work={work} index={idx} theme={getTheme(work.theme)} navigate={navigate} />
            ))}
          </motion.div>
        )}
      </div>
    </div>
  )
}

// ============ 作品卡片 ============
function WorkCard({ work, index, theme, navigate }) {
  const statusMap = {
    completed: { label: '已完成', color: '#68d391', bg: 'rgba(104, 211, 145, 0.15)', icon: CheckCircle2 },
    generating: { label: '创作中', color: '#f6ad55', bg: 'rgba(246, 173, 85, 0.15)', icon: Loader2 },
    draft: { label: '草稿', color: '#a0aec0', bg: 'rgba(160, 174, 192, 0.15)', icon: FileText },
  }
  const status = statusMap[work.status] || statusMap.completed
  const StatusIcon = status.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -6, scale: 1.01 }}
      onClick={() => navigate('/works/' + work.id)}
      className="glass-card rounded-3xl p-6 cursor-pointer group relative overflow-hidden transition-all hover:shadow-lg hover:shadow-gold-500/10 border border-navy-600/20"
    >
      {/* 装饰渐变 */}
      <div
        className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-20 blur-3xl group-hover:opacity-30 transition-opacity"
        style={{ background: theme.color, transform: 'translate(50%, -50%)' }}
      />

      <div className="relative">
        {/* 顶部：题材 + 状态 */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl" style={{ background: theme.color + '20' }}>
            <span className="text-lg">{theme.emoji}</span>
            <span className="text-xs font-medium" style={{ color: theme.color }}>
              {theme.name}
            </span>
          </div>
          <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl"
            style={{ background: status.bg, color: status.color }}
          >
            {work.status === 'generating' ? (
              <StatusIcon className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <StatusIcon className="w-3.5 h-3.5" />
            )}
            <span className="text-xs font-medium">{status.label}</span>
          </div>
        </div>

        {/* 标题 */}
        <h3 className="text-xl font-bold text-white mb-3 group-hover:text-gold-400 transition-colors line-clamp-2">
          {work.title}
        </h3>

        {/* 创意摘要 */}
        <p className="text-sm text-navy-300 leading-relaxed mb-5 line-clamp-3 min-h-[4.5rem]">
          {work.idea}
        </p>

        {/* 元信息 */}
        <div className="flex flex-wrap gap-3 mb-5 text-xs text-navy-400">
          <div className="flex items-center gap-1.5">
            <Film className="w-3.5 h-3.5 text-navy-400" />
            <span>{work.episodes} 集</span>
          </div>
          <div className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-navy-400" />
            <span>{work.format}</span>
          </div>
          {work.score && (
            <div className="flex items-center gap-1.5">
              <Star className="w-3.5 h-3.5 text-gold-400 fill-gold-400" />
              <span className="text-gold-400 font-semibold">{work.score}</span>
            </div>
          )}
        </div>

        {/* 底部：时间 + 箭头 */}
        <div className="flex items-center justify-between pt-4 border-t border-navy-700/40">
          <div className="flex items-center gap-1.5 text-xs text-navy-400">
            <Calendar className="w-3.5 h-3.5" />
            <span>{work.createdAt}</span>
          </div>
          <div className="flex items-center gap-1 text-sm text-gold-400 group-hover:gap-2 transition-all">
            <span>查看详情</span>
            <ArrowRight className="w-4 h-4" />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// ============ 加载骨架屏 ============
function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {Array.from({ length: 6 }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.05 }}
          className="glass-card rounded-3xl p-6 border border-navy-600/20 overflow-hidden"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="h-7 w-24 rounded-xl bg-navy-700/40 animate-pulse" />
            <div className="h-7 w-16 rounded-xl bg-navy-700/40 animate-pulse" />
          </div>
          <div className="h-6 w-4/5 rounded-lg bg-navy-700/40 animate-pulse mb-3" />
          <div className="h-4 w-full rounded bg-navy-700/30 animate-pulse mb-2" />
          <div className="h-4 w-5/6 rounded bg-navy-700/30 animate-pulse mb-2" />
          <div className="h-4 w-3/4 rounded bg-navy-700/30 animate-pulse mb-5" />
          <div className="flex gap-4 mb-5">
            <div className="h-4 w-16 rounded bg-navy-700/30 animate-pulse" />
            <div className="h-4 w-20 rounded bg-navy-700/30 animate-pulse" />
            <div className="h-4 w-12 rounded bg-navy-700/30 animate-pulse" />
          </div>
          <div className="flex justify-between pt-4 border-t border-navy-700/40">
            <div className="h-3 w-24 rounded bg-navy-700/30 animate-pulse" />
            <div className="h-4 w-16 rounded bg-navy-700/30 animate-pulse" />
          </div>
        </motion.div>
      ))}
    </div>
  )
}

// ============ 空状态 ============
function EmptyState({ onNew, hasFilter }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card rounded-3xl p-16 text-center border border-navy-600/20"
    >
      <motion.div
        animate={{ rotate: [0, -10, 10, -10, 0], y: [0, -10, 0] }}
        transition={{ duration: 3, repeat: Infinity, repeatDelay: 2 }}
        className="text-7xl mb-6"
      >
        📂
      </motion.div>
      <h3 className="text-2xl font-bold text-white mb-3">
        {hasFilter ? '没有找到匹配的作品' : '暂无作品'}
      </h3>
      <p className="text-navy-300 mb-8 max-w-md mx-auto">
        {hasFilter
          ? '试试调整搜索关键词或筛选条件，看看其他作品吧'
          : '从一句话创意开始，让 AI 帮你生成完整的短剧剧本'}
      </p>
      <button
        onClick={onNew}
        className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl font-semibold btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
      >
        <Sparkles className="w-5 h-5" />
        {hasFilter ? '清除筛选' : '开始第一次创作'}
        <ArrowRight className="w-5 h-5" />
      </button>
    </motion.div>
  )
}
