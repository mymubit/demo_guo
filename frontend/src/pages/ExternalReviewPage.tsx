import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/Button'
import { ErrorBanner } from '@/components/ui/Tabs'
import { PageShell } from '@/components/layout/PageShell'
import { GenerationJobPanel } from '@/components/workbench/GenerationJobPanel'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { createCommandId } from '@/utils/cn'
import type { GenerationJob } from '@/types/domain'

export function ExternalReviewPage() {
  const [content, setContent] = useState('')
  const [scoringPreset, setScoringPreset] = useState('standard')
  const [checkMode, setCheckMode] = useState<'standard' | 'values-risk' | 'full'>('standard')
  const [file, setFile] = useState<File | null>(null)
  const [job, setJob] = useState<GenerationJob | null>(null)

  const mutation = useMutation({
    mutationFn: async () => {
      const commandId = createCommandId('external_review')
      if (file) {
        const form = new FormData()
        form.append('command_id', commandId)
        form.append('scoring_preset', scoringPreset)
        form.append('check_mode', checkMode)
        form.append('file', file)
        return dramaApi.createExternalScriptReview(form)
      }
      return dramaApi.createExternalScriptReview({
        command_id: commandId,
        scoring_preset: scoringPreset,
        check_mode: checkMode,
        script_content: content,
      })
    },
    onSuccess: (result) => {
      setJob(result)
    },
  })

  return (
    <PageShell
      title="外部剧本评测"
      description="上传或粘贴外部剧本，并行运行评分官与合规官"
      width="narrow"
    >
      <form
        className="sf-panel space-y-4 p-5"
        onSubmit={(e) => {
          e.preventDefault()
          mutation.mutate()
        }}
      >
        {mutation.isError ? <ErrorBanner message={formatApiError(mutation.error)} /> : null}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="sf-label">评分预设</label>
            <select
              className="sf-control"
              value={scoringPreset}
              onChange={(e) => setScoringPreset(e.target.value)}
            >
              <option value="standard">standard</option>
              <option value="strict">strict</option>
              <option value="relaxed">relaxed</option>
              <option value="rhythm_first">rhythm_first</option>
            </select>
          </div>
          <div>
            <label className="sf-label">合规模式</label>
            <select
              className="sf-control"
              value={checkMode}
              onChange={(e) => setCheckMode(e.target.value as typeof checkMode)}
            >
              <option value="standard">standard</option>
              <option value="values-risk">values-risk</option>
              <option value="full">full</option>
            </select>
          </div>
        </div>

        <div>
          <label className="sf-label">上传文件（txt / md / json）</label>
          <input
            type="file"
            accept=".txt,.md,.json,text/plain,text/markdown,application/json"
            className="block w-full text-sm text-ink-muted"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>

        <div>
          <label className="sf-label">或粘贴正文</label>
          <textarea
            className="sf-control min-h-48"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="粘贴外部剧本文本…"
            disabled={Boolean(file)}
          />
        </div>

        <Button
          type="submit"
          variant="action"
          loading={mutation.isPending}
          disabled={!file && !content.trim()}
        >
          开始评测
        </Button>
      </form>

      {job ? (
        <div className="mt-6">
          <GenerationJobPanel projectId={null} job={job} />
        </div>
      ) : null}
    </PageShell>
  )
}
