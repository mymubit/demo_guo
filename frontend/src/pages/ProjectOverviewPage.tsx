import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { formatApiError } from '@/services/errors'
import { listArtifactVersions, rollbackArtifact } from '@/services/v3/artifacts'
import { archiveProject, deleteProject, getProject } from '@/services/v3/projects'
import type { RollbackArtifactKey } from '@/types/v3/domain'
import { ArchiveConfirmDialog } from './ArchiveConfirmDialog'
import { DeleteConfirmDialog } from './DeleteConfirmDialog'
import { ENTRY_LABEL, resolveOverviewStageCta, STAGE_LABEL } from './projectLabels'

const ROLLBACK_KEY_OPTIONS: { value: RollbackArtifactKey; label: string }[] = [
  { value: 'project_brief', label: '选题简报' },
  { value: 'story_bible', label: '故事圣经' },
  { value: 'character_system', label: '角色体系' },
  { value: 'world_system', label: '世界观' },
  { value: 'emotion_system', label: '情绪曲线' },
  { value: 'originality_report', label: '原创性报告' },
  { value: 'episode_plan', label: '分集规划' },
  { value: 'episode_scripts', label: '分集正文' },
]

const selectClassName =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50'

function statusLabel(status: string): string {
  if (status === 'committed') return '当前确认'
  if (status === 'superseded') return '历史版本'
  return status
}

