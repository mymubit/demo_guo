import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import { PageShell } from '@/components/layout/PageShell'
import { ThemeMatrixPicker } from '@/components/theme/ThemeMatrixPicker'
import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { isGenreMatrixComplete } from '@/utils/firstRunGuide'
import { cn } from '@/utils/cn'
import type { EntryType, GenreMatrix, ProjectSettings } from '@/types/domain'
import type { FieldOption } from '@/types/workbench'

function optionLabel(opt: FieldOption): string {
  return opt.label_zh || opt.label || opt.value
}

/**
 * 字段对齐技能契约：
 * - 原创：topic-director required_params_any_of = core_idea | synopsis | genre_matrix
 * - 改编：orchestration 要求 external_story；跳过选题，直接 story-bible
 * - title：项目级字段（settings.title），写入各角色 prompt；剧名 drama_title 由蓝图等产物生成
 */

const IDEA_MAX = 10000

const ENTRY_CARDS: Array<{
  value: EntryType
  title: string
  desc: string
}> = [
  {
    value: 'original_track',
    title: '原创短剧',
    desc: '从零选题：先走「选题定调官」出立项简报，再进剧本蓝图。创意与题材矩阵至少填一项。',
  },
  {
    value: 'story_adapt',
    title: '故事改编',
    desc: '自带小说/故事/大纲：跳过选题，直接由「剧本蓝图官」按改编模式提取并补全蓝图。',
  },
]

