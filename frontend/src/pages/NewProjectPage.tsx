import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { HelpCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { ErrorBanner } from '@/components/ui/Tabs'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import type { EntryType, ProjectSettings } from '@/types/domain'

/** 借鉴商业灵感页的信息结构：名称 → 类型/受众 → 集数与篇幅 → 大段灵感，而非暗色照抄 */

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

export function NewProjectPage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [entryType, setEntryType] = useState<EntryType>('original_track')
  const [audience, setAudience] = useState('general')
  const [episodeCount, setEpisodeCount] = useState<number | ''>('')
  const [outlineMode, setOutlineMode] = useState('full')
  const [lengthBand, setLengthBand] = useState('standard')
  const [inspiration, setInspiration] = useState('')

  const entryHint = useMemo(
    () => ENTRY_OPTIONS.find((o) => o.value === entryType)?.hint,
    [entryType],
  )
  const audienceHint = useMemo(
    () => AUDIENCE_OPTIONS.find((o) => o.value === audience)?.hint,
    [audience],
  )

  const mutation = useMutation({
    mutationFn: async () => {
      if (!title.trim()) throw new Error('请填写剧本名称')
      if (!episodeCount) throw new Error('请先选择分集数')
      if (!inspiration.trim()) throw new Error('请填写创作灵感')

      const audienceLabel = AUDIENCE_OPTIONS.find((o) => o.value === audience)?.label ?? ''
      const ideaPrefix = audienceLabel ? `【受众：${audienceLabel}】\n` : ''
      const isOriginal = entryType === 'original_track'

      const project = await dramaApi.createProject({
        title: title.trim(),
        entry_type: entryType,
        episode_count: Number(episodeCount),
        core_idea: isOriginal ? `${ideaPrefix}${inspiration.trim()}` : undefined,
        external_story: isOriginal ? undefined : inspiration.trim(),
      })

      const settings = await dramaApi.getSettings(project.id)
      const next: ProjectSettings = {
        ...settings,
        creation_preferences: {
          ...settings.creation_preferences,
          outline_mode: outlineMode as 'full' | 'structure_only',
          batch_episode_max: settings.creation_preferences?.batch_episode_max ?? 5,
          scoring_preset: settings.creation_preferences?.scoring_preset ?? 'standard',
          compliance_check_mode:
            settings.creation_preferences?.compliance_check_mode ?? 'standard',
          enable_delivery: settings.creation_preferences?.enable_delivery ?? false,
          delivery_items: settings.creation_preferences?.delivery_items ?? [],
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
      return project
    },
    onSuccess: (project) => {
      // 基础信息完成后先完善题材/平台，再进工作台，避免「设定已完成」的误导
      navigate(`/projects/${project.id}/settings?from=new`)
    },
  })

  const canSubmit = Boolean(title.trim() && episodeCount && inspiration.trim())

  return (
    <div className="mx-auto max-w-3xl px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-ink">新建创作</h1>
        <p className="mt-1 text-sm text-ink-muted">
          先填写名称、类型、集数和灵感；创建后将进入创作设定，补齐题材与平台后再开工
        </p>
      </div>

      <form
        className="sf-panel space-y-5 p-6"
        onSubmit={(e) => {
          e.preventDefault()
          mutation.mutate()
        }}
      >
        {mutation.isError ? <ErrorBanner message={formatApiError(mutation.error)} /> : null}

        <div>
          <Label required>剧本名称</Label>
          <input
            className="sf-control"
            placeholder="给这部短剧起个名字"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label required hint={entryHint}>
              创作类型
            </Label>
            <select
              className="sf-control"
              value={entryType}
              onChange={(e) => setEntryType(e.target.value as EntryType)}
            >
              {ENTRY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-ink-muted">{entryHint}</p>
          </div>
          <div>
            <Label required hint={audienceHint}>
              主要受众
            </Label>
            <select
              className="sf-control"
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
            >
              {AUDIENCE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-ink-muted">{audienceHint}</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <Label required>计划集数</Label>
            <select
              className="sf-control"
              value={episodeCount === '' ? '' : String(episodeCount)}
              onChange={(e) =>
                setEpisodeCount(e.target.value ? Number(e.target.value) : '')
              }
              required
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

        <div>
          <Label required>
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
              required
            />
            <div className="pointer-events-none absolute bottom-2.5 right-3 text-xs text-ink-faint">
              {inspiration.length}/{INSPIRATION_MAX}
            </div>
          </div>
        </div>

        {!episodeCount ? (
          <p className="text-sm text-amber-700">选择分集数后即可创建项目。</p>
        ) : (
          <p className="text-sm text-ink-muted">
            当前为快速建项；题材矩阵与目标平台请在下一步「创作设定」中完善。
          </p>
        )}

        <div className="flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
          <Button type="button" variant="secondary" onClick={() => navigate('/projects')}>
            取消
          </Button>
          <Button type="submit" loading={mutation.isPending} disabled={!canSubmit}>
            创建并完善创作设定
          </Button>
        </div>
      </form>
    </div>
  )
}
