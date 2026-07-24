import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { DimensionBars } from '@/components/quality/DimensionBars'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import {
  isStageRunInProgress,
  STAGE_RUN_STATUS_LABEL,
  StageStatusPanel,
} from '@/components/workflow/StageStatusPanel'
import { formatApiError } from '@/services/errors'
import {
  acceptFindings,
  checkCompliance,
  getQualityState,
  reviseFromFindings,
  scoreQuality,
} from '@/services/v3/quality'
import { confirmScriptCandidate, getScriptsState } from '@/services/v3/scripts'
import type { QualityFinding, QualityFindingSource } from '@/types/v3/domain'
import {
  complianceRiskTypeLabelZh,
  formatComplianceIssueZh,
} from '@/utils/reportLabels'
import { parseEpisodeNumber } from '@/utils/parseEpisodeHint'
import { resolveNextStageCta, STAGE_LABEL } from './projectLabels'

type IssueRow = {
  source: QualityFindingSource
  finding_key: string
  title: string
  detail: string
  severity: string
  kindLabel: string
  raw: unknown
}

function resolveIssueEpisode(row: IssueRow): number | null {
  return (
    parseEpisodeNumber(row.raw) ??
    parseEpisodeNumber(`${row.title} ${row.detail}`.trim())
  )
}

function buildEditorJumpPath(projectId: string, row: IssueRow): string {
  const params = new URLSearchParams()
  params.set('finding', row.finding_key)
  const episode = resolveIssueEpisode(row)
  if (episode != null) {
    params.set('episode', String(episode))
  }
  return `/projects/${projectId}/editor?${params.toString()}`
}

function firstNonEmptyField(
  row: Record<string, unknown>,
  fields: readonly string[],
): string | null {
  for (const field of fields) {
    const value = row[field]
    if (value != null && String(value).trim()) {
      return String(value).trim().slice(0, 128)
    }
  }
  return null
}

/** 与 delivery_gate._blocking_issue_key 对齐：finding_key → id → title → blocking:{index} */
function blockingIssueKey(item: unknown, index: number): string {
  if (item && typeof item === 'object' && !Array.isArray(item)) {
    const key = firstNonEmptyField(item as Record<string, unknown>, [
      'finding_key',
      'id',
      'title',
    ])
    if (key) return key
  }
  return `blocking:${index}`
}

/** 质量缺陷：finding_key → id → title → defect:{index} */
function qualityDefectKey(item: unknown, index: number): string {
  if (item && typeof item === 'object' && !Array.isArray(item)) {
    const key = firstNonEmptyField(item as Record<string, unknown>, [
      'finding_key',
      'id',
      'title',
    ])
    if (key) return key
  }
  return `defect:${index}`
}

/** 合规风险：finding_key → id → title → issue → risk:{index} */
function riskItemKey(item: unknown, index: number): string {
  if (item && typeof item === 'object' && !Array.isArray(item)) {
    const key = firstNonEmptyField(item as Record<string, unknown>, [
      'finding_key',
      'id',
      'title',
      'issue',
    ])
    if (key) return key
  }
  return `risk:${index}`
}

function defectTitle(item: unknown, index: number): { title: string; detail: string; severity: string } {
  if (typeof item === 'string') {
    const text = item.trim()
    return { title: text || `质量缺陷 ${index + 1}`, detail: '', severity: '' }
  }
  if (item && typeof item === 'object' && !Array.isArray(item)) {
    const row = item as Record<string, unknown>
    const title =
      String(row.title ?? row.name ?? row.issue ?? row.summary ?? '').trim() ||
      `质量缺陷 ${index + 1}`
    const detail = String(row.description ?? row.detail ?? row.suggestion ?? '').trim()
    const severity = String(row.severity ?? row.level ?? '').trim()
    return { title, detail, severity }
  }
  return { title: `质量缺陷 ${index + 1}`, detail: '', severity: '' }
}

