import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { FilterEmptyState } from '@/components/layout/FilterEmptyState'
import { PageShell } from '@/components/layout/PageShell'
import { MarkdownPreview } from '@/components/MarkdownPreview'
import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { formatApiError } from '@/services/errors'
import { getLogCall, getLogRun, listLogRuns } from '@/services/v3/logs'
import { listProjects } from '@/services/v3/projects'
import { PRODUCT_COMMAND_TYPES, type ProductCommandType } from '@/types/v3/commands'
import type {
  CommandRunStatus,
  CommandRunSummary,
  FailoverAttempt,
  FailoverAttemptStatus,
  LogCall,
  LogRun,
  ProjectSummary,
} from '@/types/v3/domain'
import { cn } from '@/utils/cn'

const RUNS_QUERY_KEY = ['v3', 'logs', 'runs'] as const
const PROJECTS_QUERY_KEY = ['v3', 'projects', 'list'] as const
const PAGE_SIZE = 20

/** 创作者日志页不展示无项目绑定的系统试连 */
const PROJECT_LOG_COMMAND_TYPES = PRODUCT_COMMAND_TYPES.filter(
  (type) => type !== 'test_model_provider',
)

function downloadJsonFile(filename: string, data: unknown): void {
  const blob = new Blob([`${JSON.stringify(data, null, 2)}\n`], {
    type: 'application/json',
  })
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

const RUN_STATUS_LABEL: Record<CommandRunStatus, string> = {
  queued: '排队中',
  running: '生成中',
  succeeded: '已完成',
  failed: '失败',
  unsupported: '暂不支持',
}

const COMMAND_TYPE_LABEL: Record<ProductCommandType, string> = {
  create_project: '创建项目',
  generate_topic_brief: '生成选题简报',
  confirm_topic_brief: '确认选题简报',
  generate_blueprint: '生成故事蓝图',
  confirm_blueprint: '确认故事蓝图',
  generate_episode_plan: '生成分集规划',
  confirm_episode_plan: '确认分集规划',
  revise_episode_plan: '局部修订分集',
  write_episode_batch: '分批写正文',
  confirm_script_candidate: '确认正文候选',
  score_quality: '质量评分',
  check_compliance: '合规审查',
  accept_findings: '接受质检问题',
  revise_from_findings: '按问题修订',
  prepare_delivery: '生成交付包',
  test_model_provider: '试连模型',
}

const STATUS_FILTER_OPTIONS: { value: '' | CommandRunStatus; label: string }[] = [
  { value: '', label: '全部状态' },
  { value: 'queued', label: RUN_STATUS_LABEL.queued },
  { value: 'running', label: RUN_STATUS_LABEL.running },
  { value: 'succeeded', label: RUN_STATUS_LABEL.succeeded },
  { value: 'failed', label: RUN_STATUS_LABEL.failed },
  { value: 'unsupported', label: RUN_STATUS_LABEL.unsupported },
]

const selectClassName =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50'

function isInternalCommandId(commandType: string): boolean {
  const value = commandType.trim()
  if (!value) return false
  if (value.startsWith('operation.') || value.includes('operation.')) return true
  if (/^[a-z][a-z0-9]*(-[a-z0-9]+)+$/.test(value)) return true
  return false
}

const REDACTED_TOKEN = '〔已隐藏〕'

function sanitizePromptForDisplay(text: string): string {
  if (!text) return text
  let next = text
  next = next.replace(/\boperation\.[a-z0-9][a-z0-9._-]*/gi, REDACTED_TOKEN)
  next = next.replace(
    /("recipe_id"\s*:\s*)"(?:[^"\\]|\\.)*"/gi,
    `$1"${REDACTED_TOKEN}"`,
  )
  next = next.replace(/\b[a-z][a-z0-9]*(?:-[a-z0-9]+)+\b/g, REDACTED_TOKEN)
  return next
}

