import { useState } from 'react'
import { AlertTriangle, Rocket, RotateCcw, History, Eye } from 'lucide-react'
import { Badge } from '@/components/ui'
import { cn } from '@/utils/cn'
import { formatDateTime } from '@/utils/date'

const STATUS_TONE = {
  draft: 'default',
  active: 'success',
  gray: 'warning',
  deprecated: 'danger',
  archived: 'danger',
}

const STATUS_LABEL = {
  draft: '草稿',
  active: '已发布',
  gray: '灰度',
  deprecated: '已废弃',
  archived: '已归档',
}

function PackStatusBadge({ status }) {
  return (
    <Badge tone={STATUS_TONE[status] || 'default'} size="sm">
      {STATUS_LABEL[status] || status}
    </Badge>
  )
}

/**
 * 灰度控制面板
 *
 * 显示当前 active 工作流包的版本/状态/灰度权重等信息，
 * 支持灰度权重调整、灰度预览和回滚操作。
 */
export default function GrayScaleControlPanel({
  pack = null,
  loading = false,
  onGraySwitch,
  onRollback,
  onShowHistory,
  onPreview,
  message,
}) {
  const [grayWeight, setGrayWeight] = useState(pack?.gray_weight ?? 0)
  const [saving, setSaving] = useState(false)

  const currentPack = pack

  async function handleGraySwitch() {
    setSaving(true)
    try {
      await onGraySwitch?.({ gray_weight: grayWeight })
    } finally {
      setSaving(false)
    }
  }

  async function handleRollback() {
    setSaving(true)
    try {
      await onRollback?.()
    } finally {
      setSaving(false)
    }
  }

  if (!currentPack && !loading) {
    return (
      <div className="sf-console-panel p-4">
        <p className="text-sm text-navy-400">暂无活跃工作流包</p>
      </div>
    )
  }

  return (
    <div className="sf-console-panel p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-white">灰度控制</h3>
          <PackStatusBadge status={currentPack?.pack_status || 'draft'} />
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onShowHistory}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs border border-white/10 text-navy-300 hover:bg-white/[0.06]"
          >
            <History className="w-3.5 h-3.5" />
            历史版本
          </button>
        </div>
      </div>

      {/* 基础信息 */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-xs text-navy-400">版本</div>
          <div className="text-white font-mono mt-0.5">
            v{currentPack?.version || 1}
          </div>
        </div>
        <div>
          <div className="text-xs text-navy-400">灰度权重</div>
          <div className="text-white mt-0.5">{currentPack?.gray_weight ?? 0}%</div>
        </div>
        <div>
          <div className="text-xs text-navy-400">发布人</div>
          <div className="text-navy-200 mt-0.5">{currentPack?.published_by || '—'}</div>
        </div>
        <div>
          <div className="text-xs text-navy-400">发布时间</div>
          <div className="text-navy-300 mt-0.5">
            {currentPack?.published_at ? formatDateTime(currentPack.published_at) : '—'}
          </div>
        </div>
      </div>

      {/* 灰度调整 */}
      <div className="border-t border-white/5 pt-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-navy-400">灰度权重调整</span>
          <span className="text-sm text-white font-medium">{grayWeight}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={grayWeight}
          onChange={(e) => setGrayWeight(Number(e.target.value))}
          className="sf-control w-full"
        />
        <div className="flex justify-between text-xs text-navy-500 mt-1">
          <span>0%（全量）</span>
          <span>50%（均衡）</span>
          <span>100%（灰度）</span>
        </div>

        {grayWeight > 0 && (
          <div className="flex items-start gap-2 mt-3 rounded-lg border border-yellow-500/20 bg-yellow-500/10 p-3">
            <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-yellow-300">
              灰度发布后，按 user_id hash 命中的用户将使用新版本，其余继续使用当前版本。
            </p>
          </div>
        )}

        {grayWeight === 0 && (
          <div className="flex items-start gap-2 mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3">
            <AlertTriangle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-emerald-300">
              将直接全量发布，所有用户均可使用新版本。
            </p>
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex flex-wrap gap-2 border-t border-white/5 pt-4">
        <button
          type="button"
          disabled={saving}
          onClick={handleGraySwitch}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-300 text-sm hover:bg-emerald-500/30 disabled:opacity-50"
        >
          <Rocket className="w-4 h-4" />
          {saving ? '切换中…' : '确认灰度'}
        </button>
        <button
          type="button"
          disabled={saving}
          onClick={onPreview}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 text-sm text-navy-200 hover:bg-white/[0.06] disabled:opacity-40"
        >
          <Eye className="w-4 h-4" />
          灰度预览
        </button>
        <button
          type="button"
          disabled={saving}
          onClick={handleRollback}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-orange-500/20 text-orange-300 text-sm hover:bg-orange-500/20 disabled:opacity-40"
        >
          <RotateCcw className="w-4 h-4" />
          回滚到上一版本
        </button>
      </div>

      {message && (
        <p className={cn(
          'text-xs',
          message.type === 'error' ? 'text-red-400' : 'text-emerald-400'
        )}>
          {message.text}
        </p>
      )}
    </div>
  )
}