export function NewProjectPage() {
  const navigate = useNavigate()
  const { definition } = useWorkbenchDefinition()
  const themeMatrix = definition.theme_matrix

  const [title, setTitle] = useState('')
  const [entryType, setEntryType] = useState<EntryType>('original_track')
  const [episodeCount, setEpisodeCount] = useState<number | ''>('')
  const [idea, setIdea] = useState('')
  const [targetPlatform, setTargetPlatform] = useState(
    () => String(definition.fields.target_platform?.default ?? 'generic'),
  )
  const [audienceChannel, setAudienceChannel] = useState(
    () =>
      String(
        themeMatrix?.audience_channel?.default ??
          definition.fields.audience_channel?.default ??
          'general',
      ),
  )
  const [protagonistStructure, setProtagonistStructure] = useState<string | null>(null)
  const [genreMatrix, setGenreMatrix] = useState<Partial<GenreMatrix>>({})
  const [flavorTags, setFlavorTags] = useState<string[]>([])
  const [presetThemeCode, setPresetThemeCode] = useState<string | null>(null)
  const [showTopicHint, setShowTopicHint] = useState(false)

  const platformField = definition.fields.target_platform
  const audienceField = definition.fields.audience_channel
  const protagonistField = definition.fields.protagonist_structure
  const platformOptions = platformField?.options ?? [{ value: 'generic', label: '通用' }]
  const audienceOptions =
    themeMatrix?.audience_channel?.options ??
    audienceField?.options ??
    [
      { value: 'general', label_zh: '普适' },
      { value: 'female', label_zh: '女频' },
      { value: 'male', label_zh: '男频' },
    ]
  const protagonistOptions =
    themeMatrix?.protagonist_structure?.options ?? protagonistField?.options ?? []

  const themeReady = isGenreMatrixComplete(genreMatrix as GenreMatrix)
  const isOriginal = entryType === 'original_track'
  const ideaText = idea.trim()

  const ideaLabel = isOriginal
    ? definition.fields.core_idea?.label_zh || '核心创意'
    : definition.fields.external_story?.label_zh || '外部故事原文'

  /** 选题定调：创意与完整题材矩阵至少其一；改编：外部故事必填 */
  const hasTopicInput = isOriginal
    ? Boolean(ideaText) || themeReady
    : Boolean(ideaText)

  const canSubmit = Boolean(
    title.trim() && episodeCount && targetPlatform && hasTopicInput,
  )

  /** 仅「创意/题材」这类 HTML required 兜不住的规则，在点提交后提示 */
  const topicHint = useMemo(() => {
    if (!isOriginal && !ideaText) return '改编通道请填写外部故事原文'
    if (isOriginal && !hasTopicInput) {
      return '原创通道：核心创意与题材矩阵至少填一项'
    }
    return null
  }, [isOriginal, ideaText, hasTopicInput])

  const mutation = useMutation({
    mutationFn: async () => {
      if (!canSubmit) throw new Error(topicHint || '请完善必填项')

      const project = await dramaApi.createProject({
        title: title.trim(),
        entry_type: entryType,
        episode_count: Number(episodeCount),
        core_idea: isOriginal ? ideaText : undefined,
        external_story: isOriginal ? undefined : ideaText,
      })

      const settings = await dramaApi.getSettings(project.id)
      const next: ProjectSettings = {
        ...settings,
        entry_type: entryType,
        title: title.trim(),
        episode_count: Number(episodeCount),
        core_idea: isOriginal ? ideaText : settings.core_idea,
        external_story: isOriginal ? settings.external_story : ideaText,
        target_platform: targetPlatform,
        audience_channel: audienceChannel,
        protagonist_structure: protagonistStructure,
        flavor_tags: flavorTags,
        preset_theme_code: presetThemeCode,
      }

      if (themeReady) {
        next.genre_matrix = {
          emotion: genreMatrix.emotion!,
          identity: genreMatrix.identity!,
          conflict: genreMatrix.conflict!,
          world: genreMatrix.world!,
        }
      } else {
        delete next.genre_matrix
      }

      await dramaApi.updateSettings(project.id, next, settings.audit.revision)
      return project
    },
    onSuccess: (project) => {
      navigate(`/projects/${project.id}/workbench?guide=1`)
    },
  })

  if (!themeMatrix) {
    return (
      <div className="p-8">
        <LoadingBlock label="加载题材契约…" />
      </div>
    )
  }

  return (
    <PageShell
      title="新建创作"
      description="按编排通道与选题定调官入参填写；更细的偏好可稍后在创作设定中调整。"
      width="form"
    >
      <form
        className="sf-panel space-y-6 p-6"
        onSubmit={(e) => {
          e.preventDefault()
          if (!canSubmit) {
            setShowTopicHint(true)
            return
          }
          setShowTopicHint(false)
          mutation.mutate()
        }}
      >
        {mutation.isError ? <ErrorBanner message={formatApiError(mutation.error)} /> : null}

        <section className="space-y-4">
          <div>
            <label className="sf-label">
              项目名称<span className="ml-0.5 text-red-500">*</span>
            </label>
            <input
              className="sf-control"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="给这部短剧起个项目名"
              required
            />
          </div>

          <div>
            <label className="sf-label">
              创作入口<span className="ml-0.5 text-red-500">*</span>
            </label>
            <div className="mt-2 grid gap-3 sm:grid-cols-2">
              {ENTRY_CARDS.map((card) => {
                const active = entryType === card.value
                return (
                  <button
                    key={card.value}
                    type="button"
                    onClick={() => setEntryType(card.value)}
                    className={cn(
                      'rounded-xl border px-4 py-3 text-left transition',
                      active
                        ? 'border-action bg-action/10'
                        : 'border-border bg-surface hover:border-action/30',
                    )}
                  >
                    <div className="text-sm font-semibold text-ink">{card.title}</div>
                    <p className="mt-1 text-xs leading-relaxed text-ink-muted">{card.desc}</p>
                  </button>
                )
              })}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="sf-label">
                {definition.fields.episode_count?.label_zh || '计划集数'}
                <span className="ml-0.5 text-red-500">*</span>
              </label>
              <input
                className="sf-control"
                type="number"
                min={1}
                value={episodeCount === '' ? '' : episodeCount}
                onChange={(e) =>
                  setEpisodeCount(e.target.value ? Number(e.target.value) : '')
                }
                placeholder="例如 40"
                required
              />
            </div>
            <div>
              <label className="sf-label">
                {platformField?.label_zh || '目标平台'}
                <span className="ml-0.5 text-red-500">*</span>
              </label>
              <select
                className="sf-control"
                value={targetPlatform}
                onChange={(e) => setTargetPlatform(e.target.value)}
              >
                {platformOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {optionLabel(o)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="sf-label">
              {ideaLabel}
              {isOriginal ? (
                <span className="ml-2 font-normal text-ink-muted">选填</span>
              ) : (
                <span className="ml-0.5 text-red-500">*</span>
              )}
            </label>
            <div className="relative">
              <textarea
                className="sf-control min-h-28 pr-16"
                maxLength={IDEA_MAX}
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder={
                  isOriginal
                    ? '一句话写清冲突与人物，也可留空只选题材'
                    : '粘贴或概述待改编故事的人物、主线与必留情节'
                }
                required={!isOriginal}
              />
              <div className="pointer-events-none absolute bottom-2.5 right-3 text-xs text-ink-faint">
                {idea.length}/{IDEA_MAX}
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-4 border-t border-border pt-5">
          <h2 className="sf-section-title text-base">题材与受众</h2>

          <div>
            <label className="sf-label">
              {themeMatrix.audience_channel?.label_zh ||
                audienceField?.label_zh ||
                '受众频道'}
              <span className="ml-0.5 text-red-500">*</span>
            </label>
            <p className="mt-0.5 text-xs text-ink-muted">
              女频偏情感与关系，男频偏强爽与逆袭，普适则不刻意区分
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {audienceOptions.map((o) => {
                const active = audienceChannel === o.value
                const desc = (o as { desc?: string }).desc
                return (
                  <button
                    key={o.value}
                    type="button"
                    title={desc}
                    onClick={() => setAudienceChannel(o.value)}
                    className={cn(
                      'rounded-full border px-4 py-2 text-sm transition',
                      active
                        ? 'border-action bg-action/10 font-medium text-action'
                        : 'border-border bg-surface text-ink-muted hover:border-action/30',
                    )}
                  >
                    {optionLabel(o)}
                  </button>
                )
              })}
            </div>
          </div>

          {protagonistOptions.length > 0 ? (
            <div>
              <label className="sf-label">
                {themeMatrix.protagonist_structure?.label_zh ||
                  protagonistField?.label_zh ||
                  '主角结构'}
                <span className="ml-2 font-normal text-ink-muted">选填</span>
              </label>
              <p className="mt-0.5 text-xs text-ink-muted">
                大男主/大女主/双强等；点「不限」表示不指定
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setProtagonistStructure(null)}
                  className={cn(
                    'rounded-full border px-4 py-2 text-sm transition',
                    protagonistStructure === null
                      ? 'border-action bg-action/10 font-medium text-action'
                      : 'border-border bg-surface text-ink-muted hover:border-action/30',
                  )}
                >
                  不限
                </button>
                {protagonistOptions.map((o) => {
                  const active = protagonistStructure === o.value
                  return (
                    <button
                      key={o.value}
                      type="button"
                      onClick={() => setProtagonistStructure(o.value)}
                      className={cn(
                        'rounded-full border px-4 py-2 text-sm transition',
                        active
                          ? 'border-action bg-action/10 font-medium text-action'
                          : 'border-border bg-surface text-ink-muted hover:border-action/30',
                      )}
                    >
                      {optionLabel(o)}
                    </button>
                  )
                })}
              </div>
            </div>
          ) : null}

          <div>
            <label className="sf-label">
              {definition.fields.genre_matrix?.label_zh || '题材矩阵'}
              <span className="ml-2 font-normal text-ink-muted">选填</span>
            </label>
            <ThemeMatrixPicker
              density="quick"
              matrix={themeMatrix}
              genreMatrix={genreMatrix}
              flavorTags={flavorTags}
              presetThemeCode={presetThemeCode}
              onChangeGenre={setGenreMatrix}
              onChangeFlavorTags={setFlavorTags}
              onChangePreset={setPresetThemeCode}
              onChangeAudienceChannel={setAudienceChannel}
              onChangeProtagonistStructure={setProtagonistStructure}
            />
          </div>
        </section>

        {showTopicHint && topicHint ? (
          <p className="text-sm text-amber-700">{topicHint}</p>
        ) : null}

        <div className="flex items-center justify-end gap-3 border-t border-border pt-4">
          <Button type="button" variant="secondary" onClick={() => navigate('/projects')}>
            取消
          </Button>
          <Button type="submit" variant="action" loading={mutation.isPending}>
            创建并进入工作台
          </Button>
        </div>
      </form>
    </PageShell>
  )
}
