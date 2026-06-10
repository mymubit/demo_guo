import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Settings2,
  Sparkles,
  Palette,
  Zap,
  Save,
  Plus,
  Pencil,
  Trash2,
  Film,
  Search,
  BookOpen,
  Tag,
  Check,
  AlertTriangle,
  Gauge,
  Bot,
  KeyRound,
  Database,
  Layers,
} from 'lucide-react'
import { adminApi } from '@/services/api'

export default function SkillConfig() {
  const [activeTab, setActiveTab] = useState('configs')
  const [message, setMessage] = useState(null)

  function showMessage(text, type = 'success') {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 3000)
  }

  return (
    <div className="space-y-6">
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`px-5 py-4 rounded-2xl flex items-center gap-3 ${
            message.type === 'success'
              ? 'bg-green-500/10 border border-green-500/30 text-green-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}
        >
          <Check className="w-5 h-5" />
          {message.text}
        </motion.div>
      )}

      <div>
        <h1 className="text-2xl font-bold text-white mb-1">技能配置</h1>
        <p className="text-navy-300 text-sm">管理 AI 创作技能、题材模板库与钩子库</p>
      </div>

      <div className="flex gap-2 p-1 glass-card rounded-2xl w-fit">
        {[
          { key: 'configs', label: '技能参数', icon: Settings2 },
          { key: 'themes', label: '题材模板', icon: Palette },
          { key: 'hooks', label: '钩子库管理', icon: Zap },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab.key
                ? 'bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 shadow-lg shadow-gold-500/30'
                : 'text-navy-200 hover:bg-navy-800/50'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'configs' && <ConfigList onMessage={showMessage} />}
      {activeTab === 'themes' && <ThemeList onMessage={showMessage} />}
      {activeTab === 'hooks' && <HookLibrary onMessage={showMessage} />}
    </div>
  )
}

// ============ 技能配置列表 ============
function ConfigList({ onMessage }) {
  const [configs, setConfigs] = useState([
    { key: 'ai.model', value: 'gpt-4-turbo', label: '默认AI模型', description: '用于主要内容生成的基础模型', type: 'select', options: ['gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo', 'claude-sonnet'], category: '模型' },
    { key: 'ai.temperature', value: '0.7', label: '生成温度', description: '控制内容创造性，0为保守，1为创意', type: 'number', min: 0, max: 1, step: 0.1, category: '模型' },
    { key: 'ai.max_tokens', value: '4096', label: '最大Token数', description: '单次生成最大Token数量限制', type: 'number', min: 512, max: 16384, step: 256, category: '模型' },
    { key: 'creation.max_daily', value: '50', label: '每日创作上限', description: '旗舰版用户每日最大创作次数', type: 'number', min: 1, max: 1000, category: '配额' },
    { key: 'creation.min_quality', value: '0.6', label: '最低质量阈值', description: '剧本自动审查通过的最低质量分', type: 'number', min: 0, max: 1, step: 0.05, category: '质量' },
    { key: 'format.episode_length', value: '1500', label: '单集字数', description: '标准单集剧本字数目标', type: 'number', min: 500, max: 5000, step: 100, category: '格式' },
    { key: 'api.timeout', value: '120', label: '请求超时', description: 'API请求超时时间（秒）', type: 'number', min: 10, max: 600, category: '系统' },
    { key: 'feature.beta_mode', value: 'false', label: '测试模式', description: '启用Beta阶段新功能', type: 'boolean', category: '功能' },
  ])
  const [editingKey, setEditingKey] = useState(null)
  const [editValue, setEditValue] = useState('')

  async function startEdit(config) {
    setEditingKey(config.key)
    setEditValue(String(config.value))
  }

  async function saveEdit(config) {
    try {
      await adminApi.updateSkillConfig(config.key, editValue)
    } catch (err) {
      // fall through
    }
    setConfigs((prev) =>
      prev.map((c) => (c.key === config.key ? { ...c, value: editValue } : c))
    )
    setEditingKey(null)
    onMessage(`已更新配置: ${config.label}`)
  }

  function cancelEdit() {
    setEditingKey(null)
    setEditValue('')
  }

  // 按类别分组
  const categories = [...new Set(configs.map((c) => c.category))]

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {categories.map((cat) => (
        <div key={cat} className="glass-card rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-navy-700/40 bg-navy-800/30 flex items-center gap-3">
            <Database className="w-5 h-5 text-gold-400" />
            <h3 className="text-lg font-bold text-white">{cat}</h3>
            <span className="text-xs text-navy-400">· {configs.filter((c) => c.category === cat).length} 项配置</span>
          </div>

          <div className="divide-y divide-navy-700/30">
            {configs
              .filter((c) => c.category === cat)
              .map((config, idx) => (
                <div key={config.key} className="px-6 py-4 flex items-start md:items-center justify-between gap-4 hover:bg-navy-800/20 transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h4 className="font-semibold text-white">{config.label}</h4>
                      <code className="text-xs text-navy-400 font-mono bg-navy-800/60 px-2 py-0.5 rounded">{config.key}</code>
                    </div>
                    <p className="text-sm text-navy-300">{config.description}</p>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {editingKey === config.key ? (
                      <>
                        {config.type === 'select' ? (
                          <select
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60"
                          >
                            {config.options.map((opt) => (
                              <option key={opt} value={opt}>{opt}</option>
                            ))}
                          </select>
                        ) : config.type === 'boolean' ? (
                          <select
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60"
                          >
                            <option value="true">true</option>
                            <option value="false">false</option>
                          </select>
                        ) : (
                          <input
                            type={config.type === 'number' ? 'number' : 'text'}
                            value={editValue}
                            min={config.min}
                            max={config.max}
                            step={config.step}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="w-32 px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60 text-right font-mono"
                          />
                        )}
                        <button
                          onClick={() => saveEdit(config)}
                          className="p-2 rounded-lg text-green-400 hover:bg-green-500/10 transition-colors"
                        >
                          <Save className="w-4 h-4" />
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="p-2 rounded-lg text-navy-400 hover:bg-navy-700/50 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </>
                    ) : (
                      <>
                        <span className="text-sm text-gold-400 font-mono px-3 py-1.5 bg-gold-500/10 rounded-lg border border-gold-500/20 min-w-[80px] text-center">
                          {String(config.value)}
                        </span>
                        <button
                          onClick={() => startEdit(config)}
                          className="p-2 rounded-lg text-navy-300 hover:bg-navy-700/50 hover:text-gold-400 transition-colors"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      ))}
    </motion.div>
  )
}

// ============ 题材模板 ============
function ThemeList({ onMessage }) {
  const [themes, setThemes] = useState([
    { id: 1, name: '豪门霸总', description: '霸道总裁与倔强女主的现代都市爱情故事', color: '#f6ad55', active: true, episode_count: 80, avg_ratings: 4.7, usage_count: 15200 },
    { id: 2, name: '家庭伦理复仇', description: '家庭恩怨与亲情纠葛的反转故事', color: '#ed64a6', active: true, episode_count: 80, avg_ratings: 4.5, usage_count: 12800 },
    { id: 3, name: '甜宠虐恋', description: '甜蜜与虐心交织的极致情感体验', color: '#9f7aea', active: true, episode_count: 80, avg_ratings: 4.8, usage_count: 18600 },
    { id: 4, name: '穿越重生', description: '跨越时空的命运改写', color: '#667eea', active: true, episode_count: 80, avg_ratings: 4.6, usage_count: 14300 },
    { id: 5, name: '都市逆袭', description: '小人物在大城市中的奋斗史', color: '#48bb78', active: true, episode_count: 80, avg_ratings: 4.4, usage_count: 9800 },
    { id: 6, name: '古装权谋', description: '宫斗与权谋的古代政治剧', color: '#d69e2e', active: true, episode_count: 80, avg_ratings: 4.5, usage_count: 11200 },
    { id: 7, name: '悬疑反转', description: '层层递进的推理与惊人反转', color: '#4fd1c5', active: true, episode_count: 80, avg_ratings: 4.7, usage_count: 13400 },
    { id: 8, name: '混合题材', description: '多种题材元素融合的创新故事', color: '#f687b3', active: false, episode_count: 80, avg_ratings: 4.3, usage_count: 5600 },
  ])

  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState({})

  function startEdit(theme) {
    setEditingId(theme.id)
    setForm({ ...theme })
  }

  function save() {
    setThemes((prev) =>
      prev.map((t) => (t.id === form.id ? { ...t, ...form } : t))
    )
    setEditingId(null)
    onMessage('题材模板已更新')
  }

  function toggleActive(theme) {
    setThemes((prev) =>
      prev.map((t) => (t.id === theme.id ? { ...t, active: !t.active } : t))
    )
    onMessage(`已${theme.active ? '禁用' : '启用'}题材: ${theme.name}`)
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {themes.map((theme) => (
        <div key={theme.id} className="glass-card rounded-2xl p-6 relative overflow-hidden">
          <div
            className="absolute top-0 right-0 w-32 h-32 rounded-full opacity-10"
            style={{ background: theme.color, transform: 'translate(50%, -50%)' }}
          />

          {editingId === theme.id ? (
            <div className="relative z-10 space-y-3">
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white font-bold focus:outline-none focus:border-gold-500/60"
              />
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60 resize-none"
              />
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-navy-400 mb-1">集数</label>
                  <input
                    type="number"
                    value={form.episode_count}
                    onChange={(e) => setForm({ ...form, episode_count: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60"
                  />
                </div>
                <div>
                  <label className="block text-xs text-navy-400 mb-1">颜色</label>
                  <input
                    type="color"
                    value={form.color}
                    onChange={(e) => setForm({ ...form, color: e.target.value })}
                    className="w-full h-10 rounded-lg bg-navy-800/60 border border-navy-700/40 cursor-pointer"
                  />
                </div>
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  onClick={save}
                  className="flex-1 py-2 rounded-lg bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold flex items-center justify-center gap-2"
                >
                  <Save className="w-4 h-4" /> 保存
                </button>
                <button
                  onClick={() => setEditingId(null)}
                  className="px-4 py-2 rounded-lg bg-navy-800/60 text-navy-200 text-sm"
                >
                  取消
                </button>
              </div>
            </div>
          ) : (
            <div className="relative z-10">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${theme.color}30` }}>
                    <Film className="w-5 h-5" style={{ color: theme.color }} />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">{theme.name}</h3>
                    <span className={`text-xs ${theme.active ? 'text-green-400' : 'text-navy-400'}`}>
                      {theme.active ? '● 已启用' : '○ 已停用'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => startEdit(theme)}
                    className="p-2 rounded-lg text-gold-400 hover:bg-gold-500/10 transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => toggleActive(theme)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      theme.active ? 'bg-green-500/10 text-green-400 hover:bg-green-500/20' : 'bg-navy-800/60 text-navy-300 hover:bg-navy-700/60'
                    }`}
                  >
                    {theme.active ? '禁用' : '启用'}
                  </button>
                </div>
              </div>

              <p className="text-sm text-navy-300 mb-4 leading-relaxed">{theme.description}</p>

              <div className="grid grid-cols-3 gap-2 pt-3 border-t border-navy-700/30">
                <div className="text-center">
                  <div className="text-lg font-bold text-white">{theme.episode_count}</div>
                  <div className="text-xs text-navy-400">集数</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-gold-400">{theme.avg_ratings}</div>
                  <div className="text-xs text-navy-400">平均分</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-purple-400">{(theme.usage_count / 1000).toFixed(1)}k</div>
                  <div className="text-xs text-navy-400">使用次数</div>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}

      {/* 添加新题材 */}
      <div className="glass-card rounded-2xl p-6 flex items-center justify-center border-2 border-dashed border-navy-700/40 hover:border-gold-500/40 transition-colors cursor-pointer hover:bg-navy-800/20">
        <div className="flex items-center gap-3 text-navy-300 hover:text-gold-400 transition-colors">
          <Plus className="w-5 h-5" />
          <span className="font-medium">添加新题材模板</span>
        </div>
      </div>
    </motion.div>
  )
}

// ============ 钩子库管理 ============
function HookLibrary({ onMessage }) {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')

  const [hooks, setHooks] = useState([
    { id: 1, title: '开局暴击型', category: '开篇', content: '在第1集前30秒内设置一个强烈的戏剧性冲突，让观众立刻进入情绪高潮', example: '女主在婚礼上被当众揭穿秘密，未婚夫当场悔婚', usage_count: 15820, strength: 95 },
    { id: 2, title: '误会悬念型', category: '情感', content: '制造一个主角间的重大误会，使观众持续期待真相大白', example: '男主隐瞒了自己的真实身份，但这并非出于恶意', usage_count: 12400, strength: 88 },
    { id: 3, title: '反差逆袭型', category: '节奏', content: '让看似弱小的角色在关键时刻爆发出惊人力量', example: '被家族轻视的私生子竟是最大财团继承人', usage_count: 18900, strength: 92 },
    { id: 4, title: '生死抉择型', category: '高潮', content: '在高潮处设置非此即彼的终极选择', example: '救爱人还是救女儿？两者只能选其一', usage_count: 9600, strength: 90 },
    { id: 5, title: '层层反转型', category: '结构', content: '每3集一个反转，不断推翻观众的预期', example: '反派是亲生父亲，主角是被收养的真正继承人', usage_count: 14500, strength: 93 },
    { id: 6, title: '甜虐交织型', category: '情感', content: '甜蜜与虐心按3:7比例交替，最大化情绪张力', example: '刚告白成功，女主就被诊断出绝症', usage_count: 16700, strength: 89 },
    { id: 7, title: '神秘铺垫型', category: '悬疑', content: '在前5集悄悄埋下多个伏笔，后5集集中揭露', example: '主角童年的记忆碎片其实是关键线索', usage_count: 11200, strength: 85 },
    { id: 8, title: '金手指开启型', category: '爽点', content: '在第2集结尾处为主角赋予一项特殊能力或身份', example: '濒死时获得了预知未来的能力', usage_count: 21300, strength: 91 },
  ])

  const categories = ['all', ...new Set(hooks.map((h) => h.category))]
  const filteredHooks = hooks.filter(
    (h) =>
      (category === 'all' || h.category === category) &&
      (search === '' || h.title.includes(search) || h.content.includes(search))
  )

  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState({})

  function startEdit(hook) {
    setEditingId(hook.id)
    setForm({ ...hook })
  }

  function save() {
    setHooks((prev) =>
      prev.map((h) => (h.id === form.id ? { ...h, ...form } : h))
    )
    setEditingId(null)
    onMessage('钩子已更新')
  }

  function deleteHook(id) {
    setHooks((prev) => prev.filter((h) => h.id !== id))
    onMessage('已删除钩子')
  }

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      {/* 搜索 + 筛选 */}
      <div className="glass-card rounded-2xl p-4 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索钩子标题或内容..."
            className="w-full pl-12 pr-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white placeholder:text-navy-500 focus:outline-none focus:border-gold-500/60"
          />
        </div>
        <div className="flex items-center gap-2">
          <Tag className="w-5 h-5 text-navy-400" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                category === cat
                  ? 'bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950'
                  : 'bg-navy-800/60 text-navy-200 hover:bg-navy-700/60'
              }`}
            >
              {cat === 'all' ? '全部' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* 统计 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: '总钩子数', value: hooks.length, icon: BookOpen, color: '#667eea' },
          { label: '累计使用', value: `${(hooks.reduce((a, b) => a + b.usage_count, 0) / 1000).toFixed(1)}k`, icon: Sparkles, color: '#f6ad55' },
          { label: '分类数', value: categories.length - 1, icon: Layers, color: '#48bb78' },
          { label: '平均强度', value: `${Math.round(hooks.reduce((a, b) => a + b.strength, 0) / hooks.length)}分`, icon: Gauge, color: '#9f7aea' },
        ].map((stat, idx) => (
          <div key={idx} className="glass-card rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${stat.color}20` }}>
              <stat.icon className="w-5 h-5" style={{ color: stat.color }} />
            </div>
            <div>
              <div className="text-xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-navy-400">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* 钩子列表 */}
      <div className="space-y-3">
        {filteredHooks.map((hook) => (
          <div key={hook.id} className="glass-card rounded-2xl p-5">
            {editingId === hook.id ? (
              <div className="space-y-3">
                <div className="flex gap-3">
                  <input
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    placeholder="钩子标题"
                    className="flex-1 px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white font-bold focus:outline-none focus:border-gold-500/60"
                  />
                  <select
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    className="px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60"
                  >
                    {categories.filter((c) => c !== 'all').map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <textarea
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  rows={2}
                  placeholder="钩子描述"
                  className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60 resize-none"
                />
                <textarea
                  value={form.example}
                  onChange={(e) => setForm({ ...form, example: e.target.value })}
                  rows={2}
                  placeholder="示例场景"
                  className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60 resize-none"
                />
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-navy-400 mb-1">强度分数 (0-100)</label>
                    <input
                      type="number"
                      value={form.strength}
                      min={0}
                      max={100}
                      onChange={(e) => setForm({ ...form, strength: Number(e.target.value) })}
                      className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm focus:outline-none focus:border-gold-500/60"
                    />
                  </div>
                  <div className="flex items-end gap-2">
                    <button
                      onClick={save}
                      className="flex-1 py-2 rounded-lg bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold flex items-center justify-center gap-2"
                    >
                      <Save className="w-4 h-4" /> 保存
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-4 py-2 rounded-lg bg-navy-800/60 text-navy-200 text-sm"
                    >
                      取消
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-bold text-white">{hook.title}</h3>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30">
                      {hook.category}
                    </span>
                    <div className="flex items-center gap-1 text-xs">
                      <Gauge className="w-3 h-3 text-gold-400" />
                      <span className="text-gold-400 font-semibold">{hook.strength}分</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => startEdit(hook)}
                      className="p-2 rounded-lg text-gold-400 hover:bg-gold-500/10 transition-colors"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteHook(hook.id)}
                      className="p-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <p className="text-sm text-navy-200 mb-3 leading-relaxed">{hook.content}</p>

                <div className="p-3 rounded-xl bg-navy-800/40 border border-navy-700/30 mb-3">
                  <div className="text-xs text-navy-400 mb-1">📝 示例场景</div>
                  <p className="text-sm text-navy-200 italic">"{hook.example}"</p>
                </div>

                <div className="text-xs text-navy-400">
                  使用次数: <span className="text-white font-medium">{hook.usage_count.toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>
        ))}

        {filteredHooks.length === 0 && (
          <div className="glass-card rounded-2xl p-12 text-center text-navy-400">
            <Search className="w-12 h-12 mx-auto mb-3 text-navy-500" />
            <div>没有匹配的钩子，尝试调整搜索或筛选条件</div>
          </div>
        )}

        {/* 添加新钩子 */}
        <button className="w-full glass-card rounded-2xl p-5 flex items-center justify-center border-2 border-dashed border-navy-700/40 hover:border-gold-500/40 transition-colors hover:bg-navy-800/20">
          <div className="flex items-center gap-3 text-navy-300 hover:text-gold-400 transition-colors">
            <Plus className="w-5 h-5" />
            <span className="font-medium">添加新钩子</span>
          </div>
        </button>
      </div>
    </motion.div>
  )
}
