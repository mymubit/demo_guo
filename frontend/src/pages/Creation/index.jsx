import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles,
  Check,
  ArrowLeft,
  ArrowRight,
  Film,
  FileText,
  Users,
  Download,
  Share2,
  Copy,
  BookOpen,
  Clock,
  Search,
  Compass,
  Users as UsersIcon,
  LayoutList,
  PenTool,
  ClipboardCheck,
  Package,
  RefreshCw,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { creationApi } from '@/services/api'

// ============ 常量配置 ============
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

const FORMAT_VARIANTS = [
  { key: 'standard', name: '标准版', desc: '完整剧本，含场景动作对白', icon: FileText },
  { key: 'industry', name: '行业通用版', desc: '制作团队优化格式，可直接拍摄', icon: Film },
  { key: 'lite', name: '精简版', desc: '核心要点，快速阅读', icon: BookOpen },
  { key: 'storyboard', name: '分镜版', desc: '含镜头描述，适合短视频', icon: Compass },
]

const PIPELINE_NODES = [
  { step: 1, name: '信息收集', icon: Search, desc: '提炼创意核心，生成项目简报' },
  { step: 2, name: '结构规划', icon: LayoutList, desc: '6阶段架构 + 情绪节奏曲线' },
  { step: 3, name: '人设开发', icon: UsersIcon, desc: '主角/反派/配角完整设定' },
  { step: 4, name: '大纲撰写', icon: PenTool, desc: '每集钩子 + 反转 + 悬念' },
  { step: 5, name: '剧本创作', icon: FileText, desc: '逐集生成符合格式的剧本' },
  { step: 6, name: '质量审查', icon: ClipboardCheck, desc: '四维评分 + 问题清单' },
  { step: 7, name: '输出交付', icon: Package, desc: '4种格式 + 数字水印' },
]

// Mock 数据
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

