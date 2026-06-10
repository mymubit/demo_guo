import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  Download,
  Share2,
  Copy,
  Check,
  Film,
  FileText,
  Calendar,
  Star,
  Sparkles,
  Search,
  LayoutList,
  Users,
  PenTool,
  ClipboardCheck,
  Package,
  Clock,
  ChevronRight,
  RefreshCw,
} from 'lucide-react'
import { useParams, useNavigate } from 'react-router-dom'
import { worksApi } from '@/services/api'

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

const PIPELINE_NODES = [
  { step: 1, name: '信息收集', icon: Search, desc: '提炼创意核心，生成项目简报' },
  { step: 2, name: '结构规划', icon: LayoutList, desc: '6阶段架构 + 情绪节奏曲线' },
  { step: 3, name: '人设开发', icon: Users, desc: '主角/反派/配角完整设定' },
  { step: 4, name: '大纲撰写', icon: PenTool, desc: '每集钩子 + 反转 + 悬念' },
  { step: 5, name: '剧本创作', icon: FileText, desc: '逐集生成符合格式的剧本' },
  { step: 6, name: '质量审查', icon: ClipboardCheck, desc: '四维评分 + 问题清单' },
  { step: 7, name: '输出交付', icon: Package, desc: '4种格式 + 数字水印' },
]

