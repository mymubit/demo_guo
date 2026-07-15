import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { ThemeMatrixPicker } from '@/components/theme/ThemeMatrixPicker'
import { dramaApi } from '@/services/drama'
import { ApiError, formatApiError } from '@/services/errors'
import {
  isFieldRequired,
  readSettingValue,
  visibleGroups,
  writeSettingValue,
} from '@/utils/settingsForm'
import type { AdaptNotes, GenreMatrix, ProjectSettings } from '@/types/domain'
import type { SettingsFieldDef } from '@/types/workbench'
import type { ThemeMatrix } from '@/types/workbench'

export function ProjectSettingsPage() {
  const { projectId = '' } = useParams()
  const qc = useQueryClient()
  const [draft, setDraft] = useState<ProjectSettings | null>(null)
  const [conflict, setConflict] = useState<string | null>(null)
  const [policyHint, setPolicyHint] = useState<string | null>(null)

  const settingsQuery = useQuery({
    queryKey: ['settings', projectId],
    queryFn: () => dramaApi.getSettings(projectId),
    enabled: Boolean(projectId),
  })

  const matrixQuery = useQuery({
    queryKey: ['theme-matrix'],
    queryFn: () => dramaApi.getThemeMatrix(),
  })

  useEffect(() => {
    if (settingsQuery.data) setDraft(settingsQuery.data)
  }, [settingsQuery.data])

  const platformUnverified =
    Boolean(draft) &&
    draft!.target_platform !== 'generic' &&
    !draft!.platform_policy?.verified_at

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!draft) throw new Error('没有可保存的设置')
      if (
        draft.target_platform !== 'generic' &&
        !draft.platform_policy?.verified_at
      ) {
        throw new ApiError({
          code: 42203,
          httpStatus: 422,
          message:
            '目标平台政策尚未核验：非「通用」平台需先完成平台政策核验后再保存，否则服务端将返回 42203。',
        })
      }
      return dramaApi.updateSettings(projectId, draft, draft.audit.revision)
    },
    onSuccess: (data) => {
      setConflict(null)
      setPolicyHint(null)
      setDraft(data)
      void qc.invalidateQueries({ queryKey: ['settings', projectId] })
    },
    onError: (err) => {
      if (err instanceof ApiError && err.isOptimisticLock) {
        setConflict(formatApiError(err))
        setPolicyHint(null)
        return
      }
      if (err instanceof ApiError && err.isPlatformPolicyUnverified) {
        setPolicyHint(formatApiError(err))
        return
      }
      setPolicyHint(null)
    },
  })

  const groups = useMemo(() => (draft ? visibleGroups(draft) : []), [draft])

  if (settingsQuery.isLoading) return <LoadingBlock />
  if (settingsQuery.isError) {
    return (
      <div className="p-8">
        <ErrorBanner
          message={formatApiError(settingsQuery.error)}
          onRetry={() => void settingsQuery.refetch()}
        />
      </div>
    )
  }
  if (!draft) return null

  function patch(updater: (prev: ProjectSettings) => ProjectSettings) {
    setDraft((prev) => (prev ? updater(prev) : prev))
  }

  function updateField(field: SettingsFieldDef, value: unknown) {
    patch((prev) => writeSettingValue(prev, field, value))
  }

  return (
    <div className="mx-auto max-w-5xl px-8 py-8">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink">项目设置</h1>
          <p className="mt-1 text-sm text-ink-muted">
            契约驱动分组表单 · revision {draft.audit.revision}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to={`/projects/${projectId}/workbench`}>
            <Button variant="secondary">进入工作台</Button>
          </Link>
          <Button loading={saveMutation.isPending} onClick={() => saveMutation.mutate()}>
            保存设置
          </Button>
        </div>
      </div>

      {conflict ? (
        <div className="mb-4 space-y-2">
          <ErrorBanner message={conflict} />
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              void settingsQuery.refetch().then((res) => {
                if (res.data) setDraft(res.data)
                setConflict(null)
              })
            }}
          >
            重新加载最新版本
          </Button>
        </div>
      ) : null}

      {(platformUnverified || policyHint) && !conflict ? (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900" role="status" aria-live="polite">
          <p className="font-medium">平台政策未核验</p>
          <p className="mt-1">
            {policyHint ||
              `当前目标平台为「${draft.target_platform}」，尚未完成政策核验（platform_policy.verified_at 为空）。保存将被拒绝（错误码 42203），请先切换为「通用」或完成平台政策核验。`}
          </p>
        </div>
      ) : null}

      {saveMutation.isError && !conflict && !policyHint ? (
        <div className="mb-4">
          <ErrorBanner message={formatApiError(saveMutation.error)} />
        </div>
      ) : null}

      {matrixQuery.isError ? (
        <div className="mb-4">
          <ErrorBanner
            message={formatApiError(matrixQuery.error)}
            onRetry={() => void matrixQuery.refetch()}
          />
        </div>
      ) : null}

      <div className="space-y-8">
        {groups.map((group) => (
          <section key={group.id} className="sf-panel p-5">
            <h2 className="sf-section-title">{group.label_zh}</h2>
            <div className="mt-4 space-y-4">
              {group.id === 'theme' ? (
                <ThemeSection
                  draft={draft}
                  matrix={matrixQuery.data}
                  loading={matrixQuery.isLoading}
                  onPatch={patch}
                />
              ) : (
                group.fields.map((field) => (
                  <FieldEditor
                    key={field.key}
                    field={field}
                    draft={draft}
                    required={isFieldRequired(field, draft)}
                    onChange={(value) => updateField(field, value)}
                  />
                ))
              )}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}

function ThemeSection({
  draft,
  matrix,
  loading,
  onPatch,
}: {
  draft: ProjectSettings
  matrix: ThemeMatrix | undefined
  loading: boolean
  onPatch: (updater: (prev: ProjectSettings) => ProjectSettings) => void
}) {
  if (loading) return <LoadingBlock label="加载题材矩阵…" />
  if (!matrix) return <p className="text-sm text-ink-muted">题材矩阵不可用</p>

  return (
    <div className="space-y-4">
      <ThemeMatrixPicker
        matrix={matrix}
        genreMatrix={(draft.genre_matrix as GenreMatrix | undefined) ?? {}}
        flavorTags={draft.flavor_tags ?? []}
        presetThemeCode={draft.preset_theme_code}
        onChangeGenre={(next) =>
          onPatch((prev) => ({ ...prev, genre_matrix: next as GenreMatrix }))
        }
        onChangeFlavorTags={(tags) => onPatch((prev) => ({ ...prev, flavor_tags: tags }))}
        onChangePreset={(code) => onPatch((prev) => ({ ...prev, preset_theme_code: code }))}
      />
      <div>
        <label className="sf-label">目标平台</label>
        <select
          className="sf-control"
          value={draft.target_platform}
          onChange={(e) => onPatch((prev) => ({ ...prev, target_platform: e.target.value }))}
        >
          <option value="generic">通用</option>
          <option value="douyin">抖音</option>
          <option value="kuaishou">快手</option>
          <option value="wechat_miniprogram">微信小程序</option>
        </select>
      </div>
    </div>
  )
}

function FieldEditor({
  field,
  draft,
  required,
  onChange,
}: {
  field: SettingsFieldDef
  draft: ProjectSettings
  required: boolean
  onChange: (value: unknown) => void
}) {
  const value = readSettingValue(draft, field)

  if (field.key === 'adapt_notes') {
    const notes = (value as AdaptNotes | undefined) ?? {
      retained: [],
      enhanced: [],
      rewritten: [],
    }
    return (
      <div className="grid grid-cols-3 gap-3">
        {(['retained', 'enhanced', 'rewritten'] as const).map((key) => (
          <div key={key}>
            <label className="sf-label">{key}</label>
            <textarea
              className="sf-control min-h-24"
              value={(notes[key] ?? []).join('\n')}
              onChange={(e) =>
                onChange({
                  ...notes,
                  [key]: e.target.value
                    .split('\n')
                    .map((s) => s.trim())
                    .filter(Boolean),
                })
              }
            />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div>
      <label className="sf-label">
        {field.label_zh}
        {required ? <span className="text-red-500"> *</span> : null}
      </label>
      {field.ui_widget === 'textarea' ? (
        <textarea
          className="sf-control min-h-28"
          value={String(value ?? '')}
          onChange={(e) => onChange(e.target.value)}
          required={required}
        />
      ) : field.ui_widget === 'number' ? (
        <input
          type="number"
          className="sf-control"
          min={field.minimum}
          max={field.maximum}
          value={Number(value ?? field.default ?? 0)}
          onChange={(e) => onChange(Number(e.target.value))}
          required={required}
        />
      ) : field.ui_widget === 'switch' ? (
        <label className="inline-flex items-center gap-2 text-sm text-ink">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => onChange(e.target.checked)}
          />
          {value ? '已启用' : '未启用'}
        </label>
      ) : field.ui_widget === 'select' ? (
        <select
          className="sf-control"
          value={String(value ?? field.default ?? '')}
          onChange={(e) => onChange(e.target.value)}
          required={required}
        >
          {(field.options ?? []).map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : field.ui_widget === 'checklist' ? (
        <div className="flex flex-wrap gap-3">
          {(field.options ?? []).map((opt) => {
            const selected = Array.isArray(value) ? value.includes(opt.value) : false
            return (
              <label key={opt.value} className="inline-flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={(e) => {
                    const current = Array.isArray(value) ? [...(value as string[])] : []
                    if (e.target.checked) onChange([...current, opt.value])
                    else onChange(current.filter((v) => v !== opt.value))
                  }}
                />
                {opt.label}
              </label>
            )
          })}
        </div>
      ) : field.ui_widget === 'tags' ? (
        <textarea
          className="sf-control min-h-20"
          placeholder="每行一项"
          value={Array.isArray(value) ? (value as string[]).join('\n') : ''}
          onChange={(e) =>
            onChange(
              e.target.value
                .split('\n')
                .map((s) => s.trim())
                .filter(Boolean),
            )
          }
        />
      ) : (
        <input
          className="sf-control"
          value={String(value ?? '')}
          onChange={(e) => onChange(e.target.value)}
          required={required}
        />
      )}
    </div>
  )
}
