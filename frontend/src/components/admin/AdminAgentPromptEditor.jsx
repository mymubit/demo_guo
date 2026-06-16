import { Save } from 'lucide-react'
import AdminAgentKindBadge from './AdminAgentKindBadge'
import { AdminBadge } from './AdminUI'

/**
 * 统一 Agent 编辑区：填表 Agent 与流水线步骤共用视觉结构。
 * 仅 UI 封装，保存逻辑由父组件传入。
 */
export default function AdminAgentPromptEditor({
  kind = 'form',
  title,
  subtitle,
  sourceBadge,
  displayName,
  onDisplayNameChange,
  displayNameHint,
  llmProviders = [],
  llmProviderId,
  onLlmProviderChange,
  coinCost,
  onCoinCostChange,
  currencyName = '创作币',
  showCoinCost = true,
  responseJson,
  onResponseJsonChange,
  isActive,
  onIsActiveChange,
  systemPrompt,
  onSystemPromptChange,
  userPromptTpl,
  onUserPromptTplChange,
  systemPromptFallback,
  onSystemPromptFallbackChange,
  showFallback = true,
  extraFields,
  dirty = false,
  saving = false,
  onSave,
  saveLabel = '保存',
}) {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3 pb-4 border-b border-white/5">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <AdminAgentKindBadge kind={kind} />
            {sourceBadge ? (
              <AdminBadge tone={sourceBadge === 'db' ? 'success' : 'default'}>
                {sourceBadge === 'db' ? '已入库' : '代码默认'}
              </AdminBadge>
            ) : null}
          </div>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          {subtitle ? <p className="text-xs font-mono text-navy-300 mt-1 truncate">{subtitle}</p> : null}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {onDisplayNameChange ? (
          <label className="block text-sm text-navy-300 md:col-span-2">
            <span className="text-navy-400 text-xs mb-1 block">展示名称</span>
            <input
              className="w-full max-w-md rounded-xl bg-slate-900 border border-white/5 px-3 py-2.5 text-white text-sm sf-focus-ring"
              value={displayName || ''}
              onChange={(e) => onDisplayNameChange(e.target.value)}
              placeholder="面向运营与 C 端展示"
            />
            {displayNameHint ? (
              <span className="text-xs text-navy-400 mt-1 block">{displayNameHint}</span>
            ) : null}
          </label>
        ) : null}

        {onLlmProviderChange ? (
          <label className="block text-sm text-navy-300">
            <span className="text-navy-400 text-xs mb-1 block">绑定大模型</span>
            <select
              className="w-full rounded-xl bg-slate-900 border border-white/5 px-3 py-2.5 text-white text-sm sf-focus-ring"
              value={llmProviderId || ''}
              onChange={(e) => onLlmProviderChange(e.target.value || null)}
            >
              <option value="">跟随全局默认</option>
              {llmProviders.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.name}
                  {provider.is_active ? '（全局默认）' : ''}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        {showCoinCost && onCoinCostChange ? (
          <label className="block text-sm text-navy-300">
            <span className="text-navy-400 text-xs mb-1 block">单次扣费（{currencyName}）</span>
            <input
              type="number"
              min={0}
              className="w-full max-w-xs rounded-xl bg-slate-900 border border-white/5 px-3 py-2.5 text-white text-sm sf-focus-ring"
              value={coinCost ?? 0}
              onChange={(e) => onCoinCostChange(e.target.value)}
            />
          </label>
        ) : null}
      </div>

      {(onResponseJsonChange || onIsActiveChange) && (
        <div className="flex flex-wrap gap-6 text-sm text-navy-200">
          {onResponseJsonChange ? (
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!!responseJson}
                onChange={(e) => onResponseJsonChange(e.target.checked)}
              />
              返回 JSON
            </label>
          ) : null}
          {onIsActiveChange ? (
            <label className="inline-flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!!isActive}
                onChange={(e) => onIsActiveChange(e.target.checked)}
              />
              启用
            </label>
          ) : null}
        </div>
      )}

      {extraFields}

      {onSystemPromptChange ? (
        <label className="block">
          <span className="text-xs text-navy-400 mb-1.5 block">System 提示词</span>
          <textarea
            className="w-full h-32 rounded-xl bg-slate-900 border border-white/5 px-3 py-2.5 text-white text-sm font-mono resize-y sf-focus-ring"
            value={systemPrompt || ''}
            onChange={(e) => onSystemPromptChange(e.target.value)}
          />
        </label>
      ) : null}

      {onUserPromptTplChange ? (
        <label className="block">
          <span className="text-xs text-navy-400 mb-1.5 block">User 模板</span>
          <textarea
            className="w-full h-28 rounded-xl bg-slate-900 border border-white/5 px-3 py-2.5 text-white text-sm font-mono resize-y sf-focus-ring"
            value={userPromptTpl || ''}
            onChange={(e) => onUserPromptTplChange(e.target.value)}
          />
        </label>
      ) : null}

      {showFallback && onSystemPromptFallbackChange ? (
        <label className="block">
          <span className="text-xs text-navy-400 mb-1.5 block">备用 System（JSON 失败降级，可选）</span>
          <textarea
            className="w-full h-20 rounded-xl bg-slate-900 border border-white/5 px-3 py-2.5 text-white text-sm font-mono resize-y sf-focus-ring"
            value={systemPromptFallback || ''}
            onChange={(e) => onSystemPromptFallbackChange(e.target.value)}
          />
        </label>
      ) : null}

      {onSave ? (
        <div className="flex items-center justify-between gap-3 pt-2 border-t border-white/5">
          <span className="text-xs text-navy-400">{dirty ? '有未保存修改' : '已同步'}</span>
          <button
            type="button"
            disabled={saving}
            onClick={onSave}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-50 sf-focus-ring"
          >
            <Save className="w-4 h-4" />
            {saving ? '保存中…' : saveLabel}
          </button>
        </div>
      ) : null}
    </div>
  )
}
