import { useState, type FormEvent } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MarkdownPreview } from '@/components/MarkdownPreview'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { formatApiError } from '@/services/errors'
import { getKnowledgeDoc, listKnowledge } from '@/services/v3/knowledge'
import { cn } from '@/utils/cn'

const KNOWLEDGE_LIST_KEY = ['v3', 'knowledge', 'list'] as const

export function KnowledgePage() {
  const [draftQ, setDraftQ] = useState('')
  const [q, setQ] = useState('')
  const [selectedPath, setSelectedPath] = useState<string | null>(null)

  const listQuery = useQuery({
    queryKey: [...KNOWLEDGE_LIST_KEY, { q }],
    queryFn: () => listKnowledge(q ? { q } : undefined),
  })

  const docQuery = useQuery({
    queryKey: ['v3', 'knowledge', 'doc', selectedPath],
    queryFn: () => getKnowledgeDoc(selectedPath as string),
    enabled: Boolean(selectedPath),
  })

  const handleSearch = (event: FormEvent) => {
    event.preventDefault()
    setQ(draftQ.trim())
  }

  const items = listQuery.data?.items ?? []

  return (
    <PageShell title="知识库" description="只读浏览 drama-skills 知识文档，支持关键词检索。">
      <form className="mb-5 flex flex-wrap items-end gap-3" onSubmit={handleSearch}>
        <label className="min-w-[16rem] flex-1 space-y-1.5 text-sm font-medium text-ink">
          搜索
          <Input
            value={draftQ}
            onChange={(e) => setDraftQ(e.target.value)}
            placeholder="按路径、标题或摘要检索"
            aria-label="知识库搜索"
          />
        </label>
        <Button type="submit" variant="secondary">
          搜索
        </Button>
      </form>

      {listQuery.isLoading ? <p className="text-sm text-ink-muted">正在加载知识索引…</p> : null}
      {listQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(listQuery.error)}</p>
      ) : null}

      {listQuery.isSuccess ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,18rem)_minmax(0,1fr)]">
          <aside className="sf-panel max-h-[70vh] overflow-y-auto p-2">
            {items.length === 0 ? (
              <p className="p-3 text-sm text-ink-muted">无匹配文档</p>
            ) : (
              <ul className="space-y-1">
                {items.map((item) => {
                  const active = selectedPath === item.path
                  return (
                    <li key={item.path}>
                      <button
                        type="button"
                        data-testid={`knowledge-item-${item.path}`}
                        className={cn(
                          'w-full rounded-md px-3 py-2 text-left text-sm transition',
                          active
                            ? 'bg-action/10 text-action'
                            : 'text-ink hover:bg-canvas-muted',
                        )}
                        onClick={() => setSelectedPath(item.path)}
                      >
                        <span className="block font-medium">{item.title}</span>
                        <span className="mt-0.5 block truncate text-xs text-ink-faint">
                          {item.path}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </aside>

          <section className="sf-panel min-h-[20rem] p-4">
            {!selectedPath ? (
              <p className="text-sm text-ink-muted">点击左侧文档查看正文预览</p>
            ) : null}
            {selectedPath && docQuery.isLoading ? (
              <p className="text-sm text-ink-muted">正在加载文档…</p>
            ) : null}
            {selectedPath && docQuery.isError ? (
              <p className="text-sm text-danger">{formatApiError(docQuery.error)}</p>
            ) : null}
            {docQuery.isSuccess ? (
              <div>
                <h2 className="text-base font-semibold text-ink">{docQuery.data.title}</h2>
                <p className="mt-1 text-xs text-ink-faint">{docQuery.data.path}</p>
                <MarkdownPreview
                  data-testid="knowledge-doc-preview"
                  content={docQuery.data.content}
                  className="mt-4 max-h-[60vh] overflow-auto rounded-md border border-border bg-canvas p-4"
                />
              </div>
            ) : null}
          </section>
        </div>
      ) : null}
    </PageShell>
  )
}
