import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { ArtifactPreview } from '@/components/ArtifactPreview'
import { Button } from '@/components/ui/Button'
import {
  isStageRunInProgress,
  StageStatusPanel,
} from '@/components/workflow/StageStatusPanel'
import { formatApiError } from '@/services/errors'
import { exportDeliveryDocx, getDeliveryState, prepareDelivery } from '@/services/v3/delivery'
import { STAGE_LABEL } from './projectLabels'

const COMPLEXITY_BAND_LABEL: Record<string, string> = {
  lean: '精简',
  standard: '标准',
  complex: '复杂',
}

type PackageSummary = {
  title: string
  complexityBand: string
  complexityBandLabel: string
  storyboardCount: number
  visualCount: number
  marketingCount: number
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return value as Record<string, unknown>
}

function arrayLength(value: unknown): number {
  return Array.isArray(value) ? value.length : 0
}

function complexityBandLabelZh(band: string): string {
  return COMPLEXITY_BAND_LABEL[band] || band || '未评估'
}

export function summarizePackagePayload(
  payload: Record<string, unknown> | null | undefined,
): PackageSummary | null {
  if (!payload) return null
  const title = String(payload.drama_title ?? '').trim() || '未命名短剧'
  const plan = asRecord(payload.production_plan)
  const band = String(plan?.complexity_band ?? '').trim()
  return {
    title,
    complexityBand: band,
    complexityBandLabel: complexityBandLabelZh(band),
    storyboardCount: arrayLength(payload.storyboard),
    visualCount: arrayLength(payload.visual_assets),
    marketingCount: arrayLength(payload.marketing_assets),
  }
}

function listSection(title: string, items: unknown): string {
  if (!Array.isArray(items) || items.length === 0) {
    return `## ${title}\n\n（空）\n`
  }
  const lines = items.map((item, index) => {
    if (typeof item === 'string' && item.trim()) return `- ${item.trim()}`
    if (item && typeof item === 'object' && !Array.isArray(item)) {
      const row = item as Record<string, unknown>
      const label =
        String(row.title ?? row.name ?? row.id ?? row.scene_id ?? '').trim() ||
        `条目 ${index + 1}`
      return `- ${label}`
    }
    return `- 条目 ${index + 1}`
  })
  return `## ${title}\n\n${lines.join('\n')}\n`
}

export function buildDeliveryMarkdown(payload: Record<string, unknown>): string {
  const summary = summarizePackagePayload(payload)
  const plan = asRecord(payload.production_plan)
  const checklist = asRecord(payload.release_checklist)
  const costDrivers = Array.isArray(plan?.cost_drivers)
    ? plan.cost_drivers.map(String).filter((item) => item.trim())
    : []
  const canRelease =
    typeof checklist?.can_release === 'boolean'
      ? checklist.can_release
        ? '可上架'
        : '暂不可上架'
      : '未评估'

  const parts = [
    `# ${summary?.title ?? '制作交付包'}`,
    '',
    `- 复杂度带：${summary?.complexityBandLabel ?? '未评估'}`,
    `- 分镜清单：${summary?.storyboardCount ?? 0} 条`,
    `- 视觉资产：${summary?.visualCount ?? 0} 条`,
    `- 营销资产：${summary?.marketingCount ?? 0} 条`,
    `- 上架状态：${canRelease}`,
    '',
    listSection('分镜清单', payload.storyboard),
    listSection('视觉资产', payload.visual_assets),
    listSection('营销资产', payload.marketing_assets),
    '## 制作计划',
    '',
    costDrivers.length > 0
      ? costDrivers.map((item) => `- ${item}`).join('\n')
      : '（无成本驱动说明）',
    '',
    '## 上架检查',
    '',
    `- 目标平台：${String(checklist?.target_platform ?? '未设置')}`,
    `- 阻断项：${arrayLength(checklist?.blocking_items)}`,
    `- 缺失材料：${arrayLength(checklist?.missing_materials)}`,
    '',
  ]
  return parts.join('\n')
}

export function downloadTextFile(filename: string, content: string, mimeType: string): void {
  downloadBlob(filename, new Blob([content], { type: mimeType }))
}

