import { useCallback, useEffect, useState } from 'react'
import { admin } from '@/services/api'
import { perMillionToPerThousand, perThousandToPerMillion } from '@/utils/llmPricingUnits'

export function hasSavedCatalogPricing(row) {
  return row?.input_price_per_million != null || row?.output_price_per_million != null
}

export function useCatalogPricing(catalog, { onMessage, onUpdated } = {}) {
  const [drafts, setDrafts] = useState({})
  const [savingId, setSavingId] = useState('')

  useEffect(() => {
    const next = {}
    for (const row of catalog) {
      next[row.id] = {
        input_price_per_thousand:
          row.input_price_per_million != null && row.input_price_per_million !== ''
            ? perMillionToPerThousand(row.input_price_per_million)
            : '',
        output_price_per_thousand:
          row.output_price_per_million != null && row.output_price_per_million !== ''
            ? perMillionToPerThousand(row.output_price_per_million)
            : '',
      }
    }
    setDrafts(next)
  }, [catalog])

  const patchDraft = useCallback((id, field, value) => {
    setDrafts((prev) => ({
      ...prev,
      [id]: { ...prev[id], [field]: value },
    }))
  }, [])

  const saveRow = useCallback(
    async (row) => {
      const draft = drafts[row.id]
      if (!draft) return
      setSavingId(row.id)
      try {
        const data = await admin.updateLlmCatalog(row.id, {
          input_price_per_million: draft.input_price_per_thousand
            ? perThousandToPerMillion(draft.input_price_per_thousand)
            : null,
          output_price_per_million: draft.output_price_per_thousand
            ? perThousandToPerMillion(draft.output_price_per_thousand)
            : null,
        })
        onMessage?.(`已保存「${row.name}」Token 单价`)
        onUpdated?.(data)
      } catch (err) {
        onMessage?.(err.message || '保存单价失败', 'error')
      } finally {
        setSavingId('')
      }
    },
    [drafts, onMessage, onUpdated],
  )

  return { drafts, patchDraft, saveRow, savingId }
}
