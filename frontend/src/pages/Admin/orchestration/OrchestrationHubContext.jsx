import { createContext, useContext } from 'react'

export const OrchestrationHubContext = createContext(null)

export function useOrchestrationHubContext() {
  return useContext(OrchestrationHubContext)
}