export function downloadBlob(filename: string, blob: Blob): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function DeliveryPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const deliveryQuery = useQuery({
    queryKey: ['v3', 'delivery', id],
    queryFn: () => getDeliveryState(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const run = query.state.data?.latest_run
      return isStageRunInProgress(run) ? 2000 : false
    },
  })

  const delivery = deliveryQuery.data
  const packageSummary = useMemo(
    () => summarizePackagePayload(delivery?.package?.payload),
    [delivery?.package?.payload],
  )

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['v3', 'delivery', id] })
    void queryClient.invalidateQueries({ queryKey: ['v3', 'project', id] })
  }

  const prepareMutation = useMutation({
    mutationFn: () => prepareDelivery(id!),
    onSuccess: invalidate,
  })

  const exportDocxMutation = useMutation({
    mutationFn: () => exportDeliveryDocx(id!),
    onSuccess: (blob) => {
      const base =
        packageSummary?.title ||
        String(delivery?.package?.payload?.drama_title ?? '').trim() ||
        'script'
      downloadBlob(`${base}.docx`, blob)
    },
  })

  if (!id) {
    return (
      <PageShell title="交付中心" description="门禁通过后生成制作交付包，并下载 JSON / Markdown。">
        <p className="text-sm text-ink-muted">缺少项目信息。</p>
      </PageShell>
    )
  }

  const gatePassed = Boolean(delivery?.gate.passed)
  const blockers = delivery?.gate.blockers ?? []
  const latestRun = delivery?.latest_run ?? null
  const runBusy = isStageRunInProgress(latestRun) || prepareMutation.isPending
  const canPrepare = gatePassed && Boolean(delivery) && !runBusy
  const actionError = prepareMutation.isError ? formatApiError(prepareMutation.error) : null
  const exportError = exportDocxMutation.isError ? formatApiError(exportDocxMutation.error) : null

  const actions = (
    <>
      <Button
        type="button"
        loading={prepareMutation.isPending}
        disabled={!canPrepare}
        onClick={() => prepareMutation.mutate()}
      >
        生成交付包
      </Button>
    </>
  )

  return (
    <PageShell
      title="交付中心"
      description="门禁通过后生成制作交付包，并下载 JSON / Markdown。"
      actions={actions}
    >
      {deliveryQuery.isLoading ? (
        <p className="text-sm text-ink-muted">正在加载交付状态…</p>
      ) : null}

      {deliveryQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(deliveryQuery.error)}</p>
      ) : null}

      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}
      {exportError ? <p className="mb-3 text-sm text-danger">{exportError}</p> : null}

      {delivery && !deliveryQuery.isLoading ? (
        <div className="space-y-4">
          <StageStatusPanel
            run={latestRun}
            runTitle="交付任务"
            idleHint={
              gatePassed && !latestRun && !delivery.package
                ? '尚未生成交付包，点击「生成交付包」开始。'
                : undefined
            }
            prerequisite={
              !gatePassed
                ? {
                    message: '交付门禁未通过，请先完成质检与合规。',
                    to: `/projects/${id}/quality`,
                    linkLabel: '去质检中心',
                  }
                : null
            }
          >
            <p className="text-sm text-ink">
              当前阶段：{STAGE_LABEL[delivery.stage] ?? delivery.stage}
            </p>
            <p className="text-sm text-ink">
              交付门禁：{gatePassed ? '已通过' : '未通过'}
            </p>
            {!gatePassed ? (
              <div className="space-y-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-900">
                <p>请先处理以下阻断项后再生成交付包：</p>
                {blockers.length > 0 ? (
                  <ul className="list-disc space-y-1 pl-5">
                    {blockers.map((blocker) => (
                      <li key={blocker}>{blocker}</li>
                    ))}
                  </ul>
                ) : (
                  <p>门禁未通过，请先完成质检与合规。</p>
                )}
              </div>
            ) : (
              <p className="text-sm text-ink-muted">门禁已通过，可生成制作交付包。</p>
            )}
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <Button
                type="button"
                variant="secondary"
                loading={exportDocxMutation.isPending}
                disabled={!gatePassed || exportDocxMutation.isPending}
                onClick={() => exportDocxMutation.mutate()}
              >
                下载 Word
              </Button>
              <p className="text-xs text-ink-faint">PDF 请使用浏览器打印为 PDF</p>
            </div>
            {delivery.package ? (
              <p className="text-sm text-ink-muted">交付包已就绪。</p>
            ) : null}
          </StageStatusPanel>

          {delivery.package && packageSummary ? (
            <section className="sf-panel space-y-4 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-ink">制作交付包</h2>
                  <p className="mt-1 text-sm text-ink-muted">
                    版本 v{delivery.package.version} · 已提交
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() =>
                      downloadTextFile(
                        'production_package.json',
                        `${JSON.stringify(delivery.package!.payload, null, 2)}\n`,
                        'application/json;charset=utf-8',
                      )
                    }
                  >
                    下载 JSON
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() =>
                      downloadTextFile(
                        'delivery.md',
                        buildDeliveryMarkdown(delivery.package!.payload),
                        'text/markdown;charset=utf-8',
                      )
                    }
                  >
                    下载 Markdown
                  </Button>
                </div>
              </div>

              <dl className="grid gap-3 sm:grid-cols-3">
                <div>
                  <dt className="text-xs text-ink-faint">剧名</dt>
                  <dd className="mt-1 text-sm font-medium text-ink">{packageSummary.title}</dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-faint">复杂度带</dt>
                  <dd className="mt-1 text-sm font-medium text-ink">
                    {packageSummary.complexityBandLabel}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-ink-faint">清单条数</dt>
                  <dd className="mt-1 text-sm text-ink">
                    分镜 {packageSummary.storyboardCount} · 视觉 {packageSummary.visualCount} ·
                    营销 {packageSummary.marketingCount}
                  </dd>
                </div>
              </dl>
              <ArtifactPreview
                payload={delivery.package.payload}
                title="交付包内容"
              />
            </section>
          ) : null}
        </div>
      ) : null}
    </PageShell>
  )
}
