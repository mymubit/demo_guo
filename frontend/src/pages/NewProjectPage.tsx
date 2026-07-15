import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ErrorBanner } from '@/components/ui/Tabs'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import type { EntryType } from '@/types/domain'
import { cn } from '@/utils/cn'

export function NewProjectPage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [entryType, setEntryType] = useState<EntryType>('original_track')
  const [coreIdea, setCoreIdea] = useState('')
  const [externalStory, setExternalStory] = useState('')
  const [episodeCount, setEpisodeCount] = useState(80)

  const mutation = useMutation({
    mutationFn: () =>
      dramaApi.createProject({
        title: title.trim(),
        entry_type: entryType,
        episode_count: episodeCount,
        core_idea: entryType === 'original_track' ? coreIdea : undefined,
        external_story: entryType === 'story_adapt' ? externalStory : undefined,
      }),
    onSuccess: (project) => {
      navigate(`/projects/${project.id}/settings`)
    },
  })

  return (
    <div className="mx-auto max-w-3xl px-8 py-8">
      <h1 className="text-2xl font-semibold text-ink">新建项目</h1>
      <p className="mt-1 text-sm text-ink-muted">选择创作入口，进入契约驱动的项目设置</p>

      <div className="mt-6 grid grid-cols-2 gap-4">
        {(
          [
            {
              id: 'original_track' as const,
              title: '原创通道',
              desc: '从零选题：选题定调 → 蓝图 → 分集 → 正文',
            },
            {
              id: 'story_adapt' as const,
              title: '故事改编通道',
              desc: '基于外部故事：蓝图汇合 → 分集 → 正文',
            },
          ] as const
        ).map((opt) => (
          <button
            key={opt.id}
            type="button"
            onClick={() => setEntryType(opt.id)}
            className={cn(
              'rounded-xl border px-5 py-4 text-left transition',
              entryType === opt.id
                ? 'border-brand-500 bg-brand-50 ring-1 ring-brand-200'
                : 'border-slate-200 bg-white hover:border-slate-300',
            )}
          >
            <div className="text-base font-semibold text-ink">{opt.title}</div>
            <p className="mt-2 text-sm text-ink-muted">{opt.desc}</p>
          </button>
        ))}
      </div>

      <form
        className="mt-8 space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          mutation.mutate()
        }}
      >
        {mutation.isError ? <ErrorBanner message={formatApiError(mutation.error)} /> : null}
        <div>
          <label className="sf-label" htmlFor="title">
            项目标题
          </label>
          <input
            id="title"
            className="sf-control"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="sf-label" htmlFor="episodes">
            计划集数
          </label>
          <input
            id="episodes"
            type="number"
            min={1}
            className="sf-control"
            value={episodeCount}
            onChange={(e) => setEpisodeCount(Number(e.target.value))}
            required
          />
        </div>
        {entryType === 'original_track' ? (
          <div>
            <label className="sf-label" htmlFor="core">
              核心创意
            </label>
            <textarea
              id="core"
              className="sf-control min-h-28"
              value={coreIdea}
              onChange={(e) => setCoreIdea(e.target.value)}
              required
            />
          </div>
        ) : (
          <div>
            <label className="sf-label" htmlFor="story">
              外部故事原文
            </label>
            <textarea
              id="story"
              className="sf-control min-h-40"
              value={externalStory}
              onChange={(e) => setExternalStory(e.target.value)}
              required
            />
          </div>
        )}
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={mutation.isPending}>
            创建并进入设置
          </Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/projects')}>
            取消
          </Button>
        </div>
      </form>
    </div>
  )
}
