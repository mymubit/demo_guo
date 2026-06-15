import { useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'

export function useSubmitGuard({ minInterval = 800, onError, shouldThrow = false } = {}) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const isSubmittingRef = useRef(false)
  const lastSubmitAtRef = useRef(0)

  const runSubmit = useCallback(
    async (task) => {
      const now = Date.now()
      if (isSubmittingRef.current || now - lastSubmitAtRef.current < minInterval) return null

      isSubmittingRef.current = true
      lastSubmitAtRef.current = now
      setIsSubmitting(true)

      try {
        return await task()
      } catch (error) {
        if (onError) onError(error)
        else toast.error(error.message || '提交失败，请稍后重试')
        if (shouldThrow) throw error
        return null
      } finally {
        isSubmittingRef.current = false
        setIsSubmitting(false)
      }
    },
    [minInterval, onError, shouldThrow],
  )

  return { isSubmitting, runSubmit }
}