// ============ 主组件 ============
export default function Creation() {
  const navigate = useNavigate()
  const [stage, setStage] = useState(1)
  const [formData, setFormData] = useState({
    theme: '',
    idea: '',
    episodes: 80,
    format: 'standard',
    audience: '',
    references: '',
  })
  const [currentNode, setCurrentNode] = useState(0)
  const [completedNodes, setCompletedNodes] = useState([])
  const [nodeStatus, setNodeStatus] = useState('')
  const [scriptHtml, setScriptHtml] = useState('')
  const [projectId, setProjectId] = useState('')
  const [totalScore, setTotalScore] = useState(92.5)

  // 阶段3：进度模拟
  useEffect(() => {
    if (stage !== 3) return

    let nodeIndex = 0
    setCurrentNode(0)
    setCompletedNodes([])

    const runNode = () => {
      if (nodeIndex >= PIPELINE_NODES.length) {
        setTimeout(() => {
          setStage(4)
          setScriptHtml(MOCK_SCRIPT_HTML)
          setProjectId('PRJ' + Date.now().toString().slice(-8))
        }, 500)
        return
      }

      setNodeStatus(PIPELINE_NODES[nodeIndex].desc)

      const duration = 1000 + Math.random() * 2000
      setTimeout(() => {
        setCompletedNodes((prev) => [...prev, nodeIndex])
        nodeIndex++
        setCurrentNode(nodeIndex)
        runNode()
      }, duration)
    }

    runNode()
  }, [stage])

  const handleSubmit = async () => {
    try {
      await creationApi.submit({
        theme: formData.theme,
        idea: formData.idea,
        episodes: formData.episodes,
        format: formData.format,
        audience: formData.audience,
        references: formData.references,
      })
    } catch (e) {
      console.log('API 调用失败，使用 Mock 模式继续')
    }
    setStage(3)
  }

  const getThemeName = (key) => THEMES.find((t) => t.key === key)?.name || '未选择'
  const getFormatName = (key) => FORMAT_VARIANTS.find((f) => f.key === key)?.name || '标准版'

  return (
    <div className="relative min-h-screen py-12">
      <div className="particles-bg" />
      <div className="max-w-5xl mx-auto px-6 relative z-10">
        {/* 标题 */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4 badge">
            <Sparkles className="w-4 h-4" />
            <span>AI 智能创作引擎</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            从一句话创意到<span className="gradient-text">80集A级剧本</span>
          </h1>
          <p className="text-lg text-navy-200">7节点智能流水线，几分钟内生成完整可拍摄剧本</p>
        </motion.div>

        {/* 阶段指示器 */}
        <StageIndicator stage={stage} />

        <AnimatePresence mode="wait">
          {/* 阶段1：创意输入 */}
          {stage === 1 && (
            <StageInputForm
              key="stage1"
              formData={formData}
              setFormData={setFormData}
              onSubmit={handleSubmit}
            />
          )}

          {/* 阶段2：项目简报确认 */}
          {stage === 2 && (
            <StageBrief
              key="stage2"
              formData={formData}
              getThemeName={getThemeName}
              getFormatName={getFormatName}
              onBack={() => setStage(1)}
              onConfirm={() => setStage(3)}
            />
          )}

          {/* 阶段3：7节点进度动画 */}
          {stage === 3 && (
            <StageProgress
              key="stage3"
              currentNode={currentNode}
              completedNodes={completedNodes}
              nodeStatus={nodeStatus}
            />
          )}

          {/* 阶段4：结果展示 */}
          {stage === 4 && (
            <StageResult
              key="stage4"
              scriptHtml={scriptHtml}
              projectId={projectId}
              totalScore={totalScore}
              onRestart={() => {
                setStage(1)
                setFormData({
                  theme: '',
                  idea: '',
                  episodes: 80,
                  format: 'standard',
                  audience: '',
                  references: '',
                })
              }}
              onDownloadMarkdown={() => downloadAsFile('script-' + projectId, MOCK_SCRIPT_HTML, 'md')}
              onDownloadPDF={() => downloadAsFile('script-' + projectId, MOCK_SCRIPT_HTML, 'pdf')}
              onViewDetail={() => navigate('/works/' + projectId)}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// ============ 阶段指示器 ============
function StageIndicator({ stage }) {
  const stages = [
    { id: 1, label: '创意输入' },
    { id: 2, label: '项目确认' },
    { id: 3, label: '智能创作' },
    { id: 4, label: '创作完成' },
  ]
  return (
    <div className="glass-card rounded-2xl p-6 mb-8">
      <div className="flex items-center justify-between">
        {stages.map((s, idx) => {
          const active = stage === s.id
          const passed = stage > s.id
          return (
            <div key={s.id} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center">
                <motion.div
                  animate={{ scale: active ? 1.1 : 1 }}
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                    passed
                      ? 'bg-gradient-to-br from-gold-400 to-gold-600 text-navy-950'
                      : active
                      ? 'bg-gradient-to-br from-gold-400 to-gold-600 text-navy-950 node-active'
                      : 'bg-navy-700/50 text-navy-300 border border-navy-600/50'
                  }`}
                >
                  {passed ? <Check className="w-5 h-5" /> : s.id}
                </motion.div>
                <div className={`text-xs mt-2 ${active ? 'text-gold-400 font-semibold' : passed ? 'text-white' : 'text-navy-400'}`}>
                  {s.label}
                </div>
              </div>
              {idx < stages.length - 1 && (
                <div className="flex-1 mx-2 h-0.5 bg-navy-700/50 relative overflow-hidden">
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
    </div>
  )
}

// ============ 阶段1：创意输入表单 ============
function StageInputForm({ formData, setFormData, onSubmit }) {
  const canSubmit = formData.theme && formData.idea.trim().length >= 10

  const update = (key, value) => setFormData((prev) => ({ ...prev, [key]: value }))

  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* 题材选择 */}
      <SectionCard title="选择题材" subtitle="选择最契合你创意的热门题材（单选）" icon={Film}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {THEMES.map((theme) => {
            const active = formData.theme === theme.key
            return (
              <motion.button
                key={theme.key}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => update('theme', theme.key)}
                className={`p-4 rounded-2xl text-left transition-all relative overflow-hidden ${
                  active
                    ? 'ring-2 ring-gold-400 bg-navy-700/40'
                    : 'bg-navy-800/30 hover:bg-navy-700/30 border border-navy-600/30'
                }`}
                style={active ? { borderColor: theme.color + '60' } : {}}
              >
                <div className="text-2xl mb-2">{theme.emoji}</div>
                <div className={`text-sm font-semibold ${active ? 'text-white' : 'text-navy-100'}`}>{theme.name}</div>
                {active && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute top-2 right-2 w-6 h-6 rounded-full flex items-center justify-center"
                    style={{ background: theme.color }}
                  >
                    <Check className="w-3.5 h-3.5 text-white" />
                  </motion.div>
                )}
              </motion.button>
            )
          })}
        </div>
      </SectionCard>

      {/* 一句话创意 */}
      <SectionCard
        title="一句话创意"
        subtitle="用最简洁的语言描述你的故事核心（建议 20-80 字）"
        icon={Sparkles}
      >
        <div className="relative">
          <textarea
            value={formData.idea}
            onChange={(e) => update('idea', e.target.value.slice(0, 100))}
            placeholder="例：一位惨遭背叛被害的豪门少奶奶重生回到悲剧发生前三年，决心改写命运并与真爱相遇..."
            className="w-full h-36 p-5 rounded-2xl bg-navy-900/50 border border-navy-600/30 text-white placeholder-navy-400 focus:border-gold-400/50 focus:ring-2 focus:ring-gold-400/20 outline-none resize-none text-base leading-relaxed transition-all"
          />
          <div className="absolute bottom-4 right-5 flex items-center gap-2">
            <span
              className={`text-sm font-medium ${
                formData.idea.length >= 80
                  ? 'text-gold-400'
                  : formData.idea.length >= 20
                  ? 'text-green-400'
                  : 'text-navy-400'
              }`}
            >
              {formData.idea.length}
            </span>
            <span className="text-navy-500 text-sm">/ 100</span>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-4 text-xs text-navy-300">
          <span className="flex items-center gap-1.5">
            <Check className="w-3 h-3 text-green-400" />
            建议包含主角身份
          </span>
          <span className="flex items-center gap-1.5">
            <Check className="w-3 h-3 text-green-400" />
            说明核心冲突
          </span>
          <span className="flex items-center gap-1.5">
            <Check className="w-3 h-3 text-green-400" />
            点明故事卖点
          </span>
        </div>
      </SectionCard>

      {/* 集数选择 */}
      <SectionCard title="集数设置" subtitle="选择剧本总集数（每集约 2-3 分钟）" icon={Clock}>
        <div className="flex items-center gap-6">
          <div className="flex-1">
            <input
              type="range"
              min="20"
              max="200"
              step="10"
              value={formData.episodes}
              onChange={(e) => update('episodes', parseInt(e.target.value))}
              className="w-full h-2 rounded-full bg-navy-700/50 appearance-none cursor-pointer accent-gold-400"
              style={{
                background: `linear-gradient(to right, #f6d365 0%, #fda085 ${
                  ((formData.episodes - 20) / 180) * 100
                }%, rgba(30, 58, 138, 0.5) ${((formData.episodes - 20) / 180) * 100}%, rgba(30, 58, 138, 0.5) 100%)`,
              }}
            />
            <div className="flex justify-between mt-2 text-xs text-navy-400">
              <span>20集</span>
              <span>60集</span>
              <span>100集</span>
              <span>150集</span>
              <span>200集</span>
            </div>
          </div>
          <motion.div
            key={formData.episodes}
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="w-24 h-24 rounded-2xl glass-card-gold flex flex-col items-center justify-center"
          >
            <span className="text-3xl font-bold gradient-text">{formData.episodes}</span>
            <span className="text-xs text-navy-300 mt-1">集</span>
          </motion.div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {[20, 40, 60, 80, 100, 120, 150, 200].map((n) => (
            <button
              key={n}
              onClick={() => update('episodes', n)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                formData.episodes === n
                  ? 'bg-gold-400/20 text-gold-400 border border-gold-400/40'
                  : 'bg-navy-700/30 text-navy-300 hover:bg-navy-700/50 border border-transparent'
              }`}
            >
              {n}集
            </button>
          ))}
        </div>
      </SectionCard>

      {/* 格式变体 */}
      <SectionCard title="格式变体" subtitle="选择剧本输出格式（影响最终剧本的详细程度和结构）" icon={FileText}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {FORMAT_VARIANTS.map((f) => {
            const active = formData.format === f.key
            const Icon = f.icon
            return (
              <motion.button
                key={f.key}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => update('format', f.key)}
                className={`p-5 rounded-2xl text-left flex items-start gap-4 transition-all ${
                  active
                    ? 'ring-2 ring-gold-400/50 bg-navy-700/40'
                    : 'bg-navy-800/30 hover:bg-navy-700/30 border border-navy-600/30'
                }`}
              >
                <div
                  className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    active ? 'bg-gold-400/20' : 'bg-navy-700/50'
                  }`}
                >
                  <Icon className={`w-5 h-5 ${active ? 'text-gold-400' : 'text-navy-300'}`} />
                </div>
                <div className="flex-1">
                  <div className={`font-semibold ${active ? 'text-white' : 'text-navy-100'}`}>{f.name}</div>
                  <div className="text-xs text-navy-400 mt-1 leading-relaxed">{f.desc}</div>
                </div>
                {active && (
                  <div className="w-5 h-5 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
                    <Check className="w-3 h-3 text-navy-950" />
                  </div>
                )}
              </motion.button>
            )
          })}
        </div>
      </SectionCard>

      {/* 目标受众 + 参考作品 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SectionCard title="目标受众" subtitle="可选：描述目标观众画像" icon={Users}>
          <textarea
            value={formData.audience}
            onChange={(e) => update('audience', e.target.value)}
            placeholder="例：25-40岁都市女性，喜欢甜宠+虐恋+逆袭题材..."
            className="w-full h-28 p-4 rounded-2xl bg-navy-900/50 border border-navy-600/30 text-white placeholder-navy-500 focus:border-gold-400/50 outline-none resize-none text-sm transition-all"
          />
        </SectionCard>
        <SectionCard title="参考作品" subtitle="可选：列举风格相近的参考剧本/影视作品" icon={BookOpen}>
          <textarea
            value={formData.references}
            onChange={(e) => update('references', e.target.value)}
            placeholder="例：《回家的诱惑》、《顶楼》风格，带点韩剧反转感..."
            className="w-full h-28 p-4 rounded-2xl bg-navy-900/50 border border-navy-600/30 text-white placeholder-navy-500 focus:border-gold-400/50 outline-none resize-none text-sm transition-all"
          />
        </SectionCard>
      </div>

      {/* 提交按钮 */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <button
          onClick={onSubmit}
          disabled={!canSubmit}
          className={`w-full py-5 rounded-2xl font-semibold text-lg flex items-center justify-center gap-3 transition-all ${
            canSubmit
              ? 'btn-gold hover:shadow-lg hover:shadow-gold-500/30'
              : 'bg-navy-700/50 text-navy-400 cursor-not-allowed'
          }`}
        >
          <Sparkles className="w-5 h-5" />
          {canSubmit ? '生成项目简报，开始创作' : '请先选择题材并填写创意（至少10字）'}
          {canSubmit && <ArrowRight className="w-5 h-5" />}
        </button>
      </motion.div>
    </motion.div>
  )
}

// ============ 阶段2：项目简报确认 ============
function StageBrief({ formData, getThemeName, getFormatName, onBack, onConfirm }) {
  const theme = THEMES.find((t) => t.key === formData.theme)
  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.4 }}
    >
      <div className="glass-card rounded-3xl p-8 md:p-10">
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', delay: 0.1 }}
            className="w-20 h-20 rounded-3xl mx-auto mb-4 flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(246, 211, 101, 0.2) 0%, rgba(253, 160, 133, 0.2) 100%)',
              border: '1px solid rgba(244, 183, 25, 0.3)',
            }}
          >
            <FileText className="w-9 h-9 text-gold-400" />
          </motion.div>
          <h2 className="text-3xl font-bold mb-2">项目简报</h2>
          <p className="text-navy-300">请确认以下创作参数，确认后将开始智能生成</p>
        </div>

        <div className="space-y-4 mb-10">
          <BriefRow icon={Film} label="选择题材">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{theme?.emoji}</span>
              <span className="font-semibold text-white">{getThemeName(formData.theme)}</span>
            </div>
          </BriefRow>

          <BriefRow icon={Sparkles} label="核心创意">
            <div className="bg-navy-800/40 rounded-2xl p-5 border border-navy-600/20">
              <p className="text-navy-100 leading-relaxed">{formData.idea}</p>
            </div>
          </BriefRow>

          <BriefRow icon={Clock} label="集数设置">
            <span className="text-2xl font-bold gradient-text">{formData.episodes}</span>
            <span className="text-navy-300 ml-1">集</span>
          </BriefRow>

          <BriefRow icon={FileText} label="输出格式">
            <span className="font-semibold text-white">{getFormatName(formData.format)}</span>
          </BriefRow>

          {formData.audience && (
            <BriefRow icon={Users} label="目标受众">
              <span className="text-navy-100">{formData.audience}</span>
            </BriefRow>
          )}

          {formData.references && (
            <BriefRow icon={BookOpen} label="参考作品">
              <span className="text-navy-100">{formData.references}</span>
            </BriefRow>
          )}
        </div>

        {/* 预估信息 */}
        <div className="bg-navy-800/30 rounded-2xl p-5 mb-8 border border-navy-600/20">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-navy-300">
              <Clock className="w-4 h-4" />
              <span>预计创作时间</span>
            </div>
            <span className="text-gold-400 font-semibold">约 3-5 分钟</span>
          </div>
        </div>

        {/* 按钮 */}
        <div className="flex flex-col md:flex-row gap-3">
          <button
            onClick={onBack}
            className="flex-1 py-4 rounded-2xl font-semibold flex items-center justify-center gap-2 bg-navy-700/40 hover:bg-navy-700/60 text-white transition-all border border-navy-600/30"
          >
            <ArrowLeft className="w-4 h-4" />
            返回修改
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-4 rounded-2xl font-semibold flex items-center justify-center gap-2 btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
          >
            <Sparkles className="w-5 h-5" />
            确认开始创作
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  )
}

function BriefRow({ icon: Icon, label, children }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.1 }}
      className="flex items-start gap-4 py-4 border-b border-navy-700/30 last:border-0"
    >
      <div className="w-10 h-10 rounded-xl bg-navy-700/50 flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-gold-400" />
      </div>
      <div className="flex-1">
        <div className="text-xs text-navy-400 mb-1.5 uppercase tracking-wider">{label}</div>
        <div className="text-white">{children}</div>
      </div>
    </motion.div>
  )
}

// ============ 阶段3：7节点进度动画 ============
function StageProgress({ currentNode, completedNodes, nodeStatus }) {
  const totalProgress = Math.round((completedNodes.length / PIPELINE_NODES.length) * 100)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 1.05 }}
      transition={{ duration: 0.4 }}
      className="glass-card rounded-3xl p-8 md:p-12"
    >
      <div className="text-center mb-12">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
          style={{
            background: 'linear-gradient(135deg, rgba(246, 211, 101, 0.2) 0%, rgba(253, 160, 133, 0.2) 100%)',
            border: '2px solid rgba(244, 183, 25, 0.4)',
          }}
        >
          <RefreshCw className="w-7 h-7 text-gold-400" />
        </motion.div>
        <h2 className="text-3xl font-bold mb-2">AI 智能创作中...</h2>
        <p className="text-navy-300">正在执行 7 节点创作流水线，请耐心等待</p>
      </div>

      {/* 总进度 */}
      <div className="mb-12">
        <div className="flex justify-between text-sm mb-3">
          <span className="text-navy-200 font-medium">总进度</span>
          <span className="text-gold-400 font-bold">{totalProgress}%</span>
        </div>
        <div className="h-3 rounded-full bg-navy-700/50 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: totalProgress + '%' }}
            transition={{ duration: 0.5 }}
            className="h-full rounded-full"
            style={{
              background: 'linear-gradient(90deg, #667eea 0%, #f6d365 50%, #fda085 100%)',
              boxShadow: '0 0 20px rgba(244, 183, 25, 0.4)',
            }}
          />
        </div>
      </div>

      {/* 节点网格 */}
      <div className="relative">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {PIPELINE_NODES.map((node, idx) => {
            const isCompleted = completedNodes.includes(idx)
            const isActive = currentNode === idx
            const Icon = node.icon
            return (
              <motion.div
                key={node.step}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className={`relative p-5 rounded-2xl transition-all ${
                  isCompleted
                    ? 'bg-gradient-to-br from-gold-400/10 to-gold-600/10 border border-gold-400/30'
                    : isActive
                    ? 'bg-navy-700/40 border-2 border-gold-400/60 node-active'
                    : 'bg-navy-800/30 border border-navy-600/20 opacity-60'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      isCompleted
                        ? 'bg-gradient-to-br from-gold-400 to-gold-600'
                        : isActive
                        ? 'bg-gold-400/20'
                        : 'bg-navy-700/50'
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="w-5 h-5 text-navy-950 font-bold" />
                    ) : (
                      <Icon className={`w-5 h-5 ${isActive ? 'text-gold-400' : 'text-navy-400'}`} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-navy-400">节点 {node.step}</span>
                      {isActive && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gold-400/20 text-gold-400 animate-pulse">
                          进行中
                        </span>
                      )}
                      {isCompleted && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-400/20 text-green-400">
                          完成
                        </span>
                      )}
                    </div>
                    <div className={`font-semibold ${isActive || isCompleted ? 'text-white' : 'text-navy-200'}`}>
                      {node.name}
                    </div>
                    <div className="text-xs text-navy-400 mt-1 leading-relaxed">{node.desc}</div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* 状态文字 */}
      <motion.div
        key={nodeStatus}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-10 text-center"
      >
        <div className="inline-flex items-center gap-3 px-6 py-3 rounded-2xl bg-navy-800/50 border border-navy-600/30">
          <motion.div
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-2 h-2 rounded-full bg-gold-400"
          />
          <span className="text-navy-100">{nodeStatus || '正在初始化...'}</span>
        </div>
      </motion.div>
    </motion.div>
  )
}

// ============ 阶段4：结果展示 ============
function StageResult({
  scriptHtml,
  projectId,
  totalScore,
  onRestart,
  onDownloadMarkdown,
  onDownloadPDF,
  onViewDetail,
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = scriptHtml
    navigator.clipboard?.writeText(tempDiv.innerText || '剧本内容')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -30 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* 成功大标题 */}
      <div className="text-center py-10">
        <motion.div
          initial={{ scale: 0, rotate: -20 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: 'spring', bounce: 0.5 }}
          className="inline-block mb-4"
        >
          <span className="text-7xl">🎉</span>
        </motion.div>
        <h1 className="text-4xl md:text-6xl font-bold mb-3">
          创作<span className="gradient-text">完成</span>！
        </h1>
        <p className="text-xl text-navy-300 mb-4">
          项目 ID: <span className="text-gold-400 font-mono">{projectId}</span>
        </p>
        <div className="inline-flex items-center gap-3 px-6 py-3 rounded-2xl glass-card-gold">
          <span className="text-navy-200">综合评分</span>
          <span className="text-3xl font-bold gradient-text">{totalScore}</span>
          <span className="text-gold-400 text-sm">/ 100 · A级</span>
        </div>
      </div>

      {/* 操作按钮组 */}
      <div className="glass-card rounded-2xl p-5">
        <div className="flex flex-wrap gap-3 justify-center">
          <button
            onClick={onRestart}
            className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/40 hover:bg-navy-700/60 text-white transition-all border border-navy-600/30"
          >
            <RefreshCw className="w-4 h-4" />
            返回创作
          </button>
          <button
            onClick={onDownloadMarkdown}
            className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/40 hover:bg-navy-700/60 text-white transition-all border border-navy-600/30"
          >
            <Download className="w-4 h-4" />
            下载 Markdown
          </button>
          <button
            onClick={onDownloadPDF}
            className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/40 hover:bg-navy-700/60 text-white transition-all border border-navy-600/30"
          >
            <Download className="w-4 h-4" />
            下载 PDF
          </button>
          <button
            onClick={handleCopy}
            className="px-5 py-3 rounded-xl font-medium flex items-center gap-2 bg-navy-700/40 hover:bg-navy-700/60 text-white transition-all border border-navy-600/30"
          >
            {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
            {copied ? '已复制' : '复制文本'}
          </button>
          <button
            onClick={onViewDetail}
            className="px-5 py-3 rounded-xl font-semibold flex items-center gap-2 btn-gold hover:shadow-lg hover:shadow-gold-500/30 transition-all"
          >
            <Share2 className="w-4 h-4" />
            查看作品详情
          </button>
        </div>
      </div>

      {/* 剧本内容展示 */}
      <div className="glass-card rounded-3xl p-6 md:p-10">
        <div dangerouslySetInnerHTML={{ __html: scriptHtml }} />
      </div>

      {/* 底部再次操作 */}
      <div className="flex flex-col md:flex-row gap-3 pb-10">
        <button
          onClick={onRestart}
          className="flex-1 py-4 rounded-2xl font-semibold flex items-center justify-center gap-2 bg-navy-700/40 hover:bg-navy-700/60 text-white transition-all border border-navy-600/30"
        >
          <RefreshCw className="w-5 h-5" />
          创作新剧本
        </button>
        <button
          onClick={onViewDetail}
          className="flex-1 py-4 rounded-2xl font-semibold flex items-center justify-center gap-2 btn-gold"
        >
          <Share2 className="w-5 h-5" />
          保存并查看作品
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  )
}

// ============ 通用：分区卡片 ============
function SectionCard({ title, subtitle, icon: Icon, children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-3xl p-6 md:p-7"
    >
      <div className="flex items-start gap-3 mb-5">
        {Icon && (
          <div className="w-10 h-10 rounded-xl bg-gold-400/15 flex items-center justify-center flex-shrink-0">
            <Icon className="w-5 h-5 text-gold-400" />
          </div>
        )}
        <div>
          <h3 className="text-lg font-bold text-white">{title}</h3>
          {subtitle && <p className="text-sm text-navy-300 mt-1">{subtitle}</p>}
        </div>
      </div>
      {children}
    </motion.div>
  )
}

// ============ 工具函数 ============
function downloadAsFile(filename, content, ext) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}.${ext}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