function extractIssueRows(
  qualityPayload: Record<string, unknown> | null | undefined,
  compliancePayload: Record<string, unknown> | null | undefined,
): IssueRow[] {
  const rows: IssueRow[] = []

  const defects = qualityPayload?.defects
  if (Array.isArray(defects)) {
    defects.forEach((item, index) => {
      const { title, detail, severity } = defectTitle(item, index)
      rows.push({
        source: 'quality',
        finding_key: qualityDefectKey(item, index),
        title,
        detail,
        severity,
        kindLabel: '质量缺陷',
        raw: item,
      })
    })
  }

  const blocking = compliancePayload?.blocking_issues
  if (Array.isArray(blocking)) {
    blocking.forEach((item, index) => {
      const formatted = formatComplianceIssueZh(item)
      const severity =
        item && typeof item === 'object' && !Array.isArray(item)
          ? String(
              (item as Record<string, unknown>).severity ??
                (item as Record<string, unknown>).level ??
                'blocking',
            ).trim()
          : 'blocking'
      rows.push({
        source: 'compliance',
        finding_key: blockingIssueKey(item, index),
        title: formatted.title,
        detail: [formatted.detail, ...formatted.meta].filter(Boolean).join(' · '),
        severity,
        kindLabel: '合规阻断',
        raw: item,
      })
    })
  }

  const risks = compliancePayload?.risk_items
  if (Array.isArray(risks)) {
    risks.forEach((item, index) => {
      const formatted = formatComplianceIssueZh(item)
      let severity = ''
      if (item && typeof item === 'object' && !Array.isArray(item)) {
        const row = item as Record<string, unknown>
        severity = String(row.type ?? row.severity ?? row.level ?? '').trim()
      }
      rows.push({
        source: 'compliance',
        finding_key: riskItemKey(item, index),
        title: formatted.title,
        detail: [
          severity ? `等级 ${complianceRiskTypeLabelZh(severity)}` : '',
          formatted.detail,
          ...formatted.meta,
        ]
          .filter(Boolean)
          .join(' · '),
        severity,
        kindLabel: '合规风险',
        raw: item,
      })
    })
  }

  return rows
}

function findingStatusMap(findings: QualityFinding[]): Map<string, QualityFinding> {
  const map = new Map<string, QualityFinding>()
  for (const finding of findings) {
    map.set(`${finding.source}:${finding.finding_key}`, finding)
  }
  return map
}

function selectionKey(source: QualityFindingSource, findingKey: string): string {
  return `${source}:${findingKey}`
}

