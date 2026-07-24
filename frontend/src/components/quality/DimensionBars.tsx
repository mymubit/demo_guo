import {
  QUALITY_DIMENSION_LABEL_ZH,
  qualityDimensionLabelZh,
} from '@/utils/reportLabels'

const DIMENSION_KEYS = Object.keys(QUALITY_DIMENSION_LABEL_ZH)

function readDimensionScore(dimensions: unknown, key: string): number | null {
  if (!dimensions || typeof dimensions !== 'object' || Array.isArray(dimensions)) {
    return null
  }
  const dim = (dimensions as Record<string, unknown>)[key]
  if (typeof dim === 'number' && Number.isFinite(dim)) return dim
  if (!dim || typeof dim !== 'object' || Array.isArray(dim)) return null
  const score = (dim as Record<string, unknown>).score
  return typeof score === 'number' && Number.isFinite(score) ? score : null
}

interface DimensionBarsProps {
  dimensions: unknown
}

/** 十维质量评分条（CSS），维名中文来自 reportLabels。 */
export function DimensionBars({ dimensions }: DimensionBarsProps) {
  return (
    <div className="space-y-4">
      {DIMENSION_KEYS.map((key) => {
        const score = readDimensionScore(dimensions, key)
        const width = score == null ? 0 : Math.min(100, Math.max(0, score))
        return (
          <div key={key}>
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-medium text-ink">{qualityDimensionLabelZh(key)}</span>
              <span className="tabular-nums text-ink-muted">
                {score == null ? '—' : `${Math.round(score)} 分`}
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-sm bg-canvas-muted">
              <div
                className="h-full bg-action transition-[width]"
                style={{ width: `${width}%` }}
                data-testid={`dimension-bar-${key}`}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
