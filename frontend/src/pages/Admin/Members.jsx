import { motion } from 'framer-motion'
import { useState } from 'react'
import {
  Crown,
  Sparkles,
  Pencil,
  Save,
  Plus,
  X,
  Copy,
  Check,
  Ticket,
  Calendar,
  DollarSign,
  Clock,
  Settings2,
  KeyRound,
  Package,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Copy as CopyIcon,
} from 'lucide-react'

export default function MembersAdmin() {
  const [activeTab, setActiveTab] = useState('plans')
  const [message, setMessage] = useState(null)

  // ========== 套餐列表 ==========
  const [plans, setPlans] = useState([
    { id: 1, name: '体验版', price_month: 99, price_year: 999, credits_month: 3, credits_year: 36, features: '3次创作/月 · 8大题材 · Markdown导出', description: '体验AI剧本创作的魅力，适合个人尝鲜用户', color: '#667eea', sort_order: 1 },
    { id: 2, name: '专业版', price_month: 299, price_year: 2999, credits_month: 20, credits_year: 240, features: '20次创作/月 · 所有题材 · 4种格式变体', description: '最受欢迎套餐，适合定期产出的创作者和小型团队', color: '#f6ad55', sort_order: 2 },
    { id: 3, name: '旗舰版', price_month: 999, price_year: 9999, credits_month: -1, credits_year: -1, features: '无限次创作 · 定制模板 · 专属客服', description: '专业团队首选，适合制作团队和内容工作室', color: '#9f7aea', sort_order: 3 },
    { id: 4, name: '企业版', price_month: 2999, price_year: 29999, credits_month: -1, credits_year: -1, features: '独立部署 · 定制题材库 · API接入', description: '为大型企业和机构定制的企业级解决方案', color: '#48bb78', sort_order: 4 },
  ])

  const [editingPlan, setEditingPlan] = useState(null)
  const [planForm, setPlanForm] = useState({})

  function startEdit(plan) {
    setEditingPlan(plan.id)
    setPlanForm({ ...plan })
  }

  function cancelEdit() {
    setEditingPlan(null)
    setPlanForm({})
  }

  function savePlan() {
    setPlans((prev) =>
      prev.map((p) => (p.id === planForm.id ? { ...p, ...planForm } : p))
    )
    setEditingPlan(null)
    setPlanForm({})
    showMessage('套餐配置已保存')
  }

  // ========== 卡密管理 ==========
  const [generateForm, setGenerateForm] = useState({
    plan_id: 2,
    count: 5,
    duration_days: 30,
    prefix: 'SF',
  })
  const [codes, setCodes] = useState([
    { id: 1, code: 'SF-2026-0610-A1B2', plan: '专业版', duration: '30天', created_at: '2026-06-10 10:30:00', used: false, used_by: null },
    { id: 2, code: 'SF-2026-0610-C3D4', plan: '专业版', duration: '30天', created_at: '2026-06-10 10:30:00', used: true, used_by: '陈思远' },
    { id: 3, code: 'SF-2026-0610-E5F6', plan: '旗舰版', duration: '90天', created_at: '2026-06-09 15:20:00', used: false, used_by: null },
    { id: 4, code: 'SF-2026-0609-G7H8', plan: '体验版', duration: '7天', created_at: '2026-06-09 08:10:00', used: true, used_by: '林小雨' },
    { id: 5, code: 'SF-2026-0609-I9J0', plan: '专业版', duration: '30天', created_at: '2026-06-08 14:45:00', used: false, used_by: null },
    { id: 6, code: 'SF-2026-0608-K1L2', plan: '企业版', duration: '365天', created_at: '2026-06-08 09:00:00', used: false, used_by: null },
  ])
  const [copiedId, setCopiedId] = useState(null)

  function handleGenerate() {
    const newCodes = []
    for (let i = 0; i < generateForm.count; i++) {
      const rand = Math.random().toString(36).substring(2, 6).toUpperCase()
      newCodes.push({
        id: codes.length + i + 1,
        code: `${generateForm.prefix}-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${rand}`,
        plan: plans.find((p) => p.id === generateForm.plan_id)?.name || '专业版',
        duration: `${generateForm.duration_days}天`,
        created_at: new Date().toLocaleString('zh-CN'),
        used: false,
        used_by: null,
      })
    }
    setCodes((prev) => [...newCodes, ...prev])
    showMessage(`成功生成 ${generateForm.count} 个兑换码`)
  }

  function copyCode(code, id) {
    navigator.clipboard?.writeText(code)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  function showMessage(text, type = 'success') {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 3000)
  }

  return (
    <div className="space-y-6">
      {/* 消息提示 */}
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`px-5 py-4 rounded-2xl flex items-center gap-3 ${
            message.type === 'success' ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}
        >
          <Check className="w-5 h-5" />
          {message.text}
        </motion.div>
      )}

      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">会员配置</h1>
        <p className="text-navy-300 text-sm">管理会员套餐与兑换卡密系统</p>
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-2 p-1 glass-card rounded-2xl w-fit">
        {[
          { key: 'plans', label: '套餐列表', icon: Package },
          { key: 'codes', label: '卡密管理', icon: KeyRound },
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

      {/* 套餐列表 Tab */}
      {activeTab === 'plans' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          {plans
            .sort((a, b) => a.sort_order - b.sort_order)
            .map((plan) => (
              <div
                key={plan.id}
                className="glass-card rounded-2xl p-6 relative overflow-hidden"
              >
                <div
                  className="absolute top-0 right-0 w-32 h-32 rounded-full opacity-10"
                  style={{ background: plan.color, transform: 'translate(50%, -50%)' }}
                />

                {editingPlan === plan.id ? (
                  <div className="relative z-10 space-y-4">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${plan.color}30` }}>
                        <Crown className="w-5 h-5" style={{ color: plan.color }} />
                      </div>
                      <input
                        type="text"
                        value={planForm.name}
                        onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                        className="flex-1 px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-lg font-bold focus:outline-none focus:border-gold-500/60"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-navy-400 mb-1">月付价格 (¥)</label>
                        <input
                          type="number"
                          value={planForm.price_month}
                          onChange={(e) => setPlanForm({ ...planForm, price_month: Number(e.target.value) })}
                          className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-navy-400 mb-1">年付价格 (¥)</label>
                        <input
                          type="number"
                          value={planForm.price_year}
                          onChange={(e) => setPlanForm({ ...planForm, price_year: Number(e.target.value) })}
                          className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-navy-400 mb-1">每月创作次数 (-1=无限)</label>
                        <input
                          type="number"
                          value={planForm.credits_month}
                          onChange={(e) => setPlanForm({ ...planForm, credits_month: Number(e.target.value) })}
                          className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-navy-400 mb-1">每年创作次数</label>
                        <input
                          type="number"
                          value={planForm.credits_year}
                          onChange={(e) => setPlanForm({ ...planForm, credits_year: Number(e.target.value) })}
                          className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs text-navy-400 mb-1">套餐描述</label>
                      <input
                        type="text"
                        value={planForm.description}
                        onChange={(e) => setPlanForm({ ...planForm, description: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60 text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-xs text-navy-400 mb-1">功能亮点</label>
                      <input
                        type="text"
                        value={planForm.features}
                        onChange={(e) => setPlanForm({ ...planForm, features: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60 text-sm"
                      />
                    </div>

                    <div className="flex items-center gap-2 pt-2">
                      <button
                        onClick={savePlan}
                        className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 font-semibold text-sm flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-gold-500/30 transition-all"
                      >
                        <Save className="w-4 h-4" /> 保存
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="px-4 py-2.5 rounded-xl bg-navy-800/60 text-navy-200 text-sm hover:bg-navy-700/60"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="relative z-10">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${plan.color}30` }}>
                          <Crown className="w-5 h-5" style={{ color: plan.color }} />
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                          <p className="text-xs text-navy-400">{plan.description}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => startEdit(plan)}
                        className="p-2 rounded-lg text-gold-400 hover:bg-gold-500/10 transition-colors"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-3 mb-4">
                      <div className="p-3 rounded-xl bg-navy-800/40 border border-navy-700/30">
                        <div className="text-xs text-navy-400 mb-1">月付</div>
                        <div className="text-xl font-bold text-white">¥{plan.price_month}</div>
                      </div>
                      <div className="p-3 rounded-xl bg-navy-800/40 border border-navy-700/30">
                        <div className="text-xs text-navy-400 mb-1">年付</div>
                        <div className="text-xl font-bold text-gold-400">¥{plan.price_year}</div>
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-navy-800/40 border border-navy-700/30 mb-3">
                      <div className="text-xs text-navy-400 mb-1 flex items-center gap-1.5">
                        <Sparkles className="w-3 h-3" /> 功能包含
                      </div>
                      <div className="text-sm text-navy-200">{plan.features}</div>
                    </div>

                    <div className="text-xs text-navy-400 flex items-center gap-1.5">
                      <DollarSign className="w-3 h-3" />
                      每月创作: {plan.credits_month === -1 ? '无限次' : `${plan.credits_month} 次`}
                    </div>
                  </div>
                )}
              </div>
            ))}
        </motion.div>
      )}

      {/* 卡密管理 Tab */}
      {activeTab === 'codes' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          {/* 生成卡密 */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-3">
              <Plus className="w-5 h-5 text-gold-400" /> 生成新兑换码
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-5">
              <div>
                <label className="block text-sm text-navy-300 mb-2">套餐类型</label>
                <select
                  value={generateForm.plan_id}
                  onChange={(e) => setGenerateForm({ ...generateForm, plan_id: Number(e.target.value) })}
                  className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60"
                >
                  {plans.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-navy-300 mb-2">生成数量</label>
                <input
                  type="number"
                  value={generateForm.count}
                  onChange={(e) => setGenerateForm({ ...generateForm, count: Number(e.target.value) })}
                  min={1}
                  max={100}
                  className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60"
                />
              </div>
              <div>
                <label className="block text-sm text-navy-300 mb-2">有效期 (天)</label>
                <input
                  type="number"
                  value={generateForm.duration_days}
                  onChange={(e) => setGenerateForm({ ...generateForm, duration_days: Number(e.target.value) })}
                  className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60"
                />
              </div>
              <div>
                <label className="block text-sm text-navy-300 mb-2">前缀</label>
                <input
                  type="text"
                  value={generateForm.prefix}
                  onChange={(e) => setGenerateForm({ ...generateForm, prefix: e.target.value.toUpperCase() })}
                  className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60"
                />
              </div>
            </div>

            <button
              onClick={handleGenerate}
              className="py-3 px-8 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 font-semibold flex items-center gap-2 hover:shadow-lg hover:shadow-gold-500/30 transition-all"
            >
              <Ticket className="w-5 h-5" />
              生成 {generateForm.count} 个兑换码
            </button>
          </div>

          {/* 已生成卡密列表 */}
          <div className="glass-card rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-navy-700/40 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-3">
                <KeyRound className="w-5 h-5 text-gold-400" />
                已生成兑换码
              </h3>
              <div className="text-sm text-navy-400">共 {codes.length} 个 · 未使用 {codes.filter((c) => !c.used).length} 个</div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-navy-700/40 bg-navy-800/30">
                    <th className="text-left text-navy-300 font-medium py-4 px-6">兑换码</th>
                    <th className="text-left text-navy-300 font-medium py-4 px-6">套餐</th>
                    <th className="text-left text-navy-300 font-medium py-4 px-6">有效期</th>
                    <th className="text-left text-navy-300 font-medium py-4 px-6">生成时间</th>
                    <th className="text-left text-navy-300 font-medium py-4 px-6">使用状态</th>
                    <th className="text-left text-navy-300 font-medium py-4 px-6">使用者</th>
                    <th className="text-left text-navy-300 font-medium py-4 px-6">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {codes.map((c, idx) => (
                    <motion.tr
                      key={c.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: idx * 0.02 }}
                      className="border-b border-navy-700/30 hover:bg-navy-800/20 transition-colors"
                    >
                      <td className="py-4 px-6">
                        <code className="text-gold-400 font-mono text-sm">{c.code}</code>
                      </td>
                      <td className="py-4 px-6 text-navy-200">{c.plan}</td>
                      <td className="py-4 px-6 text-navy-200">{c.duration}</td>
                      <td className="py-4 px-6 text-navy-300">{c.created_at}</td>
                      <td className="py-4 px-6">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                          c.used
                            ? 'bg-navy-700/60 text-navy-300 border border-navy-700/40'
                            : 'bg-green-500/20 text-green-400 border border-green-500/30'
                        }`}>
                          {c.used ? <CheckCircle2 className="w-3 h-3 text-navy-400" /> : <Clock className="w-3 h-3" />}
                          {c.used ? '已使用' : '未使用'}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-navy-200">{c.used_by || '-'}</td>
                      <td className="py-4 px-6">
                        {!c.used && (
                          <button
                            onClick={() => copyCode(c.code, c.id)}
                            className="p-2 rounded-lg text-navy-300 hover:bg-navy-700/50 hover:text-gold-400 transition-colors"
                            title="复制"
                          >
                            {copiedId === c.id ? (
                              <Check className="w-4 h-4 text-green-400" />
                            ) : (
                              <CopyIcon className="w-4 h-4" />
                            )}
                          </button>
                        )}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
