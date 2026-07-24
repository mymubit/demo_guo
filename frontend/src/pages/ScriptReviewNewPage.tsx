import { useMemo, useState, type FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { formatApiError } from '@/services/errors'
import { createScriptReview, createScriptReviewUpload } from '@/services/v3/reviews'
import { cn } from '@/utils/cn'

type Tab = 'paste' | 'upload'

export function ScriptReviewNewPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const prefilledProjectId = (params.get('project_id') || '').trim()

  const [tab, setTab] = useState<Tab>('paste')
  const [title, setTitle] = useState('')
  const [scriptText, setScriptText] = useState('')
  const [projectId, setProjectId] = useState(prefilledProjectId)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: async () => {
      if (tab === 'paste') {
        return createScriptReview({
          title: title.trim() || undefined,
          script_text: scriptText,
          project_id: projectId.trim() || null,
        })
      }
      if (!file) throw new Error('请选择 .txt 或 .md 文件')
      const form = new FormData()
      form.append('file', file)
      if (title.trim()) form.append('title', title.trim())
      if (projectId.trim()) form.append('project_id', projectId.trim())
      return createScriptReviewUpload(form)
    },
    onSuccess: (data) => {
      navigate(`/reviews/${data.id}`, { replace: true })
    },
    onError: (err) => setError(formatApiError(err)),
  })

  const canSubmit = useMemo(() => {
    if (createMutation.isPending) return false
    if (tab === 'paste') return scriptText.trim().length > 0
    return Boolean(file)
  }, [createMutation.isPending, tab, scriptText, file])

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    createMutation.mutate()
  }

  return (
    <PageShell title="新建剧本评审" description="粘贴全文或上传 .txt / .md，可选关联现有项目。">
      <div className="mb-4 flex gap-2">
        <Button
          type="button"
          variant={tab === 'paste' ? 'action' : 'secondary'}
          onClick={() => setTab('paste')}
          data-testid="tab-paste"
        >
          粘贴
        </Button>
        <Button
          type="button"
          variant={tab === 'upload' ? 'action' : 'secondary'}
          onClick={() => setTab('upload')}
          data-testid="tab-upload"
        >
          上传
        </Button>
      </div>

      <form className="sf-panel max-w-3xl space-y-4 p-5" onSubmit={handleSubmit}>
        <label className="block space-y-1.5 text-sm font-medium text-ink">
          标题（可选）
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="默认取首行或文件名"
          />
        </label>

        <label className="block space-y-1.5 text-sm font-medium text-ink">
          关联项目 ID（可选）
          <Input
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            placeholder="从质检页跳转时会自动预填"
            data-testid="project-id-input"
          />
        </label>

        {tab === 'paste' ? (
          <label className="block space-y-1.5 text-sm font-medium text-ink">
            剧本正文
            <textarea
              className={cn(
                'min-h-[16rem] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm',
                'shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring',
              )}
              value={scriptText}
              onChange={(e) => setScriptText(e.target.value)}
              placeholder="粘贴纯文本或 Markdown 剧本…"
              data-testid="script-text-input"
            />
          </label>
        ) : (
          <label className="block space-y-1.5 text-sm font-medium text-ink">
            上传文件（.txt / .md，≤2MB）
            <Input
              type="file"
              accept=".txt,.md,text/plain,text/markdown"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              data-testid="script-file-input"
            />
          </label>
        )}

        {error ? <p className="text-sm text-danger">{error}</p> : null}

        <Button type="submit" disabled={!canSubmit} data-testid="create-review-submit">
          {createMutation.isPending ? '创建中…' : '创建评审'}
        </Button>
      </form>
    </PageShell>
  )
}
