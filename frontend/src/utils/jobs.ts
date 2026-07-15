import type { GenerationJob } from '@/types/domain'

export function isTerminalJobStatus(status: GenerationJob['status']): boolean {
  return status === 'completed' || status === 'failed' || status === 'disabled'
}

/** Only completed counts as success — failed/disabled must not trigger success handlers. */
export function isSuccessfulJob(status: GenerationJob['status']): boolean {
  return status === 'completed'
}
