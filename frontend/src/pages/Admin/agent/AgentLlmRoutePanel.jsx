import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Save } from 'lucide-react'
import { admin } from '@/services/api'
import AdminMasterDetail, {
  AdminMasterDetailListButton,
  useAdminSelection,
} from '@/components/admin/AdminMasterDetail'
import { AdminPenetrationLink } from '@/components/admin/workbench/AdminWorkbenchKit'

const ROUTE_HINTS = {
  // drama.* 重组体系
  'drama.topic-director': '选题定调官 - 故事梗概+市场判断+爆款策略',
  'drama.character-relations': '人物关系官 - 人物小传+关系网+轻量世界规则',
  'drama.series-architect': '全剧架构官 - 六阶段结构+主支线+伏笔总表',
  'drama.episode-designer': '分集设计官 - 逐集钩子+爽点+反转+付费卡点',
  'drama.script-writer': '剧本正文官 - 正式剧本生成（最高Token）',
  'drama.revision-master': '剧本修订官 - 对白/格式/字数/分镜摘要返修',
  'drama.script-scorer': '剧本评分官 - 十维 G-Eval 独立评分',
  'drama.compliance-guard': '合规审查官 - P0/P1/P2合规检测',
  'drama.delivery-tool': '宣发交付工具 - 视觉+营销+交付检查',
  ai_field: '创作页 AI 字段生成',
}

