import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { Tabs, ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
import { adminApi } from '@/services/admin'
import { ApiError, formatApiError } from '@/services/errors'
import type { OpsConfigOverlay } from '@/types/domain'

export function AdminConfigPage() {
  const qc = useQueryClient()
  const { definition } = useWorkbenchDefinition()
  const sections = definition.admin_sections
  const [sectionId, setSectionId] = useState<string>(sections[0]?.id ?? '')
  const [draft, setDraft] = useState<OpsConfigOverlay | null>(null)
  const [changeReason, setChangeReason] = useState('')
  const [rollbackTarget, setRollbackTarget] = useState('')
  const [conflict, setConflict] = useState<string | null>(null)

  const query = useQuery({
    queryKey: ['admin-config'],
    queryFn: () => adminApi.getConfig(),
  })

  useEffect(() => {
    if (query.data) setDraft(query.data)
  }, [query.data])

  useEffect(() => {
    if (sections.length && !sections.some((s) => s.id === sectionId)) {
      setSectionId(sections[0].id)
    }
  }, [sections, sectionId])

  const activeSection = sections.find((s) => s.id === sectionId) ?? sections[0]
  const overrideJson = useMemo(() => {
    if (!draft || !activeSection) return '{}'
    const value = draft.overrides[activeSection.source] ?? {}
    return JSON.stringify(value, null, 2)
  }, [draft, activeSection])

  const [editorText, setEditorText] = useState(overrideJson)
  useEffect(() => {
    setEditorText(overrideJson)
  }, [overrideJson])

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!draft) throw new Error('配置未加载')
      if (!activeSection) throw new Error('工作台定义未提供 admin_settings.sections')
      if (!changeReason.trim()) throw new Error('必须填写修改原因')
      let parsed: Record<string, unknown>
      try {
        parsed = JSON.parse(editorText) as Record<string, unknown>
      } catch {
        throw new Error('覆盖 JSON 解析失败')
      }
      const next: OpsConfigOverlay = {
        ...draft,
        overrides: {
          ...draft.overrides,
          [activeSection.source]: parsed,
        },
        audit: {
          ...draft.audit,
          change_reason: changeReason.trim(),
        },
      }
      return adminApi.updateConfig(next, draft.audit.revision)
    },
    onSuccess: (data) => {
      setConflict(null)
      setDraft(data)
      setChangeReason('')
      void qc.invalidateQueries({ queryKey: ['admin-config'] })
    },
    onError: (err) => {
      if (err instanceof ApiError && err.isOptimisticLock) {
        setConflict(formatApiError(err))
      }
    },
  })

  const rollbackMutation = useMutation({
    mutationFn: () => {
      if (!changeReason.trim()) throw new Error('回滚也必须填写修改原因')
      const target = Number(rollbackTarget)
      if (!Number.isFinite(target) || target < 1) throw new Error('请输入有效的 target_revision')
      return adminApi.rollback({
        target_revision: target,
        change_reason: changeReason.trim(),
      })
    },
    onSuccess: (data) => {
      setDraft(data)
      setChangeReason('')
      void qc.invalidateQueries({ queryKey: ['admin-config'] })
    },
  })

  if (query.isLoading) return <LoadingBlock />
  if (query.isError) {
    return (
      <div className="p-8">
        <ErrorBanner message={formatApiError(query.error)} onRetry={() => void query.refetch()} />
      </div>
    )
  }
  if (!draft) return null

  if (!sections.length || !activeSection) {
    return (
      <div className="p-8">
        <ErrorBanner message="工作台定义未提供 admin_settings.sections" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-ink">配置后台</h1>
        <p className="mt-1 text-sm text-ink-muted">
          {sections.length} 分区 overlay · 强制修改原因 · revision {draft.audit.revision} · skills{' '}
          {draft.skills_version}
        </p>
      </div>

      <Tabs
        items={sections.map((s) => ({ id: s.id, label: s.label_zh || s.id }))}
        value={sectionId}
        onChange={setSectionId}
      />

      <div className="mt-4 space-y-4">
        <div className="text-xs text-ink-muted">{activeSection.source}</div>

        {conflict ? (
          <div className="space-y-2">
            <ErrorBanner message={conflict} />
            <Button variant="secondary" size="sm" onClick={() => void query.refetch()}>
              重新加载
            </Button>
          </div>
        ) : null}

        {saveMutation.isError && !conflict ? (
          <ErrorBanner message={formatApiError(saveMutation.error)} />
        ) : null}
        {rollbackMutation.isError ? (
          <ErrorBanner message={formatApiError(rollbackMutation.error)} />
        ) : null}

        <textarea
          className="sf-control min-h-80 font-mono text-xs"
          value={editorText}
          onChange={(e) => setEditorText(e.target.value)}
          spellCheck={false}
        />

        <div>
          <label className="sf-label">修改原因（必填）</label>
          <input
            className="sf-control"
            value={changeReason}
            onChange={(e) => setChangeReason(e.target.value)}
            placeholder="说明本次变更目的与影响面"
            required
          />
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <Button loading={saveMutation.isPending} onClick={() => saveMutation.mutate()}>
            保存覆盖（新 revision）
          </Button>
          <div className="flex items-end gap-2">
            <div>
              <label className="sf-label">回滚到 revision</label>
              <input
                className="sf-control w-32"
                value={rollbackTarget}
                onChange={(e) => setRollbackTarget(e.target.value)}
                placeholder="e.g. 3"
              />
            </div>
            <Button
              variant="secondary"
              loading={rollbackMutation.isPending}
              onClick={() => rollbackMutation.mutate()}
            >
              执行回滚
            </Button>
          </div>
        </div>

        <p className="text-xs text-ink-muted">
          最近更新：{draft.audit.updated_by} · {draft.audit.updated_at} ·{' '}
          {draft.audit.change_reason}
        </p>
      </div>
    </div>
  )
}
