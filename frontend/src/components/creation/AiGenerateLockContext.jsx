import { createContext, useCallback, useContext, useState } from 'react'
import { toast } from 'sonner'

const AiGenerateLockContext = createContext(null)

/** 创作页全局：同一时间只允许一个字段 AI 请求，避免并发覆盖/丢结果 */
export function AiGenerateLockProvider({ children }) {
  const [busy, setBusy] = useState(false)

  const runLocked = useCallback(async (fn) => {
    if (busy) {
      toast.message('请等待当前 AI 生成完成后再试')
      return null
    }
    setBusy(true)
    try {
      return await fn()
    } finally {
      setBusy(false)
    }
  }, [busy])

  return (
    <AiGenerateLockContext.Provider value={{ busy, runLocked }}>
      {children}
    </AiGenerateLockContext.Provider>
  )
}

export function useAiGenerateLock() {
  return useContext(AiGenerateLockContext)
}
