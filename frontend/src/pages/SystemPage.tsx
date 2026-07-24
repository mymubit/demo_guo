import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { formatApiError } from '@/services/errors'
import { getSystemConfig, putSystemConfig } from '@/services/v3/system'
import type {
  ScoringPreset,
  SystemConfigOverlay,
  TargetPlatform,
} from '@/types/v3/domain'

const SYSTEM_CONFIG_QUERY_KEY = ['v3', 'system', 'config'] as const

const PLATFORM_OPTIONS: { value: TargetPlatform; label: string }[] = [
  { value: 'generic', label: '通用' },
  { value: 'douyin', label: '抖音' },
  { value: 'kuaishou', label: '快手' },
  { value: 'wechat_miniprogram', label: '微信小程序' },
]

const SCORING_PRESET_OPTIONS: { value: ScoringPreset; label: string }[] = [
  { value: 'standard', label: '标准' },
  { value: 'strict', label: '严格' },
  { value: 'relaxed', label: '宽松' },
  { value: 'rhythm_first', label: '节奏优先' },
]

const PLATFORM_LABEL: Record<TargetPlatform, string> = Object.fromEntries(
  PLATFORM_OPTIONS.map((item) => [item.value, item.label]),
) as Record<TargetPlatform, string>

const SCORING_PRESET_LABEL: Record<ScoringPreset, string> = Object.fromEntries(
  SCORING_PRESET_OPTIONS.map((item) => [item.value, item.label]),
) as Record<ScoringPreset, string>

const selectClassName =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50'

function formatThreshold(value: number): string {
  return Number.isInteger(value) ? String(value) : String(value)
}