// Mock HTML 内容
const MOCK_SCRIPT_HTML = `
<div class="sf-script-result">
  <h1 class="sf-title">✨ 豪门霸总的重生娇妻 - 80集短剧剧本</h1>
  <div class="sf-meta">
    <span class="sf-tag">题材：豪门霸总 + 穿越重生</span>
    <span class="sf-tag">集数：80集</span>
    <span class="sf-tag">格式：行业通用版</span>
    <span class="sf-score">综合评分：92.5</span>
  </div>

  <div class="sf-idea">
    <strong>核心创意：</strong>一位惨遭背叛被害的豪门少奶奶重生回到悲剧发生前三年，决心改写命运，揭穿伪善丈夫与继妹的阴谋，守护自己的家族，并在过程中与真正爱她的霸道总裁相遇相爱。
  </div>

  <h2 class="sf-section">🎭 主要人物设定</h2>
  <div class="sf-characters">
    <div class="sf-character-card">
      <div class="sf-char-name">苏晚晴</div>
      <div class="sf-char-role">女主角 / 25岁 / 重生者</div>
      <div class="sf-char-desc">苏氏集团千金，前世温婉善良却被丈夫和继妹联手害死。重生后变得聪慧果敢，外表冷静内心炽热，擅长隐忍与布局。</div>
    </div>
    <div class="sf-character-card">
      <div class="sf-char-name">顾言深</div>
      <div class="sf-char-role">男主角 / 30岁 / 顾氏集团总裁</div>
      <div class="sf-char-desc">商界传奇，冷酷寡言，行事杀伐果断。前世默默守护苏晚晴却未能表白，今生被她的转变所吸引，逐渐敞开心扉。</div>
    </div>
    <div class="sf-character-card">
      <div class="sf-char-name">林子墨</div>
      <div class="sf-char-role">反派 / 28岁 / 伪善丈夫</div>
      <div class="sf-char-desc">表面温文尔雅的入赘女婿，实则野心勃勃心狠手辣。利用苏家资源建立自己的商业帝国，与苏雨柔暗中勾结。</div>
    </div>
    <div class="sf-character-card">
      <div class="sf-char-name">苏雨柔</div>
      <div class="sf-char-role">反派 / 23岁 / 继妹</div>
      <div class="sf-char-desc">苏家养女，嫉妒苏晚晴的一切。外表柔弱内心恶毒，擅长挑拨离间和装可怜，与林子墨是情人关系。</div>
    </div>
    <div class="sf-character-card">
      <div class="sf-char-name">苏振邦</div>
      <div class="sf-char-role">配角 / 55岁 / 苏氏集团董事长</div>
      <div class="sf-char-desc">苏晚晴的父亲，威严正直。前世被阴谋气死，今生在女儿的保护下逐渐识破真相，成为女儿坚强的后盾。</div>
    </div>
    <div class="sf-character-card">
      <div class="sf-char-name">林婉清</div>
      <div class="sf-char-role">配角 / 28岁 / 顾言深的助理</div>
      <div class="sf-char-desc">干练聪慧的职业女性，顾言深最信任的人。暗中帮助苏晚晴收集证据，是男女主角感情的重要推手。</div>
    </div>
  </div>

  <h2 class="sf-section">📝 分集剧本（精选前5集）</h2>

  <div class="sf-episode">
    <h3>第1集 · 重生归来</h3>
    <p><strong>场景：</strong>豪华别墅卧室 - 夜</p>
    <p><strong>画面：</strong>雨水拍打窗户，苏晚晴从噩梦中惊醒。她大口喘着气，眼神从惊恐逐渐转为冰冷的恨意。</p>
    <p><strong>苏晚晴（独白）：</strong>林子墨、苏雨柔……你们没想到我还能回来吧？这一次，我要让你们血债血偿。</p>
    <p><strong>动作：</strong>她拿起手机，屏幕显示日期 - 正是悲剧发生的三年前。嘴角勾起一抹冷笑。</p>
    <p><strong>悬念结尾：</strong>手机突然响起，来电显示：丈夫 林子墨。</p>
  </div>

  <div class="sf-episode">
    <h3>第2集 · 初次交锋</h3>
    <p><strong>场景：</strong>苏家餐厅 - 日</p>
    <p><strong>画面：</strong>林子墨温柔地为苏晚晴夹菜，苏雨柔在一旁乖巧地陪笑。苏晚晴不动声色地观察着。</p>
    <p><strong>林子墨：</strong>晚晴，你昨晚没睡好吗？脸色不太好看。</p>
    <p><strong>苏晚晴（内心）：</strong>当然没睡好，毕竟我刚从你们害死我的那个噩梦里醒来。</p>
    <p><strong>苏晚晴（微笑）：</strong>只是做了个有趣的梦。子墨，雨柔，你们最近好像走得很近？</p>
    <p><strong>动作：</strong>两人的表情瞬间僵硬了一瞬，又迅速恢复。苏晚晴将这一切看在眼里。</p>
    <p><strong>悬念结尾：</strong>苏晚晴放下筷子，起身离开时意味深长地看了他们一眼。</p>
  </div>

  <div class="sf-episode">
    <h3>第3集 · 命运邂逅</h3>
    <p><strong>场景：</strong>高端商务酒会 - 夜</p>
    <p><strong>画面：</strong>苏晚晴身着简约优雅的礼服，主动接近顾氏集团总裁顾言深。周围人都惊呆了。</p>
    <p><strong>顾言深（冷淡）：</strong>苏小姐，我们认识吗？</p>
    <p><strong>苏晚晴（直视）：</strong>顾总，我知道您在暗中调查三年后的一场并购案。我们有共同的敌人。</p>
    <p><strong>动作：</strong>顾言深深邃的眼神第一次有了波动。他仔细打量着眼前这个与传闻中截然不同的苏家长女。</p>
    <p><strong>悬念结尾：</strong>不远处的林子墨看到这一幕，眼神阴鸷。</p>
  </div>

  <div class="sf-episode">
    <h3>第4集 · 证据初现</h3>
    <p><strong>场景：</strong>苏氏集团办公室 - 日</p>
    <p><strong>画面：</strong>苏晚晴借口查看公司账目，发现了林子墨转移资产的蛛丝马迹。</p>
    <p><strong>林婉清（OS，V.O.）：</strong>苏小姐，这些账目……有问题。子公司的现金流异常，有人在做手脚。</p>
    <p><strong>苏晚晴：</strong>继续查，但别让任何人知道。尤其是林子墨。</p>
    <p><strong>动作：</strong>苏雨柔端着咖啡走进来，假装无意地瞥向电脑屏幕。苏晚晴迅速切换了窗口。</p>
    <p><strong>悬念结尾：</strong>苏雨柔离开办公室后，迅速拨通了一个电话。</p>
  </div>

  <div class="sf-episode">
    <h3>第5集 · 公开撕破脸</h3>
    <p><strong>场景：</strong>苏家家族晚宴 - 夜</p>
    <p><strong>画面：</strong>宴会上，苏雨柔故意打碎贵重古董嫁祸给苏晚晴。</p>
    <p><strong>苏雨柔（哭腔）：</strong>姐姐，我知道你不喜欢我，但你也不用……</p>
    <p><strong>苏晚晴（打断，冷静）：</strong>雨柔，你手上的碎片花纹和你裙子上沾的一模一样。还有，走廊的监控是好的。</p>
    <p><strong>动作：</strong>全场哗然。林子墨试图圆场，苏晚晴却转向父亲。</p>
    <p><strong>苏晚晴：</strong>爸，有些事情，我想单独和您谈谈。关于公司，和您的好女婿。</p>
    <p><strong>悬念结尾：</strong>顾言深在远处看着这一切，嘴角勾起一抹欣赏的微笑。</p>
  </div>

  <h2 class="sf-section">🎯 剩余集数大纲</h2>
  <div class="sf-episode">
    <p><strong>第6-20集（揭露篇）：</strong>苏晚晴逐步向父亲揭露林子墨和苏雨柔的真面目，收集关键证据。顾言深从旁协助，两人关系升温。</p>
    <p><strong>第21-40集（反击篇）：</strong>林子墨察觉威胁，开始反击。商业斗争升级，苏晚晴在顾言深的帮助下化解多次危机，公开撕破脸。</p>
    <p><strong>第41-60集（感情篇）：</strong>男女主角确认关系，遭遇家族压力和外部阻碍。前世的真相逐渐浮出水面，顾言深藏着的秘密被揭开。</p>
    <p><strong>第61-75集（决战篇）：</strong>林子墨和苏雨柔使出杀手锏，苏家陷入危机。顾言深全力支持，两大集团展开商业决战。</p>
    <p><strong>第76-80集（结局篇）：</strong>最终对决，反派被绳之以法。苏晚晴夺回一切，与顾言深举行盛大婚礼。结局定格在两人相视而笑的幸福画面。</p>
  </div>

  <h2 class="sf-section">📊 剧本质量审查</h2>
  <div class="sf-review">
    <div class="sf-score-bar">
      <div class="sf-score-label">格式规范</div>
      <div class="flex-1 h-2 rounded-full bg-navy-700/50 overflow-hidden">
        <div class="sf-score-progress h-full" style="width: 95%"></div>
      </div>
      <div class="text-gold-400 font-semibold">95</div>
    </div>
    <div class="sf-score-bar">
      <div class="sf-score-label">节奏把控</div>
      <div class="flex-1 h-2 rounded-full bg-navy-700/50 overflow-hidden">
        <div class="sf-score-progress h-full" style="width: 92%"></div>
      </div>
      <div class="text-gold-400 font-semibold">92</div>
    </div>
    <div class="sf-score-bar">
      <div class="sf-score-label">内容质量</div>
      <div class="flex-1 h-2 rounded-full bg-navy-700/50 overflow-hidden">
        <div class="sf-score-progress h-full" style="width: 94%"></div>
      </div>
      <div class="text-gold-400 font-semibold">94</div>
    </div>
    <div class="sf-score-bar">
      <div class="sf-score-label">制作可行性</div>
      <div class="flex-1 h-2 rounded-full bg-navy-700/50 overflow-hidden">
        <div class="sf-score-progress h-full" style="width: 89%"></div>
      </div>
      <div class="text-gold-400 font-semibold">89</div>
    </div>
    <div class="sf-overall-score">
      🌟 综合评分：92.5 / 100 （A级剧本，强烈推荐）
    </div>
  </div>
</div>
`