export function ProjectOverviewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [archiveOpen, setArchiveOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [artifactKey, setArtifactKey] = useState<RollbackArtifactKey>('project_brief')
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null)

  const projectQuery = useQuery({
    queryKey: ['v3', 'project', id],
    queryFn: () => getProject(id!),
    enabled: Boolean(id),
  })

  const versionsQuery = useQuery({
    queryKey: ['v3', 'artifacts', id, artifactKey],
    queryFn: () => listArtifactVersions(id!, artifactKey),
    enabled: Boolean(id),
  })

  const archiveMutation = useMutation({
    mutationFn: () => archiveProject(id!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['v3', 'projects'] })
      void queryClient.invalidateQueries({ queryKey: ['v3', 'project', id] })
      setArchiveOpen(false)
      navigate('/dashboard')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteProject(id!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['v3', 'projects'] })
      setDeleteOpen(false)
      navigate('/dashboard')
    },
  })

  const rollbackMutation = useMutation({
    mutationFn: (sourceVersion: number) =>
      rollbackArtifact(id!, { artifact_key: artifactKey, source_version: sourceVersion }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['v3', 'artifacts', id, artifactKey] })
      void queryClient.invalidateQueries({ queryKey: ['v3', 'project', id] })
      setSelectedVersion(null)
    },
  })

  const project = projectQuery.data
  const title = project?.title ?? '项目设置'
  const progress =
    project?.progress_percent === undefined || project.progress_percent === null
      ? null
      : `${project.progress_percent}%`

  const stageCta = project ? resolveOverviewStageCta(project.id, project.stage) : null
  const versions = versionsQuery.data?.items ?? []

  const handleConfirmRollback = () => {
    if (selectedVersion == null) return
    const ok = window.confirm(
      `确认将「${ROLLBACK_KEY_OPTIONS.find((o) => o.value === artifactKey)?.label ?? artifactKey}」回滚到 v${selectedVersion}？将生成新的已确认版本。`,
    )
    if (!ok) return
    rollbackMutation.mutate(selectedVersion)
  }

  const headerActions = project ? (
    <>
      {!project.archived_at ? (
        <Button variant="secondary" onClick={() => setArchiveOpen(true)} disabled={archiveMutation.isPending}>
          归档项目
        </Button>
      ) : null}
      <Button
        variant="danger"
        onClick={() => setDeleteOpen(true)}
        disabled={deleteMutation.isPending}
      >
        删除项目
      </Button>
      <Link
        to={`/logs?project=${project.id}`}
        className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-surface px-4 text-sm font-medium text-ink hover:bg-canvas-muted"
      >
        执行日志
      </Link>
      {stageCta?.kind === 'link' ? (
        <Link
          to={stageCta.to}
          className="inline-flex h-9 items-center justify-center rounded-md border border-transparent bg-action px-4 text-sm font-medium text-white hover:bg-action-hover"
        >
          {stageCta.label}
        </Link>
      ) : null}
      {stageCta?.kind === 'placeholder' ? (
        <span
          className="inline-flex h-9 cursor-not-allowed items-center justify-center rounded-md border border-border bg-canvas-muted px-4 text-sm font-medium text-ink-faint"
          aria-disabled="true"
        >
          {stageCta.label}
        </span>
      ) : null}
    </>
  ) : null

  return (
    <PageShell
      title={title}
      description="项目设置：归档、删除、产物回滚；创作请从左侧阶段进入。"
      actions={headerActions}
    >
      {projectQuery.isLoading ? <p className="text-sm text-ink-muted">正在加载项目…</p> : null}

      {projectQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(projectQuery.error)}</p>
      ) : null}

      {project ? (
        <div className="space-y-4">
          <div className="sf-panel space-y-3 p-4">
            <dl className="grid gap-3 sm:grid-cols-3">
              <div>
                <dt className="text-xs text-ink-faint">创作来源</dt>
                <dd className="mt-1 text-sm text-ink">{ENTRY_LABEL[project.entry_type]}</dd>
              </div>
              <div>
                <dt className="text-xs text-ink-faint">当前阶段</dt>
                <dd className="mt-1 text-sm text-ink">{STAGE_LABEL[project.stage]}</dd>
              </div>
              <div>
                <dt className="text-xs text-ink-faint">进度</dt>
                <dd className="mt-1 text-sm text-ink">{progress ?? '—'}</dd>
              </div>
            </dl>
            {project.archived_at ? <p className="text-sm text-ink-muted">该项目已归档。</p> : null}
          </div>

          <section className="sf-panel space-y-3 p-4" aria-labelledby="rollback-heading">
            <div>
              <h2 id="rollback-heading" className="text-sm font-medium text-ink">
                版本回滚
              </h2>
              <p className="mt-1 text-xs text-ink-faint">
                选择主链产物与历史版本，确认后复制为新的已确认版本。
              </p>
            </div>

            <label className="block space-y-1">
              <span className="text-xs text-ink-faint">产物类型</span>
              <select
                className={selectClassName}
                value={artifactKey}
                onChange={(event) => {
                  setArtifactKey(event.target.value as RollbackArtifactKey)
                  setSelectedVersion(null)
                  rollbackMutation.reset()
                }}
                aria-label="产物类型"
              >
                {ROLLBACK_KEY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            {versionsQuery.isLoading ? (
              <p className="text-sm text-ink-muted">正在加载版本列表…</p>
            ) : null}
            {versionsQuery.isError ? (
              <p className="text-sm text-danger">{formatApiError(versionsQuery.error)}</p>
            ) : null}

            {!versionsQuery.isLoading && !versionsQuery.isError && versions.length === 0 ? (
              <p className="text-sm text-ink-muted">暂无可回滚的已确认版本。</p>
            ) : null}

            {versions.length > 0 ? (
              <ul className="space-y-2" aria-label="版本列表">
                {versions.map((row) => (
                  <li key={row.id}>
                    <label className="flex cursor-pointer items-center gap-3 rounded-md border border-border px-3 py-2 text-sm">
                      <input
                        type="radio"
                        name="rollback-version"
                        value={row.version}
                        checked={selectedVersion === row.version}
                        onChange={() => setSelectedVersion(row.version)}
                      />
                      <span className="text-ink">
                        v{row.version}
                        <span className="ml-2 text-ink-faint">{statusLabel(row.status)}</span>
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            ) : null}

            {rollbackMutation.isError ? (
              <p className="text-sm text-danger">{formatApiError(rollbackMutation.error)}</p>
            ) : null}
            {rollbackMutation.isSuccess ? (
              <p className="text-sm text-ink-muted">
                已回滚为新版本 v{rollbackMutation.data.version}。
              </p>
            ) : null}

            <Button
              variant="secondary"
              onClick={handleConfirmRollback}
              disabled={selectedVersion == null || rollbackMutation.isPending}
            >
              {rollbackMutation.isPending ? '回滚中…' : '确认回滚'}
            </Button>
          </section>
        </div>
      ) : null}

      <ArchiveConfirmDialog
        open={archiveOpen}
        busy={archiveMutation.isPending}
        projectTitle={project?.title}
        errorMessage={archiveMutation.isError ? formatApiError(archiveMutation.error) : null}
        onOpenChange={(open) => {
          setArchiveOpen(open)
          if (!open) archiveMutation.reset()
        }}
        onConfirm={() => archiveMutation.mutate()}
      />

      <DeleteConfirmDialog
        open={deleteOpen}
        busy={deleteMutation.isPending}
        projectTitle={project?.title}
        errorMessage={deleteMutation.isError ? formatApiError(deleteMutation.error) : null}
        onOpenChange={(open) => {
          setDeleteOpen(open)
          if (!open) deleteMutation.reset()
        }}
        onConfirm={() => deleteMutation.mutate()}
      />
    </PageShell>
  )
}