export function SystemPage() {
  const queryClient = useQueryClient()
  const [targetPlatform, setTargetPlatform] = useState<TargetPlatform>('generic')
  const [scoringPreset, setScoringPreset] = useState<ScoringPreset>('standard')
  const [thresholdInput, setThresholdInput] = useState('')
  const [costAlertInput, setCostAlertInput] = useState('')
  const [changeReason, setChangeReason] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const configQuery = useQuery({
    queryKey: SYSTEM_CONFIG_QUERY_KEY,
    queryFn: getSystemConfig,
  })

  const config = configQuery.data

  useEffect(() => {
    if (!config) return
    setTargetPlatform(config.effective.target_platform)
    setScoringPreset(config.effective.scoring_preset)
    setThresholdInput(
      config.overlay.quality_pass_threshold != null
        ? formatThreshold(config.overlay.quality_pass_threshold)
        : '',
    )
    setCostAlertInput(
      config.overlay.daily_cost_alert_cny != null
        ? formatThreshold(config.overlay.daily_cost_alert_cny)
        : '',
    )
    setChangeReason('')
    setFormError(null)
  }, [config])

  const saveMutation = useMutation({
    mutationFn: (body: Parameters<typeof putSystemConfig>[0]) => putSystemConfig(body),
    onSuccess: (next) => {
      queryClient.setQueryData(SYSTEM_CONFIG_QUERY_KEY, next)
      void queryClient.invalidateQueries({ queryKey: SYSTEM_CONFIG_QUERY_KEY })
    },
  })

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    setFormError(null)
    if (!config) return

    // 与后端 merge：未改动的键由服务端保留；阈值留空且原先无覆盖 → 省略；
    // 原先有覆盖且用户清空 → 显式 null 清除。
    const overlay: SystemConfigOverlay = {
      ...config.overlay,
      target_platform: targetPlatform,
      scoring_preset: scoringPreset,
    }

    const trimmedThreshold = thresholdInput.trim()
    const hadOverlayThreshold = config.overlay.quality_pass_threshold != null
    if (trimmedThreshold) {
      const parsed = Number(trimmedThreshold)
      if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) {
        setFormError('及格阈值须为 0–100 的数值')
        return
      }
      overlay.quality_pass_threshold = parsed
    } else if (hadOverlayThreshold) {
      overlay.quality_pass_threshold = null
    } else {
      delete overlay.quality_pass_threshold
    }

    const trimmedCostAlert = costAlertInput.trim()
    const hadCostAlert = config.overlay.daily_cost_alert_cny != null
    if (trimmedCostAlert) {
      const parsed = Number(trimmedCostAlert)
      if (!Number.isFinite(parsed) || parsed < 0) {
        setFormError('日费用预警阈值须为 ≥ 0 的数值')
        return
      }
      overlay.daily_cost_alert_cny = parsed
    } else if (hadCostAlert) {
      overlay.daily_cost_alert_cny = null
    } else {
      delete overlay.daily_cost_alert_cny
    }

    const reason = changeReason.trim()
    saveMutation.mutate({
      overlay,
      ...(reason ? { change_reason: reason } : {}),
    })
  }

  const busy = saveMutation.isPending
  const actionError = saveMutation.isError ? formatApiError(saveMutation.error) : null

  const actions = (
    <Button type="submit" form="system-config-form" loading={busy} disabled={busy || !config}>
      保存配置
    </Button>
  )

  return (
    <PageShell
      title="系统配置"
      description="管理工作空间平台、评分预设、及格阈值与日费用预警。"
      actions={actions}
    >
      {configQuery.isLoading ? (
        <p className="text-sm text-ink-muted">正在加载系统配置…</p>
      ) : null}

      {configQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(configQuery.error)}</p>
      ) : null}

      {formError ? <p className="mb-3 text-sm text-danger">{formError}</p> : null}
      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}

      {config ? (
        <div className="space-y-4">
          <section className="sf-panel space-y-2 p-4">
            <h2 className="text-sm font-semibold text-ink">当前生效配置</h2>
            <p className="text-sm text-ink">
              修订号：{config.revision}
            </p>
            <p className="text-sm text-ink-muted">
              目标平台：
              {config.effective.platform_label_zh ||
                PLATFORM_LABEL[config.effective.target_platform] ||
                config.effective.target_platform}
            </p>
            <p className="text-sm text-ink-muted">
              评分预设：
              {SCORING_PRESET_LABEL[config.effective.scoring_preset] ||
                config.effective.scoring_preset}
            </p>
            <p className="text-sm text-ink-muted">
              及格阈值：{formatThreshold(config.effective.pass_threshold)}
            </p>
            <p className="text-sm text-ink-muted">
              日费用预警阈值：
              {config.effective.daily_cost_alert_cny != null
                ? `${formatThreshold(config.effective.daily_cost_alert_cny)} 元`
                : '未设置'}
            </p>
          </section>

          <section className="sf-panel p-4">
            <form id="system-config-form" className="max-w-lg space-y-4" onSubmit={handleSubmit}>
              <h2 className="text-sm font-semibold text-ink">编辑覆盖项</h2>
              <label className="block space-y-1.5 text-sm font-medium text-ink">
                目标平台
                <select
                  value={targetPlatform}
                  onChange={(event) => setTargetPlatform(event.target.value as TargetPlatform)}
                  disabled={busy}
                  className={selectClassName}
                  aria-label="目标平台"
                >
                  {PLATFORM_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1.5 text-sm font-medium text-ink">
                评分预设
                <select
                  value={scoringPreset}
                  onChange={(event) => setScoringPreset(event.target.value as ScoringPreset)}
                  disabled={busy}
                  className={selectClassName}
                  aria-label="评分预设"
                >
                  {SCORING_PRESET_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1.5 text-sm font-medium text-ink">
                及格阈值（可选）
                <Input
                  type="number"
                  min={0}
                  max={100}
                  step="any"
                  value={thresholdInput}
                  onChange={(event) => setThresholdInput(event.target.value)}
                  placeholder={`默认 ${formatThreshold(config.effective.pass_threshold)}`}
                  disabled={busy}
                  aria-label="及格阈值"
                />
                <span className="block text-xs font-normal text-ink-faint">
                  留空：若原先无覆盖则不写入；若原先已有覆盖则清除，回退到评分预设默认阈值。
                </span>
              </label>
              <label className="block space-y-1.5 text-sm font-medium text-ink">
                日费用预警阈值（元）
                <Input
                  type="number"
                  min={0}
                  step="any"
                  value={costAlertInput}
                  onChange={(event) => setCostAlertInput(event.target.value)}
                  placeholder="留空表示关闭预警"
                  disabled={busy}
                  aria-label="日费用预警阈值（元）"
                />
                <span className="block text-xs font-normal text-ink-faint">
                  今日估算费用超过该阈值时，用量与仪表盘显示横幅提示；留空关闭。
                </span>
              </label>
              <label className="block space-y-1.5 text-sm font-medium text-ink">
                变更说明（可选）
                <Input
                  value={changeReason}
                  onChange={(event) => setChangeReason(event.target.value)}
                  placeholder="例如：对齐抖音节奏优先策略"
                  maxLength={500}
                  disabled={busy}
                  aria-label="变更说明"
                />
              </label>
            </form>
          </section>
        </div>
      ) : null}
    </PageShell>
  )
}