// 默认 mock 数据
const MOCK_WORK = {
  id: 'PRJ20260610',
  title: '豪门霸总的重生娇妻',
  theme: 'overbearing-ceo',
  episodes: 80,
  status: 'completed',
  score: 92.5,
  createdAt: '2026-06-10 14:32',
  idea: '一位惨遭背叛被害的豪门少奶奶重生回到悲剧发生前三年，决心改写命运并与真爱相遇。',
  format: '行业通用版',
  audience: '25-40岁都市女性，喜欢甜宠+虐恋+逆袭题材',
  references: '《回家的诱惑》、《顶楼》风格，带点韩剧反转感',
}

export default function WorksDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [work, setWork] = useState(MOCK_WORK)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await worksApi.getDetail(id)
        if (data && data.id) {
          setWork(data)
        }
      } catch (e) {
        console.log('作品详情加载失败，使用 Mock 数据')
      } finally {
        setTimeout(() => setLoading(false), 400)
      }
    }
    load()
  }, [id])

  const theme = THEMES.find((t) => t.key === work.theme) || THEMES[1]

  const handleCopy = () => {
    navigator.clipboard?.writeText(window.location.href)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = (type) => {
    const blob = new Blob([MOCK_SCRIPT_HTML], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${work.title}-${type}.${type === 'pdf' ? 'pdf' : 'md'}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="min-h-screen py-12 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 rounded-full border-4 border-gold-400 border-t-transparent"
        />
      </div>
    )
  }

  return (
    <div className="relative min-h-screen py-12">
      <div className="particles-bg" />
      <div className="max-w-5xl mx-auto px-6 relative z-10">
        {/* 顶部导航 */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <button
            onClick={() => navigate('/works')}
            className="inline-flex items-center gap-2 text-navy-300 hover:text-gold-400 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>返回作品列表</span>
          </button>
        </motion.div>

        {/* 作品头部 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-3xl p-8 mb-8 relative overflow-hidden"
        >
          {/* 背景装饰 */}
          <div
            className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-20 blur-3xl pointer-events-none"
            style={{ background: theme.color, transform: 'translate(30%, -30%)' }}
          />

          <div className="relative">
            {/* 题材徽章 */}
            <div className="flex items-center gap-3 mb-5">
              <div
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl"
                style={{ background: theme.color + '20', color: theme.color }}
              >
                <span className="text-xl">{theme.emoji}</span>
                <span className="text-sm font-semibold">{theme.name}</span>
              </div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/15 text-gold-400">
                <Star className="w-4 h-4 fill-gold-400" />
                <span className="text-sm font-bold">{work.score} 分 · A级</span>
              </div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-green-400/15 text-green-400">
                <Check className="w-4 h-4" />
                <span className="text-sm font-semibold">已完成</span>
              </div>
            </div>

            {/* 标题 */}
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-5 leading-tight">{work.title}</h1>

            {/* 核心创意 */}
            <div className="bg-navy-800/40 rounded-2xl p-5 mb-6 border border-navy-600/30">
              <div className="text-xs text-gold-400 font-semibold uppercase tracking-wider mb-2">核心创意</div>
              <p className="text-navy-100 leading-relaxed">{work.idea}</p>
            </div>

            {/* 元信息 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <MetaItem icon={Film} label="集数" value={`${work.episodes} 集`} />
              <MetaItem icon={FileText} label="格式" value={work.format} />
              <MetaItem icon={Calendar} label="创建时间" value={work.createdAt} />
              <MetaItem icon={Sparkles} label="项目ID" value={work.id} mono />
            </div>

            {/* 操作按钮组 */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => handleDownload('markdown')}
                className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/50 hover:bg-navy-700 text-white transition-all border border-navy-600/30"
              >
                <Download className="w-4 h-4" />
                下载 Markdown
              </button>
              <button
                onClick={() => handleDownload('pdf')}
                className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/50 hover:bg-navy-700 text-white transition-all border border-navy-600/30"
              >
                <Download className="w-4 h-4" />
                下载 PDF
              </button>
              <button
                onClick={handleCopy}
                className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/50 hover:bg-navy-700 text-white transition-all border border-navy-600/30"
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                {copied ? '已复制链接' : '复制链接'}
              </button>
              <button
                onClick={() => setShareOpen(true)}
                className="px-5 py-3 rounded-xl font-semibold flex items-center gap-2 btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
              >
                <Share2 className="w-4 h-4" />
                分享作品
              </button>
              <button
                onClick={() => navigate('/creation')}
                className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/50 hover:bg-navy-700 text-white transition-all border border-navy-600/30"
              >
                <RefreshCw className="w-4 h-4" />
                创作新剧本
              </button>
            </div>
          </div>
        </motion.div>

        {/* 剧本正文 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card rounded-3xl p-6 md:p-10 mb-8"
        >
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-navy-700/40">
            <FileText className="w-5 h-5 text-gold-400" />
            <h2 className="text-2xl font-bold text-white">剧本内容</h2>
          </div>
          <div dangerouslySetInnerHTML={{ __html: MOCK_SCRIPT_HTML }} />
        </motion.div>

        {/* 创作历程时间线 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card rounded-3xl p-8"
        >
          <div className="flex items-center gap-3 mb-8">
            <Clock className="w-5 h-5 text-gold-400" />
            <h2 className="text-2xl font-bold text-white">创作历程</h2>
            <span className="text-sm text-navy-400 ml-auto">7节点智能流水线</span>
          </div>

          <div className="relative">
            {/* 连接线 */}
            <div className="absolute left-6 top-8 bottom-8 w-px bg-gradient-to-b from-gold-400/50 via-navy-600/40 to-transparent" />

            {PIPELINE_NODES.map((node, idx) => {
              const Icon = node.icon
              return (
                <motion.div
                  key={node.step}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.35 + idx * 0.05 }}
                  className="relative pl-16 pb-8 last:pb-0"
                >
                  {/* 节点图标 */}
                  <div className="absolute left-0 top-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center shadow-lg shadow-gold-500/20">
                    <Icon className="w-5 h-5 text-navy-950" />
                  </div>

                  {/* 节点序号徽章 */}
                  <div className="absolute left-12 -top-1 w-6 h-6 rounded-full bg-navy-800 border-2 border-gold-400/50 flex items-center justify-center">
                    <span className="text-xs font-bold text-gold-400">{node.step}</span>
                  </div>

                  {/* 内容卡片 */}
                  <div className="bg-navy-800/30 rounded-2xl p-5 border border-navy-600/20">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-lg font-bold text-white">{node.name}</h3>
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-green-400/15 text-green-400">
                        <Check className="w-3.5 h-3.5" />
                        <span className="text-xs font-semibold">已完成</span>
                      </div>
                    </div>
                    <p className="text-sm text-navy-300 leading-relaxed">{node.desc}</p>
                  </div>

                  {/* 向下箭头 */}
                  {idx < PIPELINE_NODES.length - 1 && (
                    <div className="absolute left-[22px] top-[52px] text-gold-400/40">
                      <ChevronRight className="w-4 h-4 rotate-90" />
                    </div>
                  )}
                </motion.div>
              )
            })}
          </div>

          {/* 总结 */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.75 }}
            className="mt-8 p-6 rounded-2xl bg-gradient-to-br from-gold-400/10 to-gold-600/10 border border-gold-400/30"
          >
            <div className="flex items-center gap-3 mb-3">
              <Sparkles className="w-5 h-5 text-gold-400" />
              <span className="font-bold text-gold-400">创作完成</span>
            </div>
            <p className="text-sm text-navy-200 leading-relaxed">
              全部 7 个创作节点已完成，AI 流水线从创意收集到剧本交付进行了完整处理。剧本经过
              <span className="text-gold-400 font-semibold"> 四维质量审查 </span>
              （格式规范 95 分 · 节奏把控 92 分 · 内容质量 94 分 · 制作可行性 89 分），综合评分达到
              <span className="text-gold-400 font-semibold"> A级标准 </span>，可直接用于后续制作。
            </p>
          </motion.div>
        </motion.div>

        {/* 底部 CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 flex flex-col md:flex-row gap-3 justify-center"
        >
          <button
            onClick={() => navigate('/works')}
            className="px-8 py-4 rounded-2xl font-semibold flex items-center justify-center gap-2 bg-navy-700/40 hover:bg-navy-700/60 text-white transition-all border border-navy-600/30"
          >
            <ArrowLeft className="w-5 h-5" />
            查看更多作品
          </button>
          <button
            onClick={() => navigate('/creation')}
            className="px-8 py-4 rounded-2xl font-semibold flex items-center justify-center gap-2 btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
          >
            <Sparkles className="w-5 h-5" />
            创作新剧本
            <ChevronRight className="w-5 h-5" />
          </button>
        </motion.div>

        {/* 分享弹窗 */}
        {shareOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-navy-950/80 backdrop-blur-md z-50 flex items-center justify-center p-6"
            onClick={() => setShareOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-card rounded-3xl p-8 max-w-md w-full border border-navy-600/30"
            >
              <div className="text-center mb-6">
                <div className="w-16 h-16 rounded-2xl mx-auto mb-4 bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
                  <Share2 className="w-7 h-7 text-navy-950" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">分享作品</h3>
                <p className="text-sm text-navy-300">复制链接分享给他人查看</p>
              </div>

              <div className="bg-navy-800/50 rounded-xl p-4 mb-5 border border-navy-600/30">
                <p className="text-xs text-navy-400 mb-2">分享链接</p>
                <p className="text-sm text-navy-100 font-mono break-all">{window.location.href}</p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShareOpen(false)}
                  className="flex-1 py-3 rounded-xl font-medium bg-navy-700/50 hover:bg-navy-700 text-white transition-all"
                >
                  关闭
                </button>
                <button
                  onClick={handleCopy}
                  className="flex-1 py-3 rounded-xl font-semibold btn-gold flex items-center justify-center gap-2"
                >
                  {copied ? <Check className="w-4 h-4 text-navy-950" /> : <Copy className="w-4 h-4 text-navy-950" />}
                  {copied ? '已复制' : '复制链接'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

function MetaItem({ icon: Icon, label, value, mono }) {
  return (
    <div className="bg-navy-800/30 rounded-xl p-4 border border-navy-600/20">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-3.5 h-3.5 text-gold-400" />
        <span className="text-xs text-navy-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-white font-semibold text-sm ${mono ? 'font-mono' : ''}`}>{value}</div>
    </div>
  )
}
