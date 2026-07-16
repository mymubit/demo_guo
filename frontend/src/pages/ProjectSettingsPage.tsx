import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { ThemeMatrixPicker } from '@/components/theme/ThemeMatrixPicker'
import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
import { dramaApi } from '@/services/drama'
import { ApiError, formatApiError } from '@/services/errors'
import {
  isFieldRequired,
  readSettingValue,
  visibleGroups,
  writeSettingValue,
} from '@/utils/settingsForm'
import { isGenreMatrixComplete } from '@/utils/firstRunGuide'
import { rememberRecentProject } from '@/utils/recentProjects'
import type { AdaptNotes, GenreMatrix, ProjectSettings } from '@/types/domain'
import type { SettingsFieldDef, ThemeMatrix } from '@/types/workbench'
import { cn } from '@/utils/cn'

/** 借鉴灵感页：分组聚焦、中文说明、减少技术噪音；视觉仍用本站浅色品牌 */

export function ProjectSettingsPage() {
  const { projectId = '' } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isFromNew = searchParams.get('from') === 'new'
  const focusTheme = searchParams.get('focus') === 'theme' || isFromNew
  const qc = useQueryClient()
  const { definition } = useWorkbenchDefinition()
  const [draft, setDraft] = useState<ProjectSettings | null>(null)
  const [conflict, setConflict] = useState<string | null>(null)
  const [policyHint, setPolicyHint] = useState<string | null>(null)
  const [activeGroup, setActiveGroup] = useState('')
  const [saveOk, setSaveOk] = useState(false)
  const [themeFocusApplied, setThemeFocusApplied] = useState(false)

  const settingsQuery = useQuery({
    queryKey: ['settings', projectId],
    queryFn: () => dramaApi.getSettings(projectId),
    enabled: Boolean(projectId),
  })

  useEffect(() => {
    if (settingsQuery.data) setDraft(settingsQuery.data)
  }, [settingsQuery.data])

  useEffect(() => {
    if (!settingsQuery.data || !projectId) return
    rememberRecentProject({
      id: projectId,
      title: settingsQuery.data.title,
      entry_type: settingsQuery.data.entry_type,
    })
  }, [projectId, settingsQuery.data])

  const platformUnverified =
    Boolean(draft) &&
    draft!.target_platform !== 'generic' &&
    !draft!.platform_policy?.verified_at

  const saveMutation = useMutation({
    mutationFn: async (_opts?: { enterWorkbench?: boolean }) => {
      if (!draft) throw new Error('没有可保存的设置')
      return dramaApi.updateSettings(projectId, draft, draft.audit.revision)
    },
    onSuccess: (data, vars) => {
      setConflict(null)
      setPolicyHint(null)
      setDraft(data)
      setSaveOk(true)
      window.setTimeout(() => setSaveOk(false), 2000)
      void qc.invalidateQueries({ queryKey: ['settings', projectId] })
      if (vars?.enterWorkbench) {
        navigate(`/projects/${projectId}/workbench?guide=1`)
      }
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

  const groups = useMemo(
    () => (draft ? visibleGroups(definition, draft) : []),
    [definition, draft],
  )

  useEffect(() => {
    if (!groups.length) return
    if (focusTheme && !themeFocusApplied && groups.some((g) => g.id === 'theme')) {
      setActiveGroup('theme')
      setThemeFocusApplied(true)
      return
    }
    if (!activeGroup && groups[0]) setActiveGroup(groups[0].id)
    if (activeGroup && !groups.some((g) => g.id === activeGroup)) {
      setActiveGroup(groups[0]?.id ?? '')
    }
  }, [groups, activeGroup, focusTheme, themeFocusApplied])

  const themeMatrix = definition.theme_matrix

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
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink">创作设定</h1>
          <p className="mt-1 text-sm text-ink-muted">
            按分组调整需求；题材用点选完成，不必记英文标识
          </p>
        </div>
        <div className="flex gap-2">
          <Link to={`/projects/${projectId}/workbench${themeReady ? '?guide=1' : ''}`}>
            <Button variant="secondary">进入工作台</Button>
          </Link>
          <Button loading={saveMutation.isPending && !saveMutation.variables?.enterWorkbench} onClick={() => saveMutation.mutate()}>
            {saveOk && !saveMutation.variables?.enterWorkbench ? '已保存' : '保存设定'}
          </Button>
          {themeReady ? (
            <Button
              loading={saveMutation.isPending && Boolean(saveMutation.variables?.enterWorkbench)}
              onClick={() => saveMutation.mutate({ enterWorkbench: true })}
            >
              保存并开始创作
            </Button>
          ) : null}
        </div>
      </div>

      {isFromNew ? (
        <div className="mb-4 rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
          <p className="font-medium">项目已创建，请先完善题材与目标平台</p>
          <p className="mt-1 text-brand-700/90">
            名称与灵感已保存。点选题材矩阵并确认平台后，可「保存并开始创作」进入工作台执行立项简报。
          </p>
        </div>
      ) : null}

      {!themeReady && !isFromNew ? (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          题材未选齐：请在「题材与受众」分组点选情绪 / 身份 / 冲突 / 世界观。
        </div>
      ) : null}

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
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <p className="font-medium">平台政策未核验</p>
          <p className="mt-1">
            {policyHint ||
              `当前目标平台为「${
                platformField?.options?.find((o) => o.value === draft.target_platform)?.label ??
                draft.target_platform
              }」，设定可保存，上架交付前需完成核验。`}
          </p>
        </div>
      ) : null}

      {saveMutation.isError && !conflict && !policyHint ? (
        <div className="mb-4">
          <ErrorBanner message={formatApiError(saveMutation.error)} />
        </div>
      ) : null}

      <div className="flex gap-6">
        <nav className="hidden w-40 shrink-0 md:block">
          <div className="sticky top-6 space-y-1">
            {groups.map((group) => (
              <button
                key={group.id}
                type="button"
                onClick={() => setActiveGroup(group.id)}
                className={cn(
                  'w-full rounded-lg px-3 py-2 text-left text-sm transition',
                  currentGroup?.id === group.id
                    ? 'bg-brand-50 font-medium text-brand-700'
                    : 'text-ink-muted hover:bg-slate-100 hover:text-ink',
                )}
              >
                {group.label_zh}
              </button>
            ))}
          </div>
        </nav>

        <div className="min-w-0 flex-1">
          <div className="mb-3 flex gap-2 overflow-x-auto md:hidden">
            {groups.map((group) => (
              <button
                key={group.id}
                type="button"
                onClick={() => setActiveGroup(group.id)}
                className={cn(
                  'shrink-0 rounded-full px-3 py-1 text-xs',
                  currentGroup?.id === group.id
                    ? 'bg-brand-500 text-white'
                    : 'bg-slate-100 text-ink-muted',
                )}
              >
                {group.label_zh}
              </button>
            ))}
          </div>

      <div className="space-y-8">
        {groups.map((group) => (
          <section key={group.id} className="sf-panel p-5">
            <h2 className="sf-section-title">{group.label_zh}</h2>
            <div className="mt-4 space-y-4">
              {group.id === 'theme' && themeMatrix ? (
                <ThemeSection
                  draft={draft}
                  matrix={themeMatrix}
                  fields={group.fields}
                  onPatch={patch}
                  onFieldChange={updateField}
                />
              ) : (
                group.fields.map((field) => (
                  <FieldEditor
                    key={field.key}
                    field={field}
                    draft={draft}
                    matrix={themeMatrix}
                    platformField={platformField}
                    onPatch={patch}
                  />
                ) : (
                  <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                    {currentGroup.fields.map((field) => (
                      <div
                        key={field.key}
                        className={cn(
                          field.ui_widget === 'textarea' ||
                            field.key === 'adapt_notes' ||
                            field.ui_widget === 'checklist' ||
                            field.ui_widget === 'tags'
                            ? 'md:col-span-2'
                            : '',
                        )}
                      >
                        <FieldEditor
                          field={field}
                          draft={draft}
                          required={isFieldRequired(field, draft)}
                          onChange={(value) => updateField(field, value)}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          ) : null}
        </div>
      </div>
    </div>
  )
}

/** 由 ThemeMatrixPicker 专属渲染的字段；其余题材字段（频道/主角结构/平台）走通用 FieldEditor */
const PICKER_FIELD_KEYS = new Set(['genre_matrix', 'flavor_tags', 'preset_theme_code'])

function ThemeSection({
  draft,
  matrix,
  fields,
  onPatch,
  onFieldChange,
}: {
  draft: ProjectSettings
  matrix: ThemeMatrix
  fields: SettingsFieldDef[]
  onPatch: (updater: (prev: ProjectSettings) => ProjectSettings) => void
  onFieldChange: (field: SettingsFieldDef, value: unknown) => void
}) {
  const editorFields = fields.filter((f) => !PICKER_FIELD_KEYS.has(f.key))
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {editorFields.map((field) => (
          <FieldEditor
            key={field.key}
            field={field}
            draft={draft}
            required={isFieldRequired(field, draft)}
            onChange={(value) => onFieldChange(field, value)}
          />
        ))}
      </div>
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
    const adaptLabels: Record<'retained' | 'enhanced' | 'rewritten', string> = {
      retained: '保留',
      enhanced: '强化',
      rewritten: '重写',
    }
    return (
      <div>
        <div className="sf-label">改编说明</div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {(['retained', 'enhanced', 'rewritten'] as const).map((key) => (
            <div key={key}>
              <label className="mb-1 block text-xs text-ink-muted">{adaptLabels[key]}</label>
              <textarea
                className="sf-control min-h-24"
                placeholder={`每行一条「${adaptLabels[key]}」`}
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
          placeholder={`请输入${field.label_zh}`}
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
        <div className="flex flex-wrap gap-2">
          {(field.options ?? []).map((opt) => {
            const selected = Array.isArray(value) ? value.includes(opt.value) : false
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  const current = Array.isArray(value) ? [...(value as string[])] : []
                  if (selected) onChange(current.filter((v) => v !== opt.value))
                  else onChange([...current, opt.value])
                }}
                className={cn(
                  'rounded-lg border px-3 py-1.5 text-sm transition',
                  selected
                    ? 'border-brand-500 bg-brand-50 text-brand-700'
                    : 'border-slate-200 bg-white text-ink-muted hover:border-brand-300',
                )}
              >
                {opt.label}
              </button>
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
          placeholder={`请输入${field.label_zh}`}
        />
      )}
    </div>
  )
}