function commandTypeLabel(commandType: string): string {
  if (commandType in COMMAND_TYPE_LABEL) {
    return COMMAND_TYPE_LABEL[commandType as ProductCommandType]
  }
  if (isInternalCommandId(commandType)) {
    return '未知命令'
  }
  return commandType
}

function advancedCommandIdentifier(commandType: string): string {
  if (commandType in COMMAND_TYPE_LABEL) {
    return commandType
  }
  if (isInternalCommandId(commandType)) {
    return '未知命令'
  }
  return commandType
}

function statusLabel(status: string): string {
  if (status in RUN_STATUS_LABEL) {
    return RUN_STATUS_LABEL[status as CommandRunStatus]
  }
  return status
}

const FAILOVER_STATUS_LABEL: Record<FailoverAttemptStatus, string> = {
  succeeded: '成功',
  failed_switchable: '可切换失败',
  failed_terminal: '终态失败',
  skipped: '跳过',
}

function failoverStatusLabel(status: string): string {
  if (status in FAILOVER_STATUS_LABEL) {
    return FAILOVER_STATUS_LABEL[status as FailoverAttemptStatus]
  }
  return status
}

function formatTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function FailoverAttemptsSection({ attempts }: { attempts: FailoverAttempt[] }) {
  if (attempts.length === 0) return null

  return (
    <section>
      <h3 className="text-sm font-semibold text-ink">切换尝试</h3>
      <ul className="mt-3 space-y-2">
        {attempts.map((attempt) => (
          <li key={attempt.id} className="rounded-md border border-border p-3">
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-medium">{attempt.provider_name || '未知供应商'}</span>
              <span className="text-xs text-ink-muted">
                {failoverStatusLabel(attempt.status)}
              </span>
              <span className="text-xs text-ink-muted">#{attempt.attempt_index}</span>
              <span className="text-xs text-ink-muted">{formatTime(attempt.created_at)}</span>
            </div>
            {attempt.error_code || attempt.error_message ? (
              <p className="mt-1 text-xs text-ink-muted">
                {[attempt.error_code, attempt.error_message].filter(Boolean).join(' · ')}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  )
}

function CallPromptPanel({ callId, preview }: { callId: string; preview: LogCall }) {
  const [expanded, setExpanded] = useState(false)
  const detailQuery = useQuery({
    queryKey: ['v3', 'logs', 'calls', callId],
    queryFn: () => getLogCall(callId),
    enabled: expanded,
  })

  const snapshot = detailQuery.data ?? preview

  return (
    <div className="mt-3 space-y-2 border-t border-border pt-3">
      <Button
        type="button"
        variant="secondary"
        size="sm"
        onClick={() => setExpanded((prev) => !prev)}
      >
        {expanded ? '收起提示与响应' : '展开提示与响应'}
      </Button>
      {expanded ? (
        <div className="space-y-3">
          {detailQuery.isLoading ? (
            <p className="text-xs text-ink-muted">正在加载完整快照…</p>
          ) : null}
          {detailQuery.isError ? (
            <p className="text-xs text-destructive">{formatApiError(detailQuery.error)}</p>
          ) : null}
          <PromptBlock title="系统提示" text={snapshot.system_prompt} />
          <PromptBlock title="用户提示" text={snapshot.user_prompt} asMarkdown />
          <PromptBlock title="模型响应" text={snapshot.response_text} />
          {snapshot.error_message ? (
            <PromptBlock title="错误信息" text={snapshot.error_message} />
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

function looksLikeJson(text: string): boolean {
  const trimmed = text.trim()
  return (
    (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
    (trimmed.startsWith('[') && trimmed.endsWith(']'))
  )
}

function PromptBlock({
  title,
  text,
  asMarkdown = false,
}: {
  title: string
  text: string
  asMarkdown?: boolean
}) {
  const display = sanitizePromptForDisplay(text || '')
  if (asMarkdown) {
    const content = !display
      ? '（空）'
      : looksLikeJson(display)
        ? `\`\`\`json\n${display}\n\`\`\``
        : display
    return (
      <div className="space-y-1">
        <div className="text-xs font-medium text-ink-muted">{title}</div>
        <MarkdownPreview
          data-testid="log-md-block"
          content={content}
          className="max-h-64 overflow-auto rounded-md border border-border bg-surface px-3 py-2 text-xs [&_pre]:whitespace-pre-wrap"
        />
      </div>
    )
  }
  return (
    <div className="space-y-1">
      <div className="text-xs font-medium text-ink-muted">{title}</div>
      <pre
        data-testid="log-mono-block"
        className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-surface px-3 py-2 font-mono text-xs text-ink"
      >
        {display || '（空）'}
      </pre>
    </div>
  )
}

function RunDetailDrawer({
  runId,
  open,
  onOpenChange,
}: {
  runId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [showCommandType, setShowCommandType] = useState(false)

  const detailQuery = useQuery({
    queryKey: ['v3', 'logs', 'runs', runId],
    queryFn: () => getLogRun(runId!),
    enabled: open && Boolean(runId),
  })

  const detail: LogRun | undefined = detailQuery.data

  const handleDownload = () => {
    if (!detail) return
    downloadJsonFile(`log-run-${detail.id}.json`, detail)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) setShowCommandType(false)
        onOpenChange(next)
      }}
    >
      <DialogContent
        className="fixed inset-y-0 right-0 left-auto top-0 flex h-full max-h-none w-full max-w-xl translate-x-0 translate-y-0 flex-col gap-0 overflow-y-auto rounded-none border-l sm:rounded-none data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right"
        aria-describedby={undefined}
      >
        <DialogHeader>
          <DialogTitle>
            {detail ? commandTypeLabel(detail.command_type) : '任务详情'}
          </DialogTitle>
          <DialogDescription>
            查看本项目命令执行结果与关联的模型调用记录。
          </DialogDescription>
        </DialogHeader>

        {detailQuery.isLoading ? (
          <p className="mt-4 text-sm text-ink-muted">正在加载详情…</p>
        ) : null}
        {detailQuery.isError ? (
          <p className="mt-4 text-sm text-destructive">{formatApiError(detailQuery.error)}</p>
        ) : null}

        {detail ? (
          <div className="mt-4 flex flex-1 flex-col gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-md border border-border px-2 py-0.5 text-xs">
                {statusLabel(detail.status)}
              </span>
              <span className="text-xs text-ink-muted">{formatTime(detail.created_at)}</span>
              <Button type="button" variant="secondary" size="sm" onClick={handleDownload}>
                下载 JSON
              </Button>
            </div>

            {detail.error_message ? (
              <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                {detail.error_message}
              </p>
            ) : null}

            <div>
              <button
                type="button"
                className="text-xs text-ink-muted underline-offset-2 hover:underline"
                onClick={() => setShowCommandType((prev) => !prev)}
              >
                {showCommandType ? '隐藏命令标识' : '高级：显示命令标识'}
              </button>
              {showCommandType ? (
                <p className="mt-1 font-mono text-xs text-ink-muted">
                  {advancedCommandIdentifier(detail.command_type)}
                </p>
              ) : null}
            </div>

            <FailoverAttemptsSection attempts={detail.failover_attempts ?? []} />

            <section>
              <h3 className="text-sm font-semibold text-ink">调用明细</h3>
              {detail.calls.length === 0 ? (
                <p className="mt-2 text-sm text-ink-muted">本次任务没有关联的模型调用。</p>
              ) : (
                <ul className="mt-3 space-y-3">
                  {detail.calls.map((call) => (
                    <li key={call.id} className="rounded-md border border-border p-3">
                      <div className="flex flex-wrap items-center gap-2 text-sm">
                        <span className="font-medium">
                          {call.model_label || call.model_name || '未知模型'}
                        </span>
                        {call.model_label &&
                        call.model_name &&
                        call.model_label !== call.model_name ? (
                          <span className="font-mono text-xs text-ink-muted">{call.model_name}</span>
                        ) : null}
                        <span className="text-xs text-ink-muted">
                          {call.status === 'success' ? '成功' : '错误'}
                        </span>
                        <span className="text-xs text-ink-muted">{call.latency_ms} ms</span>
                        {call.total_tokens != null ? (
                          <span className="text-xs text-ink-muted">{call.total_tokens} tokens</span>
                        ) : null}
                      </div>
                      <div className="mt-1 text-xs text-ink-muted">
                        角色：{call.role} · 用途：{call.purpose}
                      </div>
                      <CallPromptPanel callId={call.id} preview={call} />
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function ProjectPicker({
  projects,
  selectedId,
  onSelect,
}: {
  projects: ProjectSummary[]
  selectedId: string
  onSelect: (projectId: string) => void
}) {
  if (projects.length === 0) {
    return (
      <FilterEmptyState
        title="还没有项目"
        description="先新建项目并完成生成后，再回来查看该项目的执行与模型调用。"
        variant="inbox"
      />
    )
  }

  return (
    <aside className="sf-panel max-h-[70vh] overflow-y-auto p-2" aria-label="项目列表">
      <p className="px-3 py-2 text-xs font-medium text-ink-faint">选择项目</p>
      <ul className="space-y-1">
        {projects.map((project) => {
          const active = selectedId === project.id
          return (
            <li key={project.id}>
              <button
                type="button"
                data-testid={`logs-project-${project.id}`}
                className={cn(
                  'w-full rounded-md px-3 py-2 text-left text-sm transition',
                  active ? 'bg-action/10 text-action' : 'text-ink hover:bg-canvas-muted',
                )}
                onClick={() => onSelect(project.id)}
              >
                <span className="block font-medium">{project.title}</span>
                <span className="mt-0.5 block truncate text-xs text-ink-faint">
                  {project.stage}
                  {project.archived_at ? ' · 已归档' : ''}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}

export function LogsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialProject = (searchParams.get('project') || '').trim()
  const [projectId, setProjectId] = useState(initialProject)
  const [status, setStatus] = useState<'' | CommandRunStatus>('')
  const [commandType, setCommandType] = useState('')
  const [offset, setOffset] = useState(0)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)

  useEffect(() => {
    const fromUrl = (searchParams.get('project') || '').trim()
    if (fromUrl && fromUrl !== projectId) {
      setProjectId(fromUrl)
      setOffset(0)
      setSelectedRunId(null)
    }
  }, [searchParams, projectId])

  const projectsQuery = useQuery({
    queryKey: PROJECTS_QUERY_KEY,
    queryFn: () => listProjects(true),
  })

  const filters = useMemo(
    () => ({
      project_id: projectId,
      status: status || undefined,
      command_type: commandType || undefined,
      limit: PAGE_SIZE,
      offset,
    }),
    [projectId, status, commandType, offset],
  )

  const runsQuery = useQuery({
    queryKey: [...RUNS_QUERY_KEY, filters],
    queryFn: () => listLogRuns(filters),
    enabled: Boolean(projectId),
  })

  const items: CommandRunSummary[] = runsQuery.data?.items ?? []
  const total = runsQuery.data?.total ?? 0
  const canGoPrev = offset > 0
  const canGoNext = offset + PAGE_SIZE < total
  const pageStart = total === 0 ? 0 : offset + 1
  const pageEnd = offset + items.length

  const selectedProject = (projectsQuery.data ?? []).find((item) => item.id === projectId)

  const selectProject = (nextId: string) => {
    setProjectId(nextId)
    setOffset(0)
    setSelectedRunId(null)
    setSearchParams(nextId ? { project: nextId } : {})
  }

  const resetPaging = () => setOffset(0)

  return (
    <PageShell
      title="执行日志"
      description="按项目查看生成任务与模型调用；试连等系统动作请到模型配置页。"
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,16rem)_minmax(0,1fr)]">
        {projectsQuery.isLoading ? (
          <p className="text-sm text-ink-muted">正在加载项目…</p>
        ) : null}
        {projectsQuery.isError ? (
          <p className="text-sm text-destructive">{formatApiError(projectsQuery.error)}</p>
        ) : null}
        {projectsQuery.isSuccess ? (
          <ProjectPicker
            projects={projectsQuery.data}
            selectedId={projectId}
            onSelect={selectProject}
          />
        ) : (
          <div />
        )}

        <section className="space-y-4">
          {!projectId ? (
            <FilterEmptyState
              title="请先选择项目"
              description="执行日志按项目组织。左侧点选项目后，可查看该项目下的命令与 LLM 调用。"
              variant="filter"
            />
          ) : (
            <>
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold text-ink">
                    {selectedProject?.title ?? '项目任务'}
                  </h2>
                  <p className="mt-1 text-xs text-ink-faint">仅展示绑定到该项目的执行记录</p>
                </div>
                {selectedProject ? (
                  <Link
                    to={`/projects/${selectedProject.id}/settings`}
                    className="text-sm text-action underline-offset-2 hover:underline"
                  >
                    打开项目设置
                  </Link>
                ) : null}
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <label className="block space-y-1.5 text-sm font-medium text-ink">
                  状态
                  <select
                    className={selectClassName}
                    value={status}
                    onChange={(event) => {
                      setStatus(event.target.value as '' | CommandRunStatus)
                      resetPaging()
                    }}
                    aria-label="状态"
                  >
                    {STATUS_FILTER_OPTIONS.map((option) => (
                      <option key={option.value || 'all'} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block space-y-1.5 text-sm font-medium text-ink">
                  命令类型
                  <select
                    className={selectClassName}
                    value={commandType}
                    onChange={(event) => {
                      setCommandType(event.target.value)
                      resetPaging()
                    }}
                    aria-label="命令类型"
                  >
                    <option value="">全部命令</option>
                    {PROJECT_LOG_COMMAND_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {COMMAND_TYPE_LABEL[type]}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              {runsQuery.isLoading ? (
                <p className="text-sm text-ink-muted">正在加载执行记录…</p>
              ) : null}
              {runsQuery.isError ? (
                <p className="text-sm text-destructive">{formatApiError(runsQuery.error)}</p>
              ) : null}

              {!runsQuery.isLoading && !runsQuery.isError ? (
                items.length === 0 ? (
                  <p className="text-sm text-ink-muted">该项目暂无匹配的执行记录。</p>
                ) : (
                  <ul className="divide-y divide-border rounded-md border border-border bg-surface">
                    {items.map((run) => {
                      const title = commandTypeLabel(run.command_type)
                      return (
                        <li key={run.id}>
                          <button
                            type="button"
                            className="flex w-full flex-col gap-1 px-4 py-3 text-left hover:bg-muted/40 sm:flex-row sm:items-center sm:justify-between"
                            onClick={() => setSelectedRunId(run.id)}
                            aria-label={`${title} ${statusLabel(run.status)}`}
                          >
                            <div>
                              <div className="text-sm font-medium text-ink">{title}</div>
                              <div className="mt-0.5 text-xs text-ink-muted">
                                {formatTime(run.created_at)}
                              </div>
                            </div>
                            <span className="text-xs text-ink-muted">
                              {statusLabel(run.status)}
                            </span>
                          </button>
                        </li>
                      )
                    })}
                  </ul>
                )
              ) : null}

              {runsQuery.data?.total != null ? (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs text-ink-muted">
                    共 {total} 条
                    {total > 0 ? `（第 ${pageStart}–${pageEnd} 条）` : null}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      disabled={!canGoPrev || runsQuery.isFetching}
                      onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
                    >
                      上一页
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      disabled={!canGoNext || runsQuery.isFetching}
                      onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
                    >
                      下一页
                    </Button>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </section>
      </div>

      <RunDetailDrawer
        runId={selectedRunId}
        open={Boolean(selectedRunId)}
        onOpenChange={(open) => {
          if (!open) setSelectedRunId(null)
        }}
      />
    </PageShell>
  )
}