export default function AgentLlmRoutePanel({ onMessage }) {
  const [loading, setLoading] = useState(true)
  const [savingKey, setSavingKey] = useState(null)
  const [rows, setRows] = useState([])
  const [llmProviders, setLlmProviders] = useState([])
  const [dirtyKeys, setDirtyKeys] = useState(() => new Set())
  const [selectedId, setSelectedId] = useAdminSelection(rows, (row) => row.route_key)

  function patchRow(routeKey, patch) {
    setRows((list) =>
      list.map((item) => (item.route_key === routeKey ? { ...item, ...patch } : item))
    )
    setDirtyKeys((prev) => new Set(prev).add(routeKey))
  }

  async function load() {
    setLoading(true)
    try {
      const [routes, llmRes] = await Promise.all([
        admin.listAgentLlmRoutes(),
        admin.getLlmConfig(),
      ])
      setRows(Array.isArray(routes) ? routes : [])
      setLlmProviders(Array.isArray(llmRes?.providers) ? llmRes.providers.filter((p) => p.is_enabled) : [])
      setDirtyKeys(new Set())
    } catch (err) {
      onMessage(err.message || '加载技能模型路由失败', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function saveRow(row) {
    if (!row) return
    setSavingKey(row.route_key)
    try {
      const payload = {
        route_key: row.route_key,
        display_name: row.display_name,
        max_tokens: row.max_tokens ? Number(row.max_tokens) : null,
        is_active: row.is_active !== false,
        sort_order: row.sort_order ?? 0,
        llm_provider_id: row.llm_provider_id || null,
      }
      if (row.id) {
        await admin.updateAgentLlmRoute(row.id, payload)
      } else {
        await admin.saveAgentLlmRoute(payload)
      }
      onMessage('技能模型路由已保存')
      setDirtyKeys((prev) => {
        const next = new Set(prev)
        next.delete(row.route_key)
        return next
      })
      await load()
    } catch (err) {
      onMessage(err.message || '保存失败', 'error')
    } finally {
      setSavingKey(null)
    }
  }

  async function seed() {
    try {
      await admin.seedAgentLlmRoutes()
      onMessage('已同步技能模型路由占位')
      await load()
    } catch (err) {
      onMessage(err.message || '同步失败', 'error')
    }
  }

  if (loading) {
    return (
      <div className="sf-console-panel p-8 text-center text-navy-400 mt-8">加载技能模型路由…</div>
    )
  }

  if (rows.length === 0) {
    return (
      <div className="sf-console-panel p-8 text-center space-y-4 mt-8">
        <p className="text-navy-400">暂无技能模型路由，请先同步占位。</p>
        <button
          type="button"
          onClick={seed}
          className="px-4 py-2 rounded-xl text-sm text-gold-400 border border-gold-500/30 hover:bg-gold-500/10"
        >
          同步技能路由占位
        </button>
      </div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4 mt-10">
      <div className="sf-console-panel p-5 border border-purple-500/15 bg-purple-500/5">
        <p className="text-sm text-navy-200 leading-relaxed">
          <span className="text-white font-medium">技能模型路由</span>
          ——主链与辅助技能的 Provider 与 Max Tokens 统一在此配置；流水线步骤不再绑定模型。
        </p>
      </div>

      <div className="flex items-center justify-end gap-3 flex-wrap">
        <button
          type="button"
          onClick={seed}
          className="px-4 py-2 rounded-xl text-sm text-gold-400 border border-gold-500/30 hover:bg-gold-500/10"
        >
          同步技能路由占位
        </button>
      </div>

      <AdminMasterDetail
        listTitle="技能路由"
        listHint="Provider + Max Tokens"
        detailTitle="路由配置"
        items={rows}
        selectedId={selectedId}
        onSelect={setSelectedId}
        getId={(row) => row.route_key}
        renderListItem={(row, { active, onSelect }) => (
          <AdminMasterDetailListButton
            key={row.route_key}
            active={active}
            onClick={onSelect}
            title={row.display_name || row.route_key}
            subtitle={row.route_key}
            meta={row.max_tokens ? `max ${row.max_tokens}` : '未设 Token'}
            dirty={dirtyKeys.has(row.route_key)}
          />
        )}
        renderDetail={(row) => (
          <div className="space-y-5">
            <div>
              <div className="text-lg font-semibold text-white">
                {row.display_name || row.route_key}
              </div>
              <div className="text-xs text-navy-400 mt-1">{ROUTE_HINTS[row.route_key] || row.route_key}</div>
            </div>

            <div className="flex flex-wrap gap-3 text-xs">
              <AdminPenetrationLink to="/admin/model" label="大模型配置" />
              <AdminPenetrationLink to="/admin/agent?tab=definitions" label="Agent 定义" />
              <AdminPenetrationLink to="/admin/agent?tab=runs" label="运行记录" />
            </div>

            <label className="block text-sm text-navy-300">
              Max Tokens
              <input
                type="number"
                min={256}
                step={256}
                className="sf-control mt-1 max-w-xs px-3 py-2 text-white text-sm"
                value={row.max_tokens ?? ''}
                onChange={(e) =>
                  patchRow(row.route_key, {
                    max_tokens: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
            </label>

            <label className="block text-sm text-navy-300">
              使用大模型
              <select
                className="sf-control mt-1 max-w-md"
                value={row.llm_provider_id || ''}
                onChange={(e) =>
                  patchRow(row.route_key, {
                    llm_provider_id: e.target.value || null,
                  })
                }
              >
                <option value="">跟随全局激活模型</option>
                {llmProviders.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                    {p.is_active ? '（当前全局）' : ''}
                  </option>
                ))}
              </select>
            </label>

            <div className="flex items-center justify-between gap-3 pt-1 border-t border-white/5">
              <span
                className={`text-xs ${
                  dirtyKeys.has(row.route_key) ? 'text-amber-300' : 'text-emerald-400/90'
                }`}
              >
                {dirtyKeys.has(row.route_key) ? '有未保存修改' : '已同步'}
              </span>
              <button
                type="button"
                disabled={!dirtyKeys.has(row.route_key) || savingKey === row.route_key}
                onClick={() => saveRow(rows.find((item) => item.route_key === row.route_key))}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4" />
                {savingKey === row.route_key ? '保存中…' : '保存路由'}
              </button>
            </div>
          </div>
        )}
      />
    </motion.div>
  )
}
