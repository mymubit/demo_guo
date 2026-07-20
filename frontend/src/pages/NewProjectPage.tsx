import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { HelpCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ErrorBanner } from '@/components/ui/Tabs'
import { PageSection } from '@/components/layout/PageSection'
import { PageShell } from '@/components/layout/PageShell'
import { ThemeMatrixPicker } from '@/components/theme/ThemeMatrixPicker'
import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { isThemeRequirementMet } from '@/utils/firstRunGuide'
import { rememberRecentProject } from '@/utils/recentProjects'
import { cn } from '@/utils/cn'
import type { EntryType, GenreMatrix, ProjectSettings } from '@/types/domain'

const STEPS = [
  { id: 'basic', label: '基本信息' },
  { id: 'channel', label: '通道与受众' },
  { id: 'scope', label: '篇幅设定' },
  { id: 'theme', label: '题材与平台' },
  { id: 'inspiration', label: '创作灵感' },
] as const

type StepId = (typeof STEPS)[number]['id']

const STEP_ORDER: StepId[] = STEPS.map((s) => s.id)
const STEP_TOTAL = STEPS.length

const EPISODE_OPTIONS = [
  { value: 20, label: '20 集' },
  { value: 40, label: '40 集' },
  { value: 60, label: '60 集' },
  { value: 80, label: '80 集' },
  { value: 100, label: '100 集' },
  { value: 120, label: '120 集' },
]

const AUDIENCE_OPTIONS = [
  { value: 'male', label: '男频', hint: '偏剧情爽点与对抗' },
  { value: 'female', label: '女频', hint: '偏情感关系与人物弧光' },
  { value: 'general', label: '通频', hint: '男女向兼顾' },
]

const ENTRY_OPTIONS = [
  {
    value: 'original_track' as const,
    label: '原创短剧',
    hint: '从选题定调进入主链创作',
  },
  {
    value: 'story_adapt' as const,
    label: '故事改编',
    hint: '基于外部故事汇合蓝图后创作',
  },
]

const OUTLINE_OPTIONS = [
  { value: 'full', label: '完整分卡', hint: '自动规划分集卡点' },
  { value: 'structure_only', label: '仅结构', hint: '先出骨架再补细节' },
]

const LENGTH_OPTIONS = [
  { value: 'lean', label: '精简', hint: '短篇幅、快节奏' },
  { value: 'standard', label: '标准', hint: '按题材自动适配' },
  { value: 'complex', label: '加长', hint: '复杂情节更充足' },
]

const INSPIRATION_MAX = 10000

function Label({
  children,
  required,
  hint,
}: {
  children: string
  required?: boolean
  hint?: string
}) {
  return (
    <div className="mb-1.5 flex items-center gap-1.5">
      <span className="sf-label mb-0">
        {children}
        {required ? <span className="ml-0.5 text-red-500">*</span> : null}
      </span>
      {hint ? (
        <span title={hint} className="text-ink-faint">
          <HelpCircle className="h-3.5 w-3.5" />
        </span>
      ) : null}
    </div>
  )
}

function stepIndex(id: StepId): number {
  return STEP_ORDER.indexOf(id)
}

type AdvanceCtx = {
  title: string
  episodeCount: number | ''
  genreMatrix: Partial<GenreMatrix>
  presetThemeCode: string | null
  targetPlatform: string
}

function canAdvanceFrom(step: StepId, ctx: AdvanceCtx): boolean {
  if (step === 'basic') return Boolean(ctx.title.trim())
  if (step === 'scope') return Boolean(ctx.episodeCount)
  if (step === 'theme') {
    return (
      isThemeRequirementMet({
        genre_matrix: ctx.genreMatrix as GenreMatrix,
        preset_theme_code: ctx.presetThemeCode,
      }) && Boolean(ctx.targetPlatform)
    )
  }
  return true
}

