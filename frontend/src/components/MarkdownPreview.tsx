import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/utils/cn'

const markdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="mb-4 text-2xl font-semibold tracking-tight text-ink">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-3 mt-6 text-xl font-semibold text-ink">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-2 mt-5 text-lg font-semibold text-ink">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="mb-2 mt-4 text-base font-semibold text-ink">{children}</h4>
  ),
  p: ({ children }) => <p className="mb-3 leading-relaxed text-ink">{children}</p>,
  ul: ({ children }) => (
    <ul className="mb-3 list-disc space-y-1.5 pl-5 text-ink">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-3 list-decimal space-y-1.5 pl-5 text-ink">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="mb-3 border-l-2 border-action/50 pl-3 text-ink-muted">
      {children}
    </blockquote>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      className="text-action underline-offset-2 hover:underline"
      target="_blank"
      rel="noreferrer"
    >
      {children}
    </a>
  ),
  code: ({ className, children }) => {
    const isBlock = Boolean(className)
    if (isBlock) {
      return (
        <code className="block overflow-x-auto rounded-md bg-canvas-muted p-3 font-mono text-xs text-ink">
          {children}
        </code>
      )
    }
    return (
      <code className="rounded bg-canvas-muted px-1 py-0.5 font-mono text-[0.85em] text-ink">
        {children}
      </code>
    )
  },
  pre: ({ children }) => <pre className="mb-3 overflow-x-auto">{children}</pre>,
  hr: () => <hr className="my-6 border-border" />,
  table: ({ children }) => (
    <div className="mb-3 overflow-x-auto">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-border bg-canvas-muted px-2 py-1.5 text-left font-medium">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border border-border px-2 py-1.5 align-top">{children}</td>
  ),
  input: ({ checked, ...props }) => (
    <input
      {...props}
      type="checkbox"
      checked={Boolean(checked)}
      readOnly
      className="mr-2 align-middle"
    />
  ),
}

interface MarkdownPreviewProps {
  content: string
  className?: string
  'data-testid'?: string
}

/** 只读 Markdown 渲染（GFM：任务列表 / 表格等） */
export function MarkdownPreview({
  content,
  className,
  'data-testid': testId,
}: MarkdownPreviewProps) {
  return (
    <div
      data-testid={testId}
      className={cn('max-w-none text-sm text-ink', className)}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
