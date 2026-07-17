import { Link } from 'react-router-dom'
import { diagnoseGenerationFailure, type GenerationTrouble } from '@/utils/generationDiagnostics'
import { cn } from '@/utils/cn'

export function GenerationTroubleCard({
  message,
  status,
  context,
  className,
}: {
  message?: string | null
  status?: string | null
  context?: 'workbench' | 'external_review'
  className?: string
}) {
  const trouble = diagnoseGenerationFailure(message, { status, context })
  if (!trouble) return null
  return <TroubleBody trouble={trouble} className={className} />
}

function TroubleBody({
  trouble,
  className,
}: {
  trouble: GenerationTrouble
  className?: string
}) {
  const isWarn =
    trouble.kind === 'llm_disabled' ||
    trouble.kind === 'llm_misconfigured' ||
    trouble.kind === 'llm_openai_overseas'

  return (
    <div
      role="alert"
      className={cn(
        'rounded-lg border px-4 py-3 text-sm',
        isWarn
          ? 'border-amber-200 bg-amber-50 text-amber-950'
          : 'border-red-200 bg-red-50 text-red-900',
        className,
      )}
    >
      <p className="font-medium">{trouble.title}</p>
      <p className="mt-1 opacity-90">{trouble.summary}</p>
      <ol className="mt-2 list-decimal space-y-1 pl-5 opacity-90">
        {trouble.steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      {trouble.showModelHubLink ? (
        <p className="mt-3">
          <Link
            to="/admin/model"
            className="font-medium text-action underline underline-offset-2 hover:text-action-hover"
          >
            前往模型管理 →
          </Link>
        </p>
      ) : null}
      {trouble.raw && trouble.raw !== trouble.summary ? (
        <details className="mt-2 opacity-70">
          <summary className="cursor-pointer text-xs">查看原始错误</summary>
          <pre className="mt-1 whitespace-pre-wrap break-all text-xs">{trouble.raw}</pre>
        </details>
      ) : null}
    </div>
  )
}