export function QualityPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedKeys, setSelectedKeys] = useState<string[]>([])

  const qualityQuery = useQuery({
    queryKey: ['v3', 'quality', id],
    queryFn: () => getQualityState(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const data = query.state.data
      if (isStageRunInProgress(data?.latest_quality_run) || isStageRunInProgress(data?.latest_compliance_run)) {
        return 2000
      }
      return false
    },
  })

  const scriptsQuery = useQuery({
    queryKey: ['v3', 'scripts', id],
    queryFn: () => getScriptsState(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const run = query.state.data?.latest_run
      return isStageRunInProgress(run) ? 2000 : false
    },
  })

  const quality = qualityQuery.data
  const scripts = scriptsQuery.data
  const hasCommittedScripts = Boolean(scripts?.committed)
  const hasScriptCandidate = Boolean(scripts?.candidate)

  const issueRows = useMemo(
    () =>
      extractIssueRows(
        quality?.quality_report?.payload,
        quality?.compliance_report?.payload,
      ),
    [quality?.quality_report?.payload, quality?.compliance_report?.payload],
  )

  const statusByKey = useMemo(
    () => findingStatusMap(quality?.findings ?? []),
    [quality?.findings],
  )

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['v3', 'quality', id] })
    void queryClient.invalidateQueries({ queryKey: ['v3', 'scripts', id] })
    void queryClient.invalidateQueries({ queryKey: ['v3', 'project', id] })
  }

  const scoreMutation = useMutation({
    mutationFn: () => scoreQuality(id!),
    onSuccess: invalidate,
  })

  const complianceMutation = useMutation({
    mutationFn: () => checkCompliance(id!),
    onSuccess: invalidate,
  })

  const acceptMutation = useMutation({
    mutationFn: () => {
      const findings = issueRows
        .filter((row) => selectedKeys.includes(selectionKey(row.source, row.finding_key)))
        .map((row) => ({
          source: row.source,
          finding_key: row.finding_key,
          title: row.title,
          severity: row.severity,
        }))
      return acceptFindings(id!, { findings })
    },
    onSuccess: () => {
      setSelectedKeys([])
      invalidate()
    },
  })

  const reviseMutation = useMutation({
    mutationFn: () => {
      const finding_keys = issueRows
        .filter((row) => selectedKeys.includes(selectionKey(row.source, row.finding_key)))
        .map((row) => row.finding_key)
      return reviseFromFindings(id!, { finding_keys })
    },
    onSuccess: () => {
      setSelectedKeys([])
      invalidate()
    },
  })

  const confirmMutation = useMutation({
    mutationFn: () => confirmScriptCandidate(id!, { use_drafts: false }),
    onSuccess: invalidate,
  })

  if (!id) {
    return (
      <PageShell title="质检中心" description="质量评分、合规审查与按问题修订。">
        <p className="text-sm text-ink-muted">缺少项目信息。</p>
      </PageShell>
    )
  }

  const qualityRun = quality?.latest_quality_run ?? null
  const complianceRun = quality?.latest_compliance_run ?? null
  const nextCta = id ? resolveNextStageCta(id, 'quality') : null
  const hasQualityReport = Boolean(quality?.quality_report)
  const runBusy =
    isStageRunInProgress(qualityRun) ||
    isStageRunInProgress(complianceRun) ||
    isStageRunInProgress(scripts?.latest_run) ||
    scoreMutation.isPending ||
    complianceMutation.isPending ||
    acceptMutation.isPending ||
    reviseMutation.isPending ||
    confirmMutation.isPending

  const canRunChecks = hasCommittedScripts && Boolean(quality) && !runBusy
  const canAccept = selectedKeys.length > 0 && !runBusy
  const canRevise = selectedKeys.length > 0 && hasCommittedScripts && !runBusy

  const qualityPayload = quality?.quality_report?.payload
  const grade =
    qualityPayload && typeof qualityPayload.grade === 'string' ? qualityPayload.grade : null
  const overallScore =
    qualityPayload && typeof qualityPayload.overall_score === 'number'
      ? qualityPayload.overall_score
      : null
  const verdict =
    qualityPayload && typeof qualityPayload.verdict === 'string' ? qualityPayload.verdict : null
  const complianceResult =
    quality?.compliance_report?.payload &&
    typeof quality.compliance_report.payload.overall_result === 'string'
      ? quality.compliance_report.payload.overall_result
      : null

  const actionError =
    scoreMutation.isError
      ? formatApiError(scoreMutation.error)
      : complianceMutation.isError
        ? formatApiError(complianceMutation.error)
        : acceptMutation.isError
          ? formatApiError(acceptMutation.error)
          : reviseMutation.isError
            ? formatApiError(reviseMutation.error)
            : confirmMutation.isError
              ? formatApiError(confirmMutation.error)
              : null

  const toggleSelected = (key: string) => {
    setSelectedKeys((prev) =>
      prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key],
    )
  }

  const actions = (
    <>
      <Button
        type="button"
        variant="secondary"
        loading={scoreMutation.isPending}
        disabled={!canRunChecks}
        onClick={() => scoreMutation.mutate()}
      >
        质量评分
      </Button>
      <Button
        type="button"
        variant="secondary"
        loading={complianceMutation.isPending}
        disabled={!canRunChecks}
        onClick={() => complianceMutation.mutate()}
      >
        合规审查
      </Button>
      <Button
        type="button"
        variant="secondary"
        onClick={() => navigate(`/reviews/new?project_id=${id}`)}
        data-testid="external-script-review-entry"
      >
        用外界剧本评分
      </Button>
      <Button
        type="button"
        variant="secondary"
        loading={acceptMutation.isPending}
        disabled={!canAccept}
        onClick={() => acceptMutation.mutate()}
      >
        接受已选问题
      </Button>
      <Button
        type="button"
        loading={reviseMutation.isPending}
        disabled={!canRevise}
        onClick={() => reviseMutation.mutate()}
      >
        按已选问题修订
      </Button>
    </>
  )

  return (
    <PageShell title="质检中心" description="质量评分、合规审查与按问题修订。" actions={actions}>
      {qualityQuery.isLoading || scriptsQuery.isLoading ? (
        <p className="text-sm text-ink-muted">正在加载质检状态…</p>
      ) : null}

      {qualityQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(qualityQuery.error)}</p>
      ) : null}

      {scriptsQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(scriptsQuery.error)}</p>
      ) : null}

      {actionError ? <p className="mb-3 text-sm text-danger">{actionError}</p> : null}

      {quality && !scriptsQuery.isLoading ? (
        <div className="space-y-4">
          <StageStatusPanel
            run={qualityRun}
            runTitle="质量任务"
            idleHint={
              hasCommittedScripts && !qualityRun && !complianceRun
                ? '尚未运行质检，点击「质量评分」或「合规审查」开始。'
                : undefined
            }
            prerequisite={
              !hasCommittedScripts
                ? {
                    message: '请先确认剧本正文后，再运行质量评分与合规审查。',
                    to: `/projects/${id}/editor`,
                    linkLabel: '去正文编辑',
                  }
                : null
            }
            nextStep={
              hasQualityReport && nextCta
                ? {
                    to: nextCta.to,
                    label: nextCta.label,
                    hint: '质检已完成，可进入交付阶段。',
                  }
                : null
            }
          >
            <p className="text-sm text-ink">
              当前阶段：{STAGE_LABEL[quality.stage] ?? quality.stage}
            </p>
            {quality.quality_is_stale || quality.compliance_is_stale ? (
              <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                {quality.quality_is_stale && quality.compliance_is_stale
                  ? '质量报告与合规报告已相对正文过期，请重新评分与审查。'
                  : quality.quality_is_stale
                    ? '质量报告已相对正文过期，请重新评分。'
                    : '合规报告已相对正文过期，请重新审查。'}
              </p>
            ) : null}
            {hasScriptCandidate ? (
              <div className="space-y-2 rounded-md border border-border bg-canvas-muted/40 px-3 py-3 text-sm">
                <p className="text-ink">修订已生成正文候选，请确认采用或前往编辑器细看。</p>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    size="sm"
                    loading={confirmMutation.isPending}
                    disabled={runBusy}
                    onClick={() => confirmMutation.mutate()}
                  >
                    确认修订候选
                  </Button>
                  <Link
                    to={`/projects/${id}/editor`}
                    className="inline-flex h-8 items-center justify-center rounded-md border border-border bg-surface px-3 text-sm font-medium text-ink hover:bg-canvas-muted"
                  >
                    去编辑器确认
                  </Link>
                </div>
              </div>
            ) : null}
            {complianceRun ? (
              <div className="space-y-1 text-sm">
                <p className="text-ink-muted">
                  合规任务：{STAGE_RUN_STATUS_LABEL[complianceRun.status] ?? complianceRun.status}
                  {isStageRunInProgress(complianceRun) ? '（自动刷新中…）' : ''}
                </p>
                {complianceRun.status === 'failed' && complianceRun.error_message ? (
                  <p className="text-danger">{complianceRun.error_message}</p>
                ) : null}
              </div>
            ) : null}
          </StageStatusPanel>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
            <section className="sf-panel space-y-5 p-4">
              <div className="flex flex-wrap items-end gap-6">
                <div>
                  <p className="text-xs text-ink-faint">等级</p>
                  <p className="mt-1 text-3xl font-semibold text-ink">{grade ?? '—'}</p>
                </div>
                <div>
                  <p className="text-xs text-ink-faint">综合评分</p>
                  <p className="mt-1 text-3xl font-semibold tabular-nums text-ink">
                    {overallScore == null ? '—' : Math.round(overallScore)}
                  </p>
                </div>
                <div className="space-y-1 text-sm text-ink-muted">
                  {verdict ? <p>质量结论：{verdict}</p> : null}
                  {complianceResult ? <p>合规结论：{complianceResult}</p> : null}
                </div>
              </div>
              <div>
                <h2 className="mb-3 text-sm font-semibold text-ink">十维评分</h2>
                {quality?.quality_report ? (
                  <DimensionBars dimensions={qualityPayload?.dimensions} />
                ) : (
                  <p className="text-sm text-ink-muted">尚未生成质量报告。</p>
                )}
              </div>
            </section>

            <aside className="sf-panel space-y-3 p-4">
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-sm font-semibold text-ink">问题列表</h2>
                {selectedKeys.length > 0 ? (
                  <span className="text-xs text-ink-faint">已选 {selectedKeys.length} 项</span>
                ) : null}
              </div>
              {issueRows.length === 0 ? (
                <p className="text-sm text-ink-muted">暂无质量缺陷或合规问题。</p>
              ) : (
                <ul className="space-y-3">
                  {issueRows.map((row) => {
                    const key = selectionKey(row.source, row.finding_key)
                    const persisted = statusByKey.get(key)
                    const isAccepted = persisted?.status === 'accepted'
                    return (
                      <li key={key} className="rounded-md border border-border px-3 py-3">
                        <label className="flex items-start gap-2">
                          <input
                            type="checkbox"
                            className="mt-1 h-4 w-4 rounded border-border"
                            checked={selectedKeys.includes(key)}
                            onChange={() => toggleSelected(key)}
                            aria-label={`选择问题：${row.title}`}
                          />
                          <div className="min-w-0 flex-1 space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-xs text-ink-faint">{row.kindLabel}</span>
                              {isAccepted ? (
                                <span className="text-xs text-emerald-700">已接受</span>
                              ) : (
                                <span className="text-xs text-amber-700">待处理</span>
                              )}
                            </div>
                            <p className="text-sm font-medium text-ink">{row.title}</p>
                            {row.detail ? (
                              <p className="text-xs leading-5 text-ink-muted">{row.detail}</p>
                            ) : null}
                            <Button
                              type="button"
                              size="sm"
                              variant="secondary"
                              onClick={() => navigate(buildEditorJumpPath(id, row))}
                              aria-label={`定位到正文：${row.title}`}
                            >
                              定位到正文
                            </Button>
                          </div>
                        </label>
                      </li>
                    )
                  })}
                </ul>
              )}
            </aside>
          </div>
        </div>
      ) : null}
    </PageShell>
  )
}