export function NewProjectPage() {
  const navigate = useNavigate()
  const { definition } = useWorkbenchDefinition()
  const themeMatrix = definition.theme_matrix
  const platformField = definition.fields.target_platform
  const platformOptions = platformField?.options ?? []

  const [title, setTitle] = useState('')
  const [entryType, setEntryType] = useState<EntryType>('original_track')
  const [audience, setAudience] = useState('general')
  const [episodeCount, setEpisodeCount] = useState<number | ''>('')
  const [outlineMode, setOutlineMode] = useState('full')
  const [lengthBand, setLengthBand] = useState('standard')
  const [genreMatrix, setGenreMatrix] = useState<Partial<GenreMatrix>>({})
  const [flavorTags, setFlavorTags] = useState<string[]>([])
  const [presetThemeCode, setPresetThemeCode] = useState<string | null>(null)
  const [targetPlatform, setTargetPlatform] = useState('generic')
  const [inspiration, setInspiration] = useState('')
  const [activeStep, setActiveStep] = useState<StepId>('basic')
  const [maxReachedStep, setMaxReachedStep] = useState<StepId>('basic')
  const [stepError, setStepError] = useState('')

  const audienceHint = useMemo(
    () => AUDIENCE_OPTIONS.find((o) => o.value === audience)?.hint,
    [audience],
  )

  const advanceCtx: AdvanceCtx = {
    title,
    episodeCount,
    genreMatrix,
    presetThemeCode,
    targetPlatform,
  }

  const mutation = useMutation({
    mutationFn: async () => {
      if (!title.trim()) throw new Error('请填写剧本名称')
      if (!episodeCount) throw new Error('请先选择分集数')
      if (
        !isThemeRequirementMet({
          genre_matrix: genreMatrix as GenreMatrix,
          preset_theme_code: presetThemeCode,
        })
      ) {
        throw new Error('请点齐题材矩阵四轴，或选择预设题材码')
      }
      if (!targetPlatform) throw new Error('请选择目标平台')

      const audienceLabel = AUDIENCE_OPTIONS.find((o) => o.value === audience)?.label ?? ''
      const ideaPrefix = audienceLabel ? `【受众：${audienceLabel}】\n` : ''
      const isOriginal = entryType === 'original_track'
      const inspirationText = inspiration.trim()

      const project = await dramaApi.createProject({
        title: title.trim(),
        entry_type: entryType,
        episode_count: Number(episodeCount),
        core_idea:
          isOriginal && inspirationText ? `${ideaPrefix}${inspirationText}` : undefined,
        external_story: !isOriginal && inspirationText ? inspirationText : undefined,
      })

      const settings = await dramaApi.getSettings(project.id)
      const next: ProjectSettings = {
        ...settings,
        genre_matrix: genreMatrix as GenreMatrix,
        flavor_tags: flavorTags,
        preset_theme_code: presetThemeCode,
        target_platform: targetPlatform,
        creation_preferences: {
          ...settings.creation_preferences,
          outline_mode: outlineMode as 'full' | 'structure_only',
          batch_episode_max: settings.creation_preferences?.batch_episode_max ?? 5,
          scoring_preset: settings.creation_preferences?.scoring_preset ?? 'standard',
          compliance_check_mode:
            settings.creation_preferences?.compliance_check_mode ?? 'standard',
          enable_delivery: settings.creation_preferences?.enable_delivery ?? false,
          deliverables: settings.creation_preferences?.deliverables ?? [],
        },
        production_context: {
          ...settings.production_context,
          target_band: lengthBand as 'lean' | 'standard' | 'complex',
          region: settings.production_context?.region ?? 'CN',
          currency: settings.production_context?.currency ?? 'CNY',
          pricing_version: settings.production_context?.pricing_version ?? '',
          excluded_items: settings.production_context?.excluded_items ?? [],
        },
      }
      await dramaApi.updateSettings(project.id, next, settings.audit.revision)
      rememberRecentProject({
        id: project.id,
        title: project.title,
        entry_type: entryType,
      })
      return project
    },
    onSuccess: (project) => {
      navigate(`/projects/${project.id}/workbench?guide=1`)
    },
  })

  const canSubmit =
    Boolean(title.trim() && episodeCount && targetPlatform) &&
    isThemeRequirementMet({
      genre_matrix: genreMatrix as GenreMatrix,
      preset_theme_code: presetThemeCode,
    })
  const currentIndex = stepIndex(activeStep)
  const isLastStep = activeStep === 'inspiration'

  const goToStep = (next: StepId) => {
    setActiveStep(next)
    setStepError('')
    if (stepIndex(next) > stepIndex(maxReachedStep)) {
      setMaxReachedStep(next)
    }
  }

  const handleNext = () => {
    if (!canAdvanceFrom(activeStep, advanceCtx)) {
      if (activeStep === 'basic') setStepError('请填写剧本名称')
      else if (activeStep === 'scope') setStepError('请选择计划集数')
      else if (activeStep === 'theme')
        setStepError('请点齐题材四轴或选择预设题材码，并选择目标平台')
      return
    }
    const nextId = STEP_ORDER[currentIndex + 1]
    if (nextId) goToStep(nextId)
  }

  const handlePrev = () => {
    const prevId = STEP_ORDER[currentIndex - 1]
    if (prevId) goToStep(prevId)
  }

  const handleStepClick = (id: StepId) => {
    if (stepIndex(id) <= stepIndex(maxReachedStep)) {
      goToStep(id)
    }
  }

  return (
    <PageShell
      title="新建创作"
      description="五步完成建项：名称、通道、篇幅、题材与平台、灵感（选填）；创建后进入工作台开始创作。"
      width="form"
    >
      <form
        className="space-y-5"
        onSubmit={(e) => {
          e.preventDefault()
          if (!isLastStep) {
            handleNext()
            return
          }
          mutation.mutate()
        }}
      >
        <nav aria-label="创建进度" className="sf-panel px-4 py-4">
          <ol className="flex flex-wrap items-center gap-1">
            {STEPS.map((step, index) => {
              const reached = stepIndex(step.id) <= stepIndex(maxReachedStep)
              const isCurrent = step.id === activeStep
              const isDone = stepIndex(step.id) < currentIndex
              return (
                <li key={step.id} className="flex min-w-0 flex-1 items-center gap-1">
                  <button
                    type="button"
                    disabled={!reached}
                    onClick={() => handleStepClick(step.id)}
                    className={cn(
                      'flex min-w-0 flex-1 items-center gap-2 rounded-md px-2 py-1.5 text-left transition',
                      isCurrent && 'bg-action/5',
                      reached ? 'cursor-pointer' : 'cursor-not-allowed opacity-50',
                    )}
                  >
                    <span
                      className={cn(
                        'flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-medium',
                        isCurrent || isDone
                          ? 'bg-action text-white'
                          : 'bg-canvas-muted text-ink-muted',
                      )}
                    >
                      {index + 1}
                    </span>
                    <span
                      className={cn(
                        'truncate text-sm',
                        isCurrent ? 'font-medium text-action' : 'text-ink-muted',
                      )}
                    >
                      {step.label}
                    </span>
                  </button>
                  {index < STEPS.length - 1 ? (
                    <span
                      className={cn(
                        'mx-0.5 hidden h-px w-4 shrink-0 sm:block sm:w-6',
                        isDone ? 'bg-action' : 'bg-border',
                      )}
                      aria-hidden
                    />
                  ) : null}
                </li>
              )
            })}
          </ol>
        </nav>

        <div className="sf-panel space-y-5 p-6">
          {mutation.isError ? <ErrorBanner message={formatApiError(mutation.error)} /> : null}

          {activeStep === 'basic' ? (
            <PageSection eyebrow={`步骤 1 / ${STEP_TOTAL}`} title="基本信息">
              <div>
                <Label required>剧本名称</Label>
                <input
                  className="sf-control"
                  placeholder="给这部短剧起个名字"
                  value={title}
                  onChange={(e) => {
                    setTitle(e.target.value)
                    if (stepError) setStepError('')
                  }}
                  autoFocus
                />
                {stepError && activeStep === 'basic' ? (
                  <p className="mt-1.5 text-sm text-red-600">{stepError}</p>
                ) : null}
              </div>
            </PageSection>
          ) : null}

          {activeStep === 'channel' ? (
            <PageSection eyebrow={`步骤 2 / ${STEP_TOTAL}`} title="通道与受众">
              <div className="space-y-5">
                <div>
                  <Label required>创作类型</Label>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {ENTRY_OPTIONS.map((o) => {
                      const selected = entryType === o.value
                      return (
                        <button
                          key={o.value}
                          type="button"
                          onClick={() => setEntryType(o.value)}
                          className={cn(
                            'rounded-lg border px-4 py-3 text-left transition',
                            selected
                              ? 'border-action bg-action/5'
                              : 'border-border hover:border-action/40',
                          )}
                        >
                          <div className="text-sm font-medium text-ink">{o.label}</div>
                          <p className="mt-1 text-xs text-ink-muted">{o.hint}</p>
                        </button>
                      )
                    })}
                  </div>
                </div>
                <div>
                  <Label required hint={audienceHint}>
                    主要受众
                  </Label>
                  <div className="flex flex-wrap gap-2">
                    {AUDIENCE_OPTIONS.map((o) => {
                      const selected = audience === o.value
                      return (
                        <button
                          key={o.value}
                          type="button"
                          onClick={() => setAudience(o.value)}
                          className={cn(
                            'rounded-md border px-3 py-2 text-sm transition',
                            selected
                              ? 'border-action bg-action/5 font-medium text-action'
                              : 'border-border text-ink-muted hover:border-action/40 hover:text-ink',
                          )}
                        >
                          {o.label}
                        </button>
                      )
                    })}
                  </div>
                  <p className="mt-1.5 text-xs text-ink-muted">{audienceHint}</p>
                </div>
              </div>
            </PageSection>
          ) : null}

          {activeStep === 'scope' ? (
            <PageSection eyebrow={`步骤 3 / ${STEP_TOTAL}`} title="篇幅设定">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                  <Label required>计划集数</Label>
                  <select
                    className="sf-control"
                    value={episodeCount === '' ? '' : String(episodeCount)}
                    onChange={(e) => {
                      setEpisodeCount(e.target.value ? Number(e.target.value) : '')
                      if (stepError) setStepError('')
                    }}
                  >
                    <option value="" disabled>
                      请选择集数
                    </option>
                    {EPISODE_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                  {stepError && activeStep === 'scope' ? (
                    <p className="mt-1.5 text-sm text-red-600">{stepError}</p>
                  ) : null}
                </div>
                <div>
                  <Label hint="影响大纲详细程度">分卡方式</Label>
                  <select
                    className="sf-control"
                    value={outlineMode}
                    onChange={(e) => setOutlineMode(e.target.value)}
                  >
                    {OUTLINE_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label hint="影响篇幅与制作复杂度">篇幅倾向</Label>
                  <select
                    className="sf-control"
                    value={lengthBand}
                    onChange={(e) => setLengthBand(e.target.value)}
                  >
                    {LENGTH_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </PageSection>
          ) : null}

          {activeStep === 'theme' ? (
            <PageSection
              eyebrow={`步骤 4 / ${STEP_TOTAL}`}
              title="题材与平台"
              description="点齐情绪 / 身份 / 冲突 / 世界观四轴，并确认目标平台。"
            >
              <div className="space-y-6">
                <div>
                  <Label required>目标平台</Label>
                  <select
                    className="sf-control max-w-md"
                    value={targetPlatform}
                    onChange={(e) => {
                      setTargetPlatform(e.target.value)
                      if (stepError) setStepError('')
                    }}
                  >
                    {platformOptions.length === 0 ? (
                      <option value="generic">通用</option>
                    ) : (
                      platformOptions.map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label_zh ?? o.label}
                        </option>
                      ))
                    )}
                  </select>
                </div>
                {themeMatrix ? (
                  <ThemeMatrixPicker
                    matrix={themeMatrix}
                    genreMatrix={genreMatrix}
                    flavorTags={flavorTags}
                    presetThemeCode={presetThemeCode}
                    onChangeGenre={(next) => {
                      setGenreMatrix(next)
                      if (stepError) setStepError('')
                    }}
                    onChangeFlavorTags={setFlavorTags}
                    onChangePreset={setPresetThemeCode}
                  />
                ) : (
                  <p className="text-sm text-amber-700">题材矩阵定义暂不可用，请稍后重试或刷新页面。</p>
                )}
                {stepError && activeStep === 'theme' ? (
                  <p className="text-sm text-red-600">{stepError}</p>
                ) : null}
              </div>
            </PageSection>
          ) : null}

          {activeStep === 'inspiration' ? (
            <PageSection
              eyebrow={`步骤 5 / ${STEP_TOTAL}`}
              title="创作灵感"
              description="选填。可跳过，直接创建并进入工作台。"
            >
              <div>
                <Label>
                  {entryType === 'original_track' ? '创作灵感' : '外部故事 / 改编素材'}
                </Label>
                <div className="relative">
                  <textarea
                    className="sf-control min-h-36 pr-16"
                    maxLength={INSPIRATION_MAX}
                    placeholder={
                      entryType === 'original_track'
                        ? '写清剧情走向、人物关系或悬念点。尽量具体，便于后续选题与蓝图生成。'
                        : '粘贴或概述待改编故事的核心人物、主线与必须保留的情节。'
                    }
                    value={inspiration}
                    onChange={(e) => setInspiration(e.target.value)}
                  />
                  <div className="pointer-events-none absolute bottom-2.5 right-3 text-xs text-ink-faint">
                    {inspiration.length}/{INSPIRATION_MAX}
                  </div>
                </div>
              </div>
            </PageSection>
          ) : null}

          <div className="flex items-center justify-end gap-3 border-t border-border pt-4">
            {currentIndex === 0 ? (
              <Button type="button" variant="secondary" onClick={() => navigate('/projects')}>
                取消
              </Button>
            ) : (
              <Button type="button" variant="secondary" onClick={handlePrev}>
                上一步
              </Button>
            )}
            {isLastStep ? (
              <Button
                type="submit"
                variant="action"
                loading={mutation.isPending}
                disabled={!canSubmit}
              >
                创建并开始创作
              </Button>
            ) : (
              <Button type="submit" variant="action">
                下一步
              </Button>
            )}
          </div>
        </div>
      </form>
    </PageShell>
  )
}
